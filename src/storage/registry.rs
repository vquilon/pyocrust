//! Registro único de artefactos de modelos (tarjeta `S2.0`).
//!
//! Una sola tabla `preset -> [Artifact]` y una sola fuente de verdad para el
//! `sha256` y el tamaño:
//!
//! * **ModelScope** (`greatv/oar-ocr`): se leen de `oar_ocr::download::find(name)`,
//!   el registro de `oar-ocr`; no se duplican aquí.
//! * **HuggingFace**: se fijan en el propio registro, con la revisión clavada a un
//!   commit SHA (nunca `main`) y el `sha256` del objeto LFS.
//!
//! `indra` está incluido con `required = false`: sus artefactos se sirven desde
//! `datalab-to/indra-ocr` (HuggingFace) y todavía no hay ningún preset
//! `ModelSpec` que los exija (`S2.2` añade el preset y los activa).

use crate::core::error::OcrError;
use crate::core::types::{ModelSpec, OcrSize};

use super::download::artifact_url;

/// Fuente remota de un artefacto.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Source {
    /// ModelScope `greatv/oar-ocr`. El `sha256` y el tamaño se leen de
    /// `oar_ocr::download::find(name)`; no se duplican en el registro.
    ModelScope,
    /// HuggingFace: `repo` en la revisión `revision` (un commit SHA, nunca `main`).
    HuggingFace {
        repo: &'static str,
        revision: &'static str,
    },
}

/// Un artefacto de modelo tal como lo describe el registro.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Artifact {
    /// Nombre de fichero tal como se guarda en el directorio resuelto.
    pub name: &'static str,
    /// Fuente remota del artefacto.
    pub source: Source,
    /// SHA-256 en hex minúscula. `None` en ModelScope: lo da `find(name)`.
    pub sha256: Option<&'static str>,
    /// Tamaño en bytes. `None` en ModelScope: lo da `find(name)`.
    pub size: Option<u64>,
    /// `false`: no se descarga ni bloquea el arranque (aún sin preset que lo exija).
    pub required: bool,
}

impl Artifact {
    /// Artefacto servido por ModelScope; la integridad la resuelve `find(name)`.
    const fn modelscope(name: &'static str) -> Self {
        Self {
            name,
            source: Source::ModelScope,
            sha256: None,
            size: None,
            required: true,
        }
    }

    /// Artefacto servido por HuggingFace, con integridad fijada en el registro.
    const fn huggingface(
        name: &'static str,
        repo: &'static str,
        revision: &'static str,
        sha256: &'static str,
        size: u64,
        required: bool,
    ) -> Self {
        Self {
            name,
            source: Source::HuggingFace { repo, revision },
            sha256: Some(sha256),
            size: Some(size),
            required,
        }
    }

    /// SHA-256 y tamaño ya resueltos, sin tocar la red.
    pub fn integrity(&self) -> Result<(&'static str, u64), OcrError> {
        match self.source {
            Source::ModelScope => oar_ocr::download::find(self.name)
                .map(|entry| (entry.sha256, entry.size))
                .ok_or_else(|| OcrError::Config {
                    message: format!(
                        "'{}' no está en el registro de ModelScope de oar-ocr; \
                         añádelo allí o márcallo `required = false` en src/storage/registry.rs",
                        self.name
                    ),
                }),
            Source::HuggingFace { .. } => match (self.sha256, self.size) {
                (Some(sha256), Some(size)) => Ok((sha256, size)),
                _ => Err(OcrError::Config {
                    message: format!(
                        "'{}' es HuggingFace y necesita `sha256` y `size` fijados en el registro",
                        self.name
                    ),
                }),
            },
        }
    }

    /// URL pública de descarga del artefacto.
    pub fn url(&self) -> Result<String, OcrError> {
        artifact_url(self)
    }

    /// Artefacto resuelto: nombre, URL, SHA-256 y tamaño listos para descargar.
    pub fn resolve(&self) -> Result<ResolvedArtifact, OcrError> {
        let (sha256, size) = self.integrity()?;
        Ok(ResolvedArtifact {
            name: self.name.to_string(),
            url: self.url()?,
            sha256: sha256.to_string(),
            size,
            required: self.required,
        })
    }
}

/// Artefacto resuelto, listo para descargar.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedArtifact {
    /// Nombre de fichero destino.
    pub name: String,
    /// URL pública de descarga.
    pub url: String,
    /// SHA-256 esperado, en hex minúscula.
    pub sha256: String,
    /// Tamaño esperado en bytes.
    pub size: u64,
    /// El preset lo exige.
    pub required: bool,
}

// ---------------------------------------------------------------------------
// Tablas: preset -> artefactos
// ---------------------------------------------------------------------------

/// PP-OCRv6 `Tiny`: 3 artefactos.
const PP_OCRV6_TINY: &[Artifact] = &[
    Artifact::modelscope("pp-ocrv6_tiny_det.onnx"),
    Artifact::modelscope("pp-ocrv6_tiny_rec.onnx"),
    Artifact::modelscope("ppocrv6_tiny_dict.txt"),
];

