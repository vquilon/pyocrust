//! Preflight de modelos en disco (`DESIGN.md` §7.2).
//!
//! Dado un `ModelSpec`, devuelve la lista de ficheros esperados y cuáles faltan en disco.
//! Permite informar al usuario con precisión qué artefactos faltan antes de cargar
//! las sesiones tensoriales. No descarga ni accede a la red.
//!
//! `S2.0` añade la auto-descarga: [`ensure_models`] hace preflight, baja en
//! paralelo lo que falta con el descargador propio ([`download::fetch`]) y vuelve
//! a validar. Es la pieza que cierra `S1.4` (el descargador estaba sin conectar).

use std::path::{Path, PathBuf};

use rayon::prelude::*;

use crate::core::error::OcrError;
use crate::core::types::{ModelPaths, ModelSpec};
use crate::storage::{download, registry};

/// Variable de entorno que desactiva cualquier petición de red (`S2.0`).
pub const OFFLINE_ENV: &str = "PYOCRUST_OFFLINE";

/// Hilos de descarga paralela. Cuatro: suficiente para no saturar la red ni el
/// disco, sin pelearse con el pool intra-op de ONNX Runtime (ADR-008).
const DOWNLOAD_THREADS: usize = 4;

/// `true` si `PYOCRUST_OFFLINE` pide no tocar la red.
pub fn offline_requested() -> bool {
    std::env::var_os(OFFLINE_ENV).is_some_and(|value| {
        let value = value.to_string_lossy().to_ascii_lowercase();
        !value.is_empty() && value != "0" && value != "false" && value != "no"
    })
}

/// Estado de un artefacto según el preflight.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ArtifactStatus {
    /// Nombre de fichero del artefacto.
    pub name: String,
    /// Ruta absoluta esperada en el directorio resuelto.
    pub path: PathBuf,
    /// Tamaño en bytes en disco; `0` si no existe.
    pub size: u64,
    /// Tamaño esperado según el registro; `0` si el registro no lo conoce.
    pub expected_size: u64,
    /// Existe y coincide con tamaño y hash esperado.
    pub present: bool,
    /// El preset lo exige (los opcionales siguen sin bloquear el arranque).
    pub required: bool,
}

impl ArtifactStatus {
    /// `true` si el artefacto bloquea el arranque.
    pub fn is_missing_required(&self) -> bool {
        self.required && !self.present
    }
}

/// Informe de preflight sobre la presencia física de los modelos en disco.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreflightReport {
    /// Preset evaluado.
    pub spec: ModelSpec,
    /// Directorio raíz resuelto donde se buscan los ficheros.
    pub root_dir: PathBuf,
    /// Rutas absolutas de todos los artefactos requeridos por el preset.
    pub expected: Vec<PathBuf>,
    /// Rutas de los artefactos que no existen en disco.
    pub missing: Vec<PathBuf>,
    /// Estado de cada artefacto, con su tamaño y si es obligatorio.
    pub artifacts: Vec<ArtifactStatus>,
}

impl PreflightReport {
    /// True si todos los modelos esperados se encuentran presentes en disco.
    pub fn is_ready(&self) -> bool {
        self.missing.is_empty()
    }

    /// Lista de los nombres de fichero (sin la ruta completa) que faltan en disco.
    pub fn missing_filenames(&self) -> Vec<String> {
        self.missing
            .iter()
            .map(|p| {
                p.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or_else(|| p.to_str().unwrap_or("?"))
                    .to_string()
            })
            .collect()
    }

    /// Nombres de los artefactos **obligatorios** que faltan.
    pub fn missing_required_filenames(&self) -> Vec<String> {
        self.artifacts
            .iter()
            .filter(|a| a.is_missing_required())
            .map(|a| a.name.clone())
            .collect()
    }

    /// Valida que el preset esté completo.
    ///
    /// Devuelve `OcrError::MissingModelArtifacts` con el conteo y la lista de nombres
    /// si falta al menos un fichero requerido.
    pub fn ensure_ready(&self) -> Result<(), OcrError> {
        if self.is_ready() {
            Ok(())
        } else {
            Err(OcrError::MissingModelArtifacts {
                spec: self.spec.as_str().to_string(),
                missing: self.missing_filenames(),
            })
        }
    }
}

