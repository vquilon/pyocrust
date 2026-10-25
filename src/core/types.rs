//! Tipos del core (`DESIGN.md` §2 y §3.1).
//!
//! `TextRegion` y `OcrResult` son `#[pyclass]`: son la salida del pipeline que
//! cruza el límite Rust→Python. `OcrTask`, `OcrSize`, `ModelSpec` y
//! `ModelPaths` son tipos **Rust** a propósito: `DESIGN.md` §2 los lista como
//! enums, separados de los `Pyclasses` (`TextRegion`, `OcrResult`,
//! `StructureResult`), así que la selección de preset llega a Python como
//! cadena desde la fachada (tarjeta `I4`).
//!
//! `StructureResult` (ADR-003) se define en `I4`: definirlo aquí acoplaría el
//! core a un backend concreto.
//!
//! Los nombres de artefacto son los del registro de `oar-ocr` `0.10.1`
//! (`oar-ocr/src/oarocr/ocr.rs:113-133` y
//! `oar-ocr/src/oarocr/structure.rs:345-361`), verificados en el crate. Con
//! `auto-download` caen en `$OAR_HOME` con ese mismo nombre de fichero
//! (`oar-ocr-core/src/core/download/mod.rs:127-146`).

use std::path::{Path, PathBuf};

use pyo3::prelude::*;

/// Registra las clases del core en el módulo nativo.
///
/// `OcrTask`, `OcrSize`, `ModelSpec` y `ModelPaths` no se registran: no son
/// `#[pyclass]` (ver el doc del módulo).
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BoundingBox>()?;
    m.add_class::<TextRegion>()?;
    m.add_class::<OcrResult>()?;
    Ok(())
}

/// Tamaño de los modelos de texto de PP-OCRv6.
///
/// Réplica de `oar_ocr::oarocr::ocr::PpOcrV6Size`
/// (`oar-ocr/src/oarocr/ocr.rs:99-107`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum OcrSize {
    /// Modelos más rápidos, con el diccionario reducido de 6.904 entradas.
    #[default]
    Tiny,
    /// Equilibrio, con el diccionario completo de 18.708 entradas.
    Small,
    /// Máxima precisión, con el diccionario completo.
    Medium,
}

impl OcrSize {
    /// Nombre del tamaño, para la fachada de Python y los mensajes de error.
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Tiny => "tiny",
            Self::Small => "small",
            Self::Medium => "medium",
        }
    }

    /// Nombre de registro del modelo de detección (`ocr.rs:113-116`).
    pub fn detection_model(self) -> &'static str {
        match self {
            Self::Tiny => "pp-ocrv6_tiny_det.onnx",
            Self::Small => "pp-ocrv6_small_det.onnx",
            Self::Medium => "pp-ocrv6_medium_det.onnx",
        }
    }

    /// Nombre de registro del modelo de reconocimiento (`ocr.rs:122-125`).
    pub fn recognition_model(self) -> &'static str {
        match self {
            Self::Tiny => "pp-ocrv6_tiny_rec.onnx",
            Self::Small => "pp-ocrv6_small_rec.onnx",
            Self::Medium => "pp-ocrv6_medium_rec.onnx",
        }
    }

    /// Nombre de registro del diccionario (`ocr.rs:130-133`). Solo `Tiny`
    /// trae el suyo propio y reducido; `Small` y `Medium` comparten el
    /// completo de 18.708 entradas.
    pub fn character_dict(self) -> &'static str {
        match self {
            Self::Tiny => "ppocrv6_tiny_dict.txt",
            Self::Small | Self::Medium => "ppocrv6_dict.txt",
        }
    }
}

/// Tarea de inferencia que se pide al backend.
///
/// No forma parte del trait `OcrEngineBackend`: el contrato adoptado en
/// `DESIGN.md` §3.1 no lleva parámetro de tarea. Es el discriminador que la
/// fachada de Python (`I4`) usa para elegir preset y backend.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum OcrTask {
    /// OCR de texto: `OcrResult` con `TextRegion` (texto, confianza y caja).
    #[default]
    Text,
    /// PP-StructureV3: layout, tablas y fórmulas. ADR-003.
    Structure,
}

/// Preset de pipeline (ADR-002, `DESIGN.md` §3.1).
///
/// No es `#[pyclass]`: los presets se seleccionan por cadena desde Python.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ModelSpec {
    /// PP-OCRv6 (`OAROCRBuilder::pp_ocrv6`): 3 artefactos.
    PpOcrV6(OcrSize),
    /// PP-StructureV3 (`OARStructureBuilder::pp_structurev3`): 9 fuentes
    /// (8 `.onnx` + `table_structure_dict_ch.txt`), verificadas en
    /// `oar-ocr/src/oarocr/structure.rs:345-361`.
    ///
    /// `DESIGN.md` §3.1 dice "8 ficheros" y lista 9; manda el crate.
    PpStructureV3,
}

