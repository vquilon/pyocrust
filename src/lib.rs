//! Núcleo nativo de `pyocrust`.
//!
//! Módulo PyO3 `pyocrust._pyocrust_core` (ADR-011) del crate `pyocrust_core`.
//! Registra las capas del paquete: `core` (tipos, errores, preprocesamiento,
//! tarjeta `I2`), `storage` (`I3`) e `engines` + clase pública `VeloceOCR`
//! (`I4`).
//!
//! Contrato vigente: `DESIGN.md` y `PLANNING.md` de la raíz del repositorio.

use pyo3::prelude::*;

use crate::engines::{PipelineOptions, TextDetectionOptions};
use crate::regions::RegionEngine;
use oar_ocr::core::config::OrtSessionConfig;
use oar_ocr::processors::LimitType;

pub mod core;
pub mod documents;
pub mod engines;
pub mod regions;
pub mod storage;
pub mod tasks;

use crate::core::{
    full_page_tiling_boxes, BoundingBox, FullPageTilingOptions, OcrEngineBackend, OcrError,
    OcrResult, Tile,
};

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
    /// Nombre del preset pedido, para los errores del SDK de regiones (§11).
    preset: String,
    /// Detección + rec + recorte por región (`§11 RDET`); `None` en los presets
    /// sin par det+rec propio (`indra`, VLM).
    regions: Option<RegionEngine>,
}

