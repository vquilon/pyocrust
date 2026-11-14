//! Backend VLM sobre `oar-ocr-vl` (Candle) — inferencia real página → Markdown.
//!
//! `ModelSpec::Vlm` sale de la factoría como una implementación más de
//! `OcrEngineBackend`, sin tocar la API pública (ADR-006). `oar-ocr-vl` es un
//! crate **distinto** de `oar-ocr` y no enlaza ONNX Runtime, así que este motor
//! ignora el `OrtSessionConfig` que sí reciben los demás y resuelve su propio
//! dispositivo de Candle (`cpu`, `cuda`, `auto`) con
//! `oar-ocr-vl::utils::parse_device`.
//!
//! # Pesos y descarga
//! GLM-OCR compone un detector PP-DocLayout externo, así que el preset exige
//! **dos** checkpoints (`zai-org/GLM-OCR` y `PaddlePaddle/PP-DocLayoutV3_safetensors`).
//! Ambos son snapshots inmutables que el auto-download de `oar-ocr-vl` deja en
//! `$OAR_HOME/models/<org>/<name>/<commit>`; como `storage::config` reexporta el
//! root resuelto del wrapper como `OAR_HOME`, caen **bajo el root del wrapper**
//! (`<models_dir>/models/...`) sin redirección extra.
//!
//! [`ensure_vlm_models`] (que llama `storage::models::ensure_models`) trae lo que
//! falte con ese auto-download y respeta `PYOCRUST_OFFLINE`: en offline y sin
//! pesos falla con `OcrError::OfflineMissingArtifacts` **antes** de tocar la red.
//!
//! # Salida
//! Un VLM sólo emite Markdown: `elements` y `regions` quedan vacíos (sin cajas) y
//! `StructureResult::markdown` es la página completa.
//!
//! # Ciclo de vida
//! - Construcción: `VlmEngine::new(VlmModel).with_device("cpu")`
//! - Carga: `load_model(&ModelPaths)` carga el `AnyPageParser` de Candle desde
//!   los snapshots ya presentes en disco (`ensure_vlm_models` los dejó ahí)
//! - Inferencia: `recognize(&[u8])` → `StructureResult{markdown, ..}`

use std::path::{Path, PathBuf};

use crate::core::error::OcrError;
use crate::core::types::{ModelPaths, ModelSpec, OcrOutput, VlmModel};
use crate::core::OcrEngineBackend;

#[cfg(feature = "vl")]
use crate::core::types::StructureResult;
#[cfg(feature = "vl")]
use crate::storage::models::offline_requested;
#[cfg(feature = "vl")]
use oar_ocr_vl::{
    DownloadSource, GlmOcr, LayoutPageParser, LayoutPageParserOptions, PageParser, PpDocLayout,
};

/// Error tipado de un preset VLM pedido en un build sin la feature `vl`.
///
/// Sólo existe en los builds sin `vl`: con la feature el preset es real y no hay
/// nada que rechazar. Se usa en las dos factorías para que el preset no exista
/// de forma honesta: ni se construye un motor vacío ni se anuncia como soportado.
#[cfg(not(feature = "vl"))]
pub fn requires_vl_error(model: VlmModel) -> OcrError {
    OcrError::InvalidInput {
        message: format!(
            "preset '{}' requires the `vl` feature (Candle / oar-ocr-vl); rebuild with \
             `maturin develop --features vl`",
            model.as_str()
        ),
    }
}

/// Factoría del motor VLM por `ModelPaths` y dispositivo pedido.
///
/// Con la feature `vl` construye el motor y carga el parser de Candle; sin ella
/// devuelve `OcrError::InvalidInput`.
#[cfg(feature = "vl")]
pub fn create_vlm_engine(
    model: &VlmModel,
    paths: &ModelPaths,
    device: &str,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    let mut engine = VlmEngine::new(*model).with_device(device);
    engine.load_model(paths)?;
    Ok(Box::new(engine))
}

