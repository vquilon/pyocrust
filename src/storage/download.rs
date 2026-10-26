//! Descargador Hugging Face resiliente (ADR-007 y `DESIGN.md` §7.3).
//!
//! Requisitos obligatorios (§7.3):
//! 1. Streaming a temporal `.<filename>.<pid>.part` y renombrado atómico (`fs::rename`).
//! 2. Reanudación mediante cabecera `Range: bytes=offset-`.
//! 3. Verificación de integridad: `Content-Length` y SHA-256 obligatorios.
//! 4. Errores tipados mediante `DownloadError`. Sin `unwrap()`.
//! 5. Bypass offline total si el fichero ya existe con tamaño y hash correctos.

use std::fs::{self, File, OpenOptions};
use std::io::{self, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::time::Duration;

use sha2::{Digest, Sha256};

use crate::core::error::OcrError;
use crate::storage::registry::{Artifact, Source};

/// Errores tipados de descarga (§7.3 requisito 4).
#[derive(Debug)]
pub enum DownloadError {
    /// Error devuelto por el cliente HTTP (conexión, timeouts, status >= 400).
    Http(reqwest::Error),
    /// Error de entrada/salida local en disco.
    Io(io::Error),
    /// La suma de comprobación SHA-256 no coincide con la esperada.
    ChecksumMismatch { expected: String, actual: String },
    /// La longitud de los datos descargados no coincide con el `Content-Length` esperado.
    Incomplete { expected: u64, actual: u64 },
}

impl std::fmt::Display for DownloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Http(err) => write!(f, "HTTP error during download: {err}"),
            Self::Io(err) => write!(f, "I/O error during download: {err}"),
            Self::ChecksumMismatch { expected, actual } => write!(
                f,
                "checksum mismatch: expected sha256 {expected}, got {actual}"
            ),
            Self::Incomplete { expected, actual } => write!(
                f,
                "incomplete download: expected {expected} bytes, got {actual}"
            ),
        }
    }
}

impl std::error::Error for DownloadError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Http(err) => Some(err),
            Self::Io(err) => Some(err),
            _ => None,
        }
    }
}

impl From<reqwest::Error> for DownloadError {
    fn from(err: reqwest::Error) -> Self {
        Self::Http(err)
    }
}

impl From<io::Error> for DownloadError {
    fn from(err: io::Error) -> Self {
        Self::Io(err)
    }
}

/// Calcula la suma de comprobación SHA-256 de un fichero en disco en bloques de 64 KB.
pub fn compute_sha256(path: &Path) -> Result<String, io::Error> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }
    let digest = hasher.finalize();
    Ok(format!("{digest:x}"))
}

/// Genera la ruta del fichero temporal según el patrón `.<filename>.<pid>.part` (§7.3 requisito 1).
pub fn part_file_path(dest: &Path) -> PathBuf {
    let pid = std::process::id();
    let filename = dest
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("artifact");
    dest.with_file_name(format!(".{filename}.{pid}.part"))
}

/// Construye la URL pública de descarga de un [`Artifact`] del registro.
///
/// * ModelScope: el mismo patrón que usa `oar-ocr` en
///   `oar-ocr-core-0.10.1/src/core/download/mod.rs:252`.
/// * HuggingFace: `https://huggingface.co/<repo>/resolve/<rev>/<path>`, con la
///   revisión fijada a un commit SHA.
pub fn artifact_url(artifact: &Artifact) -> Result<String, OcrError> {
    match artifact.source {
        Source::ModelScope => Ok(format!(
            "https://www.modelscope.cn/api/v1/models/{}/repo?Revision={}&FilePath={}",
            oar_ocr::download::MODELSCOPE_REPO,
            oar_ocr::download::DEFAULT_REVISION,
            artifact.name
        )),
        Source::HuggingFace { repo, revision } => Ok(format!(
            "https://huggingface.co/{repo}/resolve/{revision}/{}",
            artifact.name
        )),
    }
}

