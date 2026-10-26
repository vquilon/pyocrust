//! Gestión de almacenamiento, resolución de rutas y preflight (`DESIGN.md` §7).
//!
//! Este módulo implementa:
//! - `config`: resolución de la ubicación física de los modelos según el orden estricto de prioridad (§3.2 y §7.1).
//! - `models`: preflight de artefactos por preset antes de inferencia (§7.2).
//! - `download`: descargador Hugging Face resiliente con verificación de integridad (§7.3, ADR-007).

pub mod config;
pub mod download;
pub mod models;
pub mod registry;

pub use config::{resolve_models_dir, OcrConfig};
pub use download::{
    artifact_url, fetch, sidecar_matches, sidecar_path, write_sidecar, DownloadError,
};
pub use models::{
    ensure_models, offline_requested, preflight, preflight_paths, ArtifactStatus,
    PreflightReport, OFFLINE_ENV,
};
pub use registry::{artifacts_for, indra_artifacts, presets, Artifact, ResolvedArtifact, Source};