impl ModelSpec {
    /// Nombre estable del preset, para la factoría de `engines::mod`.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::PpOcrV6(_) => "pp_ocrv6",
            Self::PpStructureV3 => "pp_structurev3",
        }
    }

    /// Número de fuentes que el preset exige en disco.
    pub fn artifact_count(&self) -> usize {
        match self {
            Self::PpOcrV6(_) => 3,
            Self::PpStructureV3 => 9,
        }
    }
}

/// Rutas locales ya resueltas por `storage::config` para un `ModelSpec`.
///
/// El motor recibe rutas, nunca una ruta suelta: ningún pipeline de `oar-ocr`
/// se inicializa con un único fichero (ADR-002).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ModelPaths {
    pub detection_model: PathBuf,
    pub recognition_model: Option<PathBuf>,
    pub character_dict: Option<PathBuf>,
    pub layout_detection_model: Option<PathBuf>,
    pub table_classification_model: Option<PathBuf>,
    pub wired_table_structure_model: Option<PathBuf>,
    pub wireless_table_structure_model: Option<PathBuf>,
    pub wired_table_cell_detection_model: Option<PathBuf>,
    pub table_structure_dict: Option<PathBuf>,
    /// Preset al que corresponden estas rutas.
    pub spec: ModelSpec,
}

impl ModelPaths {
    /// Construye las rutas de un preset a partir del directorio resuelto.
    ///
    /// Los nombres son los del registro de `oar-ocr` `0.10.1`: con
    /// `auto-download` el caché `$OAR_HOME` los usa como nombre de fichero.
    /// El preset de estructura **embebe** PP-OCRv6 `Tiny`
    /// (`structure.rs:346-348`), diccionario reducido incluido
    /// (`size.character_dict()`).
    pub fn new(root: &Path, spec: &ModelSpec) -> Self {
        match spec {
            ModelSpec::PpOcrV6(size) => Self {
                detection_model: root.join(size.detection_model()),
                recognition_model: Some(root.join(size.recognition_model())),
                character_dict: Some(root.join(size.character_dict())),
                layout_detection_model: None,
                table_classification_model: None,
                wired_table_structure_model: None,
                wireless_table_structure_model: None,
                wired_table_cell_detection_model: None,
                table_structure_dict: None,
                spec: spec.clone(),
            },
            ModelSpec::PpStructureV3 => Self {
                detection_model: root.join(OcrSize::Tiny.detection_model()),
                recognition_model: Some(root.join(OcrSize::Tiny.recognition_model())),
                character_dict: Some(root.join(OcrSize::Tiny.character_dict())),
                layout_detection_model: Some(root.join("pp-doclayoutv3.onnx")),
                table_classification_model: Some(root.join("pp-lcnet_x1_0_table_cls.onnx")),
                wired_table_structure_model: Some(root.join("slanext_wired.onnx")),
                wireless_table_structure_model: Some(root.join("slanet_plus.onnx")),
                wired_table_cell_detection_model: Some(
                    root.join("rt-detr-l_wired_table_cell_det.onnx"),
                ),
                table_structure_dict: Some(root.join("table_structure_dict_ch.txt")),
                spec: spec.clone(),
            },
        }
    }

    /// Todas las rutas del preset, en orden de carga.
    ///
    /// Es la entrada del *preflight* de `storage::models` (`I3`), que es quien
    /// decide cuáles faltan en disco: este tipo no hace I/O.
    pub fn all(&self) -> Vec<PathBuf> {
        let mut paths = vec![self.detection_model.clone()];
        let optional = [
            &self.recognition_model,
            &self.character_dict,
            &self.layout_detection_model,
            &self.table_classification_model,
            &self.wired_table_structure_model,
            &self.wireless_table_structure_model,
            &self.wired_table_cell_detection_model,
            &self.table_structure_dict,
        ];
        paths.extend(optional.into_iter().flatten().cloned());
        paths
    }
}

/// Caja envolvente de una región, en coordenadas de imagen.
///
/// `oar-ocr` recorta las cajas de detección a nivel subpíxel, así que la
/// coordenada es flotante.
#[derive(Debug, Clone, Copy, PartialEq)]
#[pyclass(frozen)]
pub struct BoundingBox {
    #[pyo3(get)]
    pub x1: f32,
    #[pyo3(get)]
    pub y1: f32,
    #[pyo3(get)]
    pub x2: f32,
    #[pyo3(get)]
    pub y2: f32,
}

#[pymethods]
impl BoundingBox {
    /// Ancho de la caja; nunca negativo.
    #[getter]
    pub fn width(&self) -> f32 {
        (self.x2 - self.x1).abs()
    }

    /// Alto de la caja; nunca negativo.
    #[getter]
    pub fn height(&self) -> f32 {
        (self.y2 - self.y1).abs()
    }

