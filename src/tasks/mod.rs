//! Python wrapper for the individual task predictors exposed by `oar-ocr`.

use std::io::Cursor;
use std::path::{Path, PathBuf};

use image::RgbImage;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};

use crate::core::error::OcrError;
use crate::storage::{config::OcrConfig, models, registry};
use oar_ocr::core::ModelSource;

enum Predictor {
    TextDetection(oar_ocr::predictors::TextDetectionPredictor),
    TextRecognition(oar_ocr::predictors::TextRecognitionPredictor),
    LayoutDetection(oar_ocr::predictors::LayoutDetectionPredictor),
    TableClassification(oar_ocr::predictors::TableClassificationPredictor),
    TableStructure(oar_ocr::predictors::TableStructureRecognitionPredictor),
    TableCells(oar_ocr::predictors::TableCellDetectionPredictor),
    DocumentOrientation(oar_ocr::predictors::DocumentOrientationPredictor),
    DocumentRectification(oar_ocr::predictors::DocumentRectificationPredictor),
    TextLineOrientation(oar_ocr::predictors::TextLineOrientationPredictor),
    SealTextDetection(oar_ocr::predictors::SealTextDetectionPredictor),
    FormulaRecognition(oar_ocr::predictors::FormulaRecognitionPredictor),
}

#[pyclass]
pub struct TaskPredictor {
    predictor: Predictor,
    /// EP que realmente corre (`cpu`, `cuda`, ...), nunca inventado.
    provider_effective: String,
}

