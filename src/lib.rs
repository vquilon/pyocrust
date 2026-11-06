//! Núcleo nativo de `pyocrust`.
//!
//! Módulo PyO3 `pyocrust._pyocrust_core` (ADR-011) del crate `pyocrust_core`.
//! Registra las capas del paquete: `core` (tipos, errores, preprocesamiento,
//! tarjeta `I2`), `storage` (`I3`) e `engines` + clase pública `VeloceOCR`
//! (`I4`).
//!
//! Contrato vigente: `DESIGN.md` y `PLANNING.md` de la raíz del repositorio.

use pyo3::prelude::*;

pub mod core;
pub mod engines;
pub mod storage;
pub mod tasks;

use crate::core::{OcrEngineBackend, OcrError};

/// Versión del módulo nativo. La fachada `pyocrust/__init__.py` la expone.
#[pyfunction]
fn native_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// EPs aceleradores que **registran de verdad** en este host (`[]` si ninguno).
///
/// Es la única fuente honesta de soporte GPU del wheel: prueba cada candidato
/// compilado (`cuda`/`directml`) con `OrtSessionConfig::resolve_auto` y devuelve
/// solo los nombres que ONNX Runtime aceptó. Un inventario físico de GPU no
/// implica que exista el EP (ver `pyocrust/hardware.py`).
#[pyfunction]
fn available_providers() -> Vec<String> {
    crate::core::device::available_providers()
}

/// Clase pública de alto nivel (`DESIGN.md` §3.1, ADR-002, ADR-011).
#[pyclass]
struct VeloceOCR {
    engine: Box<dyn OcrEngineBackend>,
    config: storage::config::OcrConfig,
    license: storage::license::License,
    /// EP que realmente corre (`cpu`, `cuda`, ...), nunca inventado.
    provider_effective: String,
}

#[pymethods]
impl VeloceOCR {
    #[new]
    #[pyo3(signature = (preset = "pp_ocrv6", custom_path = None, device = "cpu", license_commercial_use = true, license_acknowledge = false))]
    fn new(
        py: Python<'_>,
        preset: &str,
        custom_path: Option<&str>,
        device: &str,
        license_commercial_use: bool,
        license_acknowledge: bool,
    ) -> PyResult<Self> {
        let spec = match preset {
            "pp_ocrv6" | "pp_ocrv6_tiny" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Tiny),
            "pp_ocrv6_small" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Small),
            "pp_ocrv6_medium" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Medium),
            "pp_structurev3" => crate::core::ModelSpec::PpStructureV3,
            "indra" => crate::core::ModelSpec::Indra,
            _ => {
                return Err(OcrError::InvalidInput {
                    message: format!(
                        "unknown preset '{preset}'. Expected one of: pp_ocrv6, pp_ocrv6_tiny, pp_ocrv6_small, pp_ocrv6_medium, pp_structurev3, indra"
                    ),
                }.into());
            }
        };

        let license = storage::license::License::for_artifacts(
            storage::registry::artifacts_for(&spec).iter().map(|artifact| artifact.name),
        );
        if !license.allows(license_commercial_use, license_acknowledge) {
            return Err(crate::core::error::PyOcrValueError::new_err(format!(
                "{}. Notes: {}",
                license.block_message(&format!("El preset '{preset}'")),
                license.notes,
            )));
        }

        let config = storage::config::OcrConfig::new(custom_path.map(std::path::Path::new));
        if let Ok(oar_home) = std::env::var(storage::config::OAR_HOME_ENV) {
            if let Ok(os) = py.import("os") {
                if let Ok(environ) = os.getattr("environ") {
                    let _ = environ.set_item(storage::config::OAR_HOME_ENV, oar_home);
                }
            }
        }
        let paths = config.resolve_paths(&spec);

        // `device` opt-in (ADR-010): el EP se resuelve y prueba **antes** de
        // construir el pipeline; el default `"cpu"` no toca ninguna GPU.
        let selection = crate::core::device::resolve_device(device)?;

        // `S2.0`: preflight → descarga en paralelo de lo que falte → re-preflight.
        // Se libera el GIL: la descarga es I/O de red, no inferencia.
        py.detach(|| storage::models::ensure_models(&config.models_dir, &spec))?;

        let engine = py.detach(|| engines::create_engine(&spec, &paths, &selection.config))?;

        Ok(Self {
            engine,
            config,
            license,
            provider_effective: selection.provider_effective,
        })
    }

    /// EP que realmente corre la inferencia (`cpu`, `cuda`, `directml`, ...).
    ///
    /// Refleja lo que ONNX Runtime registró de verdad al construir el pipeline,
    /// no lo que se pidió: pedir `device="cuda"` sin un EP CUDA que registre
    /// falla en el constructor y nunca etiqueta CPU como GPU.
    #[getter]
    fn provider_effective(&self) -> String {
        self.provider_effective.clone()
    }

    /// Directorio resuelto donde se buscan o almacenan los modelos.
    #[getter]
    fn models_dir(&self) -> String {
        self.config.models_dir.to_string_lossy().to_string()
    }

    /// Resolved SPDX license and use restrictions for this preset.
    #[getter]
    fn license(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        crate::license_dict(py, self.license)
    }

    /// Reconoce una imagen liberando el GIL.
    ///
    /// Admite una ruta (`str`, `Path`) o un buffer en memoria (`bytes`).
    ///
    /// El tipo de retorno depende del preset: `OcrResult` en los presets de
    /// texto (`pp_ocrv6*`) y `StructureResult` en `pp_structurev3` (ADR-003).
    fn recognize(&self, py: Python<'_>, image: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let image_bytes: Vec<u8> = if let Ok(s) = image.extract::<&str>() {
            std::fs::read(s).map_err(OcrError::from)?
        } else if let Ok(b) = image.extract::<&[u8]>() {
            b.to_vec()
        } else if let Ok(path) = image.call_method0("__fspath__") {
            let p: String = path.extract()?;
            std::fs::read(p).map_err(OcrError::from)?
        } else {
            return Err(OcrError::InvalidInput {
                message: "image must be a path string, bytes, or PathLike object".into(),
            }.into());
        };

        let output = py.detach(|| {
            self.engine.recognize(&image_bytes)
        })?;

        match output {
            crate::core::OcrOutput::Text(result) => Ok(Py::new(py, result)?.into_any()),
            crate::core::OcrOutput::Structure(result) => Ok(Py::new(py, result)?.into_any()),
        }
    }
}

