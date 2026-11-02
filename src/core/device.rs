//! Selección del *execution provider* (EP) de ONNX Runtime, **opt-in**
//! (`DESIGN.md` §3.1.4, ADR-010; armonizado con `S1.7`).
//!
//! `device` es opcional y su valor por defecto es `"cpu"`: el baseline CPU
//! reproducible sigue siendo el comportamiento de partida y los builders
//! (`OAROCRBuilder` / `OARStructureBuilder` / predictores) no fijan ningún EP
//! salvo que el llamante lo pida. Esto **no** reintroduce la gobernanza de VRAM
//! que `S1.7` retiró: `device` solo elige el EP, no impone ningún presupuesto.
//!
//! Cuando se pide un EP concreto, la selección se **prueba de verdad**:
//! `OrtSessionConfig::resolve_auto` registra cada candidato y descarta los que
//! no arrancan (p. ej. CUDA sin cuDNN en `PATH`). El nombre efectivo se expone
//! sin adornos: si CUDA no registra, `device="cuda"` **falla** en vez de
//! etiquetar CPU como GPU. Nunca hay una fila GPU falsa.

use crate::core::error::OcrError;
use oar_ocr::core::config::{OrtExecutionProvider, OrtSessionConfig};

/// Nombre estable del EP para la API Python.
pub fn provider_name(provider: &OrtExecutionProvider) -> &'static str {
    match provider {
        OrtExecutionProvider::CPU => "cpu",
        OrtExecutionProvider::CUDA { .. } => "cuda",
        OrtExecutionProvider::DirectML { .. } => "directml",
        OrtExecutionProvider::OpenVINO { .. } => "openvino",
        OrtExecutionProvider::TensorRT { .. } => "tensorrt",
        OrtExecutionProvider::CoreML { .. } => "coreml",
        OrtExecutionProvider::WebGPU => "webgpu",
    }
}

/// EPs aceleradores que **registran de verdad** en este host, o `[]` si ninguno.
///
/// `auto()` arma los candidatos según las features compiladas (`cuda`,
/// `directml`+windows, `coreml`) y `resolve_auto()` prueba cada uno; aquí solo
/// se devuelven los supervivientes, sin el `CPU` de respaldo. Es la única fuente
/// honesta de "¿hay GPU para ONNX Runtime aquí?", no el inventario físico.
pub fn available_providers() -> Vec<String> {
    OrtSessionConfig::auto()
        .resolve_auto()
        .get_execution_providers()
        .into_iter()
        .filter(|provider| !matches!(provider, OrtExecutionProvider::CPU))
        .map(|provider| provider_name(&provider).to_string())
        .collect()
}

/// Configuración de sesión resuelta más el EP que correrá de verdad.
pub struct DeviceSelection {
    /// `OrtSessionConfig` con los EPs ya resueltos y probados.
    pub config: OrtSessionConfig,
    /// Nombre del EP que correrá (`cpu`, `cuda`, `directml`, ...).
    pub provider_effective: String,
}

/// Traduce `device` a una `OrtSessionConfig` resuelta y su `provider_effective`.
///
/// * `"cpu"` (por defecto) — EP CPU explícito; no sondea ni inicializa ninguna GPU.
/// * `"auto"` — CUDA > DirectML entre los candidatos compilados; CPU si ninguno registra.
/// * `"cuda"` / `"directml"` — exige que ese EP registre; si no, error honesto.
pub fn resolve_device(device: &str) -> Result<DeviceSelection, OcrError> {
    match device {
        "cpu" => Ok(DeviceSelection {
            config: OrtSessionConfig::new()
                .with_execution_providers(vec![OrtExecutionProvider::CPU]),
            provider_effective: "cpu".to_string(),
        }),
        "auto" => {
            let config = OrtSessionConfig::auto().resolve_auto();
            let effective = first_accelerator(&config).unwrap_or_else(|| "cpu".to_string());
            Ok(DeviceSelection {
                config,
                provider_effective: effective,
            })
        }
        "cuda" | "directml" => {
            let resolved = OrtSessionConfig::auto().resolve_auto();
            let mut providers = resolved.get_execution_providers();
            match providers
                .iter()
                .position(|provider| provider_name(provider) == device)
            {
                Some(index) => {
                    let provider = providers.remove(index);
                    Ok(DeviceSelection {
                        config: OrtSessionConfig::new()
                            .with_execution_providers(vec![provider, OrtExecutionProvider::CPU]),
                        provider_effective: device.to_string(),
                    })
                }
                None => Err(OcrError::InvalidInput {
                    message: format!(
                        "device='{device}' was requested but the {device} execution provider does not \
                         register on this host (available: {:?}). Build with '--features {device}' and \
                         make sure its runtime is present (e.g. cuDNN on PATH for CUDA); CPU is never \
                         reported as an accelerator.",
                        available_providers()
                    ),
                }),
            }
        }
        other => Err(OcrError::InvalidInput {
            message: format!(
                "unknown device '{other}'. Expected one of: cpu, auto, cuda, directml"
            ),
        }),
    }
}

fn first_accelerator(config: &OrtSessionConfig) -> Option<String> {
    config
        .get_execution_providers()
        .into_iter()
        .find(|provider| !matches!(provider, OrtExecutionProvider::CPU))
        .map(|provider| provider_name(&provider).to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cpu_is_selected_without_probing_any_gpu() {
        let selection = resolve_device("cpu").unwrap();
        assert_eq!(selection.provider_effective, "cpu");
        assert_eq!(
            selection.config.get_execution_providers(),
            vec![OrtExecutionProvider::CPU]
        );
    }

    #[test]
    fn unknown_device_is_rejected() {
        assert!(resolve_device("tpu").is_err());
    }

    #[test]
    fn explicit_accelerator_is_honest_about_registration() {
        // If the accelerator really registers here, requesting it succeeds and
        // reports itself; if it does not, the request fails instead of silently
        // downgrading to CPU (never a GPU row that is really CPU).
        for device in ["cuda", "directml"] {
            match resolve_device(device) {
                Ok(selection) => {
                    assert_eq!(selection.provider_effective, device);
                    assert!(available_providers().iter().any(|p| p == device));
                }
                Err(_) => assert!(!available_providers().iter().any(|p| p == device)),
            }
        }
    }

    #[test]
    fn auto_never_reports_an_unavailable_accelerator() {
        let selection = resolve_device("auto").unwrap();
        let reported = &selection.provider_effective;
        assert!(reported == "cpu" || available_providers().contains(reported));
    }
}
