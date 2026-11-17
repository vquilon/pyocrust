//! API de alto nivel para documentos PDF (`DESIGN.md` §13, tarjeta `t_a7f78bfa`).
//!
//! Una sola biblioteca —PDFium, vía `pdfium-render`— da, por página y en el
//! **mismo** marco de coordenadas, la capa de texto con cajas y el rasterizado.
//! Cada página se decide con la regla de §13.3: si su capa de texto tiene al
//! menos `text_min_chars` caracteres se extrae tal cual (exacto, sin OCR); si no,
//! se marca `needs_ocr=True` y el llamante la rasteriza con [`render_page`] para
//! pasarla al OCR como cualquier imagen.
//!
//! Los dos errores de esta superficie son tipados y no hay *fallback* silencioso
//! (§13.2): entrada mal formada → `PyOcrValueError`; librería PDFium que no
//! carga → `PyOcrRuntimeError`. Nunca una lista vacía ni una página «sin texto»
//! fingida.
//!
//! Envelope (§13.6): una página a la vez, nunca todas. `parse_document` es
//! sólo metadatos (texto + tamaño); la memoria del raster sale de `render_page`.

use std::path::PathBuf;

use pdfium_render::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use crate::core::error::OcrError;
use crate::core::types::{BoundingBox, TextRegion};

/// Nombre de la variable con la ruta a la librería nativa de PDFium.
pub const PDFIUM_LIB_ENV: &str = "PYOCRUST_PDFIUM_LIB";

/// Metadatos de una página (`DESIGN.md` §13.2). Único tipo nuevo de la superficie.
#[derive(Debug, Clone, PartialEq)]
#[pyclass(frozen)]
pub struct PageInfo {
    /// Índice 1-indexado, como el usuario ve el PDF.
    #[pyo3(get)]
    pub index: i64,
    /// `True` si la capa de texto de la página supera `text_min_chars`.
    #[pyo3(get)]
    pub has_text_layer: bool,
    /// `== !has_text_layer`. Si es `True`, rasterizar con `render_page`.
    #[pyo3(get)]
    pub needs_ocr: bool,
    /// `round(width_pt * dpi / 72)`.
    #[pyo3(get)]
    pub width_px: i64,
    /// `round(height_pt * dpi / 72)`.
    #[pyo3(get)]
    pub height_px: i64,
    /// Segmentos del text-layer, o `[]` si la página necesita OCR.
    #[pyo3(get)]
    pub text_regions: Vec<TextRegion>,
}

#[pymethods]
impl PageInfo {
    fn __repr__(&self) -> String {
        format!(
            "PageInfo(index={}, has_text_layer={}, needs_ocr={}, width_px={}, height_px={}, \
             text_regions={})",
            self.index,
            self.has_text_layer,
            self.needs_ocr,
            self.width_px,
            self.height_px,
            self.text_regions.len()
        )
    }
}

/// Entrada rechazada por el llamante: se traduce a `PyOcrValueError`.
fn invalid(message: impl Into<String>) -> OcrError {
    OcrError::InvalidInput {
        message: message.into(),
    }
}

/// Regla text-layer vs render (`DESIGN.md` §13.3).
fn text_layer_rule(char_count: i64, text_min_chars: i64) -> bool {
    char_count >= text_min_chars
}

/// Píxeles de una medida en puntos PDF a `dpi`.
fn pixels(points: f32, dpi: i64) -> i64 {
    (points as f64 * dpi as f64 / 72.0).round() as i64
}

/// AABB de un rectángulo de PDFium en el marco único del API (`DESIGN.md` §13.2).
///
/// PDFium da el rectángulo con origen abajo-izquierda e `y` hacia arriba; el API
/// entrega AABB en puntos PDF con origen arriba-izquierda e `y` hacia abajo, así
/// que las cajas del text-layer y las del OCR son directamente comparables.
fn aabb_from_rect(left: f32, bottom: f32, right: f32, top: f32, page_height: f32) -> BoundingBox {
    BoundingBox::new(left, page_height - top, right, page_height - bottom)
}

/// Ruta de la librería nativa de PDFium.
///
/// Orden: `PYOCRUST_PDFIUM_LIB` (un fichero o un directorio) y, si no, el
/// directorio del propio módulo nativo —el wheel distribuye `pdfium.dll` junto
/// al `.pyd` (§13.4)—. Nunca se adivina ni se descarga nada.
fn pdfium_library_path(py: Python<'_>) -> Result<PathBuf, OcrError> {
    if let Some(value) = std::env::var_os(PDFIUM_LIB_ENV) {
        let candidate = PathBuf::from(value);
        return Ok(if candidate.is_dir() {
            Pdfium::pdfium_platform_library_name_at_path(&candidate)
        } else {
            candidate
        });
    }

    if let Ok(module) = py.import("pyocrust._pyocrust_core") {
        if let Ok(file) = module.getattr("__file__").and_then(|file| file.extract::<PathBuf>()) {
            if let Some(directory) = file.parent() {
                return Ok(Pdfium::pdfium_platform_library_name_at_path(directory));
            }
        }
    }

    Err(invalid(format!(
        "PDFium library not found: set {PDFIUM_LIB_ENV} to the pdfium dynamic library (or to the \
         directory that contains it)"
    )))
}

