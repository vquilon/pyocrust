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

pub use oar_structure::{create_oar_structure_engine, OarStructureEngine};
pub use oar_text::{create_oar_text_engine, OarTextEngine};

/// Factoría por nombre de preset.
///
/// `DESIGN.md` §3.1 exige dos backends: `pp_ocrv6` (texto) y `pp_structurev3`
/// (estructura). Los nombres son estables y coinciden con `ModelSpec::as_str`.
pub fn create_backend(name: &str) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    match name {
        "pp_ocrv6" => Ok(Box::new(OarTextEngine::new())),
        "pp_structurev3" => Ok(Box::new(OarStructureEngine::new())),
        "indra" => Ok(Box::new(oar_indra::OarIndraEngine::default())),
        _ => Err(OcrError::InvalidInput {
            message: format!(
                "unknown preset '{name}'. Expected one of: pp_ocrv6, pp_structurev3, indra"
            ),
        }),
    }
}

/// Crea una factoría de motores OCR por `ModelSpec`.
///
/// `ort_session` es la configuración de sesión ya resuelta por
/// `core::device::resolve_device`: fija qué EP corre el pipeline (CPU por
/// defecto). Sin ella los builders no fijan EP y ONNX Runtime cae a CPU.
pub fn create_engine(
    spec: &ModelSpec,
    paths: &ModelPaths,
    ort_session: &OrtSessionConfig,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    match spec {
        ModelSpec::PpOcrV6(_) => Ok(Box::new(create_oar_text_engine(paths, ort_session.clone())?)),
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
        let engine = create_engine(&spec, &paths, &OrtSessionConfig::new());
        assert!(matches!(engine, Err(OcrError::ModelLoad { .. })));
    }

    #[test]
    fn create_engine_with_model_spec_for_pp_structurev3() {
        let spec = ModelSpec::PpStructureV3;
        let paths = ModelPaths::new(std::path::Path::new("/nonexistent/models"), &spec);
        let engine = create_engine(&spec, &paths, &OrtSessionConfig::new());
        assert!(matches!(engine, Err(OcrError::ModelLoad { .. })));
    }
}