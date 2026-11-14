//! Backend VLM sobre `oar-ocr-vl` (Candle) — **esqueleto** (tarjeta 01).
//!
//! `ModelSpec::Vlm` sale de la factoría como una implementación más de
//! `OcrEngineBackend`, sin tocar la API pública (ADR-006). `oar-ocr-vl` es un
//! crate **distinto** de `oar-ocr` y no enlaza ONNX Runtime, así que este motor
//! ignora el `OrtSessionConfig` que sí reciben los demás.
//!
//! Alcance de esta tarjeta: **selección y andamiaje**. `load_model` valida que
//! los dos checkpoints (el VLM y el detector PP-DocLayout que compone) estén en
//! el root resuelto; la carga real con Candle y la inferencia página → Markdown
//! son la tarjeta 02. `recognize` devuelve un error **tipado**
//! (`OcrError::Inference`), nunca un pánico ni un resultado vacío que se pueda
//! confundir con una inferencia real.
//!
//! # Ciclo de vida
//! - Construcción: `VlmEngine::new(VlmModel)`
//! - Carga: `load_model(&ModelPaths)` valida los dos directorios de checkpoint
//! - Inferencia: `recognize(&[u8])` — tarjeta 02

use std::path::{Path, PathBuf};

use crate::core::error::OcrError;
use crate::core::types::{ModelPaths, ModelSpec, OcrOutput, VlmModel};
use crate::core::OcrEngineBackend;

/// Error tipado de un preset VLM pedido en un build sin la feature `vl`.
///
/// Sólo existe en los builds sin `vl`: con la feature el preset es real y no hay
/// nada que rechazar. Se usa en las dos factorías para que el preset no exista
/// de forma honesta: ni se construye un motor vacío ni se anuncia como soportado.
#[cfg(not(feature = "vl"))]
pub fn requires_vl_error(model: VlmModel) -> OcrError {
    OcrError::InvalidInput {
        message: format!(
            "preset '{}' requires the `vl` feature (Candle / oar-ocr-vl); rebuild with \
             `maturin develop --features vl`",
            model.as_str()
        ),
    }
}

/// Factoría del motor VLM por `ModelPaths`.
///
/// Con la feature `vl` construye el esqueleto y valida los checkpoints; sin
/// ella devuelve `OcrError::InvalidInput`.
#[cfg(feature = "vl")]
pub fn create_vlm_engine(
    model: &VlmModel,
    paths: &ModelPaths,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    let mut engine = VlmEngine::new(*model);
    engine.load_model(paths)?;
    Ok(Box::new(engine))
}

/// Sin la feature `vl` no hay crate VLM que enlazar: error tipado, nunca un
/// motor que no puede cargar nada.
#[cfg(not(feature = "vl"))]
pub fn create_vlm_engine(
    model: &VlmModel,
    _paths: &ModelPaths,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    Err(requires_vl_error(*model))
}

/// Motor VLM: guarda el modelo y los dos directorios de checkpoint resueltos.
///
/// No guarda el `AnyPageParser` de Candle todavía: cargarlo es la tarjeta 02.
#[derive(Debug)]
pub struct VlmEngine {
    model: VlmModel,
    /// Directorio del checkpoint del VLM, validado en `load_model`.
    model_dir: Option<PathBuf>,
    /// Directorio del detector PP-DocLayout que el VLM compone.
    layout_dir: Option<PathBuf>,
}

impl VlmEngine {
    /// Crea el motor sin checkpoints cargados (`load_model` los resuelve).
    pub fn new(model: VlmModel) -> Self {
        Self {
            model,
            model_dir: None,
            layout_dir: None,
        }
    }