/// Enlaza PDFium con la librería resuelta, o reutiliza la ya enlazada.
///
/// `pdfium-render` promueve los bindings a un `OnceCell` global: la primera
/// llamada enlaza, las siguientes reciben `PdfiumLibraryBindingsAlreadyInitialized`
/// y reutilizan lo enlazado (`Pdfium::default()` no vuelve a cargar nada en esa
/// rama, así que no hay `panic` posible).
fn open_pdfium(py: Python<'_>) -> Result<Pdfium, OcrError> {
    let path = pdfium_library_path(py)?;
    match Pdfium::bind_to_library(&path) {
        Ok(bindings) => Ok(Pdfium::new(bindings)),
        Err(PdfiumError::PdfiumLibraryBindingsAlreadyInitialized) => Ok(Pdfium::default()),
        Err(error) => Err(OcrError::Config {
            message: format!(
                "could not load the PDFium library from '{}': {error}",
                path.display()
            ),
        }),
    }
}

/// Valida `dpi` antes de tocar el documento (§13.2).
fn validate_dpi(dpi: i64) -> Result<(), OcrError> {
    if dpi < 1 {
        return Err(invalid(format!("dpi must be >= 1, got {dpi}")));
    }
    Ok(())
}

/// Valida `text_min_chars` antes de tocar el documento (§13.2).
fn validate_text_min_chars(text_min_chars: i64) -> Result<(), OcrError> {
    if text_min_chars < 1 {
        return Err(invalid(format!(
            "text_min_chars must be >= 1, got {text_min_chars}"
        )));
    }
    Ok(())
}

/// Abre el documento o falla: nunca devuelve páginas «sin texto» fingidas.
fn open_document<'a>(
    pdfium: &'a Pdfium,
    path: &std::path::Path,
) -> Result<PdfDocument<'a>, OcrError> {
    if !path.is_file() {
        return Err(invalid(format!("no such file: {}", path.display())));
    }
    pdfium
        .load_pdf_from_file(path, None)
        .map_err(|error| invalid(format!("could not open PDF '{}': {error}", path.display())))
}

/// Traduce `pages` (1-indexado) a índices seleccionados, validando rango y duplicados.
fn select_pages(pages: Option<Vec<i64>>, total: i32) -> Result<Vec<i64>, OcrError> {
    let Some(pages) = pages else {
        return Ok((1..=total as i64).collect());
    };

    let mut seen = std::collections::HashSet::new();
    for &page in &pages {
        if page < 1 {
            return Err(invalid(format!(
                "page indexes are 1-based and must be >= 1, got {page}"
            )));
        }
        if !seen.insert(page) {
            return Err(invalid(format!("duplicate page index {page} in pages")));
        }
        if page > total as i64 {
            return Err(invalid(format!(
                "page index {page} out of range: the document has {total} page(s)"
            )));
        }
    }
    Ok(pages)
}

/// Extrae la validación previa y normaliza `pages` de Python.
fn extract_pages(pages: Option<Bound<'_, PyAny>>) -> Result<Option<Vec<i64>>, OcrError> {
    let Some(object) = pages else {
        return Ok(None);
    };

    let mut list = Vec::new();
    for item in object
        .try_iter()
        .map_err(|_| invalid("pages must be a sequence of ints"))?
    {
        let item = item.map_err(|_| invalid("pages must be a sequence of ints"))?;
        list.push(
            item.extract::<i64>()
                .map_err(|_| invalid(format!("pages must contain ints, not {item}")))?,
        );
    }
    Ok(Some(list))
}

fn parse_document_impl(
    py: Python<'_>,
    path: PathBuf,
    pages: Option<Vec<i64>>,
    dpi: i64,
    text_min_chars: i64,
) -> Result<Vec<PageInfo>, OcrError> {
    validate_dpi(dpi)?;
    validate_text_min_chars(text_min_chars)?;
    let pdfium = open_pdfium(py)?;
    let document = open_document(&pdfium, &path)?;
    let selected = select_pages(pages, document.pages().len())?;

    let mut result = Vec::with_capacity(selected.len());
    for index in selected {
        let page = document
            .pages()
            .get((index - 1) as i32)
            .map_err(|error| invalid(format!("could not load page {index}: {error}")))?;

        let height = page.height().value;
        let text = page
            .text()
            .map_err(|error| invalid(format!("could not read the text layer of page {index}: {error}")))?;

        let has_text_layer = text_layer_rule(text.len() as i64, text_min_chars);
        let mut text_regions = Vec::new();
        if has_text_layer {
            for segment in text.segments().iter() {
                let bounds = segment.bounds();
                // Extracción exacta del content stream: no hay puntuación de modelo (§13.2).
                text_regions.push(TextRegion::new(
                    segment.text(),
                    1.0,
                    aabb_from_rect(
                        bounds.left().value,
                        bounds.bottom().value,
                        bounds.right().value,
                        bounds.top().value,
                        height,
                    ),
                ));
            }
        }

        result.push(PageInfo {
            index,
            has_text_layer,
            needs_ocr: !has_text_layer,
            width_px: pixels(page.width().value, dpi),
            height_px: pixels(height, dpi),
            text_regions,
        });
    }

    Ok(result)
}

