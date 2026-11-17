//! Factoría de backends OCR (`DESIGN.md` §2 y §3.1, ADR-006).
//!
//! Mapea nombres de preset a implementaciones concretas del trait
//! `OcrEngineBackend`. Las implementaciones reales viven en este mismo
//! módulo (`oar_text`, `oar_structure`) para mantener la jerarquía plana
//! (ADR-006).
//!
//! Contrato:
//! - `create_backend(name: &str) -> Box<dyn OcrEngineBackend>`
//! - `name` puede ser `"pp_ocrv6"` o `"pp_structurev3"` (ver `ModelSpec::as_str`).

use crate::core::{ModelPaths, ModelSpec, OcrError};
use oar_ocr::core::config::OrtSessionConfig;

pub use crate::core::OcrEngineBackend;

mod oar_structure;
mod oar_text;
mod oar_indra;
mod vlm;

pub use oar_structure::{create_oar_structure_engine, OarStructureEngine};
pub use oar_text::{create_oar_text_engine, OarTextEngine, PipelineOptions, TextDetectionOptions};
pub use vlm::{ensure_vlm_models, vlm_provider_effective, VlmEngine};

/// Nombres que acepta `create_backend`.
///
/// Sin la feature `vl` no se anuncia `glm_ocr`: un preset que el build no trae
/// no debe aparecer en el mensaje de error (sería un preset fantasma).
const PRESET_NAMES: &str = if cfg!(feature = "vl") {
    "pp_ocrv6, pp_structurev3, indra, glm_ocr"
} else {
    "pp_ocrv6, pp_structurev3, indra"
};

/// Factoría por nombre de preset.
///
/// `DESIGN.md` §3.1 exige dos backends: `pp_ocrv6` (texto) y `pp_structurev3`
/// (estructura). Los nombres son estables y coinciden con `ModelSpec::as_str`.
/// Devuelve motores **sin modelo cargado** (igual que `OarTextEngine::new`).
pub fn create_backend(name: &str) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    match name {
        "pp_ocrv6" => Ok(Box::new(OarTextEngine::new())),
        "pp_structurev3" => Ok(Box::new(OarStructureEngine::new())),
        "indra" => Ok(Box::new(oar_indra::OarIndraEngine::default())),
        #[cfg(feature = "vl")]
        "glm_ocr" => Ok(Box::new(VlmEngine::new(crate::core::VlmModel::GlmOcr))),
        #[cfg(not(feature = "vl"))]
        "glm_ocr" => Err(vlm::requires_vl_error(crate::core::VlmModel::GlmOcr)),
        _ => Err(OcrError::InvalidInput {
            message: format!("unknown preset '{name}'. Expected one of: {PRESET_NAMES}"),
        }),
    }
}

