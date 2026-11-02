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
use crate::core::types::{
    BoundingBox, LayoutRegion, ModelPaths, ModelSpec, OcrOutput, StructureResult, TextRegion,
};
use crate::core::OcrEngineBackend;
use oar_ocr::core::config::OrtSessionConfig;

/// Función de fábrica para crear un motor de estructura.
///
/// `ort_session` fija el execution provider de todos los submodelos del
/// pipeline (layout, tablas, OCR, fórmulas); el default de la API Python es CPU.
pub fn create_oar_structure_engine(
    paths: &ModelPaths,
    ort_session: OrtSessionConfig,
) -> Result<OarStructureEngine, OcrError> {
    let mut engine = OarStructureEngine::new().with_ort_session(ort_session);
    engine.load_model(paths)?;
    Ok(engine)
}

/// Adaptador del backend OAR para PP-StructureV3.
#[derive(Debug)]
pub struct OarStructureEngine {
    pipeline: Option<Arc<oar_ocr::oarocr::OARStructure>>,
    ort_session: Option<OrtSessionConfig>,
}

impl OarStructureEngine {
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

        let mut builder = oar_ocr::oarocr::OARStructureBuilder::new(layout_model)
            .layout_model_name("PP-DocLayoutV3")
            .with_ocr(&paths.detection_model, rec_model, dict_path)
            .with_table_classification(table_cls)
            .with_wired_table_structure(wired_struct)
            .with_wireless_table_structure(wireless_struct)
            .with_wired_table_cell_detection(cell_det)
            .table_structure_dict_path(table_dict);

        // Add formula recognition if models are available
        if let (Some(formula_model), Some(tokenizer)) = (
            &paths.formula_recognition_model,
            &paths.formula_tokenizer,
        ) {
            builder = builder.with_formula_recognition(formula_model, tokenizer, "pp_formulanet");
        }

        // `ort_session` se aplica a todos los submodelos; la fórmula lo hereda
        // cuando no hay `formula_ort_session` explícito (`structure.rs:875`).
        if let Some(ort_session) = &self.ort_session {
            builder = builder.ort_session(ort_session.clone());
        }

        let pipeline = builder.build().map_err(|e| OcrError::ModelLoad {
            model_path: layout_model.display().to_string(),
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

        let structure_result = pipeline
            .predict_image(image)
            .map_err(|e| OcrError::Inference {
                message: e.to_string(),
                source: Some(Box::new(e)),
            })?;

        Ok(OcrOutput::Structure(convert_structure(structure_result)))
    }
}

/// Caja de `oar-ocr` -> caja del core.
fn bounding_box(native: &oar_ocr::processors::BoundingBox) -> BoundingBox {
    let (x1, y1, x2, y2) = native.aabb();
    BoundingBox { x1, y1, x2, y2 }
}

/// Estructura nativa de `oar-ocr` -> `StructureResult` del core (ADR-003).
///
/// El Markdown se renderiza aquí, una sola vez, con el `to_markdown()` del
/// crate: es el que respeta la jerarquía de títulos e inyecta el HTML de las
/// tablas y el LaTeX de las fórmulas. Nada se aplana a `OcrResult`.
fn convert_structure(native: oar_ocr::domain::structure::StructureResult) -> StructureResult {
    let markdown = native.to_markdown();

    let elements = native
        .layout_elements
        .iter()
        .map(|element| LayoutRegion {
            kind: element.element_type.as_str().to_string(),
            text: element.text.clone().unwrap_or_default(),
            confidence: element.confidence,
            box_: bounding_box(&element.bbox),
        })
        .collect();

    let regions = native
        .text_regions
        .unwrap_or_default()
        .iter()
        .map(|region| TextRegion {
            text: region.text.as_deref().unwrap_or("").to_string(),
            confidence: region.confidence.unwrap_or(0.0),
            box_: bounding_box(&region.bounding_box),
        })
        .collect();

    let formulas = native
        .layout_elements
        .iter()
        .filter(|element| element.element_type.as_str() == "formula")
        .filter_map(|element| element.text.clone())
        .collect();

    StructureResult {
        markdown,
        elements,
        regions,
        formulas,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use oar_ocr::domain::structure::{
        LayoutElement, LayoutElementType, StructureResult as NativeStructureResult, TableResult,
        TableType,
    };
    use oar_ocr::processors::BoundingBox as NativeBoundingBox;

    /// Estructura nativa con título, tabla HTML y fórmula LaTeX: lo que devuelve
    /// el pipeline de PP-StructureV3 tras el stitching, sin cargar modelos.
    fn estructura_nativa() -> NativeStructureResult {
        let tabla = NativeBoundingBox::from_coords(0.0, 20.0, 100.0, 60.0);
        let elementos = vec![
            LayoutElement::new(
                NativeBoundingBox::from_coords(0.0, 0.0, 100.0, 10.0),
                LayoutElementType::DocTitle,
                0.99,
            )
            .with_text("Factura 2026-10-25"),
            LayoutElement::new(tabla.clone(), LayoutElementType::Table, 0.98),
            LayoutElement::new(
                NativeBoundingBox::from_coords(0.0, 70.0, 100.0, 90.0),
                LayoutElementType::Formula,
                0.90,
            )
            .with_text("E = mc^2"),
        ];
        let tablas = vec![
            TableResult::new(tabla, TableType::Wired).with_html_structure(
                "<html><body><table><tr><td>Total</td><td>12345</td></tr></table></body></html>",
            ),
        ];

        NativeStructureResult::new("fixture.png", 0)
            .with_layout_elements(elementos)
            .with_tables(tablas)
    }

    #[test]
    fn la_estructura_no_se_aplana_y_conserva_tablas_html_y_latex() {
        let resultado = convert_structure(estructura_nativa());

        // ADR-003: el Markdown del documento cruza con tablas HTML y LaTeX.
        assert!(resultado.markdown.contains("# Factura 2026-10-25"));
        assert!(resultado.markdown.contains("<table"));
        assert!(resultado.markdown.contains("Total"));
        assert!(resultado.markdown.contains("$$E = mc^2$$"));

        // Acceso estructurado a los elementos detectados.
        let kinds: Vec<&str> = resultado
            .elements
            .iter()
            .map(|elemento| elemento.kind.as_str())
            .collect();
        assert_eq!(kinds, ["doc_title", "table", "formula"]);

        let formula = resultado
            .elements
            .iter()
            .find(|elemento| elemento.kind == "formula")
            .expect("la fórmula debe conservarse como elemento");
        assert_eq!(formula.text, "E = mc^2");
        assert!(formula.box_.width() > 0.0 && formula.box_.height() > 0.0);

        // `to_markdown()` es el método público del pyclass, no un campo suelto.
        assert_eq!(resultado.to_markdown(), resultado.markdown);

        // Verificar que las fórmulas se extraen correctamente al campo formulas
        assert_eq!(resultado.formulas.len(), 1);
        assert_eq!(resultado.formulas[0], "E = mc^2");
    }

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