/// Ejecuta el preflight para un preset en el directorio raíz indicado.
pub fn preflight(root_dir: &Path, spec: &ModelSpec) -> PreflightReport {
    let paths = ModelPaths::new(root_dir, spec);
    preflight_paths(&paths)
}

/// Ejecuta el preflight a partir de una estructura `ModelPaths` ya construida.
pub fn preflight_paths(paths: &ModelPaths) -> PreflightReport {
    let expected = paths.all();
    let artifacts = artifact_statuses(paths, &expected);
    let missing = artifacts
        .iter()
        .filter(|a| !a.present)
        .map(|a| a.path.clone())
        .collect();

    let root_dir = paths
        .detection_model
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .to_path_buf();

    PreflightReport {
        spec: paths.spec.clone(),
        root_dir,
        expected,
        missing,
        artifacts,
    }
}

/// Cruza las rutas esperadas con el registro para decidir qué está presente.
///
/// El hash se comprueba para Indra, que usa un registro HF fijado; para los
/// modelos ModelScope se mantiene el preflight barato por tamaño.
fn artifact_statuses(paths: &ModelPaths, expected: &[PathBuf]) -> Vec<ArtifactStatus> {
    let registered = registry::artifacts_for(&paths.spec);
    expected
        .iter()
        .enumerate()
        .map(|(index, path)| {
            let name = path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("?")
                .to_string();
            let (required, integrity) = match registered.get(index) {
                Some(artifact) => (artifact.required, artifact.integrity().ok()),
                None => {
                    // El preset y el registro se salen de sincronía: se marca como
                    // obligatorio y sin tamaño conocido para apuntar a registry.rs.
                    (true, None)
                }
            };
            let expected_size = integrity.map(|(_, size)| size).unwrap_or(0);
            let size = path.metadata().map(|m| m.len()).unwrap_or(0);
            let present = path.is_file()
                && expected_size > 0
                && size == expected_size
                && (paths.spec != ModelSpec::Indra
                    || integrity.is_some_and(|(sha256, _)| {
                        download::compute_sha256(path)
                            .is_ok_and(|actual| actual.eq_ignore_ascii_case(sha256))
                    }));
            ArtifactStatus {
                name,
                path: path.clone(),
                size,
                expected_size,
                present,
                required,
            }
        })
        .collect()
}

/// Estado de un artefacto individual contra un directorio raíz.
///
/// Es la pieza que `pyocrust.models_status()` cruza a Python.
pub fn artifact_status(path: &Path, artifact: &registry::Artifact) -> ArtifactStatus {
    let integrity = artifact.integrity().ok();
    let expected_size = integrity.map(|(_, size)| size).unwrap_or(0);
    let size = path.metadata().map(|m| m.len()).unwrap_or(0);
    let verify_hash = matches!(artifact.source, registry::Source::HuggingFace { .. });
    let present = path.is_file()
        && expected_size > 0
        && size == expected_size
        && (!verify_hash
            || integrity.is_some_and(|(sha256, _)| {
                download::compute_sha256(path)
                    .is_ok_and(|actual| actual.eq_ignore_ascii_case(sha256))
            }));
    ArtifactStatus {
        name: artifact.name.to_string(),
        path: path.to_path_buf(),
        size,
        expected_size,
        present,
        required: artifact.required,
    }
}

/// Preflight → descarga en paralelo de lo que falta → re-preflight.
///
/// Cierra `S1.4`: el descargador propio deja de estar muerto. Si todo está en
/// disco no toca la red; si `PYOCRUST_OFFLINE` está activo y falta algo, falla con
/// el error tipado y el comando exacto que lo traería.
pub fn ensure_models(root: &Path, spec: &ModelSpec) -> Result<(), OcrError> {
    let paths = ModelPaths::new(root, spec);
    let first = preflight_paths(&paths);
    if first.is_ready() {
        return Ok(());
    }

    if offline_requested() {
        return Err(offline_missing_error(&first));
    }

    let pending = pending_downloads(spec, &first)?;
    if !pending.is_empty() {
        download_all(&first.root_dir, &pending)?;
    }

    let second = preflight_paths(&paths);
    second.ensure_ready()
}

/// Ensure the registered model files for an individual `oar-ocr` task.
pub fn ensure_task_models(root: &Path, task: &str) -> Result<(), OcrError> {
    let artifacts = registry::task_artifacts(task).ok_or_else(|| OcrError::InvalidInput {
        message: format!("task not implemented yet: {task}"),
    })?;
    let mut pending = Vec::new();
    for artifact in artifacts {
        let status = artifact_status(&root.join(artifact.name), artifact);
        if artifact.required && !status.present {
            pending.push(artifact.resolve()?);
        }
    }
    if pending.is_empty() { return Ok(()); }
    if offline_requested() {
        return Err(offline_task_missing_error(task, &pending));
    }
    download_all(root, &pending)?;
    for artifact in artifacts {
        let status = artifact_status(&root.join(artifact.name), artifact);
        if artifact.required && !status.present {
            return Err(OcrError::MissingModelArtifacts { spec: task.to_string(), missing: vec![artifact.name.to_string()] });
        }
    }
    Ok(())
}

fn offline_task_missing_error(task: &str, pending: &[registry::ResolvedArtifact]) -> OcrError {
    OcrError::OfflineMissingArtifacts {
        spec: task.to_string(),
        missing: pending.iter().map(|artifact| artifact.name.clone()).collect(),
        command: format!(
            "{}; {}",
            pending.iter().map(|artifact| format!("download {} from {}", artifact.name, artifact.url)).collect::<Vec<_>>().join("; "),
            format!("unset {OFFLINE_ENV}; python -c \"import pyocrust; pyocrust.TaskPredictor('{task}')\"")
        ),
    }
}

/// Artefactos obligatorios que faltan, ya resueltos con URL y SHA-256.
fn pending_downloads(
    spec: &ModelSpec,
    report: &PreflightReport,
) -> Result<Vec<registry::ResolvedArtifact>, OcrError> {
    registry::artifacts_for(spec)
        .iter()
        .zip(report.artifacts.iter())
        .filter(|(artifact, status)| artifact.required && !status.present)
        .map(|(artifact, _)| artifact.resolve())
        .collect()
}

/// Descarga en paralelo, acotada a [`DOWNLOAD_THREADS`] hilos.
fn download_all(root: &Path, pending: &[registry::ResolvedArtifact]) -> Result<(), OcrError> {
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(DOWNLOAD_THREADS.min(pending.len()).max(1))
        .build()
        .map_err(|error| OcrError::Config {
            message: format!("no se pudo crear el pool de descarga: {error}"),
        })?;

    pool.install(|| {
        pending.par_iter().try_for_each(|artifact| {
            download::fetch(
                &artifact.url,
                &root.join(&artifact.name),
                &artifact.sha256,
            )
            .map_err(|error| OcrError::DownloadFailed {
                artifact: artifact.name.clone(),
                url: artifact.url.clone(),
                reason: error.to_string(),
            })
        })
    })
}

/// Error tipado para modo offline con artefactos ausentes.
fn offline_missing_error(report: &PreflightReport) -> OcrError {
    let spec = report.spec.as_str();
    let missing = report.missing_required_filenames();
    let urls: Vec<String> = report.artifacts.iter()
        .filter(|artifact| artifact.is_missing_required())
        .filter_map(|status| registry::artifacts_for(&report.spec).iter()
            .find(|artifact| artifact.name == status.name)
            .and_then(|artifact| artifact.url().ok()))
        .collect();
    OcrError::OfflineMissingArtifacts {
        spec: spec.to_string(),
        missing,
        command: format!("{}; unset {OFFLINE_ENV}; python -c \"import pyocrust; pyocrust.VeloceOCR('{spec}')\"", urls.iter().zip(&report.missing_required_filenames()).map(|(url, name)| format!("download {name} from {url}")).collect::<Vec<_>>().join("; ")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::types::OcrSize;

    fn create_temp_dir(prefix: &str) -> PathBuf {
        let path = std::env::temp_dir().join(format!("pyocrust_test_{}_{}", prefix, std::process::id()));
        let _ = std::fs::remove_dir_all(&path);
        std::fs::create_dir_all(&path).unwrap();
        path
    }

    /// Los tamaños reales del registro de `oar-ocr` para PP-OCRv6 Tiny.
    const TINY_DET: u64 = 1_780_590;
    const TINY_REC: u64 = 4_462_639;
    const TINY_DICT: u64 = 27_156;

    /// Crea un fichero **con el tamaño esperado**: el preflight decide por
    /// existencia + tamaño, no por existencia a secas (`S2.0`).
    fn crear_con_tamano(path: &Path, size: u64) {
        std::fs::write(path, vec![0u8; size as usize]).unwrap();
    }

    #[test]
    fn empty_directory_reports_all_missing_for_pp_ocrv6_tiny() {
        let temp_dir = create_temp_dir("empty_tiny");
        let spec = ModelSpec::PpOcrV6(OcrSize::Tiny);

        let report = preflight(&temp_dir, &spec);

        assert_eq!(report.expected.len(), 3);
        assert_eq!(report.missing.len(), 3);
        assert!(!report.is_ready());

        let missing = report.missing_filenames();
        assert_eq!(
            missing,
            vec![
                "pp-ocrv6_tiny_det.onnx",
                "pp-ocrv6_tiny_rec.onnx",
                "ppocrv6_tiny_dict.txt"
            ]
        );

        match report.ensure_ready() {
            Err(OcrError::MissingModelArtifacts { spec: s, missing: m }) => {
                assert_eq!(s, "pp_ocrv6");
                assert_eq!(m.len(), 3);
            }
            other => panic!("expected MissingModelArtifacts, got {other:?}"),
        }

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn empty_directory_reports_all_missing_for_pp_ocrv6_small() {
        let temp_dir = create_temp_dir("empty_small");
        let spec = ModelSpec::PpOcrV6(OcrSize::Small);

        let report = preflight(&temp_dir, &spec);

        assert_eq!(report.expected.len(), 3);
        assert_eq!(report.missing.len(), 3);
        assert!(!report.is_ready());

        let missing = report.missing_filenames();
        assert_eq!(
            missing,
            vec![
                "pp-ocrv6_small_det.onnx",
                "pp-ocrv6_small_rec.onnx",
                "ppocrv6_dict.txt"
            ]
        );

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn empty_directory_reports_all_11_missing_for_pp_structurev3() {
        let temp_dir = create_temp_dir("empty_structure");
        let spec = ModelSpec::PpStructureV3;

        let report = preflight(&temp_dir, &spec);

        assert_eq!(report.expected.len(), 11);
        assert_eq!(report.missing.len(), 11);
        assert!(!report.is_ready());

        let missing = report.missing_filenames();
        assert!(missing.contains(&"pp-doclayoutv3.onnx".to_string()));
        assert!(missing.contains(&"pp-lcnet_x1_0_table_cls.onnx".to_string()));
        assert!(missing.contains(&"slanext_wired.onnx".to_string()));
        assert!(missing.contains(&"slanet_plus.onnx".to_string()));
        assert!(missing.contains(&"rt-detr-l_wired_table_cell_det.onnx".to_string()));
        assert!(missing.contains(&"table_structure_dict_ch.txt".to_string()));

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn partially_populated_directory_reports_only_missing_files() {
        let temp_dir = create_temp_dir("partial_tiny");
        let spec = ModelSpec::PpOcrV6(OcrSize::Tiny);

        // Crear solo 1 de los 3 ficheros
        crear_con_tamano(&temp_dir.join("pp-ocrv6_tiny_det.onnx"), TINY_DET);

        let report = preflight(&temp_dir, &spec);
        assert_eq!(report.expected.len(), 3);
        assert_eq!(report.missing.len(), 2);
        assert!(!report.is_ready());

        let missing = report.missing_filenames();
        assert!(!missing.contains(&"pp-ocrv6_tiny_det.onnx".to_string()));
        assert!(missing.contains(&"pp-ocrv6_tiny_rec.onnx".to_string()));
        assert!(missing.contains(&"ppocrv6_tiny_dict.txt".to_string()));

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn fully_populated_directory_is_ready_and_ensure_ready_succeeds() {
        let temp_dir = create_temp_dir("full_tiny");
        let spec = ModelSpec::PpOcrV6(OcrSize::Tiny);

        // Crear los 3 ficheros requeridos
        crear_con_tamano(&temp_dir.join("pp-ocrv6_tiny_det.onnx"), TINY_DET);
        crear_con_tamano(&temp_dir.join("pp-ocrv6_tiny_rec.onnx"), TINY_REC);
        crear_con_tamano(&temp_dir.join("ppocrv6_tiny_dict.txt"), TINY_DICT);

        let report = preflight(&temp_dir, &spec);
        assert_eq!(report.expected.len(), 3);
        assert_eq!(report.missing.len(), 0);
        assert!(report.is_ready());
        assert!(report.ensure_ready().is_ok());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn preflight_detecta_un_fichero_truncado_sin_re_hashearlo() {
        let temp_dir = create_temp_dir("truncado_tiny");
        let spec = ModelSpec::PpOcrV6(OcrSize::Tiny);

        // El detector existe pero con 1 byte: debe contar como ausente.
        std::fs::write(temp_dir.join("pp-ocrv6_tiny_det.onnx"), b"x").unwrap();
        crear_con_tamano(&temp_dir.join("pp-ocrv6_tiny_rec.onnx"), TINY_REC);
        crear_con_tamano(&temp_dir.join("ppocrv6_tiny_dict.txt"), TINY_DICT);

        let report = preflight(&temp_dir, &spec);
        assert_eq!(report.missing.len(), 1);
        assert_eq!(report.missing_filenames(), vec!["pp-ocrv6_tiny_det.onnx"]);

        let det = &report.artifacts[0];
        assert_eq!(det.size, 1);
        assert_eq!(det.expected_size, TINY_DET);
        assert!(!det.present);
        assert!(det.is_missing_required());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn indra_rechaza_cache_con_tamano_correcto_y_hash_incorrecto() {
        let temp_dir = create_temp_dir("indra_hash");
        let artifact = crate::storage::registry::artifacts_for(&ModelSpec::Indra)[0];
        let path = temp_dir.join(artifact.name);
        let (_, size) = artifact.integrity().unwrap();
        std::fs::write(&path, vec![0x5a; size as usize]).unwrap();

        let status = artifact_status(&path, &artifact);
        assert_eq!(status.size, size);
        assert!(!status.present, "tamaño correcto no sustituye la validación SHA-256");
        assert!(status.is_missing_required());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn indra_preflight_rechaza_hash_incorrecto_a_tamano_correcto() {
        let temp_dir = create_temp_dir("indra_preflight_hash");
        let paths = ModelPaths::new(&temp_dir, &ModelSpec::Indra);
        let artifact = crate::storage::registry::artifacts_for(&ModelSpec::Indra)[0];
        let path = paths.all()[0].clone();
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        let (_, size) = artifact.integrity().unwrap();
        std::fs::write(&path, vec![0x5a; size as usize]).unwrap();

        let report = preflight_paths(&paths);
        assert!(report.missing_filenames().contains(&artifact.name.to_string()));
        assert!(!report.artifacts[0].present);

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn offline_task_error_preserves_artifact_name_and_url() {
        let artifact = registry::task_artifacts("document_orientation").unwrap()[0].resolve().unwrap();
        let error = offline_task_missing_error("document_orientation", &[artifact.clone()]);
        assert!(error.to_string().contains(&artifact.name));
        assert!(error.to_string().contains(&artifact.url));
        match error {
            OcrError::OfflineMissingArtifacts { spec, missing, command } => {
                assert_eq!(spec, "document_orientation");
                assert_eq!(missing, vec![artifact.name]);
                assert!(command.contains(&artifact.url));
            }
            other => panic!("expected typed offline error, got {other:?}"),
        }
    }

    #[test]
    fn el_registro_y_las_rutas_del_preset_van_alineados() {
        for (name, spec) in crate::storage::registry::presets() {
            let paths = ModelPaths::new(Path::new("/models"), &spec);
            let registro = crate::storage::registry::artifacts_for(&spec);
            assert_eq!(
                paths.all().len(), registro.len(),
                "el preset '{name}' y el registro tienen longitudes distintas"
            );
            for (ruta, artifact) in paths.all().iter().zip(registro) {
                assert_eq!(ruta.file_name().and_then(|n| n.to_str()), Some(artifact.name),
                    "el preset '{name}' y el registro se desordenan en {}",
                    ruta.display());
            }
        }
    }
}