/// Sin la feature `vl` no hay crate VLM que enlazar: error tipado, nunca un
/// motor que no puede cargar nada.
#[cfg(not(feature = "vl"))]
pub fn create_vlm_engine(
    model: &VlmModel,
    _paths: &ModelPaths,
    _device: &str,
) -> Result<Box<dyn OcrEngineBackend>, OcrError> {
    Err(requires_vl_error(*model))
}

/// Error tipado de un dispositivo que Candle no puede crear.
#[cfg(feature = "vl")]
fn device_error(device: &str, error: impl std::fmt::Display) -> OcrError {
    OcrError::InvalidInput {
        message: format!(
            "device='{device}' is not usable by the VLM (Candle) backend: {error}. Use 'cpu' \
             (default), 'auto', or 'cuda' (needs a build with --features vl-cuda)."
        ),
    }
}

/// Nombre honesto del dispositivo que Candle resolverá (`cpu`, `cuda`, `metal`).
///
/// `cpu` es el default (no toca ninguna GPU); `auto` prueba CUDA y cae a CPU;
/// `cuda` exige que Candle se haya compilado con `--features vl-cuda` — si no,
/// error tipado, nunca CPU etiquetado como CUDA.
#[cfg(feature = "vl")]
fn vlm_device_label(device: &str) -> Result<String, OcrError> {
    let resolved =
        oar_ocr_vl::utils::parse_device(device).map_err(|error| device_error(device, error))?;
    let name = if resolved.is_cuda() {
        "cuda"
    } else if resolved.is_metal() {
        "metal"
    } else {
        "cpu"
    };
    Ok(name.to_string())
}

/// EP efectivo del motor VLM **sin cargar pesos**, para `provider_effective`.
///
/// Es la misma resolución de dispositivo que aplicará `load_model`, así que la
/// fachada nunca etiqueta la inferencia con un EP que no es el que corre.
pub fn vlm_provider_effective(device: &str) -> Result<String, OcrError> {
    #[cfg(feature = "vl")]
    {
        vlm_device_label(device)
    }
    #[cfg(not(feature = "vl"))]
    {
        let _ = device;
        Err(OcrError::InvalidInput {
            message: "VLM presets require the `vl` feature; rebuild with `maturin develop \
                      --features vl`"
                .into(),
        })
    }
}

/// Snapshot ya descargado dentro de `<root>/models/<org>/<name>/`.
///
/// `oar-ocr-vl` publica cada snapshot como un directorio `<commit>/` de 40-64
/// dígitos hex junto a `refs/`; `refs` no es hex, así que cualquier
/// subdirectorio hexadecimal es una revisión publicada y completa.
fn local_snapshot(base: &Path) -> Option<PathBuf> {
    for entry in std::fs::read_dir(base).ok()?.flatten() {
        if !entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false) {
            continue;
        }
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if (40..=64).contains(&name.len()) && name.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Some(entry.path());
        }
    }
    None
}

/// Preflight + descarga de los dos snapshots del VLM bajo el root del wrapper.
///
/// Sin red si ya están en disco; con `PYOCRUST_OFFLINE` activo y alguno ausente,
/// `OcrError::OfflineMissingArtifacts` tipado (y **ninguna** petición de red); en
/// cualquier otro caso, auto-download de `oar-ocr-vl` (ModelScope, revisión por
/// defecto) con su resolución de commit y verificación de hashes.
pub fn ensure_vlm_models(root: &Path, model: VlmModel) -> Result<(), OcrError> {
    let spec = ModelSpec::Vlm(model);
    let paths = ModelPaths::new(root, &spec);
    let layout_base =
        paths
            .layout_detection_model
            .clone()
            .ok_or_else(|| OcrError::ModelLoad {
                model_path: model.layout_repo().into(),
                reason: "missing PP-DocLayout directory in ModelPaths".into(),
            })?;

    let missing_model = local_snapshot(&paths.detection_model).is_none();
    let missing_layout = local_snapshot(&layout_base).is_none();
    if !missing_model && !missing_layout {
        return Ok(());
    }

    #[cfg(not(feature = "vl"))]
    {
        // Sin el crate VLM no hay descargador que ofrecer: la factoría ya
        // devuelve un error tipado para el preset.
        let _ = (missing_model, missing_layout);
        Ok(())
    }
    #[cfg(feature = "vl")]
    {
        if offline_requested() {
            let mut missing = Vec::new();
            if missing_model {
                missing.push(model.checkpoint_repo().to_string());
            }
            if missing_layout {
                missing.push(model.layout_repo().to_string());
            }
            return Err(OcrError::OfflineMissingArtifacts {
                spec: model.as_str().to_string(),
                missing,
                command: format!(
                    "unset {}; python -c \"import pyocrust; pyocrust.VeloceOCR('{}')\"",
                    crate::storage::models::OFFLINE_ENV,
                    model.as_str()
                ),
            });
        }
        for (repo, missing) in [
            (model.checkpoint_repo(), missing_model),
            (model.layout_repo(), missing_layout),
        ] {
            if !missing {
                continue;
            }
            download_snapshot_with_fallback(repo)?;
        }
        Ok(())
    }
}