/// PP-OCRv6 `Small`: 3 artefactos (diccionario completo).
const PP_OCRV6_SMALL: &[Artifact] = &[
    Artifact::modelscope("pp-ocrv6_small_det.onnx"),
    Artifact::modelscope("pp-ocrv6_small_rec.onnx"),
    Artifact::modelscope("ppocrv6_dict.txt"),
];

/// PP-OCRv6 `Medium`: 3 artefactos (diccionario completo).
const PP_OCRV6_MEDIUM: &[Artifact] = &[
    Artifact::modelscope("pp-ocrv6_medium_det.onnx"),
    Artifact::modelscope("pp-ocrv6_medium_rec.onnx"),
    Artifact::modelscope("ppocrv6_dict.txt"),
];

/// PP-StructureV3: 11 artefactos, en el orden de `ModelPaths::all()`.
const PP_STRUCTUREV3: &[Artifact] = &[
    Artifact::modelscope("pp-ocrv6_tiny_det.onnx"),
    Artifact::modelscope("pp-ocrv6_tiny_rec.onnx"),
    Artifact::modelscope("ppocrv6_tiny_dict.txt"),
    Artifact::modelscope("pp-doclayoutv3.onnx"),
    Artifact::modelscope("pp-lcnet_x1_0_table_cls.onnx"),
    Artifact::modelscope("slanext_wired.onnx"),
    Artifact::modelscope("slanet_plus.onnx"),
    Artifact::modelscope("rt-detr-l_wired_table_cell_det.onnx"),
    Artifact::modelscope("table_structure_dict_ch.txt"),
    Artifact::modelscope("pp-formulanet-s.onnx"),
    Artifact::modelscope("pp-formulanet-tokenizer.json"),
];

/// Repositorio de HuggingFace de `indra`.
const INDRA_REPO: &str = "datalab-to/indra-ocr";

/// Revisión fijada de `datalab-to/indra-ocr`: un commit SHA, nunca `main`.
const INDRA_REVISION: &str = "bd02167fdf2005a19962cc15188f8496a2c87d3b";

/// Artefactos de `indra` (HuggingFace `datalab-to/indra-ocr`).
///
/// `required = false`: aún no hay preset `ModelSpec` que los exija (`S2.2`).
/// Nombres, tamaños y SHA-256 LFS leídos del repo en [`INDRA_REVISION`].
const INDRA_ARTIFACTS: &[Artifact] = &[
    Artifact::huggingface(
        "det.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "f2bd4cba23e9c328cf7ec824634e423e191a2c6aacbbf35c62bd79dd70f62f59",
        389_948,
        false,
    ),
    Artifact::huggingface(
        "rec.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "475972a2710be4a3cbfeb2bc7f3624ffd563de07de42476fc7a290d4e1ece484",
        5_042_161,
        false,
    ),
    Artifact::huggingface(
        "order.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "a42db2e8b536ad3d84045a4b7f9b0a72667cf8be4aa02d63f7b38004719fb180",
        2_973_138,
        false,
    ),
    Artifact::huggingface(
        "meta.json",
        INDRA_REPO,
        INDRA_REVISION,
        "4ce4c94b46f5d644033c02e718322014ff4081270f385038c571912b56696339",
        211_869,
        false,
    ),
    Artifact::huggingface(
        "orient.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "20eaf670f55a7cf9facfe1bdd6c7b8e40be75bbf4d48a3df43f66aa3bbd874fd",
        371_802,
        false,
    ),
    Artifact::huggingface(
        "script.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "b6ce4e926e19c243faaf37bd46880398bf2cb4ae56a29e1177a3b017c1280e36",
        191_630,
        false,
    ),
    Artifact::huggingface(
        "lm.npz",
        INDRA_REPO,
        INDRA_REVISION,
        "6c0fb618a363a0acdd05d4f5b0edd9e8146d2d990541b87f6130bbfe17cea58d",
        15_695_957,
        false,
    ),
    Artifact::huggingface(
        "lm_cjk.npz",
        INDRA_REPO,
        INDRA_REVISION,
        "6d64f13f4f90f4e529bd63340c6df76238d007feaef2abb903d8cd28d92bc2f3",
        18_955_160,
        false,
    ),
    Artifact::huggingface(
        "lm_world.npz",
        INDRA_REPO,
        INDRA_REVISION,
        "34df5e74a2fcbb9cf5e7f360a559375ffa2e04d2d2943a42308c177bcb444d5d",
        11_641_215,
        false,
    ),
    Artifact::huggingface(
        "rec_cjk.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "4a035516a17e62cdf33a4fe2d88077654cb8841cff024685cdef4e351694ef50",
        10_176_018,
        false,
    ),
    Artifact::huggingface(
        "rec_rtl.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "468796bd684486a8388c30c8b4ed2a26e3eeb1f8ff02831c24c2e12c79a2a834",
        4_812_710,
        false,
    ),
    Artifact::huggingface(
        "rec_world.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "c8d1e59f21b04966f179d2d2d8e22b230d22110b3f89855bbbf2624a58c40043",
        5_627_990,
        false,
    ),
    Artifact::huggingface(
        "mathcls.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "818b1556e9ef337958db6be0c9791299d3f74a4575586b0cd469aaae9534ff96",
        191_005,
        false,
    ),
    Artifact::huggingface(
        "math_enc.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "d4e4a6c40dad1ee988d32c6403b1590ca42864d4483bbe1e671c5dbb999a5a97",
        9_889_575,
        false,
    ),
    Artifact::huggingface(
        "math_dec_init.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "919417fde9962c3318aeb478c1fe3955dd2bb8cd34476c68debed2ba39e5dcd6",
        1_356_364,
        false,
    ),
    Artifact::huggingface(
        "math_dec_step.onnx",
        INDRA_REPO,
        INDRA_REVISION,
        "5ff6e6cbaf0dea70314f66222a1469736a8c5e7994fab06a5b4e53c90469239f",
        8_429_418,
        false,
    ),
    Artifact::huggingface(
        "math_meta.json",
        INDRA_REPO,
        INDRA_REVISION,
        "85d9715fb8a77791b55ef89f57fb41e72eb3170ec58a7c3bee3b394268bf2b10",
        7_797,
        false,
    ),
];

