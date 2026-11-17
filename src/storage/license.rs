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

use crate::core::types::ModelSpec;

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

/// GLM-OCR (`zai-org/GLM-OCR`), el VLM que trae `oar-ocr-vl` con la
/// feature `vl`. No es un artefacto del registro del wrapper: sus snapshots los
/// descarga el auto-download del propio crate VLM, así que se clasifica por el
/// repo del checkpoint (metadatos de HuggingFace: `license: mit`,
/// revisión `2e85a62840ccac27daa451df36c736c4636b8628`).
const GLM_OCR: License = License {
    spdx: "MIT",
    commercial_use: true,
    acknowledge: false,
    notes: "GLM-OCR weights (zai-org/GLM-OCR): MIT. The detector it composes, PP-DocLayoutV3 (PaddlePaddle/PP-DocLayoutV3_safetensors), is Apache-2.0. Both permissive: commercial use allowed, no attribution gate. Served by oar-ocr-vl (Candle), not by the wrapper's own downloader.",
    url: Some("https://huggingface.co/zai-org/GLM-OCR"),
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

/// Binario nativo que **no** es un peso: la librería PDFium que usa la API de
/// documentos (`DESIGN.md` §13). `pdfium-render` (MIT/Apache-2.0) la enlaza en
/// runtime, así que hace falta declararla en el gate en vez de dejarla fuera de
/// la contabilidad (§13.7). Dual Apache-2.0 / BSD-3-Clause, ambas permisivas:
/// uso comercial sí, sin atribución obligatoria.
const PDFIUM: License = License {
    spdx: "Apache-2.0 OR BSD-3-Clause",
    commercial_use: true,
    acknowledge: false,
    notes: "PDFium dynamic library (pdfium.dll) used by the document API (DESIGN.md §13) to read \
            PDF text layers and rasterise pages. Not a model weight: it is the Chromium/Google PDF \
            library, dual-licensed Apache-2.0 / BSD-3-Clause (both permissive). pdfium-render \
            (MIT OR Apache-2.0) is the Rust binding; it does not bundle PDFium.",
    url: Some("https://pdfium.googlesource.com/pdfium/+/refs/heads/main/LICENSE"),
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

    /// Licencia del binario nativo PDFium que usa la API de documentos (§13.7).
    ///
    /// No es un artefacto del registro de pesos, así que ningún preset la
    /// agrega: se expone para que la superficie de documentos pueda declararla.
    pub fn pdfium() -> Self {
        PDFIUM
    }

    /// License for a registered artifact; unknown names are denied by default.
    pub fn for_artifact(name: &str) -> Self {
        let name = name.to_ascii_lowercase();
        if is_indra(&name) {
            return INDRA;
        }
        // Binario nativo del API de documentos (§13.7): no es un peso, pero se
        // clasifica aquí para que no caiga en el `Unknown` de default-deny.
        if name.contains("pdfium") {
            return PDFIUM;
        }
        // VLM (`oar-ocr-vl`): se clasifica por el repo del checkpoint, no por un
        // fichero del registro del wrapper (allí no hay ninguno).
        if name.contains("glm-ocr") {
            return GLM_OCR;
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

    /// Licencia efectiva de un preset.
    ///
    /// El camino normal es la combinación más restrictiva de sus artefactos. Un
    /// VLM no registra artefactos sueltos (sus snapshots los baja
    /// `oar-ocr-vl`), así que declara su licencia con el repo del checkpoint:
    /// sin esto una lista vacía caería al `Unknown` de default-deny y
    /// bloquearía un preset con licencia verificada.
    pub fn for_spec(spec: &ModelSpec) -> Self {
        match spec {
            ModelSpec::Vlm(model) => Self::for_artifact(model.checkpoint_repo()),
            _ => Self::for_artifacts(registry::artifacts_for(spec).iter().map(|a| a.name)),
        }
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
    fn pdfium_native_library_is_declared_permissive_not_unknown() {
        let license = License::for_artifact("pdfium.dll");
        assert_eq!(license.spdx, "Apache-2.0 OR BSD-3-Clause");
        assert!(license.commercial_use);
        assert!(!license.restricted());
        assert!(license.allows(true, false));
        assert_eq!(License::pdfium().spdx, license.spdx);
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

    #[test]
    fn glm_ocr_is_mit_and_the_vlm_spec_is_not_default_denied() {
        let license = License::for_artifact("zai-org/GLM-OCR");
        assert_eq!(license.spdx, "MIT");
        assert!(license.commercial_use);
        assert!(!license.restricted());
        assert!(license.allows(true, false));

        let spec = crate::core::types::ModelSpec::Vlm(crate::core::types::VlmModel::GlmOcr);
        assert_eq!(License::for_spec(&spec).spdx, "MIT");
        assert!(License::for_spec(&spec).allows(true, false));
    }

    #[test]
    fn a_vlm_spec_does_not_fall_into_the_empty_registry_default_deny() {
        // Un preset VLM no registra artefactos sueltos: si `for_spec` delegara en
        // la lista vacía, caería al `Unknown` restringido y bloquearía el preset.
        assert_eq!(License::for_artifacts(std::iter::empty::<&str>()).spdx, "Unknown");
        assert!(License::for_artifacts(std::iter::empty::<&str>()).restricted());

        let spec = crate::core::types::ModelSpec::Vlm(crate::core::types::VlmModel::GlmOcr);
        assert!(!License::for_spec(&spec).restricted());
    }

    #[test]
    fn for_spec_matches_for_artifacts_on_the_onnx_presets() {
        use crate::core::types::{OcrSize, ModelSpec};
        for spec in [
            ModelSpec::PpOcrV6(OcrSize::Tiny),
            ModelSpec::PpStructureV3,
            ModelSpec::Indra,
        ] {
            let artifacts = registry::artifacts_for(&spec);
            assert_eq!(
                License::for_spec(&spec).spdx,
                License::for_artifacts(artifacts.iter().map(|a| a.name)).spdx,
                "for_spec debe seguir siendo el combinado de los artefactos en {spec:?}"
            );
        }
    }
}
