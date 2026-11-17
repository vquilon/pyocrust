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

use std::path::{Path, PathBuf};
use std::sync::Arc;

use crate::core::{
    error::OcrError,
    types::{BoundingBox, ModelPaths, ModelSpec, OcrOutput, OcrResult, OcrSize, TextRegion},
    OcrEngineBackend,
};
use oar_ocr::core::config::OrtSessionConfig;
use oar_ocr::processors::LimitType;

/// Overrides opcionales del `TextDetectionConfig` del detector DB.
///
/// Todo `None` = comportamiento histórico: los umbrales duros de
/// `OarTextEngine::load_model` (0.2 / 0.45 (0.4 tiny) / 1.4 / 3000) más los
/// defaults "general" que aplica el adaptador de detección de oar-ocr
/// (`limit_side_len=960, limit_type=Max, max_side_limit=4000`). Ese default
/// reescala una página de 7000x5000 a ~960 px de lado mayor (~7x menos
/// resolución); con `limit_type=Min, limit_side_len=64` el detector la ve a
/// resolución nativa (que es lo que hace PaddleOCR 3.x por defecto).
#[derive(Debug, Clone, Default, PartialEq)]
pub struct TextDetectionOptions {
    /// `text_det_limit_side_len`: lado objetivo del reescalado.
    pub limit_side_len: Option<u32>,
    /// `text_det_limit_type`: `Min` (limita el lado corto) o `Max` (el largo).
    pub limit_type: Option<LimitType>,
    /// `text_det_max_side_len`: tope anti-OOM del lado largo.
    pub max_side_len: Option<u32>,
    /// `text_det_thresh` (`score_threshold`).
    pub score_threshold: Option<f32>,
    /// `text_det_box_thresh` (`box_threshold`).
    pub box_threshold: Option<f32>,
    /// `text_det_unclip_ratio` (`unclip_ratio`).
    pub unclip_ratio: Option<f32>,
    /// `text_det_max_candidates` (`max_candidates`).
    pub max_candidates: Option<usize>,
}

impl TextDetectionOptions {
    /// `self` con los campos no-`None` de `over` pisados.
    ///
    /// Permite que `VeloceOCR.detect_regions` herede los knobs del constructor y
    /// deje que sus propios kwargs los sobrescriban: el significado de `text_det_*`
    /// no puede diferir entre `recognize` y `detect_regions` (§11.2).
    pub fn or(&self, over: &Self) -> Self {
        Self {
            limit_side_len: over.limit_side_len.or(self.limit_side_len),
            limit_type: over.limit_type.clone().or_else(|| self.limit_type.clone()),
            max_side_len: over.max_side_len.or(self.max_side_len),
            score_threshold: over.score_threshold.or(self.score_threshold),
            box_threshold: over.box_threshold.or(self.box_threshold),
            unclip_ratio: over.unclip_ratio.or(self.unclip_ratio),
            max_candidates: over.max_candidates.or(self.max_candidates),
        }
    }

    /// `TextDetectionConfig` efectiva para un tamaño de preset dado.
    ///
    /// Parte del comportamiento actual y solo pisa los campos con `Some`.
    pub fn to_config(&self, size: OcrSize) -> oar_ocr::domain::tasks::TextDetectionConfig {
        let mut config = oar_ocr::domain::tasks::TextDetectionConfig {
            score_threshold: 0.2,
            box_threshold: match size {
                OcrSize::Tiny => 0.4,
                _ => 0.45,
            },
            unclip_ratio: 1.4,
            max_candidates: 3000,
            ..Default::default()
        };
        if let Some(v) = self.limit_side_len {
            config.limit_side_len = Some(v);
        }
        if let Some(v) = self.limit_type.clone() {
            config.limit_type = Some(v);
        }
        if let Some(v) = self.max_side_len {
            config.max_side_len = Some(v);
        }
        if let Some(v) = self.score_threshold {
            config.score_threshold = v;
        }
        if let Some(v) = self.box_threshold {
            config.box_threshold = v;
        }
        if let Some(v) = self.unclip_ratio {
            config.unclip_ratio = v;
        }
        if let Some(v) = self.max_candidates {
            config.max_candidates = v;
        }
        config
    }
}

