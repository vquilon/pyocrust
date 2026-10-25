//! Gestión de almacenamiento, resolución de rutas y preflight (`DESIGN.md` §7).
//!
//! Este módulo implementa:
//! - `config`: resolución de la ubicación física de los modelos según el orden estricto de prioridad (§3.2 y §7.1).
//! - `models`: preflight de artefactos por preset antes de inferencia (§7.2).
//! - `download`: descargador Hugging Face resiliente con verificación de integridad (§7.3, ADR-007).

pub mod config;
pub mod download;
pub mod models;

pub use config::{resolve_models_dir, OcrConfig};
pub use download::{fetch, DownloadError};
pub use models::{preflight, preflight_paths, PreflightReport};
