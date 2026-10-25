# pyocrust

Wrapper nativo en **Rust** (PyO3 + Maturin) que unifica OCR de texto
(PP-OCRv6) y análisis de estructura documental (PP-StructureV3) sobre el crate
[`oar-ocr`](https://crates.io/crates/oar-ocr) `0.10.1`.

Este repositorio **es** el paquete Python: `rust-bindings/pyocrust/` es a la vez
la raíz del crate `pyocrust_core` y el directorio del paquete importable
`pyocrust/`.

## Estado

Esqueleto del paquete (fase 1 del `PLANNING.md`). `cargo check` compila y
`import pyocrust` funciona; las capas `core/`, `storage/` y `engines/` llegan en
las fases 2 a 4.

## Estructura

```text
pyocrust/
├── Cargo.toml          # Crate pyocrust_core (cdylib, edition 2024)
├── pyproject.toml      # Backend Maturin, module-name = "pyocrust._pyocrust_core"
├── src/
│   └── lib.rs          # #[pymodule] #[pyo3(name = "_pyocrust_core")]
├── pyocrust/           # Paquete Python importable
│   ├── __init__.py     # Fachada pública
│   ├── __init__.pyi    # Stubs de tipos
│   └── py.typed        # Marcador PEP 561
└── tests/              # Lo crea la tarjeta V1
```

## Requisitos

- Rust toolchain con `rustc`/`cargo` **1.95** o superior (MSRV de `oar-ocr`).
- Python **3.10** o superior (el crate usa `abi3-py310`).
- Enlazador de C: en Windows, MSVC Build Tools (`cl.exe` en el `PATH`).

## Desarrollo

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git-Bash

pip install maturin
maturin develop                 # compila y deja importable pyocrust en el venv

python -c "import pyocrust; print(pyocrust.__version__)"
```

`maturin develop` usa el perfil `release` por defecto. El perfil declara
`panic = "unwind"` (ADR-004): un pánico de Rust se traduce a excepción de Python
en lugar de abortar el intérprete.

### Comprobaciones rápidas

```bash
cargo check        # sin enlazar; valida el crate y sus dependencias
cargo test         # tests unitarios de Rust (tarjeta I2)
python -m pytest tests/ -q   # tests de integración (tarjeta V1)
```

## Features

| Feature | Efecto |
| :--- | :--- |
| *(por defecto)* | CPU. `download-binaries` + `simd` de `oar-ocr`; liga el ONNX Runtime que trae el crate. |
| `cuda` | Proveedor CUDA de ONNX Runtime (NVIDIA). |
| `directml` | Proveedor DirectML de ONNX Runtime (Windows). |

```bash
maturin develop --features cuda        # build con aceleración GPU
```

La descarga de modelos desde ModelScope (`auto-download`) viene activada por
defecto en `oar-ocr` (ADR-010); el segundo camino de descarga, el descargador
propio desde Hugging Face, se implementa en `src/storage/download.rs` (tarjeta `I3`).
La feature `vl` (Candle / `oar-ocr-vl`) está reservada para v2 (ADR-001) y no
se declara todavía: no hay nada que compilar detrás de ella.

Los modelos se resuelven en este orden de prioridad (ver `DESIGN.md` §3.2):
parámetro `custom_path` → `OAR_HOME` / `OCR_MODELS_CACHE_DIR` → `~/.oar`.

## Licencia

Apache-2.0, idéntica a la de `oar-ocr`. Ver `LICENSE`.
