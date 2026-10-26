//! Errores del core y su traducción a excepciones Python (DESIGN.md §3.1).
//!
//! `OcrError` es el tipo de error de todo el crate: `Result<_, String>` está
//! prohibido por contrato (ADR-002) y `unwrap()` está prohibido en rutas de
//! datos. La traducción a `PyErr` se centraliza en `PyOcrError` para que el
//! mensaje que ve Python sea siempre el `Display` del error, sin `unwrap()`.

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;

/// Error del pipeline, con contexto y sin `unwrap()`.
#[derive(Debug)]
pub enum OcrError {
    /// Los artefactos del preset no están en disco. Lo rellena `storage::models`.
    MissingModelArtifacts {
        spec: String,
        missing: Vec<String>,
    },
    /// Modo offline activo (`PYOCRUST_OFFLINE=1`) y faltan artefactos. Lo rellena
    /// `storage::models::ensure_models`; `command` es el comando exacto que los trae.
    OfflineMissingArtifacts {
        spec: String,
        missing: Vec<String>,
        command: String,
    },
    /// La descarga de un artefacto falló. Lo rellena `storage::models::ensure_models`.
    DownloadFailed {
        artifact: String,
        url: String,
        reason: String,
    },
    /// Configuración inválida: directorio inexistente, `OAR_HOME` vacío...
    Config { message: String },
    /// La imagen no se pudo decodificar.
    ImageDecode {
        message: String,
        source: image::ImageError,
    },
    /// Falló la carga de un modelo o del pipeline.
    ModelLoad {
        model_path: String,
        reason: String,
    },
    /// Falló la inferencia.
    Inference {
        message: String,
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    /// Parámetros de preprocesamiento rechazados.
    Preprocess {
        message: String,
        source: Option<ImageProcessError>,
    },
    /// Entrada inválida (imagen vacía, preset no soportado...).
    InvalidInput { message: String },
    /// Cualquier error de E/S.
    Io(std::io::Error),
}

/// Causa del fallo de preprocesamiento, separada para que el mensaje de Python
/// no dependa de un `Display` interno.
#[derive(Debug)]
pub enum ImageProcessError {
    /// `overlap >= tile_size`: el avance sería cero o negativo y el bucle de
    /// mosaicos nunca terminaría. ADR-009 exige rechazarlo, no degradarlo.
    OverlapTooLarge { overlap: u32, tile_size: u32 },
    /// El tamaño de mosaico es cero.
    ZeroTileSize,
    /// El lado máximo de `ScaleDown` es cero.
    ZeroMaxSide,
    /// La imagen de entrada está vacía.
    EmptyImage,
}

impl std::fmt::Display for ImageProcessError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::OverlapTooLarge { overlap, tile_size } => write!(
                f,
                "overlap {overlap}px must be smaller than tile size {tile_size}px"
            ),
            Self::ZeroTileSize => write!(f, "tile size must be greater than zero"),
            Self::ZeroMaxSide => write!(f, "max side must be greater than zero"),
            Self::EmptyImage => write!(f, "input image is empty"),
        }
    }
}

impl std::error::Error for ImageProcessError {}

impl std::fmt::Display for OcrError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::MissingModelArtifacts { spec, missing } => {
                write!(
                    f,
                    "missing {count} model artifact(s) for preset '{spec}': {list}",
                    count = missing.len(),
                    list = missing.join(", ")
                )
            }
            Self::OfflineMissingArtifacts {
                spec,
                missing,
                command,
            } => {
                write!(
                    f,
                    "offline mode is active ({env}) and {count} model artifact(s) for preset \
                     '{spec}' are missing: {list}. No network request was made. Download them with: \
                     {command}",
                    env = crate::storage::models::OFFLINE_ENV,
                    count = missing.len(),
                    list = missing.join(", ")
                )
            }
            Self::DownloadFailed {
                artifact,
                url,
                reason,
            } => {
                write!(f, "download failed for '{artifact}' ({url}): {reason}")
            }
            Self::Config { message } => write!(f, "configuration error: {message}"),
            Self::ImageDecode { message, .. } => write!(f, "image decode failed: {message}"),
            Self::ModelLoad { model_path, reason } => {
                write!(f, "model load failed for '{model_path}': {reason}")
            }
            Self::Inference { message, .. } => write!(f, "inference failed: {message}"),
            Self::Preprocess { message, .. } => write!(f, "preprocessing failed: {message}"),
            Self::InvalidInput { message } => write!(f, "invalid input: {message}"),
            Self::Io(error) => write!(f, "io error: {error}"),
        }
    }
}

impl std::error::Error for OcrError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::ImageDecode { source, .. } => Some(source),
            Self::Inference { source, .. } => source
                .as_ref()
                .map(|source| source.as_ref() as &(dyn std::error::Error + 'static)),
            Self::Preprocess { source, .. } => source.as_ref().map(|e| e as &dyn std::error::Error),
            Self::Io(error) => Some(error),
            _ => None,
        }
    }
}

impl From<ImageProcessError> for OcrError {
    fn from(source: ImageProcessError) -> Self {
        Self::Preprocess {
            message: source.to_string(),
            source: Some(source),
        }
    }
}

impl From<std::io::Error> for OcrError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<image::ImageError> for OcrError {
    fn from(error: image::ImageError) -> Self {
        Self::ImageDecode {
            message: error.to_string(),
            source: error,
        }
    }
}

// Excepción Python base de `pyocrust` para todo error de `OcrError`.
//
// `ValueError` para entradas rechazadas por el llamante y `RuntimeError` para
// fallos del backend son las dos ramas que se distinguen; el resto hereda de
// `PyOcrError`, así que `except pyocrust.PyOcrError` captura cualquier error
// del crate sin depender de los tipos built-in.
create_exception!(_pyocrust_core, PyOcrError, PyException);
create_exception!(_pyocrust_core, PyOcrValueError, PyOcrError);
create_exception!(_pyocrust_core, PyOcrRuntimeError, PyOcrError);

/// Traduce `OcrError` a `PyErr` con la excepción tipada correspondiente.
impl From<OcrError> for PyErr {
    fn from(error: OcrError) -> Self {
        let message = error.to_string();
        match error {
            OcrError::InvalidInput { .. }
            | OcrError::Preprocess { .. }
            | OcrError::Config { .. } => PyOcrValueError::new_err(message),
            OcrError::ImageDecode { .. }
            | OcrError::Inference { .. }
            | OcrError::Io(_) => PyOcrRuntimeError::new_err(message),
            OcrError::MissingModelArtifacts { .. } | OcrError::ModelLoad { .. } => {
                PyOcrRuntimeError::new_err(message)
            }
            OcrError::OfflineMissingArtifacts { .. } | OcrError::DownloadFailed { .. } => {
                PyOcrRuntimeError::new_err(message)
            }
        }
    }
}

/// Registra las excepciones del crate en el módulo nativo.
///
/// `create_exception!` produce tipos que implementan `PyTypeInfo` pero **no**
/// `PyClass`, así que se registran con `add` + `get_type`, no con `add_class`
/// (que exige `PyClass`).
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("PyOcrError", m.py().get_type::<PyOcrError>())?;
    m.add("PyOcrValueError", m.py().get_type::<PyOcrValueError>())?;
    m.add("PyOcrRuntimeError", m.py().get_type::<PyOcrRuntimeError>())?;
    Ok(())
}