    /// Modelo de `oar-ocr-vl` al que corresponde el preset del wrapper.
    ///
    /// Es la única costura con el crate VLM en esta tarjeta (el parser de Candle
    /// se construye con este valor en la tarjeta 02). Un test comprueba que los
    /// dos lados no se desalinean, y de paso que la feature `vl` enlaza el crate
    /// de verdad.
    #[cfg(feature = "vl")]
    pub fn oar_ocr_vl_model(model: VlmModel) -> oar_ocr_vl::AnyPageParserModel {
        match model {
            VlmModel::GlmOcr => oar_ocr_vl::AnyPageParserModel::GlmOcr,
        }
    }

    /// Modelo VLM que sirve este motor.
    pub fn model(&self) -> VlmModel {
        self.model
    }

    /// Directorios de checkpoint resueltos (VLM, PP-DocLayout), si se cargaron.
    pub fn checkpoint_dirs(&self) -> (Option<&Path>, Option<&Path>) {
        (self.model_dir.as_deref(), self.layout_dir.as_deref())
    }
}

impl OcrEngineBackend for VlmEngine {
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError> {
        if paths.spec != ModelSpec::Vlm(self.model) {
            return Err(OcrError::InvalidInput {
                message: format!(
                    "preset '{:?}' is not supported by VlmEngine. Expected Vlm({:?})",
                    paths.spec, self.model
                ),
            });
        }

        let model_dir = &paths.detection_model;
        let layout_dir =
            paths
                .layout_detection_model
                .as_ref()
                .ok_or_else(|| OcrError::ModelLoad {
                    model_path: self.model.layout_repo().into(),
                    reason: "missing PP-DocLayout directory in ModelPaths".into(),
                })?;

        for dir in [model_dir, layout_dir] {
            if !dir.is_dir() {
                return Err(OcrError::ModelLoad {
                    model_path: dir.display().to_string(),
                    reason: format!(
                        "checkpoint for '{}' is not on disk; `oar-ocr-vl` downloads it into \
                         $OAR_HOME/models/<org>/<name>/<commit> (tarjeta 02)",
                        self.model.as_str()
                    ),
                });
            }
        }

        self.model_dir = Some(model_dir.clone());
        self.layout_dir = Some(layout_dir.clone());
        Ok(())
    }

    /// Todavía no implementado: error tipado, nunca un resultado vacío.
    fn recognize(&self, _image: &[u8]) -> Result<OcrOutput, OcrError> {
        Err(OcrError::Inference {
            message: format!(
                "VLM inference for preset '{}' is not wired yet (tarjeta 02); the Candle \
                 weights and the page parser land there",
                self.model.as_str()
            ),
            source: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn engine_rejects_a_non_vlm_preset() {
        let mut engine = VlmEngine::new(VlmModel::GlmOcr);
        let paths = ModelPaths::new(Path::new("/nonexistent"), &ModelSpec::Indra);
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::InvalidInput { .. }));
    }

    #[test]
    fn engine_reports_missing_checkpoint_directories() {
        let mut engine = VlmEngine::new(VlmModel::GlmOcr);
        let paths = ModelPaths::new(Path::new("/nonexistent"), &ModelSpec::Vlm(VlmModel::GlmOcr));
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::ModelLoad { .. }), "{err:?}");
        assert!(engine.checkpoint_dirs().0.is_none());
    }

    #[test]
    fn recognize_is_a_typed_error_and_never_panics() {
        let engine = VlmEngine::new(VlmModel::GlmOcr);
        let err = engine.recognize(b"not an image").unwrap_err();
        assert!(matches!(err, OcrError::Inference { .. }), "{err:?}");
    }

    /// El repo del wrapper y el de `oar-ocr-vl` deben coincidir: si el crate
    /// renombra el modelo, este test lo delata.
    #[cfg(feature = "vl")]
    #[test]
    fn checkpoint_repo_matches_oar_ocr_vl() {
        for model in [VlmModel::GlmOcr] {
            assert_eq!(
                model.checkpoint_repo(),
                VlmEngine::oar_ocr_vl_model(model).as_str()
            );
        }
    }
}