/// Artefactos que exige un preset, en el orden de `ModelPaths::all()`.
pub fn artifacts_for(spec: &ModelSpec) -> &'static [Artifact] {
    match spec {
        ModelSpec::PpOcrV6(OcrSize::Tiny) => PP_OCRV6_TINY,
        ModelSpec::PpOcrV6(OcrSize::Small) => PP_OCRV6_SMALL,
        ModelSpec::PpOcrV6(OcrSize::Medium) => PP_OCRV6_MEDIUM,
        ModelSpec::PpStructureV3 => PP_STRUCTUREV3,
    }
}

/// Artefactos de `indra`, aún sin preset que los exija (`S2.2`).
pub fn indra_artifacts() -> &'static [Artifact] {
    INDRA_ARTIFACTS
}

/// Presets con su nombre estable, en el orden en que los reporta `models_status`.
pub fn presets() -> Vec<(&'static str, ModelSpec)> {
    vec![
        ("pp_ocrv6_tiny", ModelSpec::PpOcrV6(OcrSize::Tiny)),
        ("pp_ocrv6_small", ModelSpec::PpOcrV6(OcrSize::Small)),
        ("pp_ocrv6_medium", ModelSpec::PpOcrV6(OcrSize::Medium)),
        ("pp_structurev3", ModelSpec::PpStructureV3),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn modelscope_integrity_comes_from_the_oar_registry() {
        let artifact = PP_OCRV6_TINY[0];
        assert_eq!(artifact.name, "pp-ocrv6_tiny_det.onnx");
        let (sha256, size) = artifact.integrity().expect("registrado");
        assert_eq!(size, 1_780_590);
        assert_eq!(
            sha256,
            "193bab7a04fca699a6c82e6abb5b81bdb28177f0abd4062552b04908dafb19f8"
        );
    }

    #[test]
    fn every_modelscope_artifact_is_in_the_oar_registry() {
        for spec in presets() {
            for artifact in artifacts_for(&spec.1) {
                artifact
                    .integrity()
                    .unwrap_or_else(|e| panic!("{} no resuelve: {e}", artifact.name));
            }
        }
    }

    #[test]
    fn huggingface_url_is_pinned_to_a_commit_sha() {
        let artifact = INDRA_ARTIFACTS[0];
        assert_eq!(artifact.name, "det.onnx");
        let url = artifact.url().expect("url");
        assert!(url.starts_with("https://huggingface.co/datalab-to/indra-ocr/resolve/"));
        assert!(!url.contains("/main/"), "la revisión no puede ser `main`: {url}");
        assert!(url.ends_with("/det.onnx"));
    }

    #[test]
    fn modelscope_url_matches_the_oar_download_pattern() {
        let artifact = PP_OCRV6_TINY[0];
        let url = artifact.url().expect("url");
        assert_eq!(
            url,
            "https://www.modelscope.cn/api/v1/models/greatv/oar-ocr/repo?Revision=master&FilePath=pp-ocrv6_tiny_det.onnx"
        );
    }

    #[test]
    fn indra_artifacts_are_marked_not_required() {
        assert!(!INDRA_ARTIFACTS.is_empty());
        for artifact in INDRA_ARTIFACTS {
            assert!(!artifact.required, "{} aún no lo exige ningún preset", artifact.name);
        }
    }

    #[test]
    fn unregistered_modelscope_artifact_is_reported_not_invented() {
        let artifact = Artifact::modelscope("no-existe-en-el-registro.onnx");
        match artifact.integrity() {
            Err(OcrError::Config { message }) => {
                assert!(message.contains("no-existe-en-el-registro.onnx"));
            }
            other => panic!("expected Config error, got {other:?}"),
        }
    }
}