#[pymethods]
impl TaskPredictor {
    #[new]
    #[pyo3(signature = (task, models=None, device = "cpu", **options))]
    fn new(
        py: Python<'_>,
        task: &str,
        models: Option<&Bound<'_, PyAny>>,
        device: &str,
        options: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Self> {
        let artifacts = match registry::task_artifacts(task) {
            Some(artifacts) => artifacts,
            None => return Err(crate::core::error::PyOcrValueError::new_err(format!("unknown task '{task}'"))),
        };
        if let Some(options) = options {
            for key in options.keys() {
                let name: String = key.extract()?;
                let supported = match task {
                    "document_orientation" => matches!(name.as_str(), "score_threshold" | "topk"),
                    "text_line_orientation" | "table_classification" => matches!(name.as_str(), "score_threshold" | "topk" | "input_shape"),
                    "seal_text_detection" => name == "score_threshold",
                    "text_recognition" => matches!(name.as_str(), "score_threshold" | "dict_path"),
                    "text_detection" => matches!(name.as_str(), "score_threshold" | "box_threshold" | "unclip_ratio" | "max_candidates"),
                    "layout_detection" | "table_cell_detection" => matches!(name.as_str(), "score_threshold" | "model_name"),
                    "table_structure_recognition" => matches!(name.as_str(), "dict_path" | "model_name" | "input_shape"),
                    _ => false,
                };
                if !supported {
                    return Err(crate::core::error::PyOcrValueError::new_err(format!("unsupported option '{name}' for task '{task}'")));
                }
            }
        }
        let default_threshold = match task { "text_detection" | "table_cell_detection" => 0.3_f32, "text_recognition" => 0.0, _ => 0.5 };
        let score_threshold = option(options, "score_threshold", default_threshold)?;
        let topk = option(options, "topk", if matches!(task, "text_line_orientation" | "table_classification") { 2_usize } else { 4_usize })?;
        let default_shape = match task { "table_classification" => (224_u32, 224_u32), "table_structure_recognition" => (512, 512), _ => (80, 160) };
        let input_shape = option(options, "input_shape", default_shape)?;
        if input_shape.0 == 0 || input_shape.1 == 0 {
            return Err(crate::core::error::PyOcrValueError::new_err("input_shape dimensions must be positive"));
        }
        let custom_root = match models {
            Some(value) if value.extract::<String>().is_ok() => {
                Some(PathBuf::from(value.extract::<String>()?))
            }
            _ => None,
        };
        let config = OcrConfig::new(custom_root.as_deref());
        let (model_path, tokenizer_path, explicit) = model_paths(models, task, &config.models_dir, artifacts)?;
        if !explicit {
            py.detach(|| models::ensure_task_models(&config.models_dir, task))?;
        }
        // Upstream auto-download ignores PYOCRUST_OFFLINE. Only hand builders
        // existing absolute files, including companion dictionaries/tokenizers.
        let model_path = existing_asset(&model_path)?;

        // `device` opt-in (ADR-010): se resuelve y prueba una vez por predictor.
        let selection = crate::core::device::resolve_device(device)?;
        let session = selection.config;

        let predictor = match task {
            "text_detection" => Predictor::TextDetection(
                oar_ocr::predictors::TextDetectionPredictor::builder()
                    .score_threshold(score_threshold)
                    .box_threshold(option(options, "box_threshold", 0.6_f32)?)
                    .unclip_ratio(option(options, "unclip_ratio", 1.5_f32)?)
                    .max_candidates(option(options, "max_candidates", 1000_usize)?)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?),
            "text_recognition" => Predictor::TextRecognition(
                oar_ocr::predictors::TextRecognitionPredictor::builder()
                    .score_threshold(score_threshold)
                    .dict_path(dictionary_path(options, models, &model_path, artifacts[1].name)?)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?),
            "layout_detection" => Predictor::LayoutDetection(
                oar_ocr::predictors::LayoutDetectionPredictor::builder()
                    .score_threshold(score_threshold).model_name(option(options, "model_name", "pp_doclayoutv3".to_string())?)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?),
            "table_classification" => Predictor::TableClassification(
                oar_ocr::predictors::TableClassificationPredictor::builder()
                    .score_threshold(score_threshold).topk(topk).input_shape(input_shape)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?),
            "table_structure_recognition" => {
                let mut builder = oar_ocr::predictors::TableStructureRecognitionPredictor::builder()
                    .dict_path(dictionary_path(options, models, &model_path, artifacts[1].name)?);
                if let Some(value) = options.and_then(|dict| dict.get_item("model_name").ok().flatten()) {
                    builder = builder.model_name(value.extract::<String>()?);
                }
                if options.is_some_and(|dict| dict.contains("input_shape").unwrap_or(false)) {
                    builder = builder.input_shape(input_shape.0, input_shape.1);
                }
                Predictor::TableStructure(builder.with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?)
            }
            "table_cell_detection" => {
                let default_variant = oar_ocr::predictors::TableCellModelVariant::detect_from_path(&model_path)
                    .unwrap_or(oar_ocr::predictors::TableCellModelVariant::RTDetrLWired);
                let name = option(options, "model_name", default_variant.as_str().to_string())?;
                let variant = oar_ocr::predictors::TableCellModelVariant::from_model_type(&name)
                    .ok_or_else(|| crate::core::error::PyOcrValueError::new_err(format!("unknown table cell model '{name}'")))?;
                Predictor::TableCells(oar_ocr::predictors::TableCellDetectionPredictor::builder()
                    .score_threshold(score_threshold).model_variant(variant)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?)
            }
            "document_orientation" => Predictor::DocumentOrientation(
                oar_ocr::predictors::DocumentOrientationPredictor::builder()
                    .score_threshold(score_threshold).topk(topk).with_ort_config(session.clone()).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "document_rectification" => Predictor::DocumentRectification(
                oar_ocr::predictors::DocumentRectificationPredictor::builder().with_ort_config(session.clone()).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "text_line_orientation" => Predictor::TextLineOrientation(
                oar_ocr::predictors::TextLineOrientationPredictor::builder()
                    // oar-ocr 0.10.1 defaults to (192, 48); this model expects (H, W).
                    .input_shape(input_shape)
                    .score_threshold(score_threshold).topk(topk).with_ort_config(session.clone()).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "seal_text_detection" => Predictor::SealTextDetection(
                oar_ocr::predictors::SealTextDetectionPredictor::builder()
                    .score_threshold(score_threshold).with_ort_config(session.clone()).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "formula_recognition" => {
                let tokenizer = tokenizer_path.unwrap_or_else(|| model_path.with_file_name("pp-formulanet-tokenizer.json"));
                let tokenizer = existing_asset(&tokenizer)?;
                Predictor::FormulaRecognition(oar_ocr::predictors::FormulaRecognitionPredictor::builder()
                    .model_name("PP-FormulaNet-S")
                    .model_kind(oar_ocr::predictors::FormulaModelKind::PPFormulaNet)
                    .tokenizer_path(tokenizer)
                    .with_ort_config(session.clone()).build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?)
            }
            _ => unreachable!("validated task name"),
        };
        Ok(Self {
            predictor,
            provider_effective: selection.provider_effective,
        })
    }

    /// EP que realmente corre la inferencia (`cpu`, `cuda`, `directml`, ...).
    ///
    /// Refleja lo que ONNX Runtime registró de verdad al construir el predictor,
    /// no lo que se pidió: pedir `device="cuda"` sin un EP CUDA que registre
    /// falla en el constructor y nunca etiqueta CPU como GPU.
    #[getter]
    fn provider_effective(&self) -> String {
        self.provider_effective.clone()
    }

    /// Run one image and return the task's documented Python dictionary.
    fn predict(&self, py: Python<'_>, image: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let bytes = image_bytes(image)?;
        let image = image::load_from_memory(&bytes).map_err(OcrError::from)?.into_rgb8();
        let mut output = self.run(py, vec![image])?;
        Ok(output.pop().expect("one input image"))
    }

    /// Run a sequence of images and return one result dictionary per image.
    fn predict_batch(&self, py: Python<'_>, images: &Bound<'_, PyAny>) -> PyResult<Vec<Py<PyAny>>> {
        let mut decoded = Vec::new();
        for image in images.try_iter()? {
            let bytes = image_bytes(&image?)?;
            decoded.push(image::load_from_memory(&bytes).map_err(OcrError::from)?.into_rgb8());
        }
        self.run(py, decoded)
    }
}

impl TaskPredictor {
    fn run(&self, py: Python<'_>, images: Vec<RgbImage>) -> PyResult<Vec<Py<PyAny>>> {
        let count = images.len();
        if count == 0 { return Ok(Vec::new()); }
        let output = self.predict_images(py, &images)?;
        if output.len() >= count {
            return output_dicts(py, output, count);
        }
        // Upstream RT-DETR (oar-ocr-core `models/detection/rtdetr.rs`) reshapes a 2-D
        // output to a batch of one, so a multi-image request silently keeps only the
        // first image. Re-run the dropped images on the SAME predictor (built once)
        // so `predict_batch` still returns one dictionary per input image.
        let mut dicts = Vec::with_capacity(count);
        for image in &images {
            let output = self.predict_images(py, std::slice::from_ref(image))?;
            dicts.push(output_dicts(py, output, 1)?.pop().expect("one input image"));
        }
        Ok(dicts)
    }

    fn predict_images(&self, py: Python<'_>, images: &[RgbImage]) -> PyResult<TaskOutput> {
        let batch = images.to_vec();
        py.detach(move || match &self.predictor {
            Predictor::TextDetection(p) => p.predict(batch).map(|r| TaskOutput::SealDetection(r.detections)),
            Predictor::TextRecognition(p) => p.predict(batch).map(|r| TaskOutput::Text((r.texts, r.scores))),
            Predictor::LayoutDetection(p) => p.predict(batch).map(|r| TaskOutput::Layout((r.elements, r.is_reading_order_sorted))),
            Predictor::TableClassification(p) => p.predict(batch).map(|r| TaskOutput::TableClasses(r.classifications)),
            Predictor::TableStructure(p) => p.predict(batch).map(|r| TaskOutput::TableStructure((r.structures, r.bboxes))),
            Predictor::TableCells(p) => p.predict(batch).map(|r| TaskOutput::Cells(r.cells)),
            Predictor::DocumentOrientation(p) => p.predict(batch).map(|r| TaskOutput::Orientation(r.orientations)),
            Predictor::DocumentRectification(p) => p.predict(batch).map(|r| TaskOutput::Rectification(r.images)),
            Predictor::TextLineOrientation(p) => p.predict(batch).map(|r| TaskOutput::LineOrientation(r.orientations)),
            Predictor::SealTextDetection(p) => p.predict(batch).map(|r| TaskOutput::SealDetection(r.detections)),
            Predictor::FormulaRecognition(p) => p.predict(batch).map(|r| TaskOutput::Formula((r.formulas, r.scores))),
        }).map_err(|error| OcrError::Inference { message: error.to_string(), source: None }.into())
    }
}

enum TaskOutput {
    Text((Vec<String>, Vec<f32>)),
    Layout((Vec<Vec<oar_ocr::domain::tasks::layout_detection::LayoutDetectionElement>>, bool)),
    TableClasses(Vec<Vec<oar_ocr::domain::tasks::Classification>>),
    TableStructure((Vec<Vec<String>>, Vec<Vec<Vec<f32>>>)),
    Cells(Vec<Vec<oar_ocr::domain::tasks::table_cell_detection::TableCellDetection>>),
    Orientation(Vec<Vec<oar_ocr::domain::tasks::Classification>>),
    Rectification(Vec<RgbImage>),
    LineOrientation(Vec<Vec<oar_ocr::domain::tasks::Classification>>),
    SealDetection(Vec<Vec<oar_ocr::domain::tasks::Detection>>),
    Formula((Vec<String>, Vec<Option<f32>>)),
}

impl TaskOutput {
    /// Number of per-image entries returned by the upstream predictor.
    fn len(&self) -> usize {
        match self {
            TaskOutput::Text((values, _)) => values.len(),
            TaskOutput::Layout((values, _)) => values.len(),
            TaskOutput::TableClasses(values) => values.len(),
            TaskOutput::TableStructure((values, _)) => values.len(),
            TaskOutput::Cells(values) => values.len(),
            TaskOutput::Orientation(values) => values.len(),
            TaskOutput::Rectification(values) => values.len(),
            TaskOutput::LineOrientation(values) => values.len(),
            TaskOutput::SealDetection(values) => values.len(),
            TaskOutput::Formula((values, _)) => values.len(),
        }
    }
}

fn output_dicts(py: Python<'_>, output: TaskOutput, count: usize) -> PyResult<Vec<Py<PyAny>>> {
    let rows = (0..count).map(|_| PyDict::new(py)).collect::<Vec<_>>();
    match output {
        TaskOutput::Text((texts, scores)) => {
            for ((row, text), score) in rows.iter().zip(texts).zip(scores) {
                row.set_item("text", text)?;
                row.set_item("score", score)?;
            }
        }
        TaskOutput::TableClasses(result) => {
            for (row, values) in rows.iter().zip(result) {
                row.set_item("classifications", classifications(py, values)?)?;
            }
        }
        TaskOutput::TableStructure((structures, bboxes)) => {
            for ((row, tokens), boxes) in rows.iter().zip(structures).zip(bboxes) {
                row.set_item("structures", tokens)?;
                row.set_item("bboxes", boxes)?;
            }
        }
        TaskOutput::Layout((elements, sorted)) => {
            for (row, elements) in rows.iter().zip(elements) {
                let list = PyList::empty(py);
                for element in elements {
                    let entry = PyDict::new(py);
                    entry.set_item("bbox", element.bbox.points.iter().map(|p| vec![p.x, p.y]).collect::<Vec<_>>())?;
                    entry.set_item("element_type", element.element_type)?;
                    entry.set_item("score", element.score)?;
                    list.append(entry)?;
                }
                row.set_item("elements", list)?;
                row.set_item("is_reading_order_sorted", sorted)?;
            }
        }
        TaskOutput::Cells(cells) => {
            for (row, cells) in rows.iter().zip(cells) {
                let list = PyList::empty(py);
                for cell in cells {
                    let entry = PyDict::new(py);
                    entry.set_item("bbox", cell.bbox.points.iter().map(|p| vec![p.x, p.y]).collect::<Vec<_>>())?;
                    entry.set_item("label", cell.label)?;
                    entry.set_item("score", cell.score)?;
                    list.append(entry)?;
                }
                row.set_item("cells", list)?;
            }
        }
        TaskOutput::Orientation(result) => {
            for (row, values) in rows.iter().zip(result) {
                row.set_item("orientations", classifications(py, values)?)?;
            }
        }
        TaskOutput::LineOrientation(result) => {
            for (row, values) in rows.iter().zip(result) {
                row.set_item("orientations", classifications(py, values)?)?;
            }
        }
        TaskOutput::Rectification(result) => {
            for (row, image) in rows.iter().zip(result) {
                let mut png = Cursor::new(Vec::new());
                image::DynamicImage::ImageRgb8(image.clone()).write_to(&mut png, image::ImageFormat::Png)
                    .map_err(|error| OcrError::Inference { message: error.to_string(), source: None })?;
                row.set_item("image", PyBytes::new(py, &png.into_inner()))?;
                row.set_item("width", image.width())?;
                row.set_item("height", image.height())?;
            }
        }
        TaskOutput::SealDetection(result) => {
            for (row, detections) in rows.iter().zip(result) {
                let list = PyList::empty(py);
                for detection in detections {
                    let entry = PyDict::new(py);
                    entry.set_item("bbox", detection.bbox.points.iter().map(|point| vec![point.x, point.y]).collect::<Vec<_>>())?;
                    entry.set_item("score", detection.score)?;
                    list.append(entry)?;
                }
                row.set_item("detections", list)?;
            }
        }
        TaskOutput::Formula(result) => {
            for (index, row) in rows.iter().enumerate() {
                row.set_item("formula", result.0.get(index).cloned().unwrap_or_default())?;
                row.set_item("score", result.1.get(index).copied().flatten())?;
            }
        }
    }
    Ok(rows.into_iter().map(|row| row.into_any().unbind()).collect())
}

fn classifications(py: Python<'_>, values: Vec<oar_ocr::domain::tasks::document_orientation::Classification>) -> PyResult<Bound<'_, PyList>> {
    let list = PyList::empty(py);
    for value in values {
        let item = PyDict::new(py);
        item.set_item("class_id", value.class_id)?;
        item.set_item("label", value.label)?;
        item.set_item("score", value.score)?;
        list.append(item)?;
    }
    Ok(list)
}

fn option<T: for<'a, 'py> FromPyObject<'a, 'py, Error = PyErr>>(options: Option<&Bound<'_, PyDict>>, name: &str, default: T) -> PyResult<T> {
    match options.and_then(|dict| dict.get_item(name).ok().flatten()) {
        Some(value) => value.extract(),
        None => Ok(default),
    }
}

fn model_error(path: &Path, error: impl std::fmt::Display) -> PyErr {
    OcrError::ModelLoad { model_path: path.display().to_string(), reason: error.to_string() }.into()
}

fn existing_asset(path: &Path) -> PyResult<PathBuf> {
    if !path.is_file() {
        return Err(model_error(path, "explicit or resolved asset must be an existing local file; implicit upstream downloads are disabled"));
    }
    std::fs::canonicalize(path).map_err(|error| model_error(path, error))
}

fn dictionary_path(options: Option<&Bound<'_, PyDict>>, models: Option<&Bound<'_, PyAny>>, model: &Path, filename: &str) -> PyResult<String> {
    let path = if let Some(value) = options.map(|dict| dict.get_item("dict_path")).transpose()?.flatten() {
        PathBuf::from(value.extract::<String>()?)
    } else if let Some(value) = models.and_then(|value| value.cast::<PyDict>().ok()).map(|dict| dict.get_item("dict")).transpose()?.flatten() {
        PathBuf::from(value.extract::<String>()?)
    } else {
        model.with_file_name(filename)
    };
    Ok(existing_asset(&path)?.to_string_lossy().into_owned())
}

fn model_paths(models: Option<&Bound<'_, PyAny>>, _task: &str, root: &Path, artifacts: &[registry::Artifact]) -> PyResult<(PathBuf, Option<PathBuf>, bool)> {
    let Some(models) = models else { return Ok((root.join(artifacts[0].name), None, false)); };
    if models.is_none() { return Ok((root.join(artifacts[0].name), None, false)); }
    if let Ok(path) = models.extract::<String>() { return Ok((PathBuf::from(path), None, true)); }
    if let Ok(dict) = models.cast::<PyDict>() {
        let model: String = dict.get_item("model")?.ok_or_else(|| crate::core::error::PyOcrValueError::new_err("models dict requires 'model' path"))?.extract()?;
        let tokenizer = dict.get_item("tokenizer")?.map(|value| value.extract::<String>()).transpose()?.map(PathBuf::from);
        return Ok((PathBuf::from(model), tokenizer, true));
    }
    Err(crate::core::error::PyOcrValueError::new_err("models must be a model path, dict, or None"))
}

fn image_bytes(image: &Bound<'_, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(path) = image.extract::<String>() { return std::fs::read(path).map_err(|error| OcrError::from(error).into()); }
    if let Ok(bytes) = image.extract::<&[u8]>() { return Ok(bytes.to_vec()); }
    if let Ok(path) = image.call_method0("__fspath__") {
        let path: String = path.extract()?;
        return std::fs::read(path).map_err(|error| OcrError::from(error).into());
    }
    Err(crate::core::error::PyOcrValueError::new_err("image must be a path string, bytes, or PathLike object"))
}
