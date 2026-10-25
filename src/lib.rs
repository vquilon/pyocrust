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

/// Versión del módulo nativo. La fachada `pyocrust/__init__.py` la expone.
#[pyfunction]
fn native_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
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
    Ok(())
}