#[pymethods]
impl VeloceOCR {
    #[new]
    #[pyo3(signature = (
        preset = "pp_ocrv6",
        custom_path = None,
        device = "cpu",
        license_commercial_use = true,
        license_acknowledge = false,
        text_det_limit_side_len = None,
        text_det_limit_type = None,
        text_det_max_side_len = None,
        text_det_thresh = None,
        text_det_box_thresh = None,
        text_det_unclip_ratio = None,
        text_det_max_candidates = None,
        use_doc_orientation = true,
        use_doc_unwarping = true,
        use_textline_orientation = true,
        text_type = "general"
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        py: Python<'_>,
        preset: &str,
        custom_path: Option<&str>,
        device: &str,
        license_commercial_use: bool,
        license_acknowledge: bool,
        text_det_limit_side_len: Option<i64>,
        text_det_limit_type: Option<&str>,
        text_det_max_side_len: Option<i64>,
        text_det_thresh: Option<f32>,
        text_det_box_thresh: Option<f32>,
        text_det_unclip_ratio: Option<f32>,
        text_det_max_candidates: Option<i64>,
        use_doc_orientation: bool,
        use_doc_unwarping: bool,
        use_textline_orientation: bool,
        text_type: &str,
    ) -> PyResult<Self> {
        // Kwargs de deteccion (solo los consume `PpOcrV6`): validados antes de
        // tocar disco o red, y `.default()` = comportamiento historico.
        let detection = detection_options(
            text_det_limit_side_len,
            text_det_limit_type,
            text_det_max_side_len,
            text_det_thresh,
            text_det_box_thresh,
            text_det_unclip_ratio,
            text_det_max_candidates,
        )?;
        // Los mismos knobs alimentan el detector del SDK de regiones (§11.2): una
        // sola fuente de verdad, y `detect_regions` solo los pisa con sus kwargs.
        let base_detection = detection.clone();
        // Composicion del pipeline (solo la consume `PpOcrV6`). Los tres flags
        // salen encendidos, como en PaddleOCR: una pagina girada 90/180 grados o
        // curvada se reconoce igual que una recta. `text_type` cambia el
        // preprocesado del detector y el tipo de caja de la tarea.
        let composition = PipelineOptions {
            use_doc_orientation,
            use_doc_unwarping,
            use_textline_orientation,
            text_type: Some(match text_type {
                "general" | "table" | "seal" => text_type.to_string(),
                other => {
                    return Err(crate::core::error::PyOcrValueError::new_err(format!(
                        "text_type must be 'general', 'table' or 'seal', got {other:?}"
                    )))
                }
            }),
        };
        let spec = match preset {
            "pp_ocrv6" | "pp_ocrv6_tiny" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Tiny),
            "pp_ocrv6_small" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Small),
            "pp_ocrv6_medium" => crate::core::ModelSpec::PpOcrV6(crate::core::OcrSize::Medium),
            "pp_structurev3" => crate::core::ModelSpec::PpStructureV3,
            "indra" => crate::core::ModelSpec::Indra,
            // VLM (ADR-001): el nombre sólo existe con la feature `vl`; sin ella
            // cae al `_` y sale un `InvalidInput` tipado, nunca un preset fantasma.
            #[cfg(feature = "vl")]
            "glm_ocr" => crate::core::ModelSpec::Vlm(crate::core::VlmModel::GlmOcr),
            _ => {
                return Err(OcrError::InvalidInput {
                    message: format!(
                        "unknown preset '{preset}'. Expected one of: pp_ocrv6, pp_ocrv6_tiny, \
                         pp_ocrv6_small, pp_ocrv6_medium, pp_structurev3, indra{}",
                        if cfg!(feature = "vl") { ", glm_ocr" } else { "" }
                    ),
                }.into());
            }
        };

        let license = storage::license::License::for_spec(&spec);
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
        // construir el pipeline; el default `"cpu"` no toca ninguna GPU. El VLM
        // corre sobre Candle y resuelve su propio dispositivo (no sondea ONNX
        // Runtime): su `provider_effective` sale de `engines::vlm`.
        let vlm = matches!(spec, crate::core::ModelSpec::Vlm(_));
        let (ort_session, provider_effective) = if vlm {
            (OrtSessionConfig::new(), engines::vlm_provider_effective(device)?)
        } else {
            let selection = crate::core::device::resolve_device(device)?;
            (selection.config, selection.provider_effective)
        };

        // `S2.0`: preflight → descarga en paralelo de lo que falte → re-preflight.
        // Se libera el GIL: la descarga es I/O de red, no inferencia.
        py.detach(|| storage::models::ensure_models(&config.models_dir, &spec))?;

        let engine =
            py.detach(|| engines::create_engine(&spec, &paths, &ort_session, device, detection, composition))?;

        // Predictores residentes del SDK de regiones (§11). `None` para `indra`
        // y VLM. Solo cargan sus sesiones ONNX en la primera llamada a
        // `detect_regions`/`recognize_regions`: quien solo usa `recognize` no
        // paga ninguna sesión extra.
        let regions = RegionEngine::new(&spec, paths, ort_session, base_detection);

        Ok(Self {
            engine,
            config,
            license,
            provider_effective,
            preset: preset.to_string(),
            regions,
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
        let bytes = image_bytes(image)?;

        let output = py.detach(|| {
            self.engine.recognize(&bytes)
        })?;

        match output {
            crate::core::OcrOutput::Text(result) => Ok(Py::new(py, result)?.into_any()),
            crate::core::OcrOutput::Structure(result) => Ok(Py::new(py, result)?.into_any()),
        }
    }

    /// Cajas AABB de las regiones de texto, a la resolución que fijen los knobs.
    ///
    /// `DESIGN.md` §11.2 (`RDET`). Los `text_det_*` son los mismos que en
    /// `__init__`: los del constructor se heredan y los de aquí los pisan
    /// (`None` = heredado; con el constructor por defecto eso es 960/Max/4000 +
    /// los umbrales de hoy). Para ver una página de 7000x5000 a resolución
    /// nativa hacen falta los **tres**: `text_det_limit_type="min"`,
    /// `text_det_limit_side_len=64` y `text_det_max_side_len>=7000` — el tope del
    /// lado largo recorta incondicionalmente (§11.1.3).
    ///
    /// Usa el modelo de detección **del preset** (`pp-ocrv6_<tamano>_det.onnx`),
    /// no el `tiny` fijo de `TaskPredictor("text_detection")`. Devuelve la caja
    /// colapsada a AABB: se pierde la rotación de líneas inclinadas (para texto
    /// rotado, `recognize`, que conserva el cuadrilátero).
    #[pyo3(signature = (
        image,
        *,
        text_det_limit_side_len = None,
        text_det_limit_type = None,
        text_det_max_side_len = None,
        text_det_thresh = None,
        text_det_box_thresh = None,
        text_det_unclip_ratio = None,
        text_det_max_candidates = None
    ))]
    #[allow(clippy::too_many_arguments)]
    fn detect_regions(
        &self,
        py: Python<'_>,
        image: &Bound<'_, PyAny>,
        text_det_limit_side_len: Option<i64>,
        text_det_limit_type: Option<&str>,
        text_det_max_side_len: Option<i64>,
        text_det_thresh: Option<f32>,
        text_det_box_thresh: Option<f32>,
        text_det_unclip_ratio: Option<f32>,
        text_det_max_candidates: Option<i64>,
    ) -> PyResult<Vec<BoundingBox>> {
        let regions = self.region_engine()?;
        // Validación antes de decodificar o cargar nada (misma política que el
        // constructor): ningún valor fuera de rango cae a un default mudo.
        let overrides = detection_options(
            text_det_limit_side_len,
            text_det_limit_type,
            text_det_max_side_len,
            text_det_thresh,
            text_det_box_thresh,
            text_det_unclip_ratio,
            text_det_max_candidates,
        )?;
        let page = decode_page(image)?;
        regions.detect(py, page, &overrides)
    }

    /// OCR de las cajas dadas, recortando la imagen **nativa** (§11.2).
    ///
    /// Devuelve un `OcrResult` con **una `TextRegion` por caja de entrada** (en
    /// el mismo orden): `box` es la caja dada, `text` el texto reconocido o `""`
    /// y `confidence` su score o `0.0`. Recorta con `image::imageops::crop_imm`
    /// (sin reescalar la página) y pasa los recortes en lotes de
    /// `region_batch_size` al reconocedor del preset; el nº de pasadas es
    /// `ceil(N / region_batch_size)` (§11.5).
    #[pyo3(signature = (image, boxes, *, rec_score_threshold = None, region_batch_size = None))]
    fn recognize_regions(
        &self,
        py: Python<'_>,
        image: &Bound<'_, PyAny>,
        boxes: &Bound<'_, PyAny>,
        rec_score_threshold: Option<f32>,
        region_batch_size: Option<i64>,
    ) -> PyResult<OcrResult> {
        let regions = self.region_engine()?;
        let score_threshold = match rec_score_threshold {
            None => 0.0,
            Some(value) if (0.0..=1.0).contains(&value) => value,
            Some(value) => {
                return Err(crate::core::error::PyOcrValueError::new_err(format!(
                    "rec_score_threshold must be within [0, 1], got {value}"
                )))
            }
        };
        let batch = match region_batch_size {
            None => regions.default_batch(),
            Some(value) if value >= 1 => value as usize,
            Some(value) => {
                return Err(crate::core::error::PyOcrValueError::new_err(format!(
                    "region_batch_size must be >= 1, got {value}"
                )))
            }
        };
        let page = decode_page(image)?;
        let boxes = extract_boxes(boxes)?;
        regions.recognize(py, &page, &boxes, score_threshold, batch)
    }

    /// OCR de extremo a extremo en mosaicos, con deduplicación por centro.
    #[pyo3(signature = (
        image, *, tile_size=2048, tile_overlap=256,
        text_det_limit_side_len=None, text_det_limit_type=None,
        text_det_max_side_len=None, text_det_thresh=None,
        text_det_box_thresh=None, text_det_unclip_ratio=None,
        text_det_max_candidates=None
    ))]
    #[allow(clippy::too_many_arguments)]
    fn recognize_tiled(
        &self,
        py: Python<'_>,
        image: &Bound<'_, PyAny>,
        tile_size: i64,
        tile_overlap: i64,
        text_det_limit_side_len: Option<i64>,
        text_det_limit_type: Option<&str>,
        text_det_max_side_len: Option<i64>,
        text_det_thresh: Option<f32>,
        text_det_box_thresh: Option<f32>,
        text_det_unclip_ratio: Option<f32>,
        text_det_max_candidates: Option<i64>,
    ) -> PyResult<OcrResult> {
        let regions = self.region_engine()?;
        let tile_size = u32::try_from(tile_size).map_err(|_| {
            crate::core::error::PyOcrValueError::new_err("tile_size must be > 0")
        })?;
        let tile_overlap = u32::try_from(tile_overlap).map_err(|_| {
            crate::core::error::PyOcrValueError::new_err("tile_overlap must be >= 0")
        })?;
        if tile_size == 0 {
            return Err(crate::core::error::PyOcrValueError::new_err("tile_size must be > 0"));
        }
        let overrides = detection_options(
            text_det_limit_side_len, text_det_limit_type, text_det_max_side_len,
            text_det_thresh, text_det_box_thresh, text_det_unclip_ratio,
            text_det_max_candidates,
        )?;
        let page = decode_page(image)?;
        let (width, height) = page.dimensions();
        let options = FullPageTilingOptions { tile_size, overlap: tile_overlap };
        let boxes = full_page_tiling_boxes(width, height, &options).map_err(OcrError::from)?;
        let mut xs: Vec<u32> = boxes.iter().map(|(x, _, _, _)| *x).collect();
        let mut ys: Vec<u32> = boxes.iter().map(|(_, y, _, _)| *y).collect();
        xs.sort_unstable(); xs.dedup();
        ys.sort_unstable(); ys.dedup();
        let mut global_boxes = Vec::new();

        for (x, y, tile_width, tile_height) in boxes {
            let tile = Tile {
                x, y, width: tile_width, height: tile_height,
                image: image::imageops::crop_imm(&page, x, y, tile_width, tile_height).to_image(),
            };
            let global_x = tile.global_x(0) as f32;
            let global_y = tile.global_y(0) as f32;
            let local_boxes = regions.detect(py, tile.image, &overrides)?;
            let xi = xs.binary_search(&x).map_err(|_| {
                crate::core::error::PyOcrRuntimeError::new_err("tiling x-grid invariant failed")
            })?;
            let yi = ys.binary_search(&y).map_err(|_| {
                crate::core::error::PyOcrRuntimeError::new_err("tiling y-grid invariant failed")
            })?;
            let own_x1 = if xi == 0 { 0.0 } else {
                let prev_right = xs[xi - 1].saturating_add(tile_size).min(width);
                (prev_right + x) as f32 / 2.0
            };
            let own_x2 = if xi + 1 == xs.len() { width as f32 } else {
                let right = x.saturating_add(tile_width).min(width);
                (right + xs[xi + 1]) as f32 / 2.0
            };
            let own_y1 = if yi == 0 { 0.0 } else {
                let prev_bottom = ys[yi - 1].saturating_add(tile_size).min(height);
                (prev_bottom + y) as f32 / 2.0
            };
            let own_y2 = if yi + 1 == ys.len() { height as f32 } else {
                let bottom = y.saturating_add(tile_height).min(height);
                (bottom + ys[yi + 1]) as f32 / 2.0
            };

            for bbox in local_boxes {
                let center_x = global_x + (bbox.x1 + bbox.x2) / 2.0;
                let center_y = global_y + (bbox.y1 + bbox.y2) / 2.0;
                if center_x < own_x1 || center_x >= own_x2 || center_y < own_y1 || center_y >= own_y2 {
                    continue;
                }
                global_boxes.push(BoundingBox {
                    x1: global_x + bbox.x1,
                    y1: global_y + bbox.y1,
                    x2: global_x + bbox.x2,
                    y2: global_y + bbox.y2,
                });
            }
        }
        regions.recognize(py, &page, &global_boxes, 0.0, regions.default_batch())
    }
}

