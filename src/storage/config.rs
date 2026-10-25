//! Resolución de rutas de modelos (`DESIGN.md` §3.2 y §7.1).
//!
//! Implementa el orden estricto de prioridad:
//! 1. Parámetro explícito (`custom_path`).
//! 2. Variables de entorno: `OAR_HOME` -> `OCR_MODELS_CACHE_DIR`.
//! 3. Fallback por defecto: `~/.oar`.
//!
//! Todas las rutas devueltas son absolutas y normalizadas.
//! No abre conexiones de red.
//! Casos tolerados sin pánico: directorios inexistentes, falta de permisos
//! de lectura y rutas relativas (se resuelven respecto al directorio actual de trabajo).

use std::env;
use std::ffi::OsString;
use std::path::{Component, Path, PathBuf};

use pyo3::prelude::*;

use crate::core::types::{ModelPaths, ModelSpec};

/// Variable de entorno estándar de `oar-ocr` (§3.2 nivel 2).
pub const OAR_HOME_ENV: &str = "OAR_HOME";

/// Variable de entorno compartida a nivel de sistema (§3.2 nivel 2).
pub const OCR_MODELS_CACHE_DIR_ENV: &str = "OCR_MODELS_CACHE_DIR";

/// Subdirectorio por defecto bajo el home del usuario (§3.2 nivel 3).
pub const DEFAULT_CACHE_SUBDIR: &str = ".oar";

/// Devuelve el directorio home del usuario de la plataforma sin dependencias externas.
pub fn home_dir() -> Option<PathBuf> {
    #[cfg(windows)]
    {
        env::var_os("USERPROFILE")
            .map(PathBuf::from)
            .or_else(|| {
                let drive = env::var_os("HOMEDRIVE")?;
                let path = env::var_os("HOMEPATH")?;
                let mut buf = PathBuf::from(drive);
                buf.push(path);
                Some(buf)
            })
    }
    #[cfg(not(windows))]
    {
        env::var_os("HOME").map(PathBuf::from)
    }
}

/// Expande `~` al inicio de una ruta si apunta al home del usuario.
pub fn expand_tilde(path: &Path) -> PathBuf {
    let s = path.to_string_lossy();
    if s == "~" {
        return home_dir().unwrap_or_else(|| PathBuf::from("~"));
    }
    if s.starts_with("~/") || s.starts_with("~\\") {
        if let Some(home) = home_dir() {
            return home.join(&s[2..]);
        }
    }
    path.to_path_buf()
}

/// Normaliza una ruta a forma absoluta sin requerir que exista en disco (§7.1).
///
/// Elimina componentes redundantes (`.` y `..`), expande tilde y antepone el
/// directorio actual de trabajo si la ruta es relativa.
pub fn normalize_path(path: &Path) -> PathBuf {
    let expanded = expand_tilde(path);
    let abs = if expanded.is_absolute() {
        expanded
    } else {
        env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(expanded)
    };

    let mut normalized = PathBuf::new();
    for comp in abs.components() {
        match comp {
            Component::CurDir => {}
            Component::ParentDir => {
                // Solo desapila si el componente anterior es un directorio normal.
                // Nunca desapila la raíz ni el prefijo de volumen.
                if let Some(Component::Normal(_)) = normalized.components().next_back() {
                    normalized.pop();
                }
            }
            c => normalized.push(c.as_os_str()),
        }
    }
    normalized
}

/// Resuelve la ruta del directorio de modelos según el orden estricto de prioridad (§3.2 y §7.1),
/// utilizando un proveedor de variables de entorno inyectable.
///
/// Orden de prioridad:
/// 1. `custom_path`: parámetro explícito provisto en la instanciación.
/// 2. `OAR_HOME`: variable de entorno estándar de `oar-ocr`.
/// 3. `OCR_MODELS_CACHE_DIR`: variable de entorno de sistema compartida.
/// 4. `~/.oar`: fallback por defecto.
pub fn resolve_models_dir_from<F>(custom_path: Option<&Path>, get_env: F) -> PathBuf
where
    F: Fn(&str) -> Option<OsString>,
{
    // Nivel 1: parámetro explícito
    if let Some(p) = custom_path {
        if !p.as_os_str().is_empty() {
            return normalize_path(p);
        }
    }

    // Nivel 2: OAR_HOME
    if let Some(val) = get_env(OAR_HOME_ENV) {
        if !val.is_empty() {
            let p = Path::new(&val);
            let normalized = normalize_path(p);
            if !p.is_absolute() {
                unsafe {
                    env::set_var(OAR_HOME_ENV, &normalized);
                }
            }
            return normalized;
        }
    }

    // Nivel 2: OCR_MODELS_CACHE_DIR
    if let Some(val) = get_env(OCR_MODELS_CACHE_DIR_ENV) {
        if !val.is_empty() {
            return normalize_path(Path::new(&val));
        }
    }

    // Nivel 3: fallback ~/.oar
    let fallback = home_dir()
        .unwrap_or_else(|| env::current_dir().unwrap_or_else(|_| PathBuf::from(".")))
        .join(DEFAULT_CACHE_SUBDIR);
    normalize_path(&fallback)
}

/// Resuelve la ruta del directorio de modelos consultando el entorno del proceso.
pub fn resolve_models_dir(custom_path: Option<&Path>) -> PathBuf {
    if let Some(val) = env::var_os(OAR_HOME_ENV) {
        if !val.is_empty() {
            let p = Path::new(&val);
            if !p.is_absolute() {
                let normalized = normalize_path(p);
                unsafe {
                    env::set_var(OAR_HOME_ENV, &normalized);
                }
            }
        }
    }
    resolve_models_dir_from(custom_path, |k| env::var_os(k))
}

