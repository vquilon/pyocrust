//! Licencias de los **pesos** de los modelos (Fase 10, tarjeta `L1`).
//!
//! La licencia del código (`Apache-2.0`) no cubre los pesos: cada artefacto
//! trae la suya. Este módulo es la única fuente de verdad para el catálogo
//! (`model_catalog()`, `pipeline_profiles()`) y para el bloqueo por defecto de
//! `VeloceOCR`/`TaskPredictor` (tarjeta `L2`).
//!
//! Clasificación verificada contra `licenses-report.pdf` y las fuentes
//! primarias: la familia Paddle/PP es `Apache-2.0` y los artefactos de `indra`
//! son un `OpenRAIL-M` modificado por Datalab. Lo no reconocido es `Unknown`
//! y queda **restringido por defecto** (default-deny).

use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::registry;

/// License terms assigned to one model or its companion artifacts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct License {
    pub spdx: &'static str,
    pub commercial_use: bool,
    pub acknowledge: bool,
    pub notes: &'static str,
    pub url: Option<&'static str>,
}

const APACHE: License = License {
    spdx: "Apache-2.0",
    commercial_use: true,
    acknowledge: false,
    notes: "Paddle/PP model family; Apache-2.0 license.",
    url: Some("https://www.apache.org/licenses/LICENSE-2.0"),
};

const INDRA: License = License {
    spdx: "OpenRAIL-M-Mod",
    commercial_use: false,
    acknowledge: true,
    notes: "OpenRAIL-M modified by Datalab (pinned revision): §7 attribution, §8 share-alike on the Output, §4 SaaS/API hosting counts as distribution and the restrictions must be passed on; §5 / Attachment A §2 forbids use above USD 20M revenue or funding and competing with any Licensor product or service, with personal/research exceptions.",
    url: Some("https://huggingface.co/datalab-to/indra-ocr/blob/bd02167fdf2005a19962cc15188f8496a2c87d3b/LICENSE"),
};

const UNKNOWN: License = License {
    spdx: "Unknown",
    commercial_use: false,
    acknowledge: false,
    notes: "License not identified; treat this artifact as restricted and do not use it.",
    url: None,
};

/// Restrictividad: `Unknown` > `OpenRAIL-M-Mod` > resto.
fn rank(license: &License) -> u8 {
    match license.spdx {
        "Unknown" => 2,
        "OpenRAIL-M-Mod" => 1,
        _ => 0,
    }
}

/// Los artefactos de `indra` se leen del registro único (`registry.rs`), nunca
/// de una lista duplicada que pueda quedar desalineada.
fn is_indra(name: &str) -> bool {
    name == "indra"
        || name.starts_with("indra-")
        || name.starts_with("indra_")
        || registry::indra_artifacts().iter().any(|artifact| artifact.name == name)
}

impl License {
    /// Licencia no verificada: el origen de los pesos no se puede comprobar.
    pub fn unknown() -> Self {
        UNKNOWN
    }

    /// License for a registered artifact; unknown names are denied by default.
    pub fn for_artifact(name: &str) -> Self {
        let name = name.to_ascii_lowercase();
        if is_indra(&name) {
            return INDRA;
        }

        let paddle_terms = [
            "pp-ocrv3", "pp-ocrv4", "pp-ocrv5", "pp-ocrv6", "ppocr",
            "pp-doclayout", "pp-docblocklayout", "picodet", "slanet", "slanext",
            "rt-detr", "pp-lcnet", "uvdoc", "pp-formulanet", "unimernet",
            "latex_ocr", "table_structure_dict_ch", "ch_repsvtr", "ch_svtrv2",
        ];
        if paddle_terms.iter().any(|term| name.contains(term))
            || name.ends_with("_dict.txt")
            || name == "table_structure_dict_ch.txt"
        {
            APACHE
        } else {
            UNKNOWN
        }
    }