impl VeloceOCR {
    /// Predictores de región del preset, o `PyOcrValueError` tipado.
    fn region_engine(&self) -> PyResult<&RegionEngine> {
        self.regions.as_ref().ok_or_else(|| {
            crate::core::error::PyOcrValueError::new_err(format!(
                "preset '{}' has no text detection+recognition pair, so it has no region SDK. \
                 Supported presets: pp_ocrv6, pp_ocrv6_tiny, pp_ocrv6_small, pp_ocrv6_medium, \
                 pp_structurev3",
                self.preset
            ))
        })
    }
}

/// Bytes de una imagen `str`/`bytes`/`PathLike` (misma forma que `recognize`).
fn image_bytes(image: &Bound<'_, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(s) = image.extract::<&str>() {
        return Ok(std::fs::read(s).map_err(OcrError::from)?);
    }
    if let Ok(b) = image.extract::<&[u8]>() {
        return Ok(b.to_vec());
    }
    if let Ok(path) = image.call_method0("__fspath__") {
        let p: String = path.extract()?;
        return Ok(std::fs::read(p).map_err(OcrError::from)?);
    }
    Err(OcrError::InvalidInput {
        message: "image must be a path string, bytes, or PathLike object".into(),
    }
    .into())
}

/// Imagen RGB a resolución nativa, sin reescalar la página.
fn decode_page(image: &Bound<'_, PyAny>) -> PyResult<image::RgbImage> {
    let bytes = image_bytes(image)?;
    Ok(image::load_from_memory(&bytes)
        .map_err(OcrError::from)?
        .into_rgb8())
}