/// Composicion del pipeline `OAROCR` que pyocrust cablea.
///
/// `Default` (todo `false` y `text_type` `None`) es el comportamiento historico:
/// solo deteccion + reconocimiento. Cada flag enciende un componente que
/// `oar-ocr` ya trae y que necesita sus propios pesos (tareas registradas
/// `document_rectification`, `document_orientation`, `text_line_orientation`);
/// `load_model` los resuelve —y los descarga si faltan— en el mismo root que
/// los artefactos del preset.
#[derive(Debug, Clone, Default)]
pub struct PipelineOptions {
    /// Clasificacion de orientacion de documento (paginas giradas 90/180/270),
    /// antes de detectar.
    pub use_doc_orientation: bool,
    /// Rectificacion UVDoc (paginas curvadas o fotografiadas), antes de detectar.
    pub use_doc_unwarping: bool,
    /// Orientacion por recorte de linea (lineas boca abajo), tras detectar.
    pub use_textline_orientation: bool,
    /// `OAROCRBuilder::text_type`: `"general"` | `"table"` | `"seal"`. Cambia el
    /// preprocesado del detector y el tipo de caja (`seal` = poligono); `None` =
    /// no fijarlo (equivale a `"general"`).
    pub text_type: Option<String>,
}

/// Ruta del unico artefacto de una tarea de composicion, garantizado en disco.
///
/// El nombre sale del registro (`registry::task_artifacts`), nunca de un literal:
/// renombrar un artefacto no puede desincronizar este punto.
fn component_model(root: &Path, task: &str) -> Result<PathBuf, OcrError> {
    crate::storage::models::ensure_task_models(root, task)?;
    let artifact = crate::storage::registry::task_artifacts(task)
        .and_then(|artifacts| artifacts.first())
        .ok_or_else(|| OcrError::Config {
            message: format!("la tarea '{task}' no tiene artefactos registrados"),
        })?;
    Ok(root.join(artifact.name))
}

/// Función de fábrica para crear un motor de texto.
///
/// `ort_session` fija el execution provider del pipeline (vía
/// `core::device::resolve_device`); el default de la API Python es CPU.
/// `detection` son los overrides del detector DB (`.default()` = comportamiento
/// actual) y `composition` la composicion del pipeline (`.default()` = solo
/// deteccion + reconocimiento). Uso típico:
/// ```rust
/// use pyocrust::engines::create_oar_text_engine;
/// use pyocrust::engines::{PipelineOptions, TextDetectionOptions};
/// use pyocrust::core::types::{ModelPaths, ModelSpec};
/// use oar_ocr::core::config::OrtSessionConfig;
///
/// let paths = ModelPaths::new(&Path::new("/models"), &ModelSpec::PpOcrV6(crate::core::OcrSize::Tiny));
/// let engine = create_oar_text_engine(&paths, OrtSessionConfig::new(), TextDetectionOptions::default(), PipelineOptions::default())?;
/// ```
pub fn create_oar_text_engine(
    paths: &ModelPaths,
    ort_session: OrtSessionConfig,
    detection: TextDetectionOptions,
    composition: PipelineOptions,
) -> Result<OarTextEngine, OcrError> {
    let mut engine = OarTextEngine::new()
        .with_ort_session(ort_session)
        .with_detection_options(detection)
        .with_pipeline_options(composition);
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
    detection: TextDetectionOptions,
    composition: PipelineOptions,
}

impl OarTextEngine {
    /// Crea un backend sin modelo cargado.
    pub fn new() -> Self {
        Self {
            pipeline: None,
            ort_session: None,
            detection: TextDetectionOptions::default(),
            composition: PipelineOptions::default(),
        }
    }

    /// Fija el execution provider que aplicará `load_model` (opt-in).
    pub fn with_ort_session(mut self, config: OrtSessionConfig) -> Self {
        self.ort_session = Some(config);
        self
    }