/// Descarga un snapshot probando ModelScope y, si falla, HuggingFace.
///
/// ModelScope es la fuente por defecto de `oar-ocr-vl`, pero su endpoint de
/// listado rechaza las peticiones anónimas desde algunos hosts (403 medido en
/// este); HuggingFace sirve los mismos repos con sus hashes LFS, así que se cae
/// a él cuando la fuente por defecto no responde. Sin esto, GLM-OCR no se podría
/// traer en un host sin sesión en ModelScope.
#[cfg(feature = "vl")]
fn download_snapshot_with_fallback(repo: &str) -> Result<PathBuf, OcrError> {
    let mut reasons = Vec::new();
    for source in [DownloadSource::ModelScope, DownloadSource::HuggingFace] {
        match oar_ocr_vl::download_snapshot(source, repo, None) {
            Ok(dir) => return Ok(dir),
            Err(error) => reasons.push(format!("{source:?}: {error}")),
        }
    }
    Err(OcrError::DownloadFailed {
        artifact: repo.to_string(),
        url: format!("https://huggingface.co/{repo}"),
        reason: reasons.join("; "),
    })
}

/// Motor VLM: modelo, dispositivo pedido, directorios resueltos y parser de
/// Candle una vez cargado.
pub struct VlmEngine {
    model: VlmModel,
    /// Dispositivo de Candle pedido (`cpu` por defecto).
    device: String,
    /// Directorio `<root>/models/<org>/<name>` del VLM, validado en `load_model`.
    model_dir: Option<PathBuf>,
    /// Directorio `<root>/models/<org>/<name>` del detector PP-DocLayout.
    layout_dir: Option<PathBuf>,
    /// Parser de `oar-ocr-vl` cargado (feature `vl`).
    ///
    /// Va tras un `Mutex` porque el VLM de Candle (`GlmOcr`) guarda su caché KV
    /// en un `RefCell`: es `Send` pero no `Sync`, y el trait del backend exige
    /// las dos. El cerrojo serializa las inferencias, que corren una a una.
    #[cfg(feature = "vl")]
    parser: Option<std::sync::Mutex<LayoutPageParser<PpDocLayout, GlmOcr>>>,
}

impl std::fmt::Debug for VlmEngine {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("VlmEngine")
            .field("model", &self.model)
            .field("device", &self.device)
            .field("model_dir", &self.model_dir)
            .field("layout_dir", &self.layout_dir)
            .finish_non_exhaustive()
    }
}

impl VlmEngine {
    /// Crea el motor sin checkpoints cargados (`load_model` los resuelve).
    pub fn new(model: VlmModel) -> Self {
        Self {
            model,
            device: "cpu".to_string(),
            model_dir: None,
            layout_dir: None,
            #[cfg(feature = "vl")]
            parser: None,
        }
    }

    /// Fija el dispositivo de Candle (`cpu`, `cuda`, `auto`) que usará `load_model`.
    pub fn with_device(mut self, device: &str) -> Self {
        self.device = device.to_string();
        self
    }