/// Validates encoded image bytes and returns their native dimensions.
#[pyfunction]
fn image_dimensions(image: &[u8]) -> PyResult<(u32, u32)> {
    let decoded = image::load_from_memory(image).map_err(|error| {
        crate::core::error::IncompatibleImageError::new_err(format!(
            "el contenido no es una imagen compatible: {error}"
        ))
    })?;
    Ok((decoded.width(), decoded.height()))
}

/// Cajas `BoundingBox` (o cualquier objeto con `x1`/`y1`/`x2`/`y2`).
fn extract_boxes(boxes: &Bound<'_, PyAny>) -> PyResult<Vec<BoundingBox>> {
    let mut extracted = Vec::new();
    for item in boxes.try_iter()? {
        let item = item?;
        let field = |name: &str| -> PyResult<f32> {
            item.getattr(name)?.extract().map_err(|_| {
                crate::core::error::PyOcrValueError::new_err(format!(
                    "boxes must be a sequence of BoundingBox; '{name}' is not a number"
                ))
            })
        };
        extracted.push(BoundingBox {
            x1: field("x1")?,
            y1: field("y1")?,
            x2: field("x2")?,
            y2: field("y2")?,
        });
    }
    Ok(extracted)
}

/// Construye `TextDetectionOptions` desde los kwargs de Python.
///
/// Todo `None` = `TextDetectionOptions::default()` (comportamiento historico).
/// Cualquier valor invalido (`limit_type` fuera de {min,max}, umbral fuera de
/// rango, lado <= 0) devuelve `PyOcrValueError`: nunca cae en silencio al default.
#[allow(clippy::too_many_arguments)]
fn detection_options(
    limit_side_len: Option<i64>,
    limit_type: Option<&str>,
    max_side_len: Option<i64>,
    thresh: Option<f32>,
    box_thresh: Option<f32>,
    unclip_ratio: Option<f32>,
    max_candidates: Option<i64>,
) -> PyResult<TextDetectionOptions> {
    let limit_type = match limit_type {
        None => None,
        Some("min") => Some(LimitType::Min),
        Some("max") => Some(LimitType::Max),
        Some(other) => {
            return Err(crate::core::error::PyOcrValueError::new_err(format!(
                "text_det_limit_type must be 'min' or 'max', got {other:?}"
            )))
        }
    };
    let unit = |value: Option<f32>, name: &str| -> PyResult<Option<f32>> {
        match value {
            None => Ok(None),
            Some(x) if (0.0..=1.0).contains(&x) => Ok(Some(x)),
            Some(x) => Err(crate::core::error::PyOcrValueError::new_err(format!(
                "{name} must be within [0, 1], got {x}"
            ))),
        }
    };
    let unclip_ratio = match unclip_ratio {
        None => None,
        Some(x) if x >= 0.0 => Some(x),
        Some(x) => {
            return Err(crate::core::error::PyOcrValueError::new_err(format!(
                "text_det_unclip_ratio must be >= 0, got {x}"
            )))
        }
    };
    let max_candidates = match max_candidates {
        None => None,
        Some(x) if x >= 1 => Some(x as usize),
        Some(x) => {
            return Err(crate::core::error::PyOcrValueError::new_err(format!(
                "text_det_max_candidates must be >= 1, got {x}"
            )))
        }
    };

    Ok(TextDetectionOptions {
        limit_side_len: positive_u32(limit_side_len, "text_det_limit_side_len")?,
        limit_type,
        max_side_len: positive_u32(max_side_len, "text_det_max_side_len")?,
        score_threshold: unit(thresh, "text_det_thresh")?,
        box_threshold: unit(box_thresh, "text_det_box_thresh")?,
        unclip_ratio,
        max_candidates,
    })
}

/// `Some(v)` solo si `1 <= v <= u32::MAX`; si no, `PyOcrValueError`.
fn positive_u32(value: Option<i64>, name: &str) -> PyResult<Option<u32>> {
    match value {
        None => Ok(None),
        Some(x) if (1..=(u32::MAX as i64)).contains(&x) => Ok(Some(x as u32)),
        Some(x) => Err(crate::core::error::PyOcrValueError::new_err(format!(
            "{name} must be a positive integer <= {}, got {x}",
            u32::MAX
        ))),
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
    m.add_function(wrap_pyfunction!(image_dimensions, m)?)?;
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
    // API de alto nivel de documentos PDF (DESIGN.md §13, tarjeta t_a7f78bfa).
    documents::register(m)?;
    Ok(())
}
