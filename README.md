# pyocrust

Wrapper nativo en **Rust** (PyO3 + Maturin) con tres familias de presets: OCR de texto
(`pp_ocrv6*`), estructura documental (`pp_structurev3`) e `indra`, sobre el crate
[`oar-ocr`](https://crates.io/crates/oar-ocr) `0.10.1`.

Este repositorio **es** el paquete Python: `rust-bindings/pyocrust/` es a la vez
la raíz del crate `pyocrust_core` y el directorio del paquete importable
`pyocrust/`.

## Estado

Instantánea histórica de las fases 0-5 del `PLANNING.md`: `cargo check` compila,
`import pyocrust` funciona y la suite de integración pasa (31 pasados, 2 `skip`,
1 `xfail`). **Sin embargo, el sign-off final `S1` es `RECHAZADO`** con 7
condiciones abiertas, dos de ellas bloqueantes; ver `DESIGN.md` §9 y
`PLANNING.md` §7.

`S2.2` (Indra) tiene aceptación arquitectónica **parcial**: smoke CPU con dos
regiones, dos elementos y Markdown; una prueba Python y una Rust de giro inverso
pasadas, según la evidencia comunicada. GPU, calidad matemática y suite global
siguen pendientes. La descarga Rust HF falla por TLS; el diagnóstico con `urllib`
no valida `ensure_models`. Ver `DESIGN.md` §3.1.1 y `PLANNING.md`.

`S2.5/S2.6`: exposición Python documentada **11/11 predictores + 3/3 familias
de pipelines**, no once inferencias verificadas. El cierre focal offline registra
**14 pass, 4 skip, 0 fallos**: Tiny reconoce texto e Indra conserva matemática
inline en Markdown. Quedan cuatro tareas layout/tablas sin inferencia por caché
faltante, PP-StructureV3 sin caché completa, descarga fría/redescarga y GPU sin
validar. Evidencia, skips y alcance en `PLANNING.md`, actualización S2.5/S2.6;
no sustituye el histórico ni constituye sign-off global.

## Presets y salida

| Preset | Salida |
| :--- | :--- |
| `pp_ocrv6` / `pp_ocrv6_tiny`, `pp_ocrv6_small`, `pp_ocrv6_medium` | `OcrResult` |
| `pp_structurev3` | `StructureResult` |
| `indra` | `StructureResult` (Markdown, regiones y bloques) |

`VeloceOCR('indra')` usa el mismo `ensure_models`, con `.math(true)` y nueve
artefactos requeridos en `<models_dir>/indra/`. `models_status()['indra']` es el
catálogo completo (`required=false`); `models_status()['presets']['indra']`
enumera los nueve requisitos efectivos (`required=true`).
En Indra, la confianza de bloque `0.0` indica score no disponible; `formulas=[]`
no implica ausencia matemática: el LaTeX inline se conserva en Markdown/regiones.

## Tareas individuales (`TaskPredictor`)

Once tareas disponibles; nombres, esquemas y opciones en `DESIGN.md` §3.1.2.
Ejemplo con un modelo local explícito (sin descarga implícita):

```python
from pyocrust import TaskPredictor

predictor = TaskPredictor("text_detection", models="/ruta/pp-ocrv6_tiny_det.onnx")
print(predictor.predict("document.png")["detections"])
results = predictor.predict_batch(["document.png", "otra.png"])
```

`predict` acepta ruta, `PathLike` o bytes; batch conserva orden. `models=None`
gestiona artefactos registrados y puede descargar; rutas explícitas deben existir.
Exposición no certifica inferencia de las once tareas, calidad ni GPU.

## Catálogo y recomendación (`S3`, aprobación acotada)

`model_catalog()` describe modelos/diccionarios/tokenizers; `pipeline_profiles()`
expone presets y tareas del registro real. Parámetros y RAM desconocidos son
`None`; los tamaños son de archivo, no memoria de ejecución. Indra conserva
`size_bytes=None`/`disk_bytes=None` en estas consultas. Contrato completo:
`DESIGN.md` §3.1.3; evidencia comunicada: `PLANNING.md`, actualización S3.

### Solo recomendar (sin modelos, descargas ni preflight)

```python
from pyocrust import TaskSpec, detect_hardware, resolve_pipeline, pipeline_profiles

hardware = detect_hardware()  # inventario físico; no prueba CUDA en el wheel
choice = resolve_pipeline(
    TaskSpec(document_kind="scanned", tables=True, output_format="markdown"),
    hardware=hardware,
)
print(choice.id, choice.tasks, choice.models_dir, choice.offline)
print(pipeline_profiles()[choice.id])
```

Un `HardwareProfile` explícito evita la detección. Resolver puede normalizar y
reexportar `OAR_HOME` relativa mediante la resolución nativa (§7.1), pero no
carga modelos. Las tareas recomendadas no se ejecutan; Indra puede aparecer como
alternativa heurística, sin garantía de disponibilidad ni GPU. `output_format`
orienta la selección, no convierte resultados.

### Ejecutar después, explícitamente (puede cargar/descargar modelos)

```python
from pyocrust import VeloceOCR

# Ejemplo independiente: requiere artefactos; offline con faltantes da error.
engine = VeloceOCR("pp_structurev3")
result = engine.recognize("document.png")
print(result.to_markdown())
```

No ejecuta automáticamente orientación/rectificación ni alternativas del resolver.
GPU, calidad y disponibilidad local no están certificadas por la aprobación S3.

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

## Benchmarking

Fuera de `src/`, `benchmarks/` mide `pyocrust` contra otros OCR sobre un dataset
real ([FUNSD](https://huggingface.co/datasets/nielsr/funsd), 149 formularios
escaneados con ground truth) y genera tablas y gráficos listos para publicar.

```bash
./.venv/Scripts/python.exe benchmarks/run_benchmarks.py --limit 30 --backends pyocrust,rapidocr,easyocr
./.venv/Scripts/python.exe benchmarks/report_benchmarks.py
./.venv/Scripts/python.exe -m pytest benchmarks/tests -q
```

Mide calidad (`word_f1` y `wer_ord` —que neutralizan el orden de lectura— más
`cer`/`wer` crudos como referencia) y velocidad (`ms/pág.`, `págs/s`); los
backends disponibles son `pyocrust`, `pyocrust_structure`, `rapidocr`, `easyocr`
y `tesseract` (los no instalados se marcan `skipped`, nunca como ejecutados).
Documentación completa y resultados en
[`benchmarks/README.md`](benchmarks/README.md); el CSV por imagen queda en
`benchmarks/results/<timestamp>/` y los artefactos publicables en
`benchmarks/output_examples/`.

Última ejecución registrada (`benchmarks/results/2026-10-25_22-26-51`: FUNSD
`train`, 30 imágenes por backend, CPU, modelo Tiny), tal cual la produce
`benchmarks/report_benchmarks.py --run benchmarks/results/2026-10-25_22-26-51`:

| Backend | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|
| easyocr | 30 | 0.426 | 0.670 | 0.526 | 0.794 | 3247 | 0.31 |
| pyocrust | 30 | **0.745** | **0.325** | 0.487 | 0.670 | **643** | **1.56** |
| rapidocr | 30 | _0.607_ | _0.487_ | 0.482 | 0.699 | 4534 | 0.22 |

`pyocrust_structure` quedó `skipped` (faltan 6 artefactos del preset
`pp_structurev3`); `tesseract` no se incluyó (no está instalado). Las columnas
`F1 palabra` y `WER ord.` son las que deciden la marca: `CER`/`WER` crudos miden
también el orden de lectura y se publican solo como referencia.

## Publicación a PyPI (CI/CD)

La publicación la realizan dos workflows de GitHub Actions con `maturin` y
*trusted publishing* (OIDC: no hay token de PyPI guardado en secretos):

| Workflow | Destino | Disparador |
| :--- | :--- | :--- |
| `.github/workflows/ci-cd.yml` | PyPI | `workflow_dispatch` (manual) |
| `.github/workflows/ci-cd-test.yml` | TestPyPI | `release: published` + `workflow_dispatch` |

Ambos compilan la matriz de plataformas, validan cada wheel (integridad ZIP y
EOCD, sin datos sobrantes) y publican. Como `pyo3` se compila con `abi3-py310`,
un único wheel por plataforma cubre CPython 3.10-3.14: no se repite el build una
vez por versión de Python.

Plataformas: `x86_64`/`aarch64` Linux, `x86_64` Windows y `aarch64` macOS
(Apple Silicon). Se omiten `i686-pc-windows-msvc` (Windows x86) y
`x86_64-apple-darwin` (macOS Intel) porque `oar-ocr` se compila con su feature
por defecto `download-binaries` y el catálogo de binarios de ONNX Runtime de
`ort-sys` no publica esas dos arquitecturas: esos jobs fallarían al compilar.

### Requisitos previos (una sola vez)

1. Crear el proyecto en [TestPyPI](https://test.pypi.org/) y en
   [PyPI](https://pypi.org/).
2. En el repositorio de GitHub, crear los entornos (`Settings > Environments`)
   `testpypi` y `pypi`.
3. Configurar *trusted publishing* en cada proyecto apuntando al repositorio y al
   workflow correspondiente (`ci-cd.yml` para PyPI, `ci-cd-test.yml` para
   TestPyPI), sin secreto compartido.

### Publicar

```text
TestPyPI:  Actions > "Publish pyocrust to TestPyPI" > Run workflow
           (o publicar un release, que lo dispara automáticamente)
PyPI:      Actions > "Publish pyocrust to PyPI" > Run workflow
```

### Comprobar el wheel antes de subir

```bash
./.venv/Scripts/python.exe -m maturin build --release --out dist
pip install dist/pyocrust-0.1.0-cp310-abi3-*.whl
python -c "import pyocrust; print(pyocrust.__version__)"
```

El wheel queda en `dist/` (ignorado por git); en CI lo genera
`PyO3/maturin-action`.

## Licencia

Apache-2.0, idéntica a la de `oar-ocr`. Ver `LICENSE`.
