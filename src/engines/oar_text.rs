//! Adaptador `OAROCRBuilder` para PP-OCRv6 (`DESIGN.md` §2 y §3.1).
//!
//! Implementa `OcrEngineBackend` para el preset `ModelSpec::PpOcrV6`
//! (tamaños `Tiny`, `Small`, `Medium`).
//!
//! El pipeline se construye **una sola vez** en `load_model` y queda residente
//! (ADR-002). La inferencia (`recognize`) decodifica la imagen a RGB, aplica
//! preprocesamiento puro (escalado nativo de `oar-ocr`) y invoca el pipeline
//! con GIL liberado (ADR-003).
//!
//! # Ciclo de vida
//! - Construcción: `new()` -> `Box<OarTextEngine>` (trait object)
//! - Carga: `load_model(&ModelPaths)` (3 artefactos: det, rec, dict)
//! - Inferencia: `recognize(&[u8])` (buffer de imagen)
//!
//! # Errores
//! - `OcrError::ModelLoad` si falta un artefacto o la carga falla.
//! - `OcrError::ImageDecode` si el buffer no es una imagen válida.
//! - `OcrError::Inference` si el pipeline falla en la detección o el reconocimiento.

use std::sync::Arc;

use crate::core::{
    error::OcrError,
    types::{BoundingBox, ModelPaths, ModelSpec, OcrOutput, OcrResult, OcrSize, TextRegion},
    OcrEngineBackend,
};
use oar_ocr::core::config::OrtSessionConfig;

/// Función de fábrica para crear un motor de texto.
///
/// `ort_session` fija el execution provider del pipeline (vía
/// `core::device::resolve_device`); el default de la API Python es CPU.
/// Uso típico:
/// ```rust
/// use pyocrust::engines::create_oar_text_engine;
/// use pyocrust::core::types::{ModelPaths, ModelSpec};
/// use oar_ocr::core::config::OrtSessionConfig;
///
/// let paths = ModelPaths::new(&Path::new("/models"), &ModelSpec::PpOcrV6(crate::core::OcrSize::Tiny));
/// let engine = create_oar_text_engine(&paths, OrtSessionConfig::new())?;
/// ```
pub fn create_oar_text_engine(
    paths: &ModelPaths,
    ort_session: OrtSessionConfig,
) -> Result<OarTextEngine, OcrError> {
    let mut engine = OarTextEngine::new().with_ort_session(ort_session);
    engine.load_model(paths)?;
    Ok(engine)
}

/// Backend OAR para texto (PP-OCRv6).
///
/// El pipeline es residente: una vez cargado con `load_model`, el `OAROCR`
/// interno no se recarga en llamadas posteriores. El GIL se libera durante
/// la inferencia (ADR-003).
#[derive(Debug)]
pub struct OarTextEngine {
    pipeline: Option<Arc<oar_ocr::oarocr::OAROCR>>,
    ort_session: Option<OrtSessionConfig>,
}

impl OarTextEngine {
    /// Crea un backend sin modelo cargado.
    pub fn new() -> Self {
        Self {
            pipeline: None,
            ort_session: None,
        }
    }

    /// Fija el execution provider que aplicará `load_model` (opt-in).
    pub fn with_ort_session(mut self, config: OrtSessionConfig) -> Self {
        self.ort_session = Some(config);
        self
    }

    /// Crea un backend y carga el modelo en una sola operación.
    pub fn new_with_model(paths: &ModelPaths) -> Result<Self, OcrError> {
        let mut engine = Self::new();
        engine.load_model(paths)?;
        Ok(engine)
    }
}

impl Default for OarTextEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl OcrEngineBackend for OarTextEngine {
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError> {
        let size = match paths.spec {
            ModelSpec::PpOcrV6(size) => size,
            _ => {
                return Err(OcrError::InvalidInput {
                    message: format!(
                        "preset '{:?}' is not supported by OarTextEngine. Expected PpOcrV6",
                        paths.spec
                    ),
                });
            }
        };

        let recognition_model = paths
            .recognition_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "recognition_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let char_dict = paths
            .character_dict
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "character_dict".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let detection_config = oar_ocr::domain::tasks::TextDetectionConfig {
            score_threshold: 0.2,
            box_threshold: match size {
                OcrSize::Tiny => 0.4,
                _ => 0.45,
            },
            unclip_ratio: 1.4,
            max_candidates: 3000,
            ..Default::default()
        };

        let builder = oar_ocr::oarocr::OAROCRBuilder::new(
            &paths.detection_model,
            recognition_model,
            char_dict,
        )
        .text_detection_config(detection_config);

        let builder = match &self.ort_session {
            Some(ort_session) => builder.ort_session(ort_session.clone()),
            None => builder,
        };

        let pipeline = builder.build().map_err(|e| OcrError::ModelLoad {
            model_path: paths.detection_model.display().to_string(),
            reason: e.to_string(),
        })?;

        self.pipeline = Some(Arc::new(pipeline));
        Ok(())
    }

    fn recognize(&self, image_bytes: &[u8]) -> Result<OcrOutput, OcrError> {
        let pipeline = self
            .pipeline
            .as_ref()
            .ok_or_else(|| OcrError::InvalidInput {
                message: "model not loaded".into(),
            })?;

        let image = image::load_from_memory(image_bytes)
            .map_err(|e| OcrError::ImageDecode {
                message: e.to_string(),
                source: e,
            })?
            .into_rgb8();

        let results = pipeline.predict(vec![image]).map_err(|e| OcrError::Inference {
            message: e.to_string(),
            source: Some(Box::new(e)),
        })?;

        let mut regions = Vec::new();
        if let Some(first) = results.into_iter().next() {
            for region in first.text_regions {
                let text = region.text.as_deref().unwrap_or("").to_string();
                let confidence = region.confidence.unwrap_or(0.0);
                let (x1, y1, x2, y2) = region.bounding_box.aabb();
                regions.push(TextRegion {
                    text,
                    confidence,
                    box_: BoundingBox { x1, y1, x2, y2 },
                });
            }
        }

        Ok(OcrOutput::Text(OcrResult { regions }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn engine_rejects_wrong_preset() {
        let mut engine = OarTextEngine::new();
        let paths = ModelPaths::new(
            std::path::Path::new("/models"),
            &ModelSpec::PpStructureV3,
        );
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::InvalidInput { .. }));
    }

    #[test]
    fn engine_rejects_missing_model_files() {
        let mut engine = OarTextEngine::new();
        let paths = ModelPaths::new(
            std::path::Path::new("/nonexistent"),
            &ModelSpec::PpOcrV6(OcrSize::Tiny),
        );
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::ModelLoad { .. }));
    }
}