    /// Most restrictive license across a set; an empty set is unknown.
    ///
    /// `commercial_use` solo es `true` si todos la permiten; `acknowledge` es
    /// `true` si alguno la exige. El `spdx` devuelto es el del más restrictivo.
    pub fn for_artifacts<'a>(names: impl IntoIterator<Item = &'a str>) -> Self {
        let mut result: Option<Self> = None;
        for license in names.into_iter().map(Self::for_artifact) {
            result = Some(match result {
                None => license,
                Some(current) => {
                    let strictest = match (rank(&license), rank(&current)) {
                        (a, b) if a > b => license,
                        (a, b) if a < b => current,
                        // Empate: gana la más restrictiva (comercial no libre o atribución).
                        _ => {
                            let current_restricted = !current.commercial_use || current.acknowledge;
                            let license_restricted = !license.commercial_use || license.acknowledge;
                            if license_restricted && !current_restricted { license } else { current }
                        }
                    };
                    Self {
                        commercial_use: current.commercial_use && license.commercial_use,
                        acknowledge: current.acknowledge || license.acknowledge,
                        ..strictest
                    }
                }
            });
        }
        result.unwrap_or(UNKNOWN)
    }

    /// Whether the requested use meets this license's declared restrictions.
    pub fn allows(&self, commercial_intent: bool, acknowledge: bool) -> bool {
        self.spdx != "Unknown"
            && (!commercial_intent || self.commercial_use)
            && (!self.acknowledge || acknowledge)
    }

    /// `true` si la licencia exige opt-in explícito (default-deny).
    pub fn restricted(&self) -> bool {
        self.spdx == "Unknown" || !self.commercial_use || self.acknowledge
    }

    /// Motivo de bloqueo con la vía de opt-in, para `PyOcrValueError`.
    pub fn block_message(&self, what: &str) -> String {
        if self.spdx == "Unknown" {
            return format!(
                "{what}: unverified license. Verify the weights' license before use; there is no automatic opt-in."
            );
        }
        let mut required = Vec::new();
        if !self.commercial_use {
            required.push("license_commercial_use=False (non-commercial use)");
        }
        if self.acknowledge {
            required.push("license_acknowledge=True (accept attribution)");
        }
        format!(
            "{what}: license {}. To use it you must pass {} (conditions are cumulative).",
            self.spdx,
            required.join(" AND ")
        )
    }

    /// Fila de licencia lista para Python (dict con los seis campos).
    pub fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("license", self.spdx)?;
        dict.set_item("license_commercial_use", self.commercial_use)?;
        dict.set_item("license_acknowledge", self.acknowledge)?;
        dict.set_item("license_restricted", self.restricted())?;
        dict.set_item("license_notes", self.notes)?;
        dict.set_item("license_url", self.url)?;
        Ok(dict)
    }
}

#[cfg(test)]
mod tests {
    use super::{registry, License};

    #[test]
    fn classifies_pp_and_indra_artifacts_and_restricts_unknowns() {
        assert_eq!(License::for_artifact("pp-ocrv6_tiny_det.onnx").spdx, "Apache-2.0");
        assert_eq!(License::for_artifact("ppocrv6_tiny_dict.txt").spdx, "Apache-2.0");
        assert_eq!(License::for_artifact("arabic_pp-ocrv3_mobile_rec.onnx").spdx, "Apache-2.0");
        assert_eq!(License::for_artifact("det.onnx").spdx, "OpenRAIL-M-Mod");
        assert_eq!(License::for_artifact("unrecognized.onnx").spdx, "Unknown");
    }

    #[test]
    fn every_registered_indra_artifact_is_openrail() {
        for artifact in registry::indra_artifacts() {
            let license = License::for_artifact(artifact.name);
            assert_eq!(license.spdx, "OpenRAIL-M-Mod", "{}", artifact.name);
            assert!(!license.commercial_use, "{}", artifact.name);
            assert!(license.acknowledge, "{}", artifact.name);
            assert!(license.restricted(), "{}", artifact.name);
        }
    }

    #[test]
    fn combined_license_is_the_most_restrictive_and_unknown_fails_closed() {
        let combined = License::for_artifacts(["pp-ocrv6_tiny_det.onnx", "det.onnx"]);
        assert_eq!(combined.spdx, "OpenRAIL-M-Mod");
        assert!(!combined.commercial_use);
        assert!(combined.restricted());
        assert!(!combined.allows(true, false));
        assert!(License::for_artifact("pp-ocrv6_tiny_det.onnx").allows(true, false));
        assert!(!License::for_artifact("unrecognized.onnx").allows(false, false));
        assert_eq!(License::for_artifacts([]).spdx, "Unknown");
    }

    #[test]
    fn indra_license_carries_the_restriction_threshold_and_source() {
        let license = License::for_artifact("det.onnx");
        assert!(license.notes.contains("20M"));
        assert_eq!(
            license.url,
            Some("https://huggingface.co/datalab-to/indra-ocr/blob/bd02167fdf2005a19962cc15188f8496a2c87d3b/LICENSE")
        );
        assert!(!license.allows(false, false), "la atribución es obligatoria (§7)");
        assert!(license.allows(false, true), "no comercial + atribución");
        assert!(!license.allows(true, true), "el uso comercial sigue prohibido");
        assert!(!license.allows(true, false));
    }

    #[test]
    fn block_message_names_the_opt_in() {
        let message = License::for_artifact("det.onnx").block_message("El preset 'indra'");
        assert!(message.contains("OpenRAIL-M-Mod"));
        assert!(message.contains("license_commercial_use=False"));
        assert!(message.contains("license_acknowledge=True"));
        assert!(message.contains("cumulative"));
        assert!(License::for_artifact("no-existe.onnx").block_message("x").contains("unverified license"));
    }
}