    /// Modelo de `oar-ocr-vl` al que corresponde el preset del wrapper.
    ///
    /// Es la costura con el crate VLM: el `AnyPageParser` se construye con este
    /// valor en `load_model`. Un test comprueba que los dos lados no se
    /// desalinean, y de paso que la feature `vl` enlaza el crate de verdad.
    #[cfg(feature = "vl")]
    pub fn oar_ocr_vl_model(model: VlmModel) -> oar_ocr_vl::AnyPageParserModel {
        match model {
            VlmModel::GlmOcr => oar_ocr_vl::AnyPageParserModel::GlmOcr,
        }
    }

    /// Modelo VLM que sirve este motor.
    pub fn model(&self) -> VlmModel {
        self.model
    }

    /// Directorios de snapshot resueltos (VLM, PP-DocLayout), si se cargaron.
    pub fn checkpoint_dirs(&self) -> (Option<&Path>, Option<&Path>) {
        (self.model_dir.as_deref(), self.layout_dir.as_deref())
    }
}

impl OcrEngineBackend for VlmEngine {
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError> {
        if paths.spec != ModelSpec::Vlm(self.model) {
            return Err(OcrError::InvalidInput {
                message: format!(
                    "preset '{:?}' is not supported by VlmEngine. Expected Vlm({:?})",
                    paths.spec, self.model
                ),
            });
        }

        let model_dir = paths.detection_model.clone();
        let layout_dir =
            paths
                .layout_detection_model
                .clone()
                .ok_or_else(|| OcrError::ModelLoad {
                    model_path: self.model.layout_repo().into(),
                    reason: "missing PP-DocLayout directory in ModelPaths".into(),
                })?;

        for dir in [&model_dir, &layout_dir] {
            if !dir.is_dir() {
                return Err(OcrError::ModelLoad {
                    model_path: dir.display().to_string(),
                    reason: format!(
                        "checkpoint for '{}' is not on disk; `oar-ocr-vl` downloads it into \
                         $OAR_HOME/models/<org>/<name>/<commit>",
                        self.model.as_str()
                    ),
                });
            }
        }

        #[cfg(feature = "vl")]
        {
            let device = oar_ocr_vl::utils::parse_device(&self.device)
                .map_err(|error| device_error(&self.device, error))?;
            let model_snapshot =
                local_snapshot(&model_dir).ok_or_else(|| OcrError::ModelLoad {
                    model_path: model_dir.display().to_string(),
                    reason: format!(
                        "no published snapshot for '{}'; let `oar-ocr-vl` fetch it (unset {})",
                        self.model.checkpoint_repo(),
                        crate::storage::models::OFFLINE_ENV
                    ),
                })?;
            let layout_snapshot =
                local_snapshot(&layout_dir).ok_or_else(|| OcrError::ModelLoad {
                    model_path: layout_dir.display().to_string(),
                    reason: format!(
                        "no published snapshot for '{}' (the PP-DocLayout the VLM composes)",
                        self.model.layout_repo()
                    ),
                })?;

            // GLM-OCR emite Markdown de la página completa; el detector
            // PP-DocLayout compone las regiones que el propio VLM reconoce.
            let layout =
                PpDocLayout::from_dir(&layout_snapshot, device.clone()).map_err(|error| {
                    OcrError::ModelLoad {
                        model_path: layout_snapshot.display().to_string(),
                        reason: error.to_string(),
                    }
                })?;
            let backend =
                GlmOcr::from_dir(&model_snapshot, device).map_err(|error| OcrError::ModelLoad {
                    model_path: model_snapshot.display().to_string(),
                    reason: error.to_string(),
                })?;
            self.parser = Some(std::sync::Mutex::new(LayoutPageParser::new(layout, backend)));
        }

        self.model_dir = Some(model_dir);
        self.layout_dir = Some(layout_dir);
        Ok(())
    }