/// Configuración de almacenamiento y rutas para el pipeline OCR (§3.2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OcrConfig {
    pub models_dir: PathBuf,
}

impl OcrConfig {
    /// Construye una nueva configuración resolviendo la ruta con la prioridad estricta.
    pub fn new(custom_path: Option<&Path>) -> Self {
        Self {
            models_dir: resolve_models_dir(custom_path),
        }
    }

    /// Resuelve las rutas de los ficheros para el preset solicitado.
    pub fn resolve_paths(&self, spec: &ModelSpec) -> ModelPaths {
        ModelPaths::new(&self.models_dir, spec)
    }
}

/// Función PyO3 para consultar la resolución de rutas desde Python / tests (`tests/test_config.py`).
#[pyfunction]
#[pyo3(name = "resolve_models_dir", signature = (custom_path=None))]
pub fn py_resolve_models_dir(py: Python<'_>, custom_path: Option<&str>) -> String {
    let p = custom_path.map(Path::new);
    let resolved = resolve_models_dir(p);
    if let Ok(oar_home) = env::var(OAR_HOME_ENV) {
        if let Ok(os) = py.import("os") {
            if let Ok(environ) = os.getattr("environ") {
                let _ = environ.set_item(OAR_HOME_ENV, oar_home);
            }
        }
    }
    resolved.to_string_lossy().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn mock_env(vars: &[(&str, &str)]) -> impl Fn(&str) -> Option<OsString> {
        let map: HashMap<String, OsString> = vars
            .iter()
            .map(|(k, v)| (k.to_string(), OsString::from(v)))
            .collect();
        move |key: &str| map.get(key).cloned()
    }

    #[test]
    fn level_1_custom_path_beats_level_2_and_level_3() {
        let custom = Path::new("/custom/models/path");
        let env_provider = mock_env(&[
            (OAR_HOME_ENV, "/env/oar_home"),
            (OCR_MODELS_CACHE_DIR_ENV, "/env/ocr_models_cache"),
        ]);

        let resolved = resolve_models_dir_from(Some(custom), env_provider);
        let expected = normalize_path(custom);
        assert_eq!(resolved, expected);
    }

    #[test]
    fn level_2_oar_home_beats_ocr_models_cache_dir_and_level_3() {
        let env_provider = mock_env(&[
            (OAR_HOME_ENV, "/env/oar_home"),
            (OCR_MODELS_CACHE_DIR_ENV, "/env/ocr_models_cache"),
        ]);

        let resolved = resolve_models_dir_from(None, env_provider);
        let expected = normalize_path(Path::new("/env/oar_home"));
        assert_eq!(resolved, expected);
    }

    #[test]
    fn level_2_ocr_models_cache_dir_beats_level_3_when_oar_home_absent() {
        let env_provider = mock_env(&[
            (OCR_MODELS_CACHE_DIR_ENV, "/env/ocr_models_cache"),
        ]);

        let resolved = resolve_models_dir_from(None, env_provider);
        let expected = normalize_path(Path::new("/env/ocr_models_cache"));
        assert_eq!(resolved, expected);
    }

    #[test]
    fn level_3_fallback_selected_when_no_inputs() {
        let env_provider = mock_env(&[]);

        let resolved = resolve_models_dir_from(None, env_provider);
        let fallback = home_dir()
            .unwrap_or_else(|| env::current_dir().unwrap())
            .join(DEFAULT_CACHE_SUBDIR);
        let expected = normalize_path(&fallback);
        assert_eq!(resolved, expected);
        assert!(resolved.ends_with(DEFAULT_CACHE_SUBDIR));
        assert!(resolved.is_absolute());
    }

    #[test]
    fn relative_oar_home_resolves_against_cwd_without_panic() {
        let env_provider = mock_env(&[(OAR_HOME_ENV, "relative/sub/dir")]);

        let resolved = resolve_models_dir_from(None, env_provider);
        let cwd = env::current_dir().unwrap();
        assert!(resolved.is_absolute());
        assert!(resolved.starts_with(&cwd));
        assert!(resolved.ends_with(Path::new("relative/sub/dir")));
        assert_eq!(env::var(OAR_HOME_ENV).unwrap(), resolved.to_string_lossy());
    }

    #[test]
    fn nonexistent_directory_does_not_panic_and_returns_normalized_absolute_path() {
        let nonexistent = Path::new("/path/that/does/not/exist/foo/../bar");
        let resolved = normalize_path(nonexistent);
        assert!(resolved.is_absolute());
        assert!(!resolved.to_string_lossy().contains("foo"));
        assert!(resolved.ends_with("bar"));
    }

    #[test]
    fn tilde_expansion_resolves_to_home_directory() {
        if let Some(home) = home_dir() {
            let tilde_path = Path::new("~/my_models");
            let expanded = expand_tilde(tilde_path);
            assert_eq!(expanded, home.join("my_models"));
        }
    }

    #[test]
    fn ocr_config_struct_resolves_paths_for_spec() {
        let custom = Path::new("/custom/ocr_models");
        let config = OcrConfig::new(Some(custom));
        let paths = config.resolve_paths(&ModelSpec::PpOcrV6(crate::core::types::OcrSize::Tiny));
        assert!(paths.detection_model.is_absolute());
        assert!(paths.detection_model.ends_with("pp-ocrv6_tiny_det.onnx"));
    }
}