/// Ruta del sidecar `.<name>.sha256` que registra un hash ya verificado.
pub fn sidecar_path(path: &Path) -> Option<PathBuf> {
    let name = path.file_name()?.to_str()?;
    Some(path.with_file_name(format!(".{name}.sha256")))
}

/// Escribe el sidecar con el hash ya verificado.
///
/// Es *best effort*: si falla, el siguiente arranque solo vuelve a hashear.
pub fn write_sidecar(path: &Path, hash: &str) -> io::Result<()> {
    match sidecar_path(path) {
        Some(sidecar) => fs::write(&sidecar, hash),
        None => Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "no filename for sidecar",
        )),
    }
}

/// `true` si el sidecar registra exactamente `expected` (ignora mayúsculas).
///
/// Permite el arranque en caliente sin re-hashear ficheros de cientos de MB.
pub fn sidecar_matches(path: &Path, expected: &str) -> bool {
    match sidecar_path(path) {
        Some(sidecar) => fs::read_to_string(&sidecar)
            .map(|contents| contents.trim().eq_ignore_ascii_case(expected))
            .unwrap_or(false),
        None => false,
    }
}

/// Descarga un fichero desde `url` hacia `dest` garantizando verificación de integridad y atomicidad.
///
/// Si el fichero ya existe en `dest` y su SHA-256 coincide con `sha256_hex`, retorna `Ok(())`
/// de forma inmediata sin realizar ninguna llamada de red (Bypass offline, §7.3 requisito 5).
pub fn fetch(url: &str, dest: &Path, sha256_hex: &str) -> Result<(), DownloadError> {
    let expected_hash = sha256_hex.to_ascii_lowercase();

    // 5. Bypass offline. El sidecar de un arranque anterior ahorra el re-hash
    //    (decisión `S2.0`: solo se hashea lo que se descarga).
    if dest.exists() {
        if sidecar_matches(dest, &expected_hash) {
            return Ok(());
        }
        if let Ok(actual_hash) = compute_sha256(dest) {
            if actual_hash == expected_hash {
                return Ok(());
            }
        }
    }

    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent)?;
    }

    // 1. Streaming a fichero temporal con patrón .<filename>.<pid>.part
    let part_path = part_file_path(dest);

    // 2. Reanudación mediante cabecera Range si existe un .part previo
    let mut existing_len = if part_path.exists() {
        part_path.metadata().map(|m| m.len()).unwrap_or(0)
    } else {
        0
    };

    // La CDN de ModelScope devuelve 403 a los clientes **sin** `User-Agent`
    // (reqwest no lo envía por defecto); hay que declararlo explícitamente.
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(1800))
        .connect_timeout(Duration::from_secs(30))
        .user_agent(format!("pyocrust/{}", env!("CARGO_PKG_VERSION")))
        .build()?;

    let mut request = client.get(url);
    if existing_len > 0 {
        request = request.header(reqwest::header::RANGE, format!("bytes={existing_len}-"));
    }

    let mut response = request.send()?.error_for_status()?;

    // Si el servidor devolvió 200 OK (en vez de 206 Partial Content), no respeta Range:
    // reiniciar descarga desde el principio.
    let append_mode = existing_len > 0 && response.status() == reqwest::StatusCode::PARTIAL_CONTENT;
    if !append_mode {
        existing_len = 0;
    }

    let content_len = response.content_length();
    let expected_total_len = content_len.map(|cl| cl + existing_len);

    let mut file = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(!append_mode)
        .append(append_mode)
        .open(&part_path)?;

    if append_mode {
        file.seek(SeekFrom::End(0))?;
    }

    let mut total_written = existing_len;
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let bytes_read = response.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        file.write_all(&buffer[..bytes_read])?;
        total_written += bytes_read as u64;
    }
    file.flush()?;
    drop(file);

    // 3. Verificación de Content-Length
    if let Some(expected_len) = expected_total_len {
        if total_written != expected_len {
            let _ = fs::remove_file(&part_path);
            return Err(DownloadError::Incomplete {
                expected: expected_len,
                actual: total_written,
            });
        }
    }

    // 3. Verificación obligatoria de SHA-256
    let actual_hash = compute_sha256(&part_path)?;
    if actual_hash != expected_hash {
        let _ = fs::remove_file(&part_path);
        return Err(DownloadError::ChecksumMismatch {
            expected: expected_hash,
            actual: actual_hash,
        });
    }

    // 1. Renombrado atómico a destino definitivo solo tras validar
    fs::rename(&part_path, dest)?;

    // 5. Sidecar con el hash ya verificado: el próximo arranque se lo ahorra.
    let _ = write_sidecar(dest, &expected_hash);

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_temp_dir(prefix: &str) -> PathBuf {
        let path = std::env::temp_dir().join(format!("pyocrust_dl_{}_{}", prefix, std::process::id()));
        let _ = std::fs::remove_dir_all(&path);
        std::fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn compute_sha256_calculates_correct_digest() {
        let temp_dir = create_temp_dir("sha256");
        let file_path = temp_dir.join("sample.txt");
        fs::write(&file_path, b"hello pyocrust\n").unwrap();

        // echo -n "hello pyocrust\n" | sha256sum
        // sha256("hello pyocrust\n")
        let hash = compute_sha256(&file_path).unwrap();
        assert_eq!(
            hash,
            "d9dc08ca0930e268ab9a71ae177a7d174c5b9796c427714681c42b5974f8b9be"
        );

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn part_file_path_follows_pid_part_convention() {
        let target = Path::new("/some/dir/model.onnx");
        let part = part_file_path(target);
        let filename = part.file_name().unwrap().to_str().unwrap();

        let pid = std::process::id();
        assert_eq!(filename, format!(".model.onnx.{pid}.part"));
    }

    #[test]
    fn offline_bypass_skips_network_when_file_exists_with_matching_sha256() {
        let temp_dir = create_temp_dir("bypass");
        let dest = temp_dir.join("local_model.onnx");
        fs::write(&dest, b"valid model content").unwrap();

        let correct_hash = compute_sha256(&dest).unwrap();

        // Con una URL deliberadamente inválida / inalcanzable, fetch debe terminar Ok(())
        // demostrando que se produjo bypass offline absoluto sin intentar petición HTTP.
        let result = fetch("http://invalid.domain.pyocrust.test/fail", &dest, &correct_hash);
        assert!(result.is_ok());

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn sidecar_records_the_hash_and_skips_the_rehash() {
        let temp_dir = create_temp_dir("sidecar");
        let dest = temp_dir.join("model.onnx");
        fs::write(&dest, b"contenido verificado").unwrap();
        let hash = compute_sha256(&dest).unwrap();

        assert!(!sidecar_matches(&dest, &hash), "sin sidecar todavía no coincide");
        write_sidecar(&dest, &hash).unwrap();
        assert!(sidecar_matches(&dest, &hash));
        assert!(!sidecar_matches(&dest, "deadbeef"));

        // Un sidecar ajeno no valida el bypass.
        fs::write(temp_dir.join(".model.onnx.sha256"), "otro-hash").unwrap();
        assert!(!sidecar_matches(&dest, &hash));

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn offline_bypass_fails_and_attempts_network_when_hash_mismatches() {
        let temp_dir = create_temp_dir("mismatch");
        let dest = temp_dir.join("local_model.onnx");
        fs::write(&dest, b"bad model content").unwrap();

        // Hash esperado no coincide con el contenido local: no debe hacer bypass
        // y al intentar descargar de la URL inalcanzable fallará con error de red.
        let result = fetch("http://127.0.0.1:9/unreachable", &dest, "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef");
        assert!(result.is_err());
        match result {
            Err(DownloadError::Http(_)) => {}
            other => panic!("expected Http error trying to contact unreachable url, got {other:?}"),
        }

        let _ = fs::remove_dir_all(&temp_dir);
    }
}
