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

use crate::core::{OcrEngineBackend, OcrError};

/// Versión del módulo nativo. La fachada `pyocrust/__init__.py` la expone.
#[pyfunction]
fn native_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Clase pública de alto nivel (`DESIGN.md` §3.1, ADR-002, ADR-011).
#[pyclass]
struct VeloceOCR {
    engine: Box<dyn OcrEngineBackend>,
    config: storage::config::OcrConfig,
}

#[pymethods]
impl VeloceOCR {
    #[new]
    #[pyo3(signature = (preset = "pp_ocrv6", custom_path = None))]
    fn new(preset: &str, custom_path: Option<&str>) -> PyResult<Self> {
        let spec = match preset {
            "pp_ocrv6" | "pp_ocrv6_tiny" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Tiny),
            "pp_ocrv6_small" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Small),
            "pp_ocrv6_medium" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Medium),
            "pp_structurev3" => crate::core::ModelSpec::PpStructureV3,
            _ => {
                return Err(OcrError::InvalidInput {
                    message: format!(
                        "unknown preset '{preset}'. Expected one of: pp_ocrv6, pp_ocrv6_tiny, pp_ocrv6_small, pp_ocrv6_medium, pp_structurev3"
                    ),
                }.into());
            }
        };

        let config = storage::config::OcrConfig::new(custom_path.map(std::path::Path::new));
        let paths = config.resolve_paths(&spec);

        let engine = engines::create_engine(&spec, &paths)?;

        Ok(Self { engine, config })
    }

    /// Directorio resuelto donde se buscan o almacenan los modelos.
    #[getter]
    fn models_dir(&self) -> String {
        self.config.models_dir.to_string_lossy().to_string()
    }

    /// Reconoce el texto de una imagen liberando el GIL.
    ///
    /// Admite una ruta (`str`, `Path`) o un buffer en memoria (`bytes`).
    fn recognize(&self, py: Python<'_>, image: &Bound<'_, PyAny>) -> PyResult<crate::core::OcrResult> {
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

        let result = py.detach(|| {
            self.engine.recognize(&image_bytes)
        })?;

        Ok(result)
    }
}

/// Registro del módulo nativo `pyocrust._pyocrust_core` (ADR-011).
#[pymodule]
#[pyo3(name = "_pyocrust_core")]
fn pyocrust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(native_version, m)?)?;
    core::error::register(m)?;
    core::types::register(m)?;
    // Utilidad de troceado opt-in (ADR-009): existe para `tests/test_tiling.py`
    // (`V1`), no la aplica el pipeline general.
    core::image_processor::pyapi::register(m)?;
    // Resolución de rutas de modelos (ADR-007, tarjeta I3) para `tests/test_config.py`.
    m.add_function(wrap_pyfunction!(storage::config::py_resolve_models_dir, m)?)?;
    // Clase pública de alto nivel (tarjeta I4).
    m.add_class::<VeloceOCR>()?;
    Ok(())
}