/// Crea una factoría de motores OCR por `ModelSpec`.
///
/// `ort_session` es la configuración de sesión ya resuelta por
/// `core::device::resolve_device`: fija qué EP corre el pipeline (CPU por
/// defecto). Sin ella los builders no fijan EP y ONNX Runtime cae a CPU.
/// `device` es el nombre pedido por el usuario (`cpu`, `cuda`, ...): los presets
/// ONNX lo ignoran (ya viene resuelto en `ort_session`) y el VLM lo usa para
/// elegir su dispositivo de Candle (no enlaza ONNX Runtime).
///
/// `detection` son los overrides del detector DB; solo los consume
/// `PpOcrV6` (`OarTextEngine`), los demás presets lo ignoran. `composition` es la
/// composicion del pipeline (orientacion, unwarping, orientacion de linea,
/// `text_type`) y se ignora igual en los presets que no son `PpOcrV6`.
pub fn create_engine(
    spec: &ModelSpec,
    paths: &ModelPaths,
    ort_session: &OrtSessionConfig,
    device: &str,
    detection: TextDetectionOptions,
    composition: PipelineOptions,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    match spec {
        ModelSpec::PpOcrV6(_) => Ok(Box::new(create_oar_text_engine(
            paths,
            ort_session.clone(),
            detection,
            composition,
        )?)),
        ModelSpec::PpStructureV3 => Ok(Box::new(create_oar_structure_engine(
            paths,
            ort_session.clone(),
        )?)),
        ModelSpec::Indra => {
            let mut engine =
                oar_indra::OarIndraEngine::default().with_ort_session(ort_session.clone());
            engine.load_model(paths)?;
            Ok(Box::new(engine))
        }
        ModelSpec::Vlm(model) => vlm::create_vlm_engine(model, paths, device),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn factory_knows_pp_ocrv6_and_pp_structurev3() {
        let text = create_backend("pp_ocrv6");
        assert!(text.is_ok());

        let structure = create_backend("pp_structurev3");
        assert!(structure.is_ok());
    }

    #[test]
    fn factory_rejects_unknown_preset() {
        match create_backend("unknown") {
            Err(err) => assert!(matches!(err, OcrError::InvalidInput { .. })),
            Ok(_) => panic!("expected error for unknown preset"),
        }
    }

    #[test]
    fn create_engine_with_model_spec_for_pp_ocrv6() {
        use crate::core::OcrSize;
        let spec = ModelSpec::PpOcrV6(OcrSize::Tiny);
        let paths = ModelPaths::new(std::path::Path::new("/nonexistent/models"), &spec);
        let engine = create_engine(&spec, &paths, &OrtSessionConfig::new(), "cpu", TextDetectionOptions::default(), PipelineOptions::default());
        assert!(matches!(engine, Err(OcrError::ModelLoad { .. })));
    }

    #[test]
    fn create_engine_with_model_spec_for_pp_structurev3() {
        let spec = ModelSpec::PpStructureV3;
        let paths = ModelPaths::new(std::path::Path::new("/nonexistent/models"), &spec);
        let engine = create_engine(&spec, &paths, &OrtSessionConfig::new(), "cpu", TextDetectionOptions::default(), PipelineOptions::default());
        assert!(matches!(engine, Err(OcrError::ModelLoad { .. })));
    }

    #[test]
    fn create_engine_for_a_vlm_preset_is_typed_either_way() {
        use crate::core::VlmModel;
        let spec = ModelSpec::Vlm(VlmModel::GlmOcr);
        let paths = ModelPaths::new(std::path::Path::new("/nonexistent/models"), &spec);
        // Con `vl` los checkpoints no están en disco (`ModelLoad`); sin `vl` el
        // preset no existe en este build (`InvalidInput`). Nunca un pánico.
        let err = create_engine(&spec, &paths, &OrtSessionConfig::new(), "cpu", TextDetectionOptions::default(), PipelineOptions::default())
            .err()
            .expect("the VLM preset must fail with a typed error");
        match err {
            OcrError::ModelLoad { .. } => assert!(cfg!(feature = "vl")),
            OcrError::InvalidInput { .. } => assert!(!cfg!(feature = "vl")),
            other => panic!("expected a typed error for the VLM preset, got {other:?}"),
        }
    }

    #[cfg(feature = "vl")]
    #[test]
    fn factory_knows_glm_ocr_only_with_the_vl_feature() {
        assert!(create_backend("glm_ocr").is_ok());
        assert!(PRESET_NAMES.contains("glm_ocr"));
    }

    #[cfg(not(feature = "vl"))]
    #[test]
    fn factory_rejects_glm_ocr_without_the_vl_feature() {
        let err = create_backend("glm_ocr")
            .err()
            .expect("'glm_ocr' must not exist without the `vl` feature");
        assert!(matches!(err, OcrError::InvalidInput { .. }), "{err:?}");

        assert!(!PRESET_NAMES.contains("glm_ocr"), "no preset fantasma: {PRESET_NAMES}");
        let err = create_backend("glm_ocr_typo").err().expect("unknown preset must fail");
        match err {
            OcrError::InvalidInput { message } => assert!(!message.contains("glm_ocr,"), "{message}"),
            other => panic!("expected InvalidInput, got {other:?}"),
        }
    }
}