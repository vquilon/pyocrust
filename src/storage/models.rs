//! Preflight de modelos en disco (`DESIGN.md` §7.2).
//!
//! Dado un `ModelSpec`, devuelve la lista de ficheros esperados y cuáles faltan en disco.
//! Permite informar al usuario con precisión qué artefactos faltan antes de cargar
//! las sesiones tensoriales. No descarga ni accede a la red.

use std::path::{Path, PathBuf};

use crate::core::error::OcrError;
use crate::core::types::{ModelPaths, ModelSpec};

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
    let missing = expected
        .iter()
        .filter(|p| !p.exists())
        .cloned()
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
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::types::OcrSize;
    use std::fs::File;

    fn create_temp_dir(prefix: &str) -> PathBuf {
        let path = std::env::temp_dir().join(format!("pyocrust_test_{}_{}", prefix, std::process::id()));
        let _ = std::fs::remove_dir_all(&path);
        std::fs::create_dir_all(&path).unwrap();
        path
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
    fn empty_directory_reports_all_9_missing_for_pp_structurev3() {
        let temp_dir = create_temp_dir("empty_structure");
        let spec = ModelSpec::PpStructureV3;

        let report = preflight(&temp_dir, &spec);

        assert_eq!(report.expected.len(), 9);
        assert_eq!(report.missing.len(), 9);
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
        File::create(temp_dir.join("pp-ocrv6_tiny_det.onnx")).unwrap();

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
        File::create(temp_dir.join("pp-ocrv6_tiny_det.onnx")).unwrap();
        File::create(temp_dir.join("pp-ocrv6_tiny_rec.onnx")).unwrap();
        File::create(temp_dir.join("ppocrv6_tiny_dict.txt")).unwrap();

        let report = preflight(&temp_dir, &spec);
        assert_eq!(report.expected.len(), 3);
        assert_eq!(report.missing.len(), 0);
        assert!(report.is_ready());
        assert!(report.ensure_ready().is_ok());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}
