//! Adaptador del backend OAR para PP-StructureV3 (`DESIGN.md` §2 y §3.1).
//!
//! Este módulo implementa el trait `OcrEngineBackend` para el pipeline de
//! estructura documental de `oar-ocr` (PP-StructureV3):
//! - layout detection (`pp-doclayoutv3.onnx`)
//! - clasificación de tablas (`pp-lcnet_x1_0_table_cls.onnx`)
//! - estructura de tablas cableadas (`slanext_wired.onnx`)
//! - estructura de tablas inalámbricas (`slanet_plus.onnx`)
//! - detección de celdas de tablas cableadas (`rt-detr-l_wired_table_cell_det.onnx`)
//! - diccionario de estructura de tablas (`table_structure_dict_ch.txt`)
//! - OCR de texto base (PP-OCRv6 Tiny embebido)
//!
//! Cumple con el riesgo R1 documentado en `DESIGN.md` §5: contrasta la API real
//! de `oar-ocr` 0.10.1 con `OARStructureBuilder`.

use std::sync::Arc;

use crate::core::error::OcrError;
use crate::core::types::{BoundingBox, ModelPaths, ModelSpec, OcrResult, TextRegion};
use crate::core::OcrEngineBackend;

/// Función de fábrica para crear un motor de estructura.
pub fn create_oar_structure_engine(paths: &ModelPaths) -> Result<OarStructureEngine, OcrError> {
    OarStructureEngine::new_with_model(paths)
}

/// Adaptador del backend OAR para PP-StructureV3.
#[derive(Debug)]
pub struct OarStructureEngine {
    pipeline: Option<Arc<oar_ocr::oarocr::OARStructure>>,
}

impl OarStructureEngine {
    /// Crea un backend sin modelo cargado.
    pub fn new() -> Self {
        Self { pipeline: None }
    }

    /// Crea un backend y carga el modelo en una sola operación.
    pub fn new_with_model(paths: &ModelPaths) -> Result<Self, OcrError> {
        let mut engine = Self::new();
        engine.load_model(paths)?;
        Ok(engine)
    }
}

impl Default for OarStructureEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl OcrEngineBackend for OarStructureEngine {
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError> {
        if !matches!(paths.spec, ModelSpec::PpStructureV3) {
            return Err(OcrError::InvalidInput {
                message: format!(
                    "preset '{:?}' is not supported by OarStructureEngine. Expected PpStructureV3",
                    paths.spec
                ),
            });
        }

        let layout_model = paths
            .layout_detection_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "layout_detection_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let rec_model = paths
            .recognition_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "recognition_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let dict_path = paths
            .character_dict
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "character_dict".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let table_cls = paths
            .table_classification_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "table_classification_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let wired_struct = paths
            .wired_table_structure_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "wired_table_structure_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let wireless_struct = paths
            .wireless_table_structure_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "wireless_table_structure_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let cell_det = paths
            .wired_table_cell_detection_model
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "wired_table_cell_detection_model".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let table_dict = paths
            .table_structure_dict
            .as_ref()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: "table_structure_dict".into(),
                reason: "missing path in ModelPaths".into(),
            })?;

        let builder = oar_ocr::oarocr::OARStructureBuilder::new(layout_model)
            .layout_model_name("PP-DocLayoutV3")
            .with_ocr(&paths.detection_model, rec_model, dict_path)
            .with_table_classification(table_cls)
            .with_wired_table_structure(wired_struct)
            .with_wireless_table_structure(wireless_struct)
            .with_wired_table_cell_detection(cell_det)
            .table_structure_dict_path(table_dict);

        let pipeline = builder.build().map_err(|e| OcrError::ModelLoad {
            model_path: layout_model.display().to_string(),
            reason: e.to_string(),
        })?;

        self.pipeline = Some(Arc::new(pipeline));
        Ok(())
    }

    fn recognize(&self, image_bytes: &[u8]) -> Result<OcrResult, OcrError> {
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

        let structure_result = pipeline
            .predict_image(image)
            .map_err(|e| OcrError::Inference {
                message: e.to_string(),
                source: Some(Box::new(e)),
            })?;

        let mut regions = Vec::new();
        if let Some(text_regions) = structure_result.text_regions {
            for r in text_regions {
                let text = r.text.as_deref().unwrap_or("").to_string();
                let confidence = r.confidence.unwrap_or(0.0);
                let (x1, y1, x2, y2) = r.bounding_box.aabb();
                regions.push(TextRegion {
                    text,
                    confidence,
                    box_: BoundingBox { x1, y1, x2, y2 },
                });
            }
        } else {
            for elem in structure_result.layout_elements {
                if let Some(text) = elem.text {
                    let (x1, y1, x2, y2) = elem.bbox.aabb();
                    regions.push(TextRegion {
                        text,
                        confidence: elem.confidence,
                        box_: BoundingBox { x1, y1, x2, y2 },
                    });
                }
            }
        }

        Ok(OcrResult { regions })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn structure_engine_rejects_wrong_preset() {
        let mut engine = OarStructureEngine::new();
        let paths = ModelPaths::new(
            std::path::Path::new("/models"),
            &ModelSpec::PpOcrV6(crate::core::types::OcrSize::Tiny),
        );
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::InvalidInput { .. }));
    }

    #[test]
    fn structure_engine_rejects_missing_model_files() {
        let mut engine = OarStructureEngine::new();
        let paths = ModelPaths::new(
            std::path::Path::new("/nonexistent"),
            &ModelSpec::PpStructureV3,
        );
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::ModelLoad { .. }));
    }
}