    fn __repr__(&self) -> String {
        format!(
            "BoundingBox(x1={:.1}, y1={:.1}, x2={:.1}, y2={:.1})",
            self.x1, self.y1, self.x2, self.y2
        )
    }
}

/// Región de texto reconocida (`DESIGN.md` §3.1: texto, confianza y caja).
#[derive(Debug, Clone, PartialEq)]
#[pyclass(frozen)]
pub struct TextRegion {
    /// Texto reconocido. Una cadena vacía significa que el reconocimiento
    /// falló o se filtró por confianza baja.
    #[pyo3(get)]
    pub text: String,
    /// Confianza del reconocimiento, en `[0.0, 1.0]`.
    #[pyo3(get)]
    pub confidence: f32,
    /// Caja envolvente de la región. Se llama `box_` en Rust para no chocar
    /// con la palabra reservada; en Python el atributo es `box`.
    #[pyo3(get, name = "box")]
    pub box_: BoundingBox,
}

#[pymethods]
impl TextRegion {
    fn __repr__(&self) -> String {
        format!(
            "TextRegion(text={:?}, confidence={:.3}, box={})",
            self.text,
            self.confidence,
            self.box_.__repr__()
        )
    }
}

/// Resultado del pipeline de texto: una imagen, muchas regiones.
#[derive(Debug, Clone, PartialEq, Default)]
#[pyclass(frozen)]
pub struct OcrResult {
    /// Regiones reconocidas, en el orden en que el backend las devuelve.
    #[pyo3(get)]
    pub regions: Vec<TextRegion>,
}

#[pymethods]
impl OcrResult {
    /// Texto de todas las regiones, concatenado en orden.
    pub fn text(&self) -> String {
        self.regions
            .iter()
            .map(|region| region.text.as_str())
            .collect::<Vec<_>>()
            .join("\n")
    }

    /// Confianza media de las regiones, o `0.0` si no hay ninguna.
    #[getter]
    pub fn confidence(&self) -> f32 {
        if self.regions.is_empty() {
            return 0.0;
        }
        self.regions.iter().map(|r| r.confidence).sum::<f32>() / self.regions.len() as f32
    }

    fn __repr__(&self) -> String {
        format!("OcrResult(regions={})", self.regions.len())
    }

    fn __len__(&self) -> usize {
        self.regions.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pp_ocrv6_uses_the_registry_names_per_size() {
        let root = Path::new("/models");
        for (size, det, rec, dict) in [
            (
                OcrSize::Tiny,
                "pp-ocrv6_tiny_det.onnx",
                "pp-ocrv6_tiny_rec.onnx",
                "ppocrv6_tiny_dict.txt",
            ),
            (
                OcrSize::Small,
                "pp-ocrv6_small_det.onnx",
                "pp-ocrv6_small_rec.onnx",
                "ppocrv6_dict.txt",
            ),
            (
                OcrSize::Medium,
                "pp-ocrv6_medium_det.onnx",
                "pp-ocrv6_medium_rec.onnx",
                "ppocrv6_dict.txt",
            ),
        ] {
            let paths = ModelPaths::new(root, &ModelSpec::PpOcrV6(size));
            assert_eq!(paths.all().len(), 3, "{size:?} exige 3 artefactos");
            assert_eq!(paths.detection_model, root.join(det));
            assert_eq!(paths.recognition_model, Some(root.join(rec)));
            assert_eq!(paths.character_dict, Some(root.join(dict)));
            // El resto de campos quedan vacíos: no son de este preset.
            assert_eq!(paths.all()[1], root.join(rec));
            assert_eq!(paths.all()[2], root.join(dict));
        }
    }

    #[test]
    fn pp_structurev3_embeds_pp_ocrv6_tiny() {
        let paths = ModelPaths::new(Path::new("/models"), &ModelSpec::PpStructureV3);
        // 8 `.onnx` + el diccionario de estructura de tablas.
        assert_eq!(paths.all().len(), 9);
        assert_eq!(paths.spec, ModelSpec::PpStructureV3);
        assert_eq!(
            paths.detection_model,
            Path::new("/models/pp-ocrv6_tiny_det.onnx")
        );
        assert_eq!(
            paths.recognition_model,
            Some(PathBuf::from("/models/pp-ocrv6_tiny_rec.onnx"))
        );
        // El preset embebe Tiny, así que usa su diccionario reducido.
        assert_eq!(
            paths.character_dict,
            Some(PathBuf::from("/models/ppocrv6_tiny_dict.txt"))
        );
        assert_eq!(
            paths.layout_detection_model,
            Some(PathBuf::from("/models/pp-doclayoutv3.onnx"))
        );
        assert_eq!(
            paths.table_structure_dict,
            Some(PathBuf::from("/models/table_structure_dict_ch.txt"))
        );
    }
}