pub(crate) fn license_dict(
    py: Python<'_>,
    license: storage::license::License,
) -> PyResult<Py<PyAny>> {
    Ok(license.to_dict(py)?.into_any().unbind())
}

/// Registro del módulo nativo `pyocrust._pyocrust_core` (ADR-011).
/// Estado de los modelos en disco: directorio resuelto y artefactos por preset.
///
/// Devuelve un `dict` con `models_dir`, `offline`, `presets` (cada preset con su
/// lista de artefactos `name`/`present`/`size`/`required`) e `indra` (aún sin
/// preset que lo exija, `required = false`).
#[pyfunction]
#[pyo3(name = "models_status", signature = (custom_path=None))]
fn py_models_status(py: Python<'_>, custom_path: Option<&str>) -> PyResult<Py<PyAny>> {
    let config = storage::config::OcrConfig::new(custom_path.map(std::path::Path::new));

    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("models_dir", config.models_dir.to_string_lossy().to_string())?;
    dict.set_item("offline", storage::models::offline_requested())?;

    let presets = pyo3::types::PyDict::new(py);
    for (name, spec) in storage::registry::presets() {
        let artifacts = storage::registry::artifacts_for(&spec);
        let paths = config.resolve_paths(&spec);
        let root = paths.detection_model.parent().unwrap_or(&config.models_dir);
        presets.set_item(name, artifact_entries(py, root, artifacts)?)?;
    }
    dict.set_item("presets", presets)?;

    dict.set_item(
        "indra",
        artifact_entries(py, &config.models_dir.join("indra"), storage::registry::indra_artifacts())?,
    )?;

    Ok(dict.into_any().into())
}

/// Lista de artefactos de un preset como `list[dict]` para `models_status`.
fn artifact_entries<'py>(
    py: Python<'py>,
    root: &std::path::Path,
    artifacts: &[storage::registry::Artifact],
) -> PyResult<Bound<'py, pyo3::types::PyList>> {
    let list = pyo3::types::PyList::empty(py);
    for artifact in artifacts {
        let status = storage::models::artifact_status(&root.join(artifact.name), artifact);
        let entry = pyo3::types::PyDict::new(py);
        entry.set_item("name", &status.name)?;
        entry.set_item("present", status.present)?;
        entry.set_item("size", status.size)?;
        entry.set_item("required", status.required)?;
        list.append(entry)?;
    }
    Ok(list)
}

/// Registro del módulo nativo `pyocrust._pyocrust_core` (ADR-011).
#[pymodule]
#[pyo3(name = "_pyocrust_core")]
fn pyocrust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(native_version, m)?)?;
    m.add_function(wrap_pyfunction!(available_providers, m)?)?;
    core::error::register(m)?;
    core::types::register(m)?;
    // Utilidad de troceado opt-in (ADR-009): existe para `tests/test_tiling.py`
    // (`V1`), no la aplica el pipeline general.
    core::image_processor::pyapi::register(m)?;
    // Resolución de rutas de modelos (ADR-007, tarjeta I3) para `tests/test_config.py`.
    m.add_function(wrap_pyfunction!(storage::config::py_resolve_models_dir, m)?)?;
    // Estado de los modelos en disco (tarjeta `S2.0`) para `tests/test_models.py`.
    m.add_function(wrap_pyfunction!(py_models_status, m)?)?;
    m.add_function(wrap_pyfunction!(storage::catalog::model_catalog, m)?)?;
    m.add_function(wrap_pyfunction!(storage::catalog::pipeline_profiles, m)?)?;
    // Clase pública de alto nivel (tarjeta I4).
    m.add_class::<VeloceOCR>()?;
    m.add_class::<tasks::TaskPredictor>()?;
    Ok(())
}