    /// Inferencia real página → Markdown con el parser de Candle.
    ///
    /// Decodifica la imagen y delega en `parse_page`; el Markdown del documento
    /// sale tal cual (un VLM no emite cajas: `elements` y `regions` vacíos).
    fn recognize(&self, image: &[u8]) -> Result<OcrOutput, OcrError> {
        #[cfg(not(feature = "vl"))]
        {
            let _ = image;
            Err(requires_vl_error(self.model))
        }
        #[cfg(feature = "vl")]
        {
            let parser = self.parser.as_ref().ok_or_else(|| OcrError::InvalidInput {
                message: "VLM model not loaded; load_model must run first".into(),
            })?;
            let parser = parser.lock().map_err(|_| OcrError::Inference {
                message: "VLM parser lock poisoned by a previous panic".into(),
                source: None,
            })?;

            let rgb = image::load_from_memory(image)
                .map_err(|error| OcrError::ImageDecode {
                    message: error.to_string(),
                    source: error,
                })?
                .into_rgb8();

            let page = parser
                .parse_page(&rgb, &LayoutPageParserOptions::default())
                .map_err(|error| OcrError::Inference {
                    message: error.to_string(),
                    source: Some(Box::new(error)),
                })?;

            Ok(OcrOutput::Structure(StructureResult {
                markdown: page.markdown.unwrap_or_default(),
                elements: Vec::new(),
                regions: Vec::new(),
                formulas: Vec::new(),
            }))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn engine_rejects_a_non_vlm_preset() {
        let mut engine = VlmEngine::new(VlmModel::GlmOcr);
        let paths = ModelPaths::new(Path::new("/nonexistent"), &ModelSpec::Indra);
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::InvalidInput { .. }));
    }

    #[test]
    fn engine_reports_missing_checkpoint_directories() {
        let mut engine = VlmEngine::new(VlmModel::GlmOcr);
        let paths = ModelPaths::new(Path::new("/nonexistent"), &ModelSpec::Vlm(VlmModel::GlmOcr));
        let err = engine.load_model(&paths).unwrap_err();
        assert!(matches!(err, OcrError::ModelLoad { .. }), "{err:?}");
        assert!(engine.checkpoint_dirs().0.is_none());
    }

    #[test]
    fn recognize_without_a_loaded_model_is_a_typed_error_and_never_panics() {
        let engine = VlmEngine::new(VlmModel::GlmOcr);
        let err = engine.recognize(b"not an image").unwrap_err();
        // Con `vl` el motor existe pero no está cargado; sin `vl` el preset no
        // está enlazado. Las dos son `InvalidInput`, nunca un pánico.
        assert!(matches!(err, OcrError::InvalidInput { .. }), "{err:?}");
    }

    /// `local_snapshot` reconoce un commit (hex) y no confunde `refs/`.
    #[test]
    fn local_snapshot_picks_a_commit_directory_and_ignores_refs() {
        let base = std::env::temp_dir().join(format!("pyocrust_vlm_snap_{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&base);
        std::fs::create_dir_all(base.join("refs/modelscope")).unwrap();
        assert_eq!(local_snapshot(&base), None, "sin commit no hay snapshot");

        let commit = base.join("0123456789abcdef0123456789abcdef01234567");
        std::fs::create_dir_all(&commit).unwrap();
        assert_eq!(local_snapshot(&base).as_deref(), Some(commit.as_path()));
        assert_eq!(local_snapshot(&base.join("missing")), None);

        let _ = std::fs::remove_dir_all(&base);
    }

    /// El repo del wrapper y el de `oar-ocr-vl` deben coincidir: si el crate
    /// renombra el modelo, este test lo delata. Igual para el PP-DocLayout.
    #[cfg(feature = "vl")]
    #[test]
    fn checkpoint_repo_matches_oar_ocr_vl() {
        for model in [VlmModel::GlmOcr] {
            assert_eq!(
                model.checkpoint_repo(),
                VlmEngine::oar_ocr_vl_model(model).as_str()
            );
            assert_eq!(model.layout_repo(), oar_ocr_vl::DEFAULT_LAYOUT_REPO);
        }
    }

    /// `cpu` es el dispositivo honesto por defecto; un nombre desconocido se
    /// rechaza en vez de caer a CPU en silencio.
    #[cfg(feature = "vl")]
    #[test]
    fn vlm_device_resolution_is_honest() {
        assert_eq!(vlm_provider_effective("cpu").unwrap(), "cpu");
        assert_eq!(vlm_provider_effective("AUTO").unwrap(), "cpu");
        assert!(matches!(
            vlm_provider_effective("tpu").unwrap_err(),
            OcrError::InvalidInput { .. }
        ));
    }
}
