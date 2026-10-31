//! Feature → model → pipeline metadata, without disk or network access.
//!
//! Classic models and companion dictionaries/tokenizers come from the upstream
//! download registry (docs/models.md). Parameters and runtime RAM are unknown:
//! file size is not a parameter count or a measured working set. Indra is ONNX,
//! not oar-ocr-vl; OAR_VL_* controls must not be advertised as its runtime knobs.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use super::registry;

/// Documented metadata for a model or its required companion artifact.
/// Sizes use find(name), never duplicated literals; params is unknown upstream.
pub struct ModelEntry {
    pub name: &'static str,
    pub task: &'static str,
    pub description: &'static str,
    pub params: Option<u64>,
    pub size_bytes: Option<u64>,
    pub env_vars: &'static [&'static str],
}

/// Exposed preset/task profile. RAM remains unknown without a measurement;
/// disk_bytes is unknown if any required artifact is absent from upstream.
pub struct PipelineProfile {
    pub id: &'static str,
    pub family: &'static str,
    pub quality: &'static str,
    pub output_format: &'static str,
    pub disk_bytes: Option<u64>,
    pub ram_bytes: Option<u64>,
    pub artifacts: Vec<&'static str>,
    pub description: &'static str,
}

/// Storage priority and offline control apply to all native ONNX models.
const ENV: &[&str] = &["OAR_HOME", "OCR_MODELS_CACHE_DIR", "PYOCRUST_OFFLINE", "CUDA_LAUNCH_BLOCKING", "RUST_LOG"];
const TASKS: &[&str] = &[
    "text_detection", "text_recognition", "layout_detection", "document_orientation",
    "document_rectification", "text_line_orientation", "seal_text_detection",
    "formula_recognition", "table_classification", "table_structure_recognition", "table_cell_detection",
];

fn feature(name: &str) -> (&'static str, &'static str) {
    if name.contains("seal_det") { ("seal_text_detection", "Detect curved seal text regions") }
    else if name.contains("textline_ori") { ("text_line_orientation", "Classify text line orientation") }
    else if name.contains("doc_ori") { ("document_orientation", "Classify document rotation") }
    else if name == "uvdoc.onnx" { ("document_rectification", "Rectify perspective-distorted documents") }
    else if name.contains("table_cell") { ("table_cell_detection", "Detect wired or wireless table cells") }
    else if name.contains("table_cls") { ("table_classification", "Classify wired versus wireless tables") }
    else if name.starts_with("slanet") || name.starts_with("slanext") || name.starts_with("table_structure") { ("table_structure_recognition", "Recognize table structure tokens and geometry") }
    else if name.contains("layout") { ("layout_detection", "Detect document layout regions and supported reading order") }
    else if name.contains("formulanet") || name.contains("unimernet") || name.contains("latex_ocr") { ("formula_recognition", "Recognize mathematical expressions; tokenizer companions decode LaTeX") }
    else if name.ends_with("_det.onnx") { ("text_detection", "Detect text regions with PP-OCR") }
    else { ("text_recognition", "Recognize text with the model-specific character dictionary") }
}

pub fn models() -> Vec<ModelEntry> {
    let mut entries: Vec<_> = oar_ocr::download::REGISTRY.iter().map(|entry| {
        let (task, description) = feature(entry.name);
        ModelEntry { name: entry.name, task, description, params: None,
            size_bytes: oar_ocr::download::find(entry.name).map(|e| e.size), env_vars: ENV }
    }).collect();
    for artifact in registry::indra_artifacts() {
        entries.push(ModelEntry { name: artifact.name, task: "indra",
            description: "Indra ONNX document OCR companion; pinned HuggingFace artifact, absent from ModelScope registry",
            params: None, size_bytes: None, env_vars: ENV });
    }
    entries
}

fn profile(id: &'static str, family: &'static str, quality: &'static str, format: &'static str, artifacts: &[registry::Artifact]) -> PipelineProfile {
    let names: Vec<_> = artifacts.iter().map(|a| a.name).collect();
    let disk_bytes = names.iter().try_fold(0_u64, |sum, name| {
        oar_ocr::download::find(name).and_then(|e| sum.checked_add(e.size))
    });
    PipelineProfile { id, family, quality, output_format: format, disk_bytes, ram_bytes: None,
        artifacts: names, description: match family {
            "pp_ocrv6" => "PP-OCRv6 detection plus recognition and matching dictionary",
            "pp_structurev3" => "Layout, OCR, table HTML and formula LaTeX document pipeline",
            "indra" => "Indra document OCR with inline mathematical Markdown",
            _ => "Standalone native task; predict and predict_batch return task-specific dictionaries",
        } }
}

pub fn profiles() -> Vec<PipelineProfile> {
    let mut entries = Vec::new();
    for (id, spec) in registry::presets() {
        let (family, quality, format) = match id {
            "pp_ocrv6_tiny" => ("pp_ocrv6", "speed", "text"),
            "pp_ocrv6_small" => ("pp_ocrv6", "balanced", "text"),
            "pp_ocrv6_medium" => ("pp_ocrv6", "accuracy", "text"),
            "indra" => ("indra", "accuracy", "markdown"),
            _ => ("pp_structurev3", "balanced", "markdown"),
        };
        entries.push(profile(id, family, quality, format, registry::artifacts_for(&spec)));
    }
    for &task in TASKS {
        if let Some(artifacts) = registry::task_artifacts(task) {
            entries.push(profile(task, "task", "default", "json", artifacts));
        }
    }
    entries
}

/// Return upstream model metadata; no download, filesystem scan or inference.
#[pyfunction]
pub fn model_catalog(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let result = PyDict::new(py);
    for model in models() {
        let row = PyDict::new(py);
        row.set_item("name", model.name)?;
        row.set_item("task", model.task)?;
        row.set_item("description", model.description)?;
        row.set_item("params", model.params)?;
        row.set_item("size_bytes", model.size_bytes)?;
        row.set_item("env_vars", model.env_vars.to_vec())?;
        result.set_item(model.name, row)?;
    }
    Ok(result.into_any().unbind())
}

/// Return exposed presets and tasks, with exact registered disk totals.
#[pyfunction]
pub fn pipeline_profiles(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let result = PyDict::new(py);
    for profile in profiles() {
        let row = PyDict::new(py);
        row.set_item("id", profile.id)?;
        row.set_item("family", profile.family)?;
        row.set_item("quality", profile.quality)?;
        row.set_item("output_format", profile.output_format)?;
        row.set_item("disk_bytes", profile.disk_bytes)?;
        row.set_item("ram_bytes", profile.ram_bytes)?;
        row.set_item("artifacts", profile.artifacts)?;
        row.set_item("description", profile.description)?;
        result.set_item(profile.id, row)?;
    }
    Ok(result.into_any().unbind())
}