    /// Fija los overrides del detector DB que aplicará `load_model` (opt-in).
    pub fn with_detection_options(mut self, detection: TextDetectionOptions) -> Self {
        self.detection = detection;
        self
    }

    /// Fija la composicion del pipeline que aplicará `load_model` (opt-in).
    pub fn with_pipeline_options(mut self, composition: PipelineOptions) -> Self {
        self.composition = composition;
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

        let detection_config = self.detection.to_config(size);

        let mut builder = oar_ocr::oarocr::OAROCRBuilder::new(
            &paths.detection_model,
            recognition_model,
            char_dict,
        )
        .text_detection_config(detection_config);

        // Composicion opt-in: los pesos de cada componente viven junto a los del
        // preset (mismo root que la deteccion) y los resuelve `ensure_task_models`
        // (preflight -> descarga -> verificacion), nunca un auto-download ciego.
        let root = paths
            .detection_model
            .parent()
            .unwrap_or_else(|| Path::new("."));
        if self.composition.use_doc_unwarping {
            builder = builder.with_document_image_rectification(component_model(
                root,
                "document_rectification",
            )?);
        }
        if self.composition.use_doc_orientation {
            builder = builder.with_document_image_orientation_classification(component_model(
                root,
                "document_orientation",
            )?);
        }
        if self.composition.use_textline_orientation {
            builder = builder.with_text_line_orientation_classification(component_model(
                root,
                "text_line_orientation",
            )?);
        }
        if let Some(text_type) = &self.composition.text_type {
            builder = builder.text_type(text_type.clone());
        }

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

    #[test]
    fn pipeline_options_default_is_detection_and_recognition_only() {
        let options = PipelineOptions::default();
        assert!(!options.use_doc_orientation);
        assert!(!options.use_doc_unwarping);
        assert!(!options.use_textline_orientation);
        assert_eq!(options.text_type, None, "sin text_type: comporta como general");
    }

    #[test]
    fn detection_options_default_is_todays_behaviour() {
        let tiny = TextDetectionOptions::default().to_config(OcrSize::Tiny);
        assert_eq!(tiny.score_threshold, 0.2);
        assert_eq!(tiny.box_threshold, 0.4);
        assert_eq!(tiny.unclip_ratio, 1.4);
        assert_eq!(tiny.max_candidates, 3000);
        assert_eq!(tiny.limit_side_len, None, "sin knob: el adaptador pone 960/Max");
        assert_eq!(tiny.limit_type, None);
        assert_eq!(tiny.max_side_len, None);
        assert_eq!(
            TextDetectionOptions::default().to_config(OcrSize::Medium).box_threshold,
            0.45
        );
    }

    #[test]
    fn detection_options_override_only_what_is_set() {
        let config = TextDetectionOptions {
            limit_side_len: Some(64),
            limit_type: Some(LimitType::Min),
            ..Default::default()
        }
        .to_config(OcrSize::Medium);
        assert_eq!(config.limit_side_len, Some(64));
        assert_eq!(config.limit_type, Some(LimitType::Min));
        assert_eq!(config.max_side_len, None, "no pisado: sigue el default del adaptador");
        assert_eq!(config.score_threshold, 0.2, "umbral no pisado");
    }

    #[test]
    fn detection_options_or_pisa_solo_los_campos_no_none() {
        let base = TextDetectionOptions {
            limit_side_len: Some(960),
            limit_type: Some(LimitType::Max),
            box_threshold: Some(0.4),
            ..Default::default()
        };
        // Overrides parciales: solo `limit_type` y `unclip_ratio`.
        let over = TextDetectionOptions {
            limit_type: Some(LimitType::Min),
            unclip_ratio: Some(2.0),
            ..Default::default()
        };
        let merged = base.or(&over);
        assert_eq!(merged.limit_type, Some(LimitType::Min), "el override gana");
        assert_eq!(merged.unclip_ratio, Some(2.0));
        assert_eq!(merged.limit_side_len, Some(960), "lo no pisado se hereda");
        assert_eq!(merged.box_threshold, Some(0.4));
        // Sin overrides el resultado es la base.
        assert_eq!(base.or(&TextDetectionOptions::default()), base);
    }
}
