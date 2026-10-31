//! Python wrapper for the individual task predictors exposed by `oar-ocr`.

use std::io::Cursor;
use std::path::{Path, PathBuf};

use image::RgbImage;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::core::error::OcrError;
use crate::storage::{config::OcrConfig, models, registry};
use oar_ocr::core::ModelSource;

enum Predictor {
    DocumentOrientation(oar_ocr::predictors::DocumentOrientationPredictor),
    DocumentRectification(oar_ocr::predictors::DocumentRectificationPredictor),
    TextLineOrientation(oar_ocr::predictors::TextLineOrientationPredictor),
    SealTextDetection(oar_ocr::predictors::SealTextDetectionPredictor),
    FormulaRecognition(oar_ocr::predictors::FormulaRecognitionPredictor),
}

#[pyclass]
pub struct TaskPredictor {
    predictor: Predictor,
}

#[pymethods]
impl TaskPredictor {
    #[new]
    #[pyo3(signature = (task, models=None, **options))]
    fn new(
        py: Python<'_>,
        task: &str,
        models: Option<&Bound<'_, PyAny>>,
        options: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Self> {
        let artifacts = match registry::task_artifacts(task) {
            Some(artifacts) => artifacts,
            None if matches!(task, "text_detection" | "text_recognition" | "layout_detection" | "table_classification" | "table_structure_recognition" | "table_cell_detection") => {
                return Err(crate::core::error::PyOcrValueError::new_err(format!("task not implemented yet: {task}")));
            }
            None => return Err(crate::core::error::PyOcrValueError::new_err(format!("unknown task '{task}'"))),
        };
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

        let score_threshold = option(options, "score_threshold", 0.5_f32)?;
        let topk = option(options, "topk", if task == "text_line_orientation" { 2_usize } else { 4_usize })?;
        let predictor = match task {
            "document_orientation" => Predictor::DocumentOrientation(
                oar_ocr::predictors::DocumentOrientationPredictor::builder()
                    .score_threshold(score_threshold).topk(topk).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "document_rectification" => Predictor::DocumentRectification(
                oar_ocr::predictors::DocumentRectificationPredictor::builder().build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "text_line_orientation" => Predictor::TextLineOrientation(
                oar_ocr::predictors::TextLineOrientationPredictor::builder()
                    .score_threshold(score_threshold).topk(topk).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "seal_text_detection" => Predictor::SealTextDetection(
                oar_ocr::predictors::SealTextDetectionPredictor::builder()
                    .score_threshold(score_threshold).build(ModelSource::from(model_path.clone()))
                    .map_err(|error| model_error(&model_path, error))?),
            "formula_recognition" => {
                let tokenizer = tokenizer_path.unwrap_or_else(|| model_path.with_file_name("pp-formulanet-tokenizer.json"));
                Predictor::FormulaRecognition(oar_ocr::predictors::FormulaRecognitionPredictor::builder()
                    .model_name("PP-FormulaNet-S")
                    .model_kind(oar_ocr::predictors::FormulaModelKind::PPFormulaNet)
                    .tokenizer_path(tokenizer)
                    .build(ModelSource::from(model_path.clone())).map_err(|error| model_error(&model_path, error))?)
            }
            _ => unreachable!("validated task name"),
        };
        Ok(Self { predictor })
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
        let results = py.detach(|| match &self.predictor {
            Predictor::DocumentOrientation(p) => p.predict(images).map(|r| TaskOutput::Orientation(r.orientations)),
            Predictor::DocumentRectification(p) => p.predict(images).map(|r| TaskOutput::Rectification(r.images)),
            Predictor::TextLineOrientation(p) => p.predict(images).map(|r| TaskOutput::LineOrientation(r.orientations)),
            Predictor::SealTextDetection(p) => p.predict(images).map(|r| TaskOutput::SealDetection(r.detections)),
            Predictor::FormulaRecognition(p) => p.predict(images).map(|r| TaskOutput::Formula((r.formulas, r.scores))),
        }).map_err(|error| OcrError::Inference { message: error.to_string(), source: None })?;
        output_dicts(py, results, count)
    }
}

enum TaskOutput {
    Orientation(Vec<Vec<oar_ocr::domain::tasks::Classification>>),
    Rectification(Vec<RgbImage>),
    LineOrientation(Vec<Vec<oar_ocr::domain::tasks::Classification>>),
    SealDetection(Vec<Vec<oar_ocr::domain::tasks::Detection>>),
    Formula((Vec<String>, Vec<Option<f32>>)),
}

fn output_dicts(py: Python<'_>, output: TaskOutput, count: usize) -> PyResult<Vec<Py<PyAny>>> {
    let rows = (0..count).map(|_| PyDict::new(py)).collect::<Vec<_>>();
    match output {
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
                row.set_item("image", png.into_inner())?;
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