fn render_page_impl(
    py: Python<'_>,
    path: PathBuf,
    index: i64,
    dpi: i64,
) -> Result<Vec<u8>, OcrError> {
    validate_dpi(dpi)?;
    if index < 1 {
        return Err(invalid(format!(
            "page index is 1-based and must be >= 1, got {index}"
        )));
    }

    let pdfium = open_pdfium(py)?;
    let document = open_document(&pdfium, &path)?;
    let total = document.pages().len();
    if index > total as i64 {
        return Err(invalid(format!(
            "page index {index} out of range: the document has {total} page(s)"
        )));
    }

    let page = document
        .pages()
        .get((index - 1) as i32)
        .map_err(|error| invalid(format!("could not load page {index}: {error}")))?;

    // Mismo `dpi -> px` que `PageInfo`, así el PNG y los metadatos coinciden.
    let config = PdfRenderConfig::new()
        .set_target_width(pixels(page.width().value, dpi) as i32)
        .set_target_height(pixels(page.height().value, dpi) as i32);
    let bitmap = page
        .render_with_config(&config)
        .map_err(|error| invalid(format!("could not render page {index}: {error}")))?;

    let mut png = std::io::Cursor::new(Vec::new());
    bitmap
        .as_image()
        .map_err(|error| invalid(format!("could not convert the bitmap of page {index}: {error}")))?
        .write_to(&mut png, image::ImageFormat::Png)?;
    Ok(png.into_inner())
}

/// Metadatos por página: text-layer (texto + cajas) o marca de `needs_ocr`.
///
/// `pages=None` ⇒ todas; si no, una secuencia de índices **1-indexados**.
#[pyfunction]
#[pyo3(signature = (path, pages=None, dpi=200, *, text_min_chars=64))]
fn parse_document(
    py: Python<'_>,
    path: PathBuf,
    pages: Option<Bound<'_, PyAny>>,
    dpi: i64,
    text_min_chars: i64,
) -> PyResult<Vec<PageInfo>> {
    let pages = extract_pages(pages)?;
    Ok(parse_document_impl(py, path, pages, dpi, text_min_chars)?)
}

/// Rasteriza UNA página a PNG, listo para `VeloceOCR.recognize()`.
#[pyfunction]
#[pyo3(signature = (path, index, dpi=200))]
fn render_page(py: Python<'_>, path: PathBuf, index: i64, dpi: i64) -> PyResult<Vec<u8>> {
    Ok(render_page_impl(py, path, index, dpi)?)
}

/// Registra la superficie de documentos en el módulo nativo.
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PageInfo>()?;
    m.add_function(wrap_pyfunction!(parse_document, m)?)?;
    m.add_function(wrap_pyfunction!(render_page, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{aabb_from_rect, pixels, select_pages, text_layer_rule};

    #[test]
    fn text_layer_rule_is_the_documented_threshold() {
        assert!(!text_layer_rule(0, 64));
        assert!(!text_layer_rule(63, 64));
        assert!(text_layer_rule(64, 64));
        assert!(text_layer_rule(5000, 64));
        assert!(text_layer_rule(1, 1));
    }

    #[test]
    fn pixels_follow_the_dpi_formula() {
        assert_eq!(pixels(612.0, 200), 1700);
        assert_eq!(pixels(792.0, 200), 2200);
        assert_eq!(pixels(612.0, 72), 612);
        assert_eq!(pixels(595.3, 100), 827); // 826.8 → round
    }

    #[test]
    fn aabb_flips_the_pdfium_y_axis_to_the_api_frame() {
        // Página de 100 pt de alto; `rect` en el marco de PDFium (origen abajo).
        let box_ = aabb_from_rect(10.0, 20.0, 40.0, 60.0, 100.0);
        assert_eq!((box_.x1, box_.y1, box_.x2, box_.y2), (10.0, 40.0, 40.0, 80.0));
    }

    #[test]
    fn select_pages_defaults_to_all_and_rejects_bad_indexes() {
        assert_eq!(select_pages(None, 3).unwrap(), vec![1, 2, 3]);
        assert_eq!(select_pages(Some(vec![2, 5]), 5).unwrap(), vec![2, 5]);
        assert!(select_pages(Some(vec![0]), 5).is_err());
        assert!(select_pages(Some(vec![2, 2]), 5).is_err());
        assert!(select_pages(Some(vec![6]), 5).is_err());
    }
}
