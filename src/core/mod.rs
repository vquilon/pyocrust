//! Capa `core` de `pyocrust`: tipos, trait del backend, errores y
//! preprocesamiento puro de imagen (ADR-009).
//!
//! Todo lo que vive aquí es independiente de `oar-ocr`: `types` nombra los
//! presets del ecosistema sin consumirlo y `image_processor` no conoce el
//! backend. El preprocesamiento es **opt-in** y no forma parte del pipeline
//! por defecto (ADR-009).

pub mod device;
pub mod error;
pub mod image_processor;
pub mod types;

pub use device::{available_providers, provider_name, resolve_device, DeviceSelection};
pub use error::{ImageProcessError, OcrError, PyOcrError};
pub use image_processor::{
    full_page_tiling, full_page_tiling_boxes, scale_down, FullPageTilingOptions, ScaleDownOptions,
    Tile, DEFAULT_MAX_SIDE, DEFAULT_OVERLAP, DEFAULT_TILE_SIZE,
};
pub use types::{
    BoundingBox, LayoutRegion, ModelPaths, ModelSpec, OcrOutput, OcrResult, OcrSize, OcrTask,
    StructureResult, TextRegion,
};

/// Contrato del backend OCR (`DESIGN.md` §3.1, ADR-002, ADR-006).
///
/// Un backend se construye **una sola vez** con rutas ya resueltas por
/// `storage::config`; a partir de ahí el pipeline queda residente e inmutable
/// y cada `recognize` se limita a inferir. No hay recarga tardía ni carga
/// mutable por llamada.
///
/// La entrada es un buffer en memoria (`&[u8]`), que es lo que produce la
/// decodificación de la imagen antes de la inferencia. Prohibido
/// `Result<_, String>` y prohibido `unwrap()` en rutas de datos.
pub trait OcrEngineBackend: Send + Sync {
    /// Construye el pipeline desde rutas locales resueltas.
    ///
    /// 3 artefactos para `ModelSpec::PpOcrV6`; 9 fuentes para
    /// `ModelSpec::PpStructureV3`.
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError>;

    /// Reconoce el texto de una imagen codificada en memoria.
    ///
    /// Devuelve `OcrOutput::Text` en los backends de texto y
    /// `OcrOutput::Structure` en PP-StructureV3: la estructura documental **no**
    /// se aplana a `OcrResult` (ADR-003).
    fn recognize(&self, image: &[u8]) -> Result<OcrOutput, OcrError>;
}
