# Documento de Diseño de Arquitectura: Wrapper Multidisciplinar OCR en Rust
# Sistema: pyocrust (antes `ocr_rust_bridge`)

> **Estado del documento:** contrato de diseño de la versión 1, **reconciliado con
> el árbol real en `D1` y `D2` (2026-10-25)**. Validado por el dictamen de arquitectura de
> la tarjeta `A1` (veredicto: **CAMBIOS OBLIGATORIOS**) y contrastado con las
> fuentes de `oar-ocr` `0.10.1` y con la intención de producto de `DECISIONS.md`.
> Toda decisión impuesta por `A1` queda registrada como ADR numerado en §4.
>
> **Aviso de estado del proyecto (D1, 2026-10-25; actualizado en `D2`, 2026-10-25;
> **superado por `D5`, 2026-11-09**, §10):** el sign-off final (`S1`, tarjeta
> `t_d005409b`) cerró como **RECHAZADO** con 7 condiciones y fue **relevado y
> APROBADO** por `t_e560fff3` (2026-11-09). Este documento describe el estado
> **real**, no el deseado: cada ADR lleva su estado de cumplimiento verificado en
> §9.1 y el estado final post-campaña en §10.

## 1. Objetivo General

Diseñar y desarrollar un wrapper nativo en Rust utilizando **PyO3** y **Maturin** que encapsule librerías de reconocimiento de caracteres (OCR) y fórmulas matemáticas del ecosistema de Rust (partiendo de `oar-ocr`). El paquete final debe ser unificado, multiplataforma, altamente eficiente en el manejo de memoria/hilos, con soporte dinámico para GPU/CPU y capaz de integrarse de forma transparente en un software existente en Python.

### 1.1 Alcance de la versión 1

| Ámbito | Entra en v1 | Fuera de v1 (hito posterior) |
| :--- | :--- | :--- |
| Texto (OCR) | PP-OCRv6 en tamaños `Tiny`, `Small`, `Medium` vía `OAROCRBuilder` | PP-OCRv4 y PP-OCRv5 |
| Estructura | PP-StructureV3 vía `OARStructureBuilder`: layout, tablas (HTML) y fórmulas (LaTeX). **Estado real (`D2`, commit `b128566`):** el backend carga los 11 artefactos y `recognize` **no aplana**: devuelve el Markdown del documento (tablas HTML + fórmulas LaTeX), los elementos de layout (`LayoutRegion`) y las regiones OCR, y todo ello cruza a Python (ADR-003 **cumplido**) | — |
| Motor de inferencia | **ONNX Runtime** exclusivamente | **Candle** y `oar-ocr-vl` (VLM ~0.9B), pospuestos a v2 (ADR-001) |
| Distribución de modelos | `auto-download` (ModelScope → `$OAR_HOME`) + descargador Hugging Face resiliente (ADR-007). **Estado actual (`S2.0`):** conectado al pipeline vía `ensure_models`; ADR-007 **cumplido** (§9.1). La nota «no conectado» de `D1` es histórica | otros repositorios |
| Plataforma de ejecución | CPU y GPU (features `cuda`, `directml`), Python 3.10+ (abi3). El **banco de benchmarks** fija el intérprete del repo a **Python 3.12** (`.venv`): `paddlepaddle-gpu` y las wheels CUDA de `torch`/`torchvision` no existen para 3.13/3.14 en Windows | `tensorrt`, `openvino`, `coreml`, `webgpu` |

`oar-ocr` `0.10.1` cubre además PP-OCRv4/v5, UniMERNet y PP-FormulaNet (fórmulas), SLANet/SLANet+/SLANeXt + RT-DETR (tablas), PP-DocLayoutV2/V3 (layout) y PP-LCNet/UVDoc (orientación y rectificación). El árbol actual expone tres familias de presets: `pp_ocrv6*`, `pp_structurev3` e `indra`; `S2.2` tiene el código **Hecho** (GPU y calidad matemática siguen sin aceptación, §3.1.1).

### 1.2 Hechos verificados del ecosistema

| Dato | Valor | Fuente |
| :--- | :--- | :--- |
| Crate base | `oar-ocr` `0.10.1` (publicado 2026-10-22) | crates.io, verificado por el orquestador |
| Licencia del backend | Apache-2.0 | idem |
| Edition / MSRV | 2024 / `rust-version` 1.95 | idem |
| Features por defecto | `download-binaries`, `simd` | idem |
| Features opcionales | `cuda`, `directml`, `tensorrt`, `openvino`, `coreml`, `webgpu`, `auto-download` | idem |
| Fuente de `auto-download` | ModelScope (`greatv/oar-ocr`) → `$OAR_HOME` (por defecto `~/.oar`) | README de `oar-ocr` `0.10.1` |
| Toolchain del host | `rustc`/`cargo` 1.95.0 | `rustc --version` / `cargo --version` en este host |
| `maturin` | **instalado** en el `.venv` del proyecto; `maturin develop` ya se ejecutó | verificado en `D1` (existe `pyocrust/_pyocrust_core.pyd`) |
| `panic = "abort"` en la referencia | `xycutppy/Cargo.toml:33` bajo `[profile.release]` (`xycutppy/Cargo.toml:28`) | verificado leyendo el fichero |

> Las citas `fichero:línea` sobre el interior del crate `oar-ocr` que aparecen en
> §3 y §4 provienen del dictamen `A1` (comentario del 2026-10-25) y siguen siendo
> **cita de segunda mano**: el árbol de `oar-ocr` no está descargado en el host.
> Las citas sobre `src/**`, `pyocrust/**` y `tests/**` **sí** están verificadas
> leyendo el repositorio en `D1`.

## 2. Arquitectura de Código y Estructura de Carpetas

El borrador inicial partía del patrón **Factoría** y del desacoplamiento mediante **Traits (Interfaces)** para permitir la incorporación de futuras librerías de Rust bajo la misma API de Python sin romper compatibilidad. `A1` declaró esa jerarquía sobre-ingeniería para un único backend real: se conserva un solo punto de extensión (el trait del core, con dos implementaciones reales) y se elimina todo lo que no tenía implementación (placeholder `scipix_engine`, adaptadores por crate, factoría con un único producto). Ver ADR-006.

```text
pyocrust/
├── Cargo.toml                  # Crate pyocrust_core: pyo3, oar-ocr, image, rayon, reqwest, sha2.
│                               # [profile.release] con panic = "unwind" (ADR-004, ADR-010)
├── pyproject.toml              # Backend Maturin; module-name = "pyocrust._pyocrust_core" (ADR-011)
├── DECISIONS.md                # Intención de producto. Entrada de diseño; no se reescribe
├── DESIGN.md                   # Este documento
├── PLANNING.md                 # Fases y mapeo de cada tarea a su tarjeta del board
├── LICENSE                     # Apache-2.0 (coincide con la licencia de oar-ocr)
├── README.md                   # Uso, build con maturin y estructura
├── .gitignore                  # target/, .venv/, Cargo.lock, .env, __pycache__/, *.pyd/*.pdb
├── src/
│   ├── lib.rs                  # Registro del módulo PyO3 y clase pública VeloceOCR
│   ├── core/
│   │   ├── mod.rs              # Re-exports y trait OcrEngineBackend (ADR-002, ADR-006)
│   │   ├── types.rs            # Pyclasses BoundingBox, TextRegion, OcrResult, LayoutRegion, StructureResult;
│   │   │                       # enums OcrSize, ModelSpec y el enum Rust OcrOutput; struct ModelPaths
│   │   ├── error.rs            # OcrError y su traducción a excepciones Python
│   │   └── image_processor.rs  # ScaleDown y FullPageTiling: funciones puras sobre RgbImage,
│   │                           # sin I/O y sin conocer oar-ocr (ADR-009). Adaptador PyO3
│   │                           # del tiling en el submódulo `pyapi`
│   ├── storage/
│   │   ├── mod.rs              # Re-exports
│   │   ├── config.rs           # Resolución de rutas por prioridad estricta. Sin descarga
│   │   ├── models.rs           # Preflight: ficheros esperados por preset y cuáles faltan;
│   │   │                       # auto-descarga paralela acotada a 4 hilos (S2.0)
│   │   ├── download.rs         # Descargador Hugging Face resiliente (ADR-007)
│   │   ├── registry.rs         # Registro único de artefactos: ModelScope + HuggingFace (S2.0)
│   │   └── catalog.rs          # Catálogo de metadatos y perfiles de pipeline (S3.0)
│   └── engines/
│       ├── mod.rs              # Factoría: preset -> backend
│       ├── oar_text.rs         # Adaptador sobre OAROCRBuilder (PP-OCRv6)
│       ├── oar_structure.rs    # Adaptador sobre OARStructureBuilder (PP-StructureV3)
│       └── oar_indra.rs        # Adaptador sobre IndraOcrBuilder (indra) (S2.2)
├── pyocrust/                   # Paquete Python importable. Comparte nombre con el repositorio
│   ├── __init__.py             # Fachada pública de alto nivel
│   ├── __init__.pyi            # Stubs de tipos
│   ├── gpu.py                  # enable_cuda(): search path del runtime CUDA (D5)
│   ├── hardware.py             # Inventario físico y dataclasses GPU/RAM (S3.1)
│   ├── resolver.py             # TaskSpec, PipelineChoice, resolve_pipeline (S3.1)
│   ├── py.typed                # Marcador PEP 561
│   └── onnxruntime_providers_*.dll  # EPs que ORT carga del dir del módulo (D5)
└── tests/
    ├── conftest.py             # Utilidades comunes: PNG sintético con la stdlib y localización
    │                           # de los modelos reales en disco
    ├── test_config.py          # Niveles de prioridad en la resolución de rutas
    ├── test_tiling.py          # Troceado con solapamiento
    ├── test_recognize.py       # recognize end-to-end (carga directa, env var y caché)
    ├── test_indra.py           # Smoke Indra (S2.2)
    ├── test_models.py          # Caché fría (ModelScope y HuggingFace) y preflight (D5)
    ├── test_catalog.py         # Catálogo y perfiles de pipeline (S3.0)
    ├── test_license.py         # Clasificación y bloqueo por defecto (ADR-017)
    ├── test_hardware.py        # Inventario físico (S3.1)
    ├── test_resolver.py        # Resolvedor de pipeline (S3.1)
    ├── test_tasks.py           # Las 11 tareas de TaskPredictor (S2.4)
    ├── test_providers.py       # Selección de EP y provider_effective (D5)
    ├── test_gpu.py             # Contrato de pyocrust.enable_cuda() (D5)
    └── data/
        ├── sample_text.png     # Imagen real de dos líneas para los tests de reconocimiento
        ├── sample_formula.png  # Fórmula real para el test de LaTeX (S2.1)
        └── indra_math.png      # Fórmula con math para el smoke de Indra (S2.2)
```

> **Ampliación del árbol en `D5` (2026-11-09).** El árbol histórico de `D1` no
> listaba `pyocrust/gpu.py` (helper `enable_cuda()`), ni ocho de los trece
> `tests/test_*.py`, ni los fixtures `sample_formula.png` e `indra_math.png`. Todos
> existen y están verificados con `read_file`. Tampoco listaba
> `benchmarks/tests/test_pp_structurev3_backend.py`, que fija el contrato del
> adaptador aislado en subproceso (§10.4).

| Ruta | Estado (D1, 2026-10-25) | Nota |
| :--- | :--- | :--- |
| `DECISIONS.md`, `DESIGN.md`, `PLANNING.md` | Existen | Documentación; `DESIGN.md` y `PLANNING.md` se reescribieron en `E1` y se reconcilian en `D1` y `D2` |
| `Cargo.toml`, `pyproject.toml`, `LICENSE`, `README.md`, `.gitignore` | Existen | Introducidos en `I1` (commit `4ede5c7`) |
| `src/**` | Existe | `core/` en `I2`, `storage/` en `I3`, `engines/` + `lib.rs` en `I4`; ampliado en `S2.0`-`S2.4` |
| `pyocrust/**` | Existe | Fachada y stubs en `I1`, ampliados en `I4`; `hardware.py`/`resolver.py` en `S3.1` |
| `tests/**` | Existe | `conftest.py`, `test_*` y `data/` introducidos en `V1` (commit `d2e445c`); `test_indra.py` en `S2.2` |

> **Ficheros enumerados y no existentes: ninguno.** Los únicos artefactos
> presentes en el árbol y no listados arriba son de build y están ignorados por
> git: `pyocrust/_pyocrust_core.pyd`, `pyocrust/pyocrust_core.pdb`
> (`.gitignore:16,21`), `Cargo.lock`, `target/`, `.venv/` y los `__pycache__/`.

## 3. Especificaciones Técnicas Clave para Hermes

### 3.1 Contrato de Interfaz: de `OcrEngineBackend` a presets tipados

Interfaz del borrador inicial, **sustituida** por el dictamen de `A1` (ADR-002):

```rust
// SUPERADO: no existe un único fichero .onnx por pipeline.
pub trait OcrEngineBackend: Send + Sync {
    fn load_model(&mut self, model_path: &str) -> Result<(), String>;
    fn recognize(&self, image_bytes: &[u8]) -> Result<OcrResult, String>;
}
```

Por qué no es válido: ningún pipeline de `oar-ocr` `0.10.1` se inicializa con un solo fichero.

| Pipeline | Artefactos requeridos | Cita |
| :--- | :--- | :--- |
| Texto básico (`OAROCRBuilder`) | detector ONNX + reconocedor ONNX + diccionario `.txt` | `oar-ocr/src/oarocr/ocr.rs:163-178` (cita `A1`) |
| Preset PP-OCRv6 | los tres anteriores + umbrales oficiales | `oar-ocr/src/oarocr/ocr.rs:218-235` (cita `A1`) |
| Preset PP-StructureV3 | **9** fuentes: 8 `.onnx` (layout det, OCR det, OCR rec, table classification, wired table structure, wireless table structure, wired cell detection) + `table_structure_dict_ch.txt` + el diccionario OCR del preset embebido | `oar-ocr/src/oarocr/structure.rs:345-361` (cita `A1`); el conteo se fijó contra el crate en `I4` (`src/core/types.rs:113-118`) y manda sobre la cifra "8 ficheros" de versiones anteriores de este documento |

Además, los builders consumen el builder y devuelven pipelines inmutables listos para inferencia (`OAROCR`, `OARStructure`): no existe un ciclo de vida con carga mutable tardía.

Contrato adoptado (nombres fijados por la tarjeta `I2`, que es la que implementa) y **verificado en el código**:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum OcrSize { #[default] Tiny, Small, Medium }    // src/core/types.rs:43-51

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ModelSpec { PpOcrV6(OcrSize), PpStructureV3 } // src/core/types.rs:110-119

/// Rutas locales ya resueltas por `storage::config` para un `ModelSpec`.
pub struct ModelPaths { /* 9 campos de ruta + spec */ } // src/core/types.rs:144-156

pub trait OcrEngineBackend: Send + Sync {                // src/core/mod.rs:33-45
    /// Construye el pipeline desde rutas locales resueltas.
    /// 3 artefactos para PP-OCRv6; 9 fuentes para PP-StructureV3.
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError>;
    fn recognize(&self, image: &[u8]) -> Result<OcrOutput, OcrError>;
}
```

Reglas del contrato:

| Regla | Detalle | Verificado |
| :--- | :--- | :--- |
| Entrada | Ruta de fichero (`str`/`Path`) **y** buffer en memoria (`&[u8]`) | `src/lib.rs:79-91` (extrae `str`, `bytes` y `__fspath__`) |
| Carga | Una sola vez, en el constructor. El modelo queda residente; no hay recarga por llamada | `src/engines/*::new_with_model`; test `test_llamar_dos_veces_no_recarga_el_pipeline` |
| Errores | `Result<_, OcrError>` tipado. Prohibido `Result<_, String>` y prohibido `unwrap()` en rutas de datos | `src/core/error.rs`; sin `unwrap()` en rutas de datos |
| Salida de texto | `OcrResult` con `TextRegion` (texto, confianza y caja) | `src/core/types.rs:265-343` |
| Salida de estructura | `StructureResult` con `to_markdown()` (tablas HTML, fórmulas LaTeX, jerarquía documental) y acceso a `elements`/`regions`, **sin** aplanar a `OcrResult` (ADR-003). **Verificado (`D2`, `b128566`):** `convert_structure` conserva el Markdown del crate y los elementos de layout (`src/engines/oar_structure.rs:185-215`); el trait devuelve `OcrOutput::{Text(OcrResult), Structure(StructureResult)}` (`src/core/types.rs:438-443`, `src/core/mod.rs:45`) | §9.1, §9.2 |

Firmas reales de estructura (cita `A1` sobre `0.10.1`):

| Elemento | Firma | Cita |
| :--- | :--- | :--- |
| Builder de preset | `OARStructureBuilder::pp_structurev3() -> Self` | `oar-ocr/src/oarocr/structure.rs:345` |
| Construcción | `fn build(mut self) -> Result<OARStructure, OCRError>` | `oar-ocr/src/oarocr/structure.rs:807` |
| Inferencia por ruta | `fn predict(&self, image_path: impl Into<PathBuf>) -> Result<StructureResult, OCRError>` | `oar-ocr/src/oarocr/structure.rs:2682` |
| Inferencia por buffer | `fn predict_image(&self, image: image::RgbImage) -> Result<StructureResult, OCRError>` | `oar-ocr/src/oarocr/structure.rs:2979` |
| A Markdown | `fn to_markdown(&self) -> String` | `oar-ocr-core-0.10.1/src/domain/structure.rs:471` |

> **Nota de discrepancia y resolución real de R1 (D1).** El docstring antiguo de
> `src/lib.rs:50-51` usaba firmas de dos parámetros
> (`with_table_cell_detection(model, cell_type)`), mientras que las fuentes de
> `0.10.1` usan métodos específicos desacoplados. El adaptador que finalmente se
> escribió **no** usa `pp_structurev3()`: construye el pipeline con
> `OARStructureBuilder::new(layout)` + `.layout_model_name`, `.with_ocr`,
> `.with_table_classification`, `.with_wired_table_structure`,
> `.with_wireless_table_structure`, `.with_wired_table_cell_detection` y
> `.table_structure_dict_path` (`src/engines/oar_structure.rs:130-137`). Manda la
> API real del crate; el riesgo R1 queda cerrado (§5).

### 3.1.1 Contrato actual de Indra (`S2.2`, **Hecho**; sólo queda el límite TLS)

> **Reetiquetado en `D5` (2026-11-09).** La cabecera histórica decía «parcial».
> `S2.2` es **Hecho** en el board (`t_027743e2`, 2026-11-02): los 9 artefactos
> están en disco (`models_status()['presets']['indra']` 9/9), `VeloceOCR('indra')`
> reconoce y produce `StructureResult`. Lo único que sigue **sin verificar** es la
> descarga fría por HuggingFace desde cero, por el bloqueo TLS del host (§10.1).
> La nota «parcial» de `S2.2` en §1.1 queda como estado histórico.

Esta sección actualiza las instantáneas históricas `D1`/`D2` de este documento
(dos implementaciones/presets); no cierra sus condiciones ni sustituye sus evidencias.
El árbol actual añade `ModelSpec::Indra` y `src/engines/oar_indra.rs` como tercer
backend del mismo trait. `VeloceOCR('indra').recognize(...)` devuelve
`StructureResult`, con Markdown, regiones de línea y elementos de bloque.

* Carga: `IndraOcrBuilder::new(root/indra).math(true)`, tras el mismo
  `ensure_models` del constructor. Requiere nueve artefactos en `<models_dir>/indra/`:
  `det.onnx`, `rec.onnx`, `order.onnx`, `meta.json`, `mathcls.onnx`, `math_enc.onnx`,
  `math_dec_init.onnx`, `math_dec_step.onnx` y `math_meta.json`.
* `models_status()['indra']` es el catálogo completo con `required=false`;
  `models_status()['presets']['indra']` lista los nueve requisitos con `required=true`.
  El catálogo no determina si el preset está listo.
* `elements[*].confidence == 0.0` significa score de bloque no disponible,
  no confianza inferida nula; las regiones conservan la confianza de línea.
* `formulas=[]` significa que Indra no expone registros separados de fórmulas,
  no ausencia de matemáticas: el LaTeX inline se conserva en Markdown/regiones.
* Evidencia comunicada para `S2.2`: smoke CPU con dos regiones, dos elementos y
  Markdown; una prueba Python y una Rust de giro inverso pasadas. No constituye
  validación de calidad matemática ni de GPU. La descarga Rust HF falla por TLS;
  el diagnóstico con `urllib` no valida `ensure_models`. Suite global pendiente.

> **Estado real (`D5`, 2026-11-09).** La suite global **no** está pendiente: el
> preset `indra` corre en la campaña (§10.3) y la suite del paquete está en
> **162 passed, 1 skipped** (`t_052d7c9c`). El test de descarga fría por HF
> (`test_cache_fria_huggingface_descarga_indra_y_verifica_sha256`) queda `skip`
> por el TLS del host, **no** por un fallo del descargador: el artefacto baja con
> `curl --ssl-no-revoke` y su SHA-256 cuadra con el registro. GPU y calidad
> matemática siguen sin aceptación formal (§10.5 y §10.8).

### 3.1.2 Contrato actual de `TaskPredictor` (`S2.4`, APROBADO acotado)

`TaskPredictor(task, models=None, **options)` amplía las cinco tareas de `S2.3`
a once. `predict(image)` devuelve un `dict`; `predict_batch(images)` devuelve
uno por imagen, en orden de entrada, y `[]` para lote vacío. Ambos admiten
`str`, `Path` y `bytes` de imagen codificada. La inferencia libera el GIL con
`py.detach`; lectura/decodificación y conversión a diccionarios lo retienen.
Fuente normativa: `src/tasks/mod.rs` (whitelist/defaults: líneas 50-128;
mappers: 214-312) y `src/storage/registry.rs::task_artifacts`.

| Tarea | Opciones admitidas (valores por defecto) | Salida completa |
| :--- | :--- | :--- |
| `text_detection` | `score_threshold=0.3`, `box_threshold=0.6`, `unclip_ratio=1.5`, `max_candidates=1000` | `{detections: list[{bbox: list[list[float]], score: float}]}` |
| `text_recognition` | `score_threshold=0.0`, `dict_path` (prioridad abajo) | `{text: str, score: float}` |
| `layout_detection` | `score_threshold=0.5`, `model_name='pp_doclayoutv3'` | `{elements: list[{bbox: list[list[float]], element_type: str, score: float}], is_reading_order_sorted: bool}` |
| `table_classification` | `score_threshold=0.5`, `topk=2`, `input_shape=(224, 224)` | `{classifications: list[{class_id: int, label: str, score: float}]}` |
| `table_structure_recognition` | `dict_path`, `model_name` e `input_shape` opcionales; sin override por defecto | `{structures: list[str], bboxes: list[list[float]]}`; tokens y geometría, **no HTML reconstruido** |
| `table_cell_detection` | `score_threshold=0.3`, `model_name` detectado de la ruta; fallback `rt-detr-l_wired_table_cell_det` | `{cells: list[{bbox: list[list[float]], label: str, score: float}]}` |
| `document_orientation` | `score_threshold=0.5`, `topk=4` | `{orientations: list[{class_id: int, label: str, score: float}]}` |
| `text_line_orientation` | `score_threshold=0.5`, `topk=2`, `input_shape=(80, 160)` | Mismo esquema de orientaciones |
| `document_rectification` | Ninguna | `{image: bytes, width: int, height: int}`; PNG codificado como `PyBytes` |
| `seal_text_detection` | `score_threshold=0.5` | Mismo esquema de detecciones de texto |
| `formula_recognition` | Ninguna | `{formula: str, score: float \| None}`; modelo fijo `PP-FormulaNet-S`, `None` si no hay score |

Las cajas de detección/layout/celdas son cuatro puntos `[x, y]`; no se debe
confundir su forma con `bboxes` de estructura de tabla. `input_shape` es `(H, W)`
con dos enteros `u32` positivos. Para estructura, el fallback local `(512, 512)`
se calcula pero **no se pasa al builder** si falta la opción: upstream detecta
shape del ONNX y familia por ruta (fallback wired). No admite `score_threshold`.
Nombre de tarea u opción desconocida y shape cero producen `PyOcrValueError`;
la whitelist se comprueba antes de resolver/cargar modelos.

| Tarea | Artefactos gestionados, en orden (registro real) |
| :--- | :--- |
| `text_detection` | `pp-ocrv6_tiny_det.onnx` |
| `text_recognition` | `pp-ocrv6_tiny_rec.onnx`, `ppocrv6_tiny_dict.txt` |
| `layout_detection` | `pp-doclayoutv3.onnx` |
| `table_classification` | `pp-lcnet_x1_0_table_cls.onnx` |
| `table_structure_recognition` | `slanext_wired.onnx`, `table_structure_dict_ch.txt` |
| `table_cell_detection` | `rt-detr-l_wired_table_cell_det.onnx` |
| `document_orientation` | `pp-lcnet_x1_0_doc_ori.onnx` |
| `document_rectification` | `uvdoc.onnx` |
| `text_line_orientation` | `pp-lcnet_x1_0_textline_ori.onnx` |
| `seal_text_detection` | `pp-ocrv4_mobile_seal_det.onnx` |
| `formula_recognition` | `pp-formulanet-s.onnx`, `pp-formulanet-tokenizer.json` |

* `models=None` invoca `ensure_task_models` para los artefactos registrados.
  `models=str` es ruta de modelo, no directorio; `models=dict` exige `model`
  y admite `dict`/`tokenizer`. Estos caminos explícitos no descargan.
* Diccionario de texto/tabla: `options['dict_path']` > `models['dict']` > hermano
  del modelo canónico con el nombre del registro. El fallback se evalúa solo
  cuando no hay override; una ruta explícita inválida no cae al hermano.
  Fórmula: `models['tokenizer']` > hermano `pp-formulanet-tokenizer.json`.
* `existing_asset` exige fichero local existente y lo canonicaliza antes de
  entregarlo a upstream, para modelo, diccionario y tokenizer. Ausente/directorio
  o fallo de canonicalización: `PyOcrRuntimeError` con ruta y causa; sin descarga
  implícita upstream, incluso cuando este ignoraría `PYOCRUST_OFFLINE`.
* Evidencia comunicada y límites: actualización `S2.4` de `PLANNING.md`.
  Aprobación del contrato/código, no once inferencias reales ni validación GPU;
  no cierra el sign-off global y preserva las instantáneas `D1`/`D2` y `S2.3`.

### 3.1.3 Catálogo, hardware y recomendación (`S3`, APROBADO acotado)

APIs ya exportadas, sin nueva API de ejecución: `model_catalog`,
`pipeline_profiles`, `GpuInfo`, `HardwareProfile`, `detect_hardware`, `TaskSpec`,
`PipelineChoice` y `resolve_pipeline`. Fuentes: `src/storage/catalog.rs`,
`pyocrust/hardware.py` y `pyocrust/resolver.py`.

* `model_catalog() -> dict[str, dict]`, indexado por nombre de artefacto:
  `{name: str, task: str, description: str, params: int | None,
  size_bytes: int | None, env_vars: list[str], license: str,
  license_commercial_use: bool, license_acknowledge: bool,
  license_restricted: bool, license_notes: str, license_url: str | None}`.
  Incluye el registro upstream
  y companions Indra; `params=None` siempre, tamaño desde `find(name)` para
  upstream y `None` para Indra (no sustituido por los tamaños HF de storage).
  `env_vars`: `OAR_HOME`, `OCR_MODELS_CACHE_DIR`, `PYOCRUST_OFFLINE`,
  `CUDA_LAUNCH_BLOCKING`, `RUST_LOG`; no promete controles `OAR_VL_*` para Indra ONNX.
  Los seis campos `license*` clasifican el artefacto contra el texto primario
  (ADR-017): `license` es el SPDX; `license_commercial_use`/`license_acknowledge`
  son lo que el modelo **permite/exige**; `license_restricted` es
  `not commercial_use or acknowledge`; `license_url` apunta a la revisión fijada.
* `pipeline_profiles() -> dict[str, dict]`, indexado por ID:
  `{id: str, family: str, quality: str, output_format: str,
  disk_bytes: int | None, ram_bytes: int | None, artifacts: list[str], description: str,
  license: str, license_commercial_use: bool, license_acknowledge: bool,
  license_restricted: bool, license_notes: str, license_url: str | None}`.
  Son los cinco presets reales del registro más las once tareas (§3.1.2).
  Tiny/Small/Medium: `pp_ocrv6`, `speed`/`balanced`/`accuracy`, `text`;
  PP-StructureV3: `pp_structurev3`, `balanced`, `markdown`; Indra:
  `indra`, `accuracy`, `markdown`; tareas: `task`, `default`, `json`.
  Artefactos desde el registro, no una lista ficticia: PP-StructureV3 tiene ahora
  once (incluye fórmula/tokenizer), frente a la instantánea histórica D1/D2.
  `disk_bytes` suma tamaños upstream con comprobación de overflow y es `None`
  si falta cualquier entrada (Indra); `ram_bytes=None` siempre. Tamaño en disco
  no es número de parámetros, RAM medida ni disponibilidad local.
  Ambas consultas carecen de escaneo de disco, red e inferencia.
* Dataclasses inmutables: `GpuInfo(name: str | None=None, vram_bytes: int | None=None)`;
  `HardwareProfile(cpu_count: int, ram_bytes: int | None, gpu: GpuInfo | None=None)`.
  CPU entero positivo; RAM/VRAM enteros positivos o `None` (no bool). GPU de otro
  tipo causa `TypeError`; valores numéricos inválidos, `ValueError`.
  `detect_hardware()` usa stdlib: CPU `os.cpu_count() or 1`, RAM total del SO
  (desconocida → `None`), primera GPU NVIDIA visible vía `nvidia-smi` (sin prueba
  de CUDA en el wheel). `CUDA_VISIBLE_DEVICES` vacío/`-1` oculta; índices o prefijos
  UUID `GPU-` filtran en orden, parando ante inválido/ambiguo/repetido. Fallo de
  inventario → `gpu=None`; VRAM desconocida → `None`, nunca memoria inventada.
* `TaskSpec(document_kind='digital', ocr_only=True, formulas='none', tables=False,
  quality='speed', output_format='text')` es inmutable. Enum válidos:
  `document_kind`: `scanned|digital|mixed`; `formulas`: `none|with_text|only`;
  `quality`: `speed|balanced|accuracy`; `output_format`: `text|markdown|html|json`.
  Enums inválidos → `ValueError`; `ocr_only`/`tables` deben ser bool (`TypeError`).
* `resolve_pipeline(task: TaskSpec, hardware: HardwareProfile | None=None)` detecta
  hardware solo sin override. Tipos incorrectos → `TypeError`. Precedencia:
  fórmulas, tablas, Markdown/HTML **o cualquier `ocr_only=False`** seleccionan
  `pp_structurev3`, `size=None`; JSON solo no fuerza estructura. Para texto:
  speed, RAM desconocida o RAM <4 GiB → tiny; después balanced o RAM <8 GiB →
  small; resto → medium. Son heurísticas, no mediciones de viabilidad.
  Scanned/mixed añade orientación y rectificación; accuracy y VRAM >=8 GiB
  añade `indra` como alternativa en `tasks`, sin cambiar preset ni probar
  disponibilidad, wheel CUDA o ejecución. Ninguna tarea se ejecuta automáticamente.
* `PipelineChoice` inmutable: `{preset: str, size: str | None, tasks: tuple[str, ...],
  models_dir: str, offline: bool}`; propiedad `id` devuelve `pp_ocrv6_{size}`
  para texto o el preset de estructura. `tasks` es recomendación, no secuencia
  de `TaskPredictor` ejecutable (puede incluir el preset `indra`).
  El resolver no descarga/carga modelos ni hace preflight. `models_dir` usa
  `resolve_models_dir()` nativo (§7.1): puede normalizar/reexportar `OAR_HOME`
  relativa; **no es ausencia absoluta de efectos laterales**. El `custom_path`
  explícito de una posterior ejecución sigue ganando. `offline` lee
  `PYOCRUST_OFFLINE`: unset/vacío/`0`/`false`/`no` → false, case-insensitive,
  sin trim de espacios. `output_format` orienta la selección, no convierte salida.

Evidencia acotada comunicada: hardware **15 pass, 1 skip**, resolver **29 pass**,
catálogo **5 pass**, Rust **53 pass previos** (`PLANNING.md`). No certifica GPU,
modelos disponibles, rendimiento ni sign-off global.

### 3.1.4 API pública: tres superficies (`S2.3`-`S3.5`)

`pyocrust` expone tres superficies de inferencia, además de las consultas de
catálogo y hardware de §3.1.3:

**Superficie 1 — pipelines tipados:**

```python
from pyocrust import VeloceOCR

engine = VeloceOCR("pp_ocrv6")          # Tiny por defecto
result = engine.recognize("page.png")    # OcrResult para texto

engine = VeloceOCR("pp_structurev3")
result = engine.recognize("doc.png")     # StructureResult con to_markdown()

engine = VeloceOCR("indra")
result = engine.recognize("page.png")    # StructureResult con Markdown + bloques
```

`VeloceOCR` acepta `"pp_ocrv6"`, `"pp_structurev3"` e `"indra"`. No hay variantes
`Small`/`Medium` como símbolos públicos separados: se seleccionan con
`PipelineChoice` + `resolve_pipeline`, o pasando `custom_path` al directorio del
modelo. `recognize` acepta `str`, `PathLike` y `bytes`; libera el GIL durante la
inferencia. `VeloceOCR` y `TaskPredictor` aceptan además
`license_commercial_use` (default `True`) y `license_acknowledge`
(default `False`): declaran la intención del **usuario** sobre la licencia de
los pesos y bloquean el constructor antes de `ensure_models`, la red y el disco
(ADR-017).

**Selección de execution provider (`device`, *opt-in*).** `VeloceOCR` y
`TaskPredictor` aceptan un `device` **opcional** con default `"cpu"`:
`"cpu"`, `"auto"`, `"cuda"` o `"directml"`. Es *opt-in* y **no** reintroduce la
gobernanza de VRAM que `S1.7` retiró de este documento: solo elige el execution
provider (EP) de ONNX Runtime, sin imponer ningún presupuesto de memoria. El EP se
resuelve y **prueba** (`OrtSessionConfig::resolve_auto`, `src/core/device.rs`)
antes de construir el pipeline; el `"cpu"` por defecto no toca ninguna GPU.
`provider_effective` (propiedad de ambas clases) reporta el EP que realmente
corrió —`cpu` si no hay acelerador—, y `available_providers() -> list[str]`
enumera los EPs aceleradores que registran **de verdad** en el host (`[]` si
ninguno: un inventario físico de GPU, `detect_hardware()`, no basta). Pedir
`device="cuda"`/`"directml"` sin un EP que registre lanza `PyOcrValueError` en el
constructor: **nunca** se etiqueta CPU como GPU.

**Helper de search path (`D5`, 2026-11-09).** `pyocrust.enable_cuda() -> list[str]`
(`pyocrust/gpu.py:42`, reexportado en `pyocrust/__init__.py:42`) añade al *search
path* de Windows (`os.add_dll_directory`) los directorios donde ya viven las DLL
del runtime CUDA (`nvidia/*/bin*`, `torch/lib`, `CUDA_PATH`/`CUDA_HOME`) y
devuelve `available_providers()` tras intentarlo. Es *best-effort* e idempotente;
en Linux/macOS es un no-op (el cargador respeta `RPATH`/`LD_LIBRARY_PATH`). Existe
porque ORT carga `onnxruntime_providers_cuda.dll` buscando en el **directorio del
módulo** y sus dependientes (`cublas64_13.dll`, `cublasLt64_13.dll`) no se
encuentran por `PATH` desde Python 3.8. Verificado en la campaña CUDA
(`t_8cd2897e`): con él, `available_providers()` → `['cuda']`. Contrato fijado por
`tests/test_gpu.py`.

**Superficie 2 — `TaskPredictor` (11 tareas):**

```python
from pyocrust import TaskPredictor

predictor = TaskPredictor("text_detection")
result = predictor.predict("page.png")           # dict
results = predictor.predict_batch(["a.png", "b.png"])  # list[dict]
```

`TaskPredictor(task, models=None, **options)` acepta los 11 nombres de tarea en
`snake_case`. `predict(image)` devuelve un `dict`; `predict_batch(images)` devuelve
un `dict` por imagen, en orden de entrada, y `[]` para lote vacío. La inferencia
libera el GIL con `py.detach`; lectura/decodificación y conversión a diccionarios
lo retienen.

**Por qué `dict` y no 11 `#[pyclass]` (ADR-013).** Los `XResult` del crate
(`TextDetectionResult`, `TableClassificationResult`, etc.) solo derivan `Debug,
Clone`, no `PyClass`. Envolver cada uno habría requerido 11 adaptadores manuales
de campos, duplicando la lógica de postprocesado que `oar-ocr` ya aplica. La
decisión es devolver `dict` con esquema fijado en `pyocrust/__init__.pyi`; el
consumidor pierde el autocompletado de tipos en Rust, pero gana una superficie
única y mantenible.

Fuente normativa: `src/tasks/mod.rs` (whitelist/defaults: líneas 50-128;
mappers: 214-312) y `src/storage/registry.rs::task_artifacts`.

**Superficie 3 — catálogo + resolvedor (`S3`):**

```python
from pyocrust import (
    model_catalog, pipeline_profiles,
    detect_hardware, HardwareProfile, GpuInfo,
    TaskSpec, PipelineChoice, resolve_pipeline,
)
```

`model_catalog() -> dict[str, dict]` y `pipeline_profiles() -> dict[str, dict]`
son consultas estáticas sin escaneo de disco, red ni inferencia (§3.1.3).
`detect_hardware() -> HardwareProfile` usa solo stdlib (`pyocrust/hardware.py`);
`HardwareProfile` y `GpuInfo` son dataclasses inmutables que aceptan overrides
explícitos.

`resolve_pipeline(task: TaskSpec, hardware: HardwareProfile | None=None) -> PipelineChoice`
elige un preset/tarea sin cargar modelos ni descargar (`pyocrust/resolver.py`).
`PipelineChoice` expone `preset`, `size`, `tasks`, `models_dir` y `offline`;
la propiedad `id` devuelve el identificador listo para pasar a
`VeloceOCR(preset=choice.id)`.

### 3.2 Estrategia de Resolución de Modelos (Paths) y Autodescarga

El componente `OcrConfig` resuelve la ubicación física del modelo en disco con el siguiente orden estricto de prioridad:

1. **Parámetro explícito (`custom_path`)**: suministrado directamente en Python al instanciar la clase.
2. **Variables de Entorno**: `OAR_HOME` (estándar de `oar-ocr`) y, tras ella, `OCR_MODELS_CACHE_DIR` (directorio compartido definido a nivel de sistema).
3. **Ruta por Defecto (Fall-back)**: `~/.oar` (caché estándar de `oar-ocr`).

| Nivel | Fuente | Gana a |
| :--- | :--- | :--- |
| 1 | parámetro `custom_path` | niveles 2 y 3 |
| 2a | `OAR_HOME` | `OCR_MODELS_CACHE_DIR` y nivel 3 |
| 2b | `OCR_MODELS_CACHE_DIR` | nivel 3 |
| 3 | `~/.oar` | — |

Verificado en `src/storage/config.rs:103-133` y por los tests `test_nivel_1..3` de `tests/test_config.py`.

**Reexportación de la ruta resuelta (`OAR_HOME`).** El directorio que gana la resolución se reexporta **siempre** como `OAR_HOME` absoluta al entorno del proceso, gane quien gane (nivel 1, 2a, 2b o 3). Motivo: la caché de autodescarga de `oar-ocr-core` se decide leyendo **solo** `OAR_HOME` (`oar_ocr_core::core::download::cache_dir`, `oar-ocr-core-0.10.1/src/core/download/mod.rs:84`), de modo que sin la reexportación un `custom_path` desde Python o un `OCR_MODELS_CACHE_DIR` resolvían bien para el descargador propio pero el de `oar-ocr` seguía escribiendo en `~/.oar` (caché en `C:`). Implementado en `src/storage/config.rs:143-158`; cubierto por `resolve_models_dir_reexporta_el_directorio_resuelto_como_oar_home` (Rust) y `test_el_custom_path_se_reexporta_como_oar_home_para_oar_ocr` / `test_ocr_models_cache_dir_se_reexporta_como_oar_home_para_oar_ocr` (`tests/test_config.py`). Efecto colateral asumido: el último directorio resuelto manda para el resto del proceso, igual que `S1.5` ya hacía con la `OAR_HOME` relativa.

*Comportamiento de descarga:* la v1 tenía previstos **dos** caminos: (1) `auto-download` de `oar-ocr` desde ModelScope hacia `$OAR_HOME`; (2) descargador propio desde Hugging Face cuando ModelScope no es alcanzable o el entorno es corporativo/offline, con el contrato de §7.3. Si el fichero existe y su tamaño/hash es correcto, **no** se hace ninguna petición de red.

> **Estado real (D1).** Solo el camino (1) está activo: `oar-ocr` trae
> `auto-download` (`Cargo.toml:20`) y es quien descarga cuando falta un artefacto.
> El camino (2) está **implementado y testeado** (`src/storage/download.rs`) pero
> **no se invoca en runtime**: no hay ninguna llamada a `fetch` en `src/lib.rs` ni
> en `src/engines/`. ADR-007 queda **parcial** (§9.1) y es el defecto que `S1`
> marcó como condición 4.
>
> **Actualización (`S2.0`, `113a490`).** El camino (2) **ya se invoca**: `ensure_models`
> llama a `download::fetch` para cada artefacto obligatorio que falte
> (`src/storage/models.rs:226`). El bloque de arriba es el estado histórico de `D1`;
> ADR-007 queda **cumplido** (§9.1).
>
> **Verificado en `D5` (2026-11-09).** `ensure_models` (`src/storage/models.rs:226-248`)
> es quien invoca `download::fetch` (`src/storage/download.rs:154`) a través de
> `download_all` (`:298`, pool `rayon` de `DOWNLOAD_THREADS = 4` en `:24`). El
> camino HF está conectado y cubierto por el test de caché fría, que en este host
> sale `skip` por TLS (§10.1). La nota «parcial» de `D1` queda como histórica.

### 3.3 Gestión de Memoria y Concurrencia de Alto Rendimiento

* **Liberación del GIL de Python:** el método `recognize` expuesto a Python invoca `py.detach()` antes de la inferencia. **Nota (D1):** en PyO3 0.30 la API es `py.detach()`; `py.allow_threads()` es su nombre anterior. Implementado en `src/lib.rs:93-95`.
* **Seguridad en GPU:** las sesiones de inferencia pesadas (ONNX Runtime, CUDA, DirectML) se encapsulan en `Arc` para permitir llamadas concurrentes seguras entre hilos nativos sin recargas destructivas de contexto. Implementado: `pipeline: Option<Arc<OAROCR>>` (`src/engines/oar_text.rs:50`) y `Option<Arc<OARStructure>>` (`src/engines/oar_structure.rs:32`).
* **Ciclo de Vida Limpio (VRAM):** ~~Los motores deben implementar el trait nativo `Drop`...~~ **Corregido (ADR-005):** `oar-ocr` ya es dueño de las sesiones `ort::Session`, cuyo `Drop` invoca `OrtReleaseSession` mediante RAII. No se implementa `Drop` manual. **Corregido de nuevo en `D1` (condición `S1.7`):** la gobernanza de VRAM **no** se hace con `OrtSessionConfig` (`gpu_memory_budget`, `idle_memory_recovery`): esas opciones no existen ni se exponen en esa forma en `oar-ocr` `0.10.1` ni aparecen en el código. La VRAM se libera exclusivamente al caer el último `Arc` y el recolector de Python.
* **Estabilidad del intérprete (ADR-004):** el perfil release declara `panic = "unwind"` (`Cargo.toml:45`).
* **GIL en la construcción (`S1.6`, re-verificado en `D2`):** `VeloceOCR::new` resuelve rutas y ejecuta el preflight **reteniendo** el GIL (`src/lib.rs:35-60`); la creación del motor ONNX se hace con `py.detach` (`src/lib.rs:62`), así que la parte pesada ya lo libera.

| Decisión de concurrencia | Regla |
| :--- | :--- |
| GIL | `py.detach()` envuelve la inferencia de `recognize` (`src/lib.rs:93`) y la creación del motor (`src/lib.rs:62`); la resolución de rutas y el preflight retienen el GIL (`S1.6`) |
| Sesiones | Envueltas en `Arc`; sin `Drop` manual (ADR-012) |
| Hilos intra-op de ONNX | Por defecto los de ORT. Con `intra_threads = 1` se habilita paralelismo inter-página explícito |
| `rayon` | En uso: `src/storage/models.rs:13,297` (pool de 4 hilos en `ensure_models`, ADR-008) |

### 3.4 Preprocesamiento: Tiling vs. Scaling

El componente `SmartImageProcessor` admite dos estrategias de segmentación visual en memoria nativa sin duplicar buffers:

1. **`ScaleDown`**: Redimensionamiento manteniendo la relación de aspecto para imágenes sencillas. **Es la estrategia por defecto** y es la que aplica el pipeline general: se delega el escalado geométrico en `oar-ocr` (`preprocess.rs`, `limit_side_len`), que respeta la relación de aspecto que esperan los modelos de layout y tablas de Paddle. Utilidad pura: `scale_down` (`src/core/image_processor.rs:97-123`).
2. **`FullPageTiling`**: Troceado en mosaicos (512x512 píxeles) con un solapamiento (*overlap*) configurable (64px por defecto) para garantizar que las fórmulas matemáticas ubicadas en los márgenes de corte no se dividan ni pierdan consistencia sintáctica. **Corrección (ADR-009):** el mosaico arbitrario **rompe la coherencia geométrica** de los modelos de detección de layout y tablas, por lo que **no** se aplica por defecto al pipeline general. Se conserva como utilidad pura, opt-in y testeable (`src/core/image_processor.rs:147-185`), expuesta a Python solo para los tests vía `pyapi` (`:209-250`).

> **Defecto abierto (D1, condición `S1.1`).** El adaptador `pyapi::full_page_tiling`
> llama a la función pura, que materializa una copia `RgbImage` de **cada** mosaico
> (`image::imageops::crop_imm(...).to_image()`, `src/core/image_processor.rs:180`)
> para descartarlas acto seguido y devolver solo `(x, y, ancho, alto)`. Con
> parámetros válidos y un `overlap` alto, el número de mosaicos explota y agota la
> memoria del proceso. Pendiente de corrección (`S1.1`, bloqueante).
>
> **Cerrado (`4502d1e`; re-verificado en `D5`).** El adaptador `pyapi` ya no
> materializa: `full_page_tiling_boxes` (`src/core/image_processor.rs:150-182`)
> devuelve solo la geometría `(x, y, ancho, alto)` y `full_page_tiling`
> (`:184-200`) es la utilidad opt-in que sí materializa, pero **no** la usa el
> adaptador de Python. `S1.1` está cerrada (§9.2) y el bloque de arriba queda como
> estado histórico de `D1`.

### 3.5 Contrato de la campaña de benchmarks (medición, no marketing)

`benchmarks/` (fuera de `src/`) es el banco de evidencia del paquete, con un banco por
feature. La campaña `t_347622f2`/`t_c2e5a1a9`/`t_7188f49a`/`t_9fe2c075` fija cuatro
reglas que los informes (`SUMMARY.md`, `SCOREBOARD.md`, `CPU_VS_GPU.md`,
`reports/<feature>/REPORT.md`) deben cumplir; incumplirlas invalida la comparación.
**Estado vigente (`D5`, 2026-11-09):** esas reglas las refuerza
`benchmarks/CRITERIO_MEDICION.md` (9 reglas «férreas») y la sonda
`benchmarks/validez_medicion.py`, que hoy da **9/9 `VALIDA`** (§10.3).

1. **`n` uniforme por feature.** Todas las filas salen del mismo barrido.
   `SUMMARY` y `SCOREBOARD` se generan del mismo colector de CSV
   (`benchmarks/features/summary.py::collect_rows`), de modo que no divergen; los
   `REPORT.md` por feature los genera `report.py` (desde los CSV de cada run) y
   `QUALITY_VS_TIME` deriva de esos `REPORT.md`. `SCOREBOARD.md` declara `n` por fila.
   **Matizado en `D5`:** el `--limit` ya no es 20 en todas las features: la muestra
   estratificada vigente es `formula` 10, `table` 8, `full_page` 6, `layout` 40 y
   20 en el resto. La uniformidad se exige **dentro** de cada feature y **entre** su
   run CPU y su run GPU, no entre features distintas.
2. **CPU vs GPU reales.** Cada adaptador reporta `provider_effective` (el EP que de
   verdad ejecutó). `--device gpu` sobre un motor sin acelerador queda `skipped` con
   motivo; un *fallback* a CPU jamás se etiqueta como GPU (`benchmarks/reports/CPU_VS_GPU.md`).
3. **Licencia por motor (informativa).** La columna `license` de los informes señala las
   licencias no permisivas de los motores de comparación (p. ej. AGPL-3.0 de los YOLOv10
   de `omoured`); la **puerta** vinculante sigue siendo el catálogo + los flags de
   política de ADR-017, no esta columna.
4. **Solo DocLayNet en `layout`.** Únicamente los detectores *fine-tuned* sobre DocLayNet
   son comparables: las filas YOLOv10 de referencia llevan mAP de DocLayNet y los YOLO
   medidos exponen las **11 clases de DocLayNet**, nunca las 80 de COCO.

Queda abierto `t_b304e350`: retirar las referencias externas que no están medidas sobre
el mismo dataset/GT y re-ejecutarlas en CPU+GPU. El detalle por motor y la provenance
(comando, dataset, `n`, runtime) viven en `benchmarks/`.

> **Estado real (`D5`, 2026-11-09).** `t_b304e350` está **archivada** (`needs_input`),
> no cerrada: lo que se hizo fue retirar el concepto de «referencias externas» de
> **todos** los artefactos publicados (`t_a62cc581`), no re-medirlas. Los `REFERENCES.md`
> se conservan como documentación de candidatos y sin cifras, pero ya nada los parsea
> hacia tablas ni gráficas. El criterio vigente es **9/9 `VALIDA`** (§10.3) y la
> muestra es la estratificada, no `n=20` uniforme.

## 4. Registro de Decisiones de Arquitectura (ADR)

Cada ADR incluye, cuando procede, una línea **Estado (D1, 2026-10-25)** con su
cumplimiento verificado; el cuadro completo está en §9.1.

### ADR-001: v1 sobre ONNX Runtime; Candle y `oar-ocr-vl` se posponen a v2

* **Contexto.** `DECISIONS.md` §1 propone alternar de forma nativa entre ONNX Runtime y Candle (motor pure-Rust de Hugging Face). `oar-ocr` (ONNX Runtime) y `oar-ocr-vl` (Candle, VLM ~0.9B) son **dos crates distintos**, y este último arrastra `candle-core`, `candle-transformers` y kernels CUDA de `candle-flash-attn`.
* **Decisión.** La v1 usa **solo ONNX Runtime**. Candle / `oar-ocr-vl` queda fuera de v1, como hito posterior bajo una feature opcional `vl`.
* **Consecuencias.** Build reproducible en el host actual (`rustc` 1.95.0) sin CUDA Toolkit completo ni `nvcc`, y sin multiplicar el tiempo de compilación. La cobertura de fórmulas se cubre en v1 con UniMERNet/PP-FormulaNet vía ONNX.
* **Coste (respuesta a `DECISIONS.md` §1).** Se pierde la ruta "CPU estricta y portátil sin binarios nativos de ONNX" hasta v2. Mitigación: `oar-ocr` trae `download-binaries`, así que no hace falta toolchain de ONNX en el host.

### ADR-002: Contrato de carga por presets; se descarta `load_model(&mut self, &str)`

* **Contexto.** El diseño inicial definía `load_model(&mut self, model_path: &str) -> Result<(), String>`. En `0.10.1` ningún pipeline se inicializa con un único `.onnx`: PP-OCRv6 necesita 3 artefactos y PP-StructureV3, 9 fuentes (`oar-ocr/src/oarocr/structure.rs:345-361`, cita `A1`); los builders devuelven pipelines inmutables.
* **Decisión.** Se sustituye por presets tipados — `ModelSpec::PpOcrV6(OcrSize)` con `Tiny`/`Small`/`Medium` y `ModelSpec::PpStructureV3` — y el trait del core recibe un `ModelPaths` ya resuelto en lugar de una ruta suelta. La entrada admite ruta (`Path`) y buffer (`&[u8]`).
* **Consecuencias.** La resolución de modelos deja de ser responsabilidad del motor: la hace `storage::config` a partir del preset. `String` como error desaparece en favor de `OcrError`.

### ADR-003: la salida de estructura no se aplana a `OcrResult`

* **Contexto.** El diseño inicial reducía toda inferencia a `recognize(&[u8]) -> OcrResult`, omitiendo `StructureResult` y `to_markdown()`. Eso mutila las tablas HTML, las fórmulas LaTeX y la jerarquía documental de PP-StructureV3.
* **Decisión.** PP-StructureV3 expone `StructureResult` con `to_markdown()` (`oar-ocr-core-0.10.1/src/domain/structure.rs:471`, cita `A1`) y acceso a las regiones.
* **Consecuencias.** La API Python debería devolver dos formas de resultado según el preset; un `OcrResult` plano seguiría disponible para PP-OCRv6.
* **Estado (`D2`, 2026-10-25, commit `b128566`).** **Cumplido.** `StructureResult` existe en `src/core/types.rs:400-409` con `to_markdown()` (`:414-416`) y datos propios (`markdown`, `elements`, `regions`); `OarStructureEngine::recognize` devuelve `OcrOutput::Structure` y no aplana (`src/engines/oar_structure.rs:148-171`; `convert_structure` en `:185-215`). La fachada `VeloceOCR.recognize` entrega `StructureResult` con `pp_structurev3` y `OcrResult` con `pp_ocrv6*` (`src/lib.rs:79-100`). La condición `S1.2` queda **cerrada** por la tarjeta `t_ab6ff8d0`; la alternativa B (degradar el alcance de v1 a texto plano) queda **descartada**.

### ADR-004: `panic = "unwind"` obligatorio en `[profile.release]`

* **Contexto.** La referencia `xycutppy` declara `panic = "abort"` (`xycutppy/Cargo.toml:33`, bajo `[profile.release]` en `:28`) para recortar binario en un algoritmo puramente aritmético. Con PyO3, un `panic` de Rust se captura con `catch_unwind` y se traduce a `PyErr`, preservando el intérprete. Con `panic = "abort"` se suprimen las tablas de unwinding: cualquier `unwrap()`, índice fuera de rango o fallo interno de ONNX Runtime llama a `abort()` y **mata el proceso Python entero**, sin traceback ni `try/except`.
* **Decisión.** `pyocrust` **no** declara `abort`; declara `panic = "unwind"` en `[profile.release]`.
* **Consecuencias.** Binario algo mayor que el de `xycutppy`. Un bug en Rust se convierte en excepción capturable, no en caída del backend.

### ADR-005: sin `impl Drop` manual para VRAM

* **Contexto.** El diseño inicial (y `DECISIONS.md` §3) pedía un `Drop` propio que liberase el contexto de CUDA/TensorRT. `OAROCR` y `OARStructure` encapsulan adaptadores que **son dueños** de las sesiones `ort::Session`; `ort::Session` implementa `Drop` e invoca `OrtReleaseSession`, liberando el Execution Provider por RAII determinista.
* **Decisión.** **No** se implementa `Drop` manual ni se llaman APIs de bajo nivel tipo `cudaDeviceReset()`. La VRAM se gobierna por el ciclo RAII de Rust al desreferenciar la clase en Python.
* **Consecuencias.** Sin riesgo de doble liberación. Riesgos evitados por la decisión: (1) `Use-After-Free` si un hilo conserva una referencia `Arc` mientras otro fuerza la liberación; (2) `cudaDeviceReset()` destruiría el contexto de CUDA de **todo el proceso Python**, rompiendo PyTorch, TensorFlow u otras sesiones ONNX; (3) el *arena allocator* de ONNX Runtime retiene pools por proceso salvo configuración explícita, así que un `Drop` manual sería inútil además de peligroso.
* **Coste (respuesta a `DECISIONS.md` §3).** La liberación "inmediata al reasignar el modelo" deja de estar bajo control del wrapper: depende de que Python suelte el último `Arc`. Mitigación posible sin `Drop` propio: exponer un `close()`/context manager que haga `drop` explícito del handle.
* **Estado (D1, 2026-10-25).** Cumplido en el código (sin `impl Drop`; `Arc` en los motores). **Corrección de este ADR (`S1.7`):** se retiran las referencias a `OrtSessionConfig` (`gpu_memory_budget`, `idle_memory_recovery`) que versiones anteriores de este documento citaban como mitigación: no existen en `oar-ocr` `0.10.1` ni en el código.

### ADR-006: estructura de módulos simplificada, sin placeholders

* **Contexto.** El árbol inicial proponía `src/core/mod.rs` + `src/engines/mod.rs` con factoría y traits dinámicos para encapsular un solo crate, más `src/engines/scipix_engine.rs` como placeholder y `src/core/image_processor.rs` como etapa obligatoria del pipeline.
* **Decisión.** Se elimina `src/engines/scipix_engine.rs` (YAGNI). Se mantiene un único trait del core (`OcrEngineBackend`) con **dos** implementaciones reales (`oar_text`, `oar_structure`) y una factoría por nombre. El código se organiza en `core/`, `storage/` y `engines/`.
* **Consecuencias.** Cada módulo tiene un motivo verificable. Cualquier tercer motor futuro entra como una implementación más del trait, sin cambiar la API.
* **Desviación registrada.** `A1` propuso además fusionar todo en `src/engine.rs` + `src/types.rs`. El orquestador fijó después la división `core/`/`storage/`/`engines/` en las tarjetas `I2`-`I4`, que son el contrato de implementación vigente. Lo sustantivo del dictamen (fuera el placeholder, fuera la factoría abstracta de un solo producto) se cumple igual.
* **Estado (D1, 2026-10-25).** Cumplido: `src/{core,storage,engines}/`, sin `scipix_engine`, un solo trait con dos implementaciones reales. La factoría `engines::mod` ofrece **dos** entradas: `create_backend(name: &str)` y `create_engine(&ModelSpec, &ModelPaths)` (`src/engines/mod.rs:26,39`); la segunda es la que usa `VeloceOCR` (`src/lib.rs:62`).

### ADR-007: política de rutas y descargador HF resiliente; se mantiene `reqwest`

* **Contexto.** El primer dictamen de `A1` pedía eliminar `src/storage/download.rs` y `reqwest` porque `oar-ocr` ya trae `auto-download` con caché `$OAR_HOME`, verificación SHA-256 y escritura atómica (`oar-ocr-core/src/core/download/mod.rs:8-85`, cita `A1`). El dictamen consolidado, contrastado con `DECISIONS.md` §4, mantiene el descargador con otra justificación: `oar-ocr` solo baja de ModelScope, que sufre bloqueos de firewall y latencia alta en entornos corporativos y CI occidentales, y el producto exige Hugging Face.
* **Decisión.** Se **mantiene** `src/storage/download.rs` con `reqwest`, pero **redefinido** y sujeto a contrato (ver §7.3): streaming a fichero temporal, reanudación por `Range`, verificación obligatoria de tamaño y SHA-256, errores tipados por `DownloadError`, y bypass total de red si el modelo ya está en disco. Se conserva `src/storage/config.rs` como resolución pura de rutas con la prioridad estricta de §3.2. Se elimina la descarga ad-hoc previa a la validación.
* **Consecuencias.** La carga de `reqwest` + TLS en el binario es el precio de no depender de ModelScope. Queda prohibido `get(url).unwrap()`.
* **Estado (D1, 2026-10-25).** **Parcial.** El módulo cumple el contrato y está cubierto por tests unitarios, pero **no se conecta a nada**: `fetch` no se llama desde `src/lib.rs` ni desde `src/engines/` (§9.1). El camino de descarga efectivo hoy es el `auto-download` de `oar-ocr`. Condición `S1.4`: el preflight se conectó (`b128566`, §7.2); el descargador sigue sin conectar.
* **Estado (`S2.0`, commit `113a490`).** **Cumplido.** `ensure_models` (`src/storage/models.rs:224-242`) ejecuta preflight, descarga en paralelo lo que falta con `download::fetch` (pool `rayon` de 4 hilos, `DOWNLOAD_THREADS` en `:24`) y re-verifica. Sidecar `<name>.sha256` evita re-hashear en caliente (`src/storage/download.rs:119-148`). `PYOCRUST_OFFLINE=1` falla con error tipado y comando exacto si faltan artefactos (`src/storage/models.rs:231-233`). El descargador propio sirve a HuggingFace (`datalab-to/indra-ocr`); ModelScope lo delega en `oar-ocr`. `S1.4` queda **cerrada** por `S2.0` (tarjeta `t_54cab62c`).

### ADR-008: `rayon` restringido al preprocesamiento de CPU

* **Contexto.** `DECISIONS.md` §2 pide `rayon` en el core para repartir lotes y tiling entre núcleos. `oar-ocr` ya usa `rayon` internamente para las regiones de texto (`rayon = "1.8"` en su `Cargo.toml`, cita `A1`) y ONNX Runtime tiene su propio pool intra-op con SIMD.
* **Decisión.** En `pyocrust`, `rayon` se usa **solo** para preprocesamiento intensivo de CPU (decodificación de imagen, conversión de espacio de color, transformaciones geométricas). El paralelismo inter-página solo se habilita cuando las sesiones están configuradas con `intra_threads = 1` o coordinadas con `OrtGlobalThreadPoolOptions`.
* **Consecuencias.** Se evita la sobre-suscripción de CPU (*thread thrashing*) y el colapso de cachés L1/L2/L3 que produce lanzar lotes concurrentes contra sesiones ORT multihilo. El cuello real (>90-95% del tiempo) es la inferencia tensorial, no el bucle de lotes.
* **Coste (respuesta a `DECISIONS.md` §2).** Sin `rayon` por defecto sobre lotes, el paralelismo inter-página no existe de fábrica. Se añade cuando una medición lo justifique, no antes.
* **Estado (`S2.0`, commit `113a490`).** **Cumplido.** `rayon` se usa en `src/storage/models.rs:13,297` para paralelizar la descarga de artefactos en `ensure_models` (pool de `DOWNLOAD_THREADS` hilos). Sigue sin haber paralelismo inter-página por defecto, que era el motivo del ADR.

### ADR-009: preprocesamiento — escalado nativo por defecto, tiling opt-in

* **Contexto.** `DECISIONS.md` §5 exige `FullPageTiling` con mosaicos de 512x512 y solapamiento de 64px para no truncar fórmulas en las líneas de corte. `A1` lo declaró contraproducente para el pipeline general: trocear rompe la relación de aspecto y la coherencia geométrica que esperan los modelos de layout y tablas, que ya escalan con `limit_side_len`.
* **Decisión.** El pipeline general aplica `ScaleDown` (escalado nativo de `oar-ocr`). `FullPageTiling` se conserva como **función pura opt-in** sobre `image::RgbImage`, sin I/O y sin conocer `oar-ocr`, con solapamiento configurable (64px por defecto) y test propio (tarjeta `I2`).
* **Consecuencias.** Nadie pierde la herramienta; se pierde solo el troceado forzado. Una imagen menor que un mosaico produce un único mosaico, y un solapamiento mayor o igual al tamaño del mosaico debe rechazarse con error, no producir un bucle degenerado (criterio que verifica `C1`).
* **Coste (respuesta a `DECISIONS.md` §5).** El usuario que necesite troceado debe invocarlo explícitamente.
* **Estado (D1, 2026-10-25).** Cumplido **con defecto**: las funciones puras y el rechazo de `overlap >= tile_size` están implementados y testeados, pero el adaptador PyO3 materializa los mosaicos que descarta (`S1.1`, bloqueante; §3.4).

### ADR-010: dependencias y features de `Cargo.toml`

* **Contexto.** Alternativas: reimplementar lo que `oar-ocr` ya hace, o apoyarse en sus features.
* **Decisión.** Dependencias: `pyo3` con `extension-module` y `abi3-py310`; `oar-ocr` `0.10.1` con `auto-download` y `simd`, y `cuda`/`directml` como features opcionales; `image`; `rayon` (ADR-008); `reqwest` con `stream` y TLS (ADR-007); `sha2` para el SHA-256 del descargador. `[profile.release]` con `panic = "unwind"` (ADR-004).
* **Consecuencias.** El binario por defecto es CPU; la GPU se activa compilando con `--features cuda` o `--features directml`. **Armonizado (`t_13a1b2b7`):** la feature *compila* el EP pero **no** lo selecciona; el EP por defecto sigue siendo CPU. La selección es *opt-in* vía `device` (§3.1.4), que no reintroduce la gobernanza de VRAM retirada por `S1.7`.
* **Estado (D1, 2026-10-25).** Cumplido: `Cargo.toml:13-36` declara `pyo3` (`:15`), `oar-ocr` con `simd`+`auto-download` (`:20`), `image` (`:23`), `rayon` (`:26`), `reqwest` con `blocking`/`stream`/`rustls-tls` (`:30`) y `sha2` (`:31`); features `cuda`/`directml` (`:35-36`).

### ADR-011: nomenclatura del paquete

* **Contexto.** `A1` propuso crate `pyocrust_core` y módulo Python `pyocrust._core`. La tarjeta `I1` fijó después `module-name = "pyocrust._pyocrust_core"`, con el paquete Python en `pyocrust/`, compartiendo nombre con el repositorio.
* **Decisión.** Crate Rust: `pyocrust_core`. Módulo nativo: `pyocrust._pyocrust_core`. Paquete Python: `pyocrust/` en la raíz. Licencia única Apache-2.0.
* **Consecuencias.** Que el directorio del repositorio y el paquete importable compartan nombre obliga a que el módulo compilado no se llame igual que el paquete; de ahí el prefijo `_pyocrust_core` en lugar de `_core` (que además chocaría con un futuro paquete `core` de Python). Manda `I1`, por ser la decisión de orquestación más reciente y explícita.
* **Estado (D1, 2026-10-25).** Cumplido: `Cargo.toml:2,10`, `pyproject.toml:23` y `src/lib.rs:106` (`#[pyo3(name = "_pyocrust_core")]`).

### ADR-012: sesiones compartidas con `Arc`, sin `Drop` manual

* **Contexto.** `DECISIONS.md` §3 exige `Arc` para que varios hilos interroguen el mismo modelo en GPU sin duplicar VRAM. Ese mismo documento pedía `Drop` manual, y ambas cosas juntas son incompatibles.
* **Decisión.** Se mantiene el `Arc` para las sesiones (ORT es thread-safe) y se retira el `Drop` manual (ADR-005). El paralelismo inter-página exige `intra_threads = 1` (ADR-008).
* **Consecuencias.** Compartir sesiones sin `Drop` propio es seguro: la liberación ocurre cuando cae el último `Arc`. Se elimina la condición de carrera que describía `A1`.
* **Estado (D1, 2026-10-25).** Cumplido: el pipeline vive en `Arc` (`src/engines/oar_text.rs:50`, `src/engines/oar_structure.rs:32`) y no hay `impl Drop` en el árbol.

### ADR-013: devolver `dict` en las tareas sueltas en vez de 11 `#[pyclass]`

* **Contexto.** `TaskPredictor` expone 11 tareas cuyos resultados en Rust son tipos
  derivados de `oar-ocr` (`TextDetectionResult`, `TableClassificationResult`,
  `FormulaRecognitionResult`, etc.). Esos tipos solo derivan `Debug, Clone` en el
  crate: no implementan `PyClass` ni exponen getters automáticos.
* **Decisión.** Cada tarea convierte su resultado a un `dict` Python con claves
  fijas documentadas en `pyocrust/__init__.pyi`. No se crean 11 wrappers
  manuales de `#[pyclass]`.
* **Consecuencias.** La superficie de API es única y mantenible; el coste es
  perder el autocompletado estático de tipos en el límite Rust-Python. El
  esquema de cada `dict` es la fuente de verdad, no la estructura de Rust.
* **Estado (S2.4, commit `1349296`).** Cumplido: `output_dicts` en
  `src/tasks/mod.rs:249-336` construye los 11 esquemas; `predict_batch` reutiliza
  el mismo predictor y devuelve un `dict` por imagen (`:181-198`).

### ADR-014: el catálogo vive en Rust y lee tamaños de `oar_ocr::download::find`

* **Contexto.** `S3.0` debía documentar el ecosistema de `oar-ocr` dentro del
  propio código, sin duplicar tamaños ni parámetros. El upstream publica
  tamaños en `docs/models.md` y `oar_ocr::download::find`, pero no parámetros
  para los modelos ONNX de PP-OCR/PP-Structure.
* **Decisión.** El catálogo se implementa en Rust (`src/storage/catalog.rs`)
  como tablas estáticas generadas contra `oar_ocr::download::REGISTRY` y
  `find(name)`. `size_bytes` viene de `find(name).map(|e| e.size)`; `params`
  es siempre `None`; los artefactos no registrados (p. ej. los de `indra`,
  que vienen de HuggingFace) tienen `size_bytes: None`.
* **Consecuencias.** Un solo origen de verdad para tamaños; sin drift entre
  documentación y código. Indra permanece con `disk_bytes: None` en
  `pipeline_profiles()` porque al menos uno de sus artefactos no está en el
  registro de `oar-ocr`.
* **Estado (S3.0, commit `113a490`).** Cumplido: `model_catalog()` devuelve
  115 filas (98 registro + 17 Indra) y `pipeline_profiles()` devuelve 16
  perfiles (5 presets + 11 tareas). `size_bytes` coincide 98/98 con
  `oar_ocr::download::find`; Indra conserva `None`.

### ADR-015: el resolvedor es un módulo Python puro, no un subproceso ni un `#[pyclass]`

* **Contexto.** El usuario pidió un "proceso a parte" para elegir pipeline.
  Un subproceso añade latencia y fragilidad para una decisión que cabe en una
  tabla; `#[pyclass]` nuevo habría requerido envolver cada resultado del
  resolvedor en una clase Rust.
* **Decisión.** `pyocrust/resolver.py` implementa `TaskSpec`, `PipelineChoice`
  y `resolve_pipeline` como dataclasses/función Python puras. Los resultados
  cruzan a Python como `dict` (siguiendo ADR-013).
* **Consecuencias.** Sin dependencias nuevas en `hardware.py` (solo stdlib);
  sin subprocesos; sin `#[pyclass]` adicional. El resolvedor delega la
  resolución de rutas en `pyocrust.resolve_models_dir()` para no reimplementar
  la prioridad `OAR_HOME`/`OCR_MODELS_CACHE_DIR`/`~/.oar` (`src/storage/config.rs`).
* **Estado (S3.1, commit `58385e6`).** Cumplido: 49 passed/1 skipped en tests
  focales de S3.

### ADR-016: variables de entorno documentadas (`OAR_HOME`, `PYOCRUST_OFFLINE`, `OAR_VL_*`)

* **Contexto.** `pyocrust` se apoya en variables de entorno para rutas de
  modelos y control de descarga. El upstream `oar-ocr` define además la familia
  `OAR_VL_*` para VLM, que queda fuera de v1 pero que el usuario puede
  encontrar en la documentación de `oar-ocr`.
* **Decisión.** Se documentan `OAR_HOME` (primaria), `OCR_MODELS_CACHE_DIR`,
  `PYOCRUST_OFFLINE`, `CUDA_LAUNCH_BLOCKING`, `RUST_LOG` y la familia
  `OAR_VL_DTYPE`, `OAR_VL_ATTN_FULL_SEQ_THRESHOLD`, `OAR_VL_DISABLE_*`.
  `OAR_HOME` manda sobre el resto en la resolución de rutas; `PYOCRUST_OFFLINE`
  se lee en el resolvedor y en el preflight nativo; `OAR_VL_*` se documenta
  pero no tiene efecto en v1.
* **Consecuencias.** El usuario no busca controles de VLM en v1 y sabe que
  están reservados para v2 (`oar-ocr-vl`, ADR-001). No se añaden lecturas
  implícitas de `OAR_VL_*` en el código de v1.
* **Estado (S3.0-S3.1, commits `113a490`/`58385e6`).** Cumplido: las variables
  aparecen en `model_catalog().env_vars`, en `resolver.py` y en `DESIGN.md`.

### ADR-017: clasificación de licencias de los pesos y flags de política (default-deny)

* **Contexto.** La licencia del código (`Apache-2.0`) no cubre los pesos: cada
  artefacto trae la suya. El usuario necesita saber si un modelo es apto para
  uso comercial antes de descargarlo o ejecutarlo, y poder declarar su
  intención de uso y su aceptación de atribución.
* **Decisión.**
  1. `src/storage/license.rs` clasifica cada artefacto contra el texto
     primario (nunca contra un resumen): Paddle/PP = `Apache-2.0`; `indra` =
     `OpenRAIL-M-Mod` (comercial no libre, atribución §7); lo no reconocido =
     `Unknown`, **restringido por defecto**.
  2. La clasificación es **datos** en el catálogo: `model_catalog()` y
     `pipeline_profiles()` exponen `license`, `license_commercial_use`,
     `license_acknowledge`, `license_restricted`, `license_notes`,
     `license_url` (URL fijada a la revisión, nunca `main`).
  3. La agregación por pipeline es la **más restrictiva**: `commercial_use`
     es AND, `acknowledge` es OR, y en empate gana la más restrictiva.
  4. Flags de usuario en `VeloceOCR`, `TaskPredictor` y `TaskSpec`:
     `license_commercial_use` (intención comercial) y `license_acknowledge`
     (aceptación de atribución). **Polaridad declarativa**: son lo que declara
     el usuario, no lo que permite el modelo.
  5. El bloqueo ocurre en el constructor, **antes** de `ensure_models`, la red
     y el disco. Las condiciones son **acumulativas** (`AND`), no alternativas.
  6. Con `models`/`custom_path` explícitos la procedencia no es verificable: el
     getter expone `Unknown`, no la licencia del catálogo.
* **Consecuencias.** Un usuario comercial no puede cargar `indra` por defecto;
  para uso no comercial debe además aceptar la atribución. Un artefacto
  desconocido nunca se trata como permitido.
* **Estado (`L1`-`L5`, 2026-11-06).** Cumplido: `cargo test` 64/0,
  `pytest tests/` 157 passed/1 skipped; sign-off `L5` **APROBADO**
  (`DICTAMEN_LICENSES.md`).

## 5. Riesgos Conocidos

| Id | Riesgo | Impacto | Mitigación | Estado (D1) |
| :--- | :--- | :--- | :--- | :--- |
| R1 | La firma exacta de `OARStructureBuilder` en `0.10.1` difiere de la documentada (docstring antiguo con firmas de dos parámetros frente a métodos específicos) | `src/engines/oar_structure.rs` no compila | Contrastar la API real del crate antes de escribir el adaptador; documentar la desviación | **Cerrado.** API real contrastada y usada (`src/engines/oar_structure.rs:130-137`, §3.1) |
| R2 | ModelScope inalcanzable (firewall corporativo, CI) | Sin modelos no hay inferencia | Descargador HF de ADR-007; bypass de red si el modelo ya está en disco | **Cerrado (`S2.0`).** El descargador HF está conectado vía `ensure_models` (`src/storage/models.rs:224-242`); no hay petición de red si el artefacto ya está en disco |
| R3 | Peso de PP-StructureV3 (11 artefactos) y VRAM en GPU de 16 GB | Fallo de carga o OOM | Caché en `$OAR_HOME`; presets `Tiny`/`Small` para texto | **Abierto** para VRAM en GPU (no validada; tarjeta `t_065205ea`). El peso ya está resuelto: los 11 artefactos están en disco y el preset carga |
| R4 | `maturin` no está instalado en el intérprete activo | No se puede construir el paquete | `pip install maturin` antes de `maturin develop` | **Cerrado.** `maturin` instalado en `.venv`; `maturin develop` ejecutado |
| R5 | Acoplamiento circular entre `config.rs` (rutas) y `download.rs` (descarga) | Módulos difíciles de testear | `download.rs` recibe rutas ya resueltas; no consulta el entorno | Cumplido: `fetch(url, dest, sha256_hex)` no lee variables de entorno |
| R6 | `pyapi::full_page_tiling` materializa y descarta los mosaicos | OOM con `overlap` alto | Reducir el adaptador a puro cálculo de geometría | **Cerrado (`4502d1e`).** El adaptador calcula geometría sin materializar (`src/core/image_processor.rs:150-185`) |
| R7 | `OAR_HOME` relativa no se reexporta absoluta | La autodescarga de `oar-ocr` falla | Rechazar la relativa o reexportar la normalizada | **Cerrado (`c30a3a9`):** se reexporta absoluta (`src/storage/config.rs:115-126,144-155`) |

## 6. Estado Actual

Actualizado en `D1` (2026-10-25), reconciliado en `D3` (2026-11-06), auditado en `D4` (2026-11-08) leyendo el árbol real y el board `pyocrust`, y **corregido en `D5` (2026-11-09)** tras la campaña definitiva (§10).

| Elemento | Estado | Evidencia |
| :--- | :--- | :--- |
| `DESIGN.md` | Reconciliado en `D1`; estado final en §10 (`D5`) | Este documento |
| `PLANNING.md` | Reconciliado en `D1`; actualización `D5` en §0 | Mapea cada tarea a su tarjeta con estado real |
| Crate `pyocrust_core` | Existe y compila | `Cargo.toml`, `src/**`; `cargo test --lib` = **67/0** (`t_e560fff3`, 2026-11-09) |
| Paquete `pyocrust` | Existe e importa | `pyocrust/__init__.py`; `maturin develop` ejecutado (`pyocrust/_pyocrust_core.pyd`) |
| Suite de integración (Python) | **162 passed, 1 skipped, 0 failed** | `pytest tests/ -q` (2026-11-09, `t_052d7c9c`); el `skip` es el TLS del CDN de HuggingFace, no código (§10.1) |
| Sign-off `S1` | **APROBADO** (relevado por `t_e560fff3`, 2026-11-09) | §10.2; las **7** condiciones `S1.1`-`S1.7` verificadas línea a línea |
| ADR cumplidos | **17 de 17** | §9.1 |
| Benchmarks (9 features) | **Campaña medida y válida** (2026-11-09): CPU `t_53080e14` + CUDA `t_8cd2897e` | `benchmarks/validez_medicion.py` → **9/9 VALIDA**; §3.5 y §10.3 |

Lo que este documento **no** sabe:

* el contenido del árbol de `oar-ocr` `0.10.1` no está descargado en el host: las citas internas de §3 y §4 atribuidas a `A1` siguen siendo de segunda mano;
* el **benchmark** existe (9 features, CPU+CUDA; §3.5 y §10.3): el rendimiento medido no cubre todas las variantes de pipeline, y la calidad de fórmula en GPU queda `N/A` para `pyocrust_formula`/`pyocrust_formulanet` (§10.5);
* la verificación de las condiciones de §9.2 está rehecha por `t_e560fff3` (2026-11-09): las siete están **cerradas** y el sign-off global está **APROBADO** (§10.2). Lo que sigue abierto es el trabajo de las tarjetas de §10.6, no el sign-off.

## 7. Resolución de Rutas, Almacenamiento y Descargador Hugging Face

### 7.1 `src/storage/config.rs` — resolución de rutas

Orden estricto de §3.2: `custom_path` → `OAR_HOME` → `OCR_MODELS_CACHE_DIR` → `~/.oar`. Devuelve rutas absolutas normalizadas y no abre conexiones de red. Casos resueltos sin pánico: directorio inexistente, falta de permisos de lectura, tilde `~` y rutas relativas (normalizadas contra el directorio de trabajo actual). Implementado en `src/storage/config.rs:103-133`.

> **Desviación (D1), corregida (`D2`, `c30a3a9`).** Una `OAR_HOME` **relativa** se
> normaliza contra el `cwd` y, si no era absoluta, se reexporta ya normalizada con
> `env::set_var` (`src/storage/config.rs:115-126,144-155`), así que la autodescarga
> interna de `oar-ocr` —que lee `OAR_HOME` por su cuenta— la resuelve bien.
> Condición `S1.5` **cerrada**.

### 7.2 `src/storage/models.rs` — preflight

Dado un `ModelSpec`, devuelve la lista de ficheros esperados y cuáles faltan en disco (`PreflightReport`, `src/storage/models.rs:61-87`). Es la pieza que permite decir al usuario, antes de cargar nada, qué modelos necesita; no descarga ni toca la red.

> **Desviación (`D1`), corregida (`D2`, `b128566`) y ampliada (`S2.0`).** El preflight está
> implementado y **conectado**: `VeloceOCR::new` llama a `ensure_models`
> (`src/lib.rs:100`), que hace preflight → descarga en paralelo lo que falte → re-preflight
> (`src/storage/models.rs:224-242`). Con `PYOCRUST_OFFLINE` y artefactos ausentes el usuario
> recibe `OfflineMissingArtifacts` con el comando exacto. `S1.4` queda **cerrada**.

### 7.3 `src/storage/download.rs` — descargador resiliente (ADR-007)

Requisitos obligatorios y testeables, todos implementados:

| # | Requisito | Detalle | Verificado |
| :--- | :--- | :--- | :--- |
| 1 | Streaming a temporal | Escritura en `.<filename>.<pid>.part` y renombrado atómico (`std::fs::rename`) solo tras validar | `src/storage/download.rs:86-93,193` |
| 2 | Reanudación | Cabecera `Range: bytes=offset-` ante corte de red; reinicio si el servidor responde 200 en vez de 206 | `:130-142` |
| 3 | Integridad | Verificación obligatoria de `Content-Length` y de SHA-256 antes de dar la descarga por buena | `:171-190` |
| 4 | Errores tipados | `enum DownloadError { Http(reqwest::Error), Io(std::io::Error), ChecksumMismatch { expected, actual }, Incomplete { expected, actual } }`. Sin `unwrap()` | `:19-28` |
| 5 | Bypass offline | Si el fichero existe en la ruta resuelta y su SHA-256 coincide, no se hace ninguna petición de red | `:102-109` |

Interfaz implementada: `fn fetch(url: &str, dest: &Path, sha256_hex: &str) -> Result<(), DownloadError>` (`src/storage/download.rs:99`). **Decisión de `I3` (recogida en `D1`):** se usa el cliente **síncrono** `reqwest::blocking` con `timeout` de 1800 s y `connect_timeout` de 30 s (`:125-128`); no se monta un runtime asíncrono propio.

> **Desviación (`D1`), cerrada en `S2.0`.** El módulo **sí** se ejecuta: `ensure_models`
> llama a `fetch` para cada artefacto obligatorio que falte (`src/storage/models.rs:224-242`),
> así que el bypass offline y la verificación de `Content-Length`/SHA-256 protegen descargas
> reales para los artefactos servidos por HuggingFace. ADR-007 **cumplido**.
>
> **Ampliado y cerrado (2026-11-08, tarjeta `t_457cd882`).** El preflight exige ahora
> **tamaño y SHA-256** para todo preset, ModelScope incluido: `hash_matches`
> (`src/storage/models.rs:211-221`) consulta primero el sidecar `.<name>.sha256` —el que deja
> `download::fetch` tras verificar— y solo hashea si falta, así que el camino caliente no
> re-hashea (medido: 4 ms con sidecar frente a 195 ms por 6,4 MB sin él). Un artefacto
> alterado que conserve el tamaño se marca `present=false` y dispara la descarga verificadora.
> Verificado: 67 tests Rust, 161 Python.
>
> **Límite restante.** Los 9 artefactos de `indra` en disco **no** tienen sidecar, así que se
> hashean en cada preflight (~28 MB, duplicados por las dos enumeraciones: `presets['indra']`
> y `['indra']`); `models_status()` tarda ≈1,2 s en build debug. Es **previo** a este cambio
> —el preflight ya hasheaba Indra— y no una regresión.

## 8. Notas de Evolución

* **v2 — Candle y `oar-ocr-vl`.** Entrarán bajo una feature opcional `vl`, nunca por defecto: requieren CUDA Toolkit completo y kernels de Flash Attention, que multiplican el tiempo de compilación (ADR-001).
* **v2 — paralelismo inter-página.** Solo si una medición lo justifica, y siempre con `intra_threads = 1` para no pelearse con el pool intra-op de ORT (ADR-008).
* **Features de aceleración adicionales.** `tensorrt`, `openvino`, `coreml` y `webgpu` existen en `oar-ocr`; se añaden cuando haya un objetivo de despliegue que los pida, no antes.
* **Gestión explícita de VRAM.** Si la liberación por RAII resulta insuficiente en producción, el camino es un `close()`/context manager que suelte el último `Arc`, **no** un `Drop` manual con llamadas a CUDA (ADR-005).
* **Cierre de las condiciones de `S1`.** Las siete están **cerradas** (`S1.1` `4502d1e`; `S1.2` `b128566`; `S1.3` y `S1.5` `c30a3a9`; `S1.4` por `S2.0`; `S1.6` `D3`, re-verificada en `D4`; `S1.7` `D1`). El **sign-off global** quedó **RECHAZADO** y fue reelevado por `t_e560fff3` (2026-11-09): veredicto **APROBADO** (§10.2). Lo que sigue abierto es el trabajo de las tarjetas de §10.6, no el sign-off.

## 9. Reconciliación `D1` (2026-10-25)

Verificado leyendo el árbol real de `src/` (no las intenciones).

### 9.1 Estado de cumplimiento de los ADR

| ADR | Asunto | Estado | Evidencia |
| :--- | :--- | :--- | :--- |
| ADR-001 | v1 solo ONNX Runtime | Cumplido | `Cargo.toml:20`; no hay `candle` en el árbol |
| ADR-002 | Contrato por presets | Cumplido | `src/core/mod.rs:33-45`; `ModelPaths` en `src/core/types.rs:144-156` |
| ADR-003 | Estructura no aplanada | **Cumplido** | `OcrOutput::Structure` en `src/engines/oar_structure.rs:148-171`; `StructureResult` con `to_markdown()` en `src/core/types.rs:400-409` (commit `b128566`) |
| ADR-004 | `panic = "unwind"` | Cumplido | `Cargo.toml:45` |
| ADR-005 | Sin `Drop` manual | Cumplido | `Arc` en los motores; sin `impl Drop`; doc de VRAM corregida (`S1.7`) |
| ADR-006 | Módulos sin placeholders | Cumplido | `src/{core,storage,engines}/`; sin `scipix_engine`; un trait, dos implementaciones |
| ADR-007 | Descargador HF resiliente | **Cumplido** | `src/storage/download.rs:99-196`; conectado en `ensure_models` (`src/storage/models.rs:224-242`, `S2.0`) |
| ADR-008 | `rayon` solo en preprocesamiento CPU | **Cumplido** | `src/storage/models.rs:13,297` (pool de 4 hilos en `ensure_models`, `S2.0`) |
| ADR-009 | Tiling opt-in | **Cumplido** | `src/core/image_processor.rs:150-185`; `S1.1` cerrada en `4502d1e` |
| ADR-010 | Dependencias y features | Cumplido | `Cargo.toml:13-36,45` |
| ADR-011 | Nomenclatura | Cumplido | `pyproject.toml:23`; `src/lib.rs:106` |
| ADR-012 | Sesiones con `Arc`, sin `Drop` | Cumplido | `src/engines/oar_text.rs:50`; `src/engines/oar_structure.rs:32` ||
| ADR-013 | `dict` en tareas sueltas, no 11 `#[pyclass]` | Cumplido | `src/tasks/mod.rs` (devolución como `dict`); §3.1.4 |
| ADR-014 | Catálogo en Rust lee tamaños de `find()` | Cumplido | `src/storage/catalog.rs:58-70`; 98/98 `size_bytes` exactos; Indra `None` ||
| ADR-015 | Resolvedor como módulo Python puro | Cumplido | `pyocrust/resolver.py:1-87`; `TaskSpec`/`PipelineChoice`/`resolve_pipeline` ||
| ADR-016 | Variables de entorno documentadas | Cumplido | `catalog.rs:37` (`ENV`), `resolver.py:83` (`PYOCRUST_OFFLINE`), `README.md` Variables de entorno ||
| ADR-017 | Licencias de los pesos + flags de política | **Cumplido** | `src/storage/license.rs`; `cargo test` 64/0; `pytest tests/` 157 passed/1 skipped; sign-off `L5` **APROBADO** |

### 9.2 Condiciones abiertas del sign-off `S1` (tarjeta `t_d005409b`, RECHAZADO → **APROBADO**)

`S1` cerró como **RECHAZADO** con 7 condiciones (comentario del 2026-10-25). Estado a día de `D3` (2026-11-06): **las siete cerradas**. El re-sign-off `t_e560fff3` (2026-11-09) las verificó línea a línea contra el árbol y emitió **APROBADO** (§10.2).

| Id | Condición | Gravedad | Estado | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| S1.1 | `pyapi::full_page_tiling` materializa los mosaicos y los descarta (OOM con `overlap` alto) | Bloqueante | **Cerrada (`4502d1e`)** | `src/core/image_processor.rs:150-185` (cajas sin materializar) |
| S1.2 | `StructureResult` (ADR-003) no existía ni cruzaba a Python | Bloqueante | **Cerrada (`D2`, `b128566`)** | `src/core/types.rs:400-409`; `src/engines/oar_structure.rs:148-171` |
| S1.3 | `PyOcrValueError`/`PyOcrRuntimeError` no heredan de `PyOcrError` | Mayor | **Cerrada (`c30a3a9`)** | `src/core/error.rs:182-184` (base `PyOcrError`) |
| S1.4 | `VeloceOCR::new` no ejecuta el preflight (ni el descargador) | Mayor | **Cerrada (`S2.0`)** | `src/storage/models.rs:224-242` (`ensure_models` conecta el descargador) |
| S1.5 | `OAR_HOME` relativa rompe la autodescarga de `oar-ocr` | Mayor | **Cerrada (`c30a3a9`)** | `src/storage/config.rs:115-126,144-155` |
| S1.6 | `VeloceOCR::new` retiene el GIL durante la carga | Menor | **Cerrada (`D3`)**, re-verificada en `D4` | `src/lib.rs:100,102` (`py.detach` en `ensure_models` y en `create_engine`) |
| S1.7 | Retirar de `DESIGN.md` las capacidades de VRAM inexistentes | Menor | **Hecho en `D1`** | §3.3 y ADR-005 corregidos |

`S1.2` la cerró el código de `t_ab6ff8d0` (`b128566`) y `S1.3`/`S1.5`, el de `c30a3a9`. `S1.1` la cerró `4502d1e` y `S1.4`, `S2.0` (`t_54cab62c`). `S1.6` la cerró `D3` (`py.detach` en `src/lib.rs:100,102`) y `D4` (2026-11-08) la re-verificó: **no queda ninguna condición abierta**.

> **Cifras de línea corregidas en `D5`.** Las citas de esta tabla se verificaron una
> por una contra el árbol: `src/core/error.rs:147-149` → **182-184** (las tres
> `create_exception!`); `src/storage/models.rs:224-242` → **226-248** (`ensure_models`);
> `src/storage/config.rs:115-126,144-155` → **103-133** (`resolve_models_dir_from`) y
> **145-158** (`resolve_models_dir`); `src/core/types.rs:400-409` → **419-433**
> (`StructureResult`); `src/engines/oar_structure.rs:148-171` → **181-216**
> (`recognize` + `convert_structure`). La sustancia no cambiaba: sólo el número de
> línea, que había quedado desplazado por las ediciones posteriores.

> **Nota de `D2` sobre las demás condiciones.** Mientras `D2` corría aterrizó el commit `c30a3a9`
> (`S1.3`-`S1.6`), que cierra la jerarquía de excepciones (`src/core/error.rs:147-149`) y la
> reexportación absoluta de `OAR_HOME` (`src/storage/config.rs:115-126,144-155`); el mismo árbol trae ya
> el preflight conectado (`src/lib.rs:60`, de `b128566`) y el GIL liberado al crear el motor
> (`src/lib.rs:62`). Ambas condiciones se cerraron después: `S1.4` con `S2.0` y `S1.6` con `D3`;
> la auditoría `D4` (2026-11-08) lo confirma en `src/lib.rs:100,102`.
>
> **Las citas de línea de esta nota son las históricas de `D2`** (2026-10-25), no las
> vigentes: `D5` las corrigió en la tabla de arriba. Se conservan para no reescribir
> el rastro de `D2`.

### 9.3 Divergencias documentales cerradas en `D1`

| Punto | Decía el documento | Dice el código | Resolución |
| :--- | :--- | :--- | :--- |
| Artefactos de PP-StructureV3 | §3.1 "8 ficheros" listando 9 | 9 fuentes (8 `.onnx` + `table_structure_dict_ch.txt` + diccionario OCR) | Manda el crate; §3.1 corregido |
| `ModelPaths` | §2 lo listaba como "enum" | es una `struct` (`src/core/types.rs:140`) | §2 corregido |
| Pyclasses del core | §2 nombraba `StructureResult` | `BoundingBox`, `TextRegion`, `OcrResult`, `LayoutRegion`, `StructureResult` y el enum Rust `OcrOutput` (`src/core/types.rs:30-34,353,400,438`) | §2 corregido en `D1`; `StructureResult` **reintroducido** en `b128566` (`D2`) y vuelve al árbol de §2 |
| Liberación del GIL | §3.3 `py.allow_threads()` | `py.detach()` (PyO3 0.30) | §3.3 corregido |
| Cliente de descarga | §7.3 "la decisión la fija `I3`" | `reqwest::blocking`, `timeout` 1800 s (`src/storage/download.rs:125-128`) | §7.3 actualizado |
| Firma de `OARStructureBuilder` | R1 abierto, firmas de 2 parámetros | `OARStructureBuilder::new(layout)` + métodos específicos | §3.1 y §5: R1 cerrado |
| Ficheros de `tests/` | §2 enumeraba 3 | hay además `conftest.py` y `data/sample_text.png` | §2 ampliado |
| Estado del proyecto | §1.1/§6 sin sign-off | `S1` cerró **RECHAZADO** y fue reelevado: **APROBADO** (`t_e560fff3`, 2026-11-09) | §6, §9.2 y §10.2 |

## 10. Reconciliación `D5` — estado final tras la campaña (2026-11-09)

Bloque **datado y nuevo**: no reescribe §9 ni las actualizaciones previas. Lo que
hace es (a) añadir el estado que las supera y (b) corregir *in situ* las tablas de
estado actual que ya no describen el árbol. Fuentes: `git log` (`7e69290`,
`9a824cf`, `7cfc1e5`, `6347910`, `4015fe1`, `ca48b32`), el árbol leído con
`read_file`, y los `summary.json` de las runs vigentes.

### 10.1 Cifras de suites (verificadas por los workers, no re-ejecutadas aquí)

| Suite | Recuento | Quién lo midió | Tarjeta |
| :--- | :--- | :--- | :--- |
| `cargo test --lib` | **67 passed, 0 failed** | re-sign-off `S1` | `t_e560fff3` |
| `pytest tests/` (`.venv` del repo) | **161 passed, 0 failed** | re-sign-off `S1` | `t_e560fff3` |
| `pytest tests/` tras la campaña CPU | **162 passed, 1 skipped** | cierre de `S1.4` (test HF fría) | `t_052d7c9c` |
| `pytest benchmarks/tests` | **175 passed, 2 skipped** | cierre de la campaña CUDA | `t_8cd2897e` |

El `skip` de `t_052d7c9c` es **entorno, no código**: el TLS de `reqwest`+`rustls`
no completa la revocación del certificado del CDN de HuggingFace
(`us.aws.cdn.hf.co`, `CRYPT_E_NO_REVOCATION_CHECK`); el test queda `skip` con el
error exacto, nunca verde. El artefacto sí es bajable por CDN con
`curl --ssl-no-revoke` (389 948 B, SHA-256 `f2bd4cba…`), luego el test pasaría en
un host sin ese bloqueo.

### 10.2 Sign-off global `S1`: **APROBADO** (2026-11-09)

`t_e560fff3` emitió **APROBADO** verificando las siete condiciones `S1.1`-`S1.7`
línea a línea contra el árbol real (no contra la prosa de los documentos):
`S1.1` `src/core/image_processor.rs:150-189`, `S1.2` `src/core/types.rs:419` y
`src/engines/oar_structure.rs:181`, `S1.3` `src/core/error.rs:182-184`,
`S1.4` `src/storage/models.rs:226`, `S1.5` `src/storage/config.rs:145`,
`S1.6` `src/lib.rs:100,102`, `S1.7` `DESIGN.md` §3.3 y ADR-005.

**Este documento deja de decir «`S1` RECHAZADO y sin reelevar»**: el re-sign-off lo
relevó y lo aprobó. Las siete condiciones siguen cerradas y ahora además hay
veredicto favorable. Lo que **no** aprueba `S1` es la calidad de los benchmarks ni
el cierre de las tarjetas de trabajo abierto de §10.6.

### 10.3 Campaña vigente y validez de medición (2026-11-09)

Reproducida aquí con `benchmarks/validez_medicion.py` (sonda sin red, **no** es una
corrida de banco): **9/9 `VALIDA`**, `RC=0`.

| feature | run CPU | n | motores | run GPU | n | motores | estado |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- |
| `text` | `2026-11-06_22-46-46` | 20 | 3 | `2026-11-09_16-19-13` | 20 | 3 | VALIDA |
| `formula` | `2026-11-09_14-13-57` | 10 | 7 | `2026-11-09_17-54-04` | 10 | 5 | VALIDA |
| `layout` | `2026-11-09_14-32-35` | 40 | 42 | `2026-11-09_16-25-15` | 40 | 41 | VALIDA |
| `orientation` | `2026-11-08_19-54-17` | 20 | 3 | `2026-11-09_16-29-18` | 20 | 1 | VALIDA |
| `rectification` | `2026-11-08_19-53-54` | 20 | 3 | `2026-11-09_16-29-33` | 20 | 1 | VALIDA |
| `text_line` | `2026-11-06_23-57-00` | 20 | 2 | `2026-11-09_16-29-48` | 20 | 1 | VALIDA |
| `seal` | `2026-11-08_15-28-48` | 20 | 2 | `2026-11-09_16-29-57` | 20 | 1 | VALIDA |
| `table` | `2026-11-09_14-22-58` | 8 | 5 | `2026-11-09_16-30-07` | 8 | 2 | VALIDA |
| `full_page` | `2026-11-09_17-15-04` | 6 | 4 | `2026-11-09_16-30-33` | 6 | 2 | VALIDA |

**La muestra no es `n=20` uniforme**: `formula` 10, `table` 8, `full_page` 6,
`layout` 40; el resto 20. La regla 1 de §3.5 («`n` uniforme por feature») se cumple
**dentro** de cada feature; la regla que fija `n=20` quedó superada por el muestreo
estratificado (`ca48b32`, `t_a1e6dc20`).

**EP de la pata GPU: CUDA 13** (`--features cuda`, ORT 1.31 parcheado en
`vendor/ort-sys`), no DirectML. Binario de la campaña: `pyocrust/_pyocrust_core.pyd`
sha256 `9acaf1878d27013c32be2a66d8631affcca700d488d0071a3a219e707e77c937`
(37 456 896 B), verificado aquí con `sha256sum`. `available_providers()` →
`['cuda']`. Las 1858 filas GPU `ok` declaran `provider_effective='cuda'`; 0
incoherencias. **Ese binario se reconstruyó tras la campaña** con el fix de §10.5
(commit `65326b8`): el `.pyd` actual ya no tiene ese hash (§10.9). Las cifras de la
pata GPU son las de la run medida con el binario de campaña, no las del rebuild.

### 10.4 Defectos reales encontrados y corregidos en la campaña

| Defecto | Causa | Corrección | Tarjeta |
| :--- | :--- | :--- | :--- |
| `pp_structurev3_api` segfaulteaba (exit 139) o colgaba el banco `full_page` | PaddleOCR PP-StructureV3 en **proceso**; nunca produjo fila pese a estar en `DEFAULT_BACKENDS` | Aislado en **subproceso con timeout 900 s** (`benchmarks/common/runner.py:1009`). Smoke real 2026-11-09 (3 páginas, rc=0, 3/3 `ok`, Markdown de 600+ chars) → **devuelto al `DEFAULT_BACKENDS`** (`benchmarks/features/full_page/bank.py:86`); es CPU-only | `t_53080e14`, `t_4298724b`, `t_838df3ad` |
| Colisión cuDNN: `import torch` moría (`WinError 127`, `cudnn_cnn64_9.dll`) y tiraba `easyocr`/`paddle_latex_ocr`/los 40 YOLO | El provider CUDA de ORT resolvía cudnn del Toolkit del `PATH` antes que la de `torch` | `preload_gpu_runtime()` precarga `torch` **antes** del provider (`benchmarks/common/runner.py:309`) | `t_8cd2897e` |
| `SCOREBOARD.md` no se regeneraba | `scoreboard._panel` formateaba `quality` sin guardar `None` | None-guard (`benchmarks/features/scoreboard.py:113-128`) | `t_8cd2897e` |
| `formula` muestreaba 80-100 % `equation_hard` | `_odb_det_groups(cap)` cortaba las primeras `limit` páginas del orden estratificado antes del reparto por página | `balance_keys=("data_source","layout","subset")` re-estratifica el pool elegible (`benchmarks/common/datasets.py:348-376`); asertado por `test_ninguna_feature_omnidocbench_muestrea_en_un_solo_estrato` | `t_a1e6dc20` |

### 10.5 Hallazgo abierto (fuera de criterio, con tarjeta)

Bajo CUDA, `pyocrust_formula` y `pyocrust_formulanet` emiten **LaTeX aislado
vacío** en las 10 muestras: su `latex_sim`/`latex_exact` queda `""` (no evaluada)
y su `cer` sale 1.0. No rompe `n` ni el EP — la fila es `ok` con
`provider_effective='cuda'` — pero la **calidad** de fórmula en GPU sale `N/A`
donde en CPU sí la hay (0.497 / 0.499). **No se presenta como cerrado.**

**Causa raíz aislada (2026-11-09, `t_e1630cbe` → `t_d80c2e58`).** No es el banco
ni el *scorer*: es el **reuso de sesión por sesión** de PP-FormulaNet bajo CUDA.
La 1ª inferencia de un motor recién construido da el LaTeX correcto (idéntico a
CPU) y **todas las siguientes salen vacías**, incluso repitiendo la misma imagen.
El `--warmup 1` del banco consume esa única inferencia buena, de ahí el 10/10.
El mecanismo es el workaround `CUDA_LAUNCH_BLOCKING=1` del propio `oar-ocr-core`
(onnxruntime#4829), que llega **tarde**: `resolve_auto()` sondea el EP CUDA e
inicializa el contexto antes de que el builder lo aplique.

**Estado del fix (2026-11-09, `t_d80c2e58` — `done` con verificación):** el commit
`65326b8` adelanta `ensure_cuda_launch_blocking()` en `available_providers()` y
`resolve_device()` (`src/core/device.rs`), con su test de regresión
`tests/test_recognize.py::test_cuda_pp_formulanet_da_el_mismo_latex_no_vacio_en_inferencias_seguidas`.
Verificado por el coder con el binario reconstruido (`f4c2a201…`): sonda aislada
`[90,90,90]` (antes `[90,0,0]`), `pytest tests/test_recognize.py` **12 passed**
(regresión ROJA→VERDE), banco `--limit 10 --device gpu` con CER 1.4669/1.1641
(antes 1.0000 exacto) y `pyocrust_formulanet` reproduciendo 10/10 el LaTeX de CPU,
y `cargo test -j 2` **67 passed**.

**Lo que sigue abierto:** las **filas GPU publicadas** de `formula`
(`2026-11-09_16-22-29`) son del binario defectuoso, no del arreglado. La
re-medición de la pata GPU de `formula` es la tarjeta `t_5c3b7dfe` (`running`). El
defecto de código está corregido y verificado; las cifras publicadas **no**.

### 10.6 Tarjetas de trabajo abierto al cerrar `D5`

Estado leído del board `pyocrust` (no de la prosa de este documento) el
2026-11-09: **154 `done`, 5 `archived`, 2 `running`, 1 `todo`**.

| Tarjeta | Título | Estado real | Motivo |
| :--- | :--- | :--- | :--- |
| `t_5c3b7dfe` | Re-medir la pata GPU de `formula` tras el fix de `CUDA_LAUNCH_BLOCKING` | `running` | Las filas GPU publicadas de `formula` son del binario defectuoso; el fix está verificado pero las cifras no están re-medidas |
| `t_dc3aaced` | Reconciliar `DESIGN.md`/`PLANNING.md`/`README` con el estado final | `running` | Esta tarjeta |
| `t_b7f13064` | Desglose por tipología de página (digital/escaneada/manuscrita) en los informes | `todo` | Trabajo nuevo creado después de este bloque; no forma parte de `D5` |

Cerradas **después** de que este bloque se escribiera (constan `done` en el board,
no se copia su estado de memoria): `t_c9f93b67` (docs GPU/CRITERIO), `t_e1630cbe`
(investigación del LaTeX vacío), `t_d80c2e58` (fix verificado, §10.5) y `t_838df3ad`
(campaña `full_page` n=6 con 4 motores + cadena de informes, §10.3).

Archivadas (`archived`, `needs_input`): `t_b304e350`, `t_a2b49874`, `t_64abfa16`,
`t_62aef58e`, `t_d6479bc0`. No están cerradas: quedan fuera de alcance de `D5`.

### 10.7 Divergencias con la documentación vigente (corregidas *in situ*)

| Dónde | Decía | Estado real (`D5`) | Resolución |
| :--- | :--- | :--- | :--- |
| §6, §9.2, §8, cabecera | «`S1` **RECHAZADO** y sin reelevar» | **APROBADO** (`t_e560fff3`, 2026-11-09) | §6 y §9.2 corregidos en este bloque |
| §6 | «Suite de integración **160 passed, 0 skipped**» | **162 passed, 1 skipped** (`t_052d7c9c`) | §6 corregido; el `skip` es entorno TLS, no código |
| §6 | «`cargo test --lib` = **65/0**» | **67/0** (`t_e560fff3`) | §6 corregido |
| §3.5 regla 1 | «Todas las filas salen del mismo barrido (`--limit 20`)» | Muestra estratificada: `formula` 10, `table` 8, `full_page` 6, `layout` 40; resto 20 | §3.5 matizado: uniforme **dentro** de cada feature |
| §3.5 | «Campaña `t_347622f2`/…» | Campaña definitiva `t_53080e14` (CPU) + `t_8cd2897e` (CUDA) | §3.5 actualizado |
| §3.1.1 | «Contrato actual de Indra (`S2.2`, **parcial**)» | `S2.2` **Hecho** (`t_027743e2`); 9/9 artefactos en disco y `VeloceOCR('indra')` reconoce | §3.1.1 reetiquetado; queda el límite TLS documentado |
| §3.4 | «Defecto abierto (`D1`, condición `S1.1`)… Pendiente de corrección» | **Cerrado** en `4502d1e` (§9.2) | §3.4 corregido |
| §3.2 | «Estado real (`D1`): solo el camino (1) está activo… ADR-007 **parcial**» | Camino (2) conectado en `ensure_models` (`src/storage/models.rs:226`) | §3.2 corregido |
| §6, §9.1 | «ADR-007 **parcial**» | **Cumplido** (`S2.0`) | §9.1 ya lo decía; §6 alineado |
| §2 | Árbol sin `pyocrust/gpu.py`, `tests/test_gpu.py`, `tests/test_providers.py`, `tests/test_models.py`, `tests/test_catalog.py`, `tests/test_license.py`, `tests/test_hardware.py`, `tests/test_resolver.py`, `tests/test_tasks.py` | Existen | §2 ampliado |
| §2 | `tests/data/` con un solo PNG | `sample_text.png`, `sample_formula.png`, `indra_math.png` | §2 corregido |
| §10.3 (esta revisión) | «Binario medido … verificado aquí» sobre el `.pyd` de campaña | El `.pyd` se reconstruyó con el fix `65326b8`: hash `f4c2a201…`, no `9acaf187…` | §10.3 y §10.9 registran ambos hashes; las cifras de la pata GPU son las de la run de campaña |
| §10.5 (esta revisión) | «el fix está en el árbol, sin verificar» | `t_d80c2e58` cerró `done` con verificación (sonda `[90,90,90]`, 12 passed, CER 1.4669/1.1641, `cargo test` 67) | §10.5 y §10.6 actualizados; sigue abierta la re-medición `t_5c3b7dfe` |

### 10.8 Lo que este documento **no** sabe

* Las citas internas de `oar-ocr` `0.10.1` (§3, §4, marcadas «cita `A1`») siguen
  siendo de segunda mano: el árbol del crate no está descargado en el host.
* El **wheel publicado en CI** no se ha verificado en una máquina con CUDA: la
  receta de `benchmarks/GPU.md` §«Cómo ejecutar con CUDA (CUDA 13)» está
  verificada en el `.venv` del repo, no en una instalación `pip install
  pyocrust-gpu`.
* La calidad de **fórmula en GPU** está sin medir **con el binario arreglado**
  para `pyocrust_formula`/`pyocrust_formulanet`: las filas publicadas son del
  binario defectuoso (§10.5) y la re-medición `t_5c3b7dfe` no ha terminado.
* `pp_structurev3_api` ya **está** en el `DEFAULT_BACKENDS` de `full_page`
  (`benchmarks/features/full_page/bank.py:86`) y **ya tiene fila publicada**: la
  run vigente `2026-11-09_17-15-04` (n=6, 4 motores) lo incluye con
  `markdown_f1=0.086` (`benchmarks/reports/SUMMARY.md`). `t_838df3ad` cerró `done`.
* Las tarjetas `running` de §10.6 pueden cerrarse después de este bloque; sus
  estados se releyeron aquí, no se infieren.

### 10.9 Citas de código sobre un árbol en movimiento

Las citas de este bloque se hicieron sobre el árbol del 2026-11-09. **Dos hashes
delatan el movimiento**, y se registran en vez de ocultarse:

| Artefacto | Hash | Significado |
| :--- | :--- | :--- |
| `pyocrust/_pyocrust_core.pyd` **de campaña** | `9acaf1878d27013c32be2a66d8631affcca700d488d0071a3a219e707e77c937` (37 456 896 B) | El binario con el que se midió la pata GPU de §10.3 |
| `pyocrust/_pyocrust_core.pyd` **actual** | `f4c2a2016458f79f55e6cdc2eef672e111180c2fa266bf9dfd907379c09a2300` | Rebuild con el fix `65326b8`, **verificado** (§10.5) |

Lo que **no** se trata como vigente aquí: las **filas GPU publicadas** de `formula`
(`2026-11-09_16-22-29`), que son del binario defectuoso y están a la espera de la
re-medición `t_5c3b7dfe`. El auditor de citas es re-ejecutable: basta recitar
`src/**` y `benchmarks/**` y recalcular el sha256 del `.pyd`.

## 11. SDK de regiones de detección + OCR por recorte (`RDET`, 2026-11-17)

> **Bloque nuevo; no reescribe §1-§10.** Fija la forma que implementa la tarjeta
> `t_3664c9a8` y resuelve cómo se relaciona con `TaskPredictor("text_detection")` y con
> el modo «no reescalar» de la tarjeta hermana `t_ad3760e5`.
>
> **Nota de procedencia de citas (corrige §1.2).** Las citas de `oar-ocr` de esta
> sección **sí** son de primera mano: el crate está en el host en
> `C:\Users\vquilon\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\oar-ocr-0.10.1\`
> y `oar-ocr-core-0.10.1\`, y se leyeron allí. Las rutas `oar-ocr*/src/...` de §11 son
> internas a esos crates; las rutas `src/...` y `tests/...` son del repo.

### 11.1 Hechos verificados hoy (leídos en el crate, no inferidos)

1. **El pipeline `OAROCR` ya recorta por región y hace rec por recorte a resolución
   nativa.** `OAROCR::predict` ejecuta: detección → `sort_detection_boxes` →
   `crop_text_regions` → `recognize_global` (`oar-ocr-0.10.1/src/oarocr/ocr.rs:720-784`).
   Los recortes salen de `preprocess.image` (imagen a resolución completa, ya
   orientada/rectificada) usando las cajas mapeadas de vuelta a coordenadas originales
   por `ImageScaleInfo` (`oar-ocr-core-0.10.1/src/processors/resize_detection.rs:190`,
   `text_detection_adapter.rs:36-79`). Conclusión: **el recorte nativo y el rec por
   región ya existen**; lo que no existe es exponer las cajas ni rec sobre cajas ajenas.
2. **El crate de det sí acepta los tres knobs de reescalado, aunque el builder no tenga
   setters dedicados.** `TextDetectionConfig` incluye `limit_side_len`, `limit_type` y
   `max_side_len` (`oar-ocr-core-0.10.1/src/domain/tasks/text_detection.rs:48-52`) y
   `TextDetectionPredictorBuilder` recibe el config completo vía el `with_config(...)`
   que genera `#[derive(TaskPredictorBuilder)]`
   (`oar-ocr-derive-0.10.1/src/lib.rs:307-313`;
   `oar-ocr-core-0.10.1/src/predictors/builder.rs:60-63`). La tarjeta hermana describe
   esto como «su builder no expone `limit_side_len/limit_type/max_side_len`»: es cierto
   sólo para los *setters* individuales (`text_detection.rs:54-92`), no para la
   capacidad — se fijan con `.with_config(TextDetectionConfig{ .. })`.
3. **`max_side_len` recorta el lado largo INCONDICIONALMENTE**, con independencia de
   `limit_type`. En `resize_image_type0` el ratio de `Min`/`Max` se calcula primero y
   **después**, siempre, `if resize_h.max(resize_w) > max_side_limit { ... }` reescala a
   la baja (`oar-ocr-core-0.10.1/src/processors/resize_detection.rs:287-296`). El
   adaptador de det arranca de `db_preprocess_for_text_type(None)` = `limit_side_len 960,
   limit_type Max, max_side_limit 4000` (`.../adapters/preprocessing.rs:81-89`) y sólo
   lo sobrescribe si el config trae el valor (`text_detection_adapter.rs:147-155`); el
   pipeline hace lo mismo (`oar-ocr-0.10.1/src/oarocr/ocr.rs:394-410`). Constantes:
   `DEFAULT_LIMIT_SIDE_LEN = 960`, `DEFAULT_MAX_SIDE_LIMIT = 4000`
   (`oar-ocr-core-0.10.1/src/core/constants.rs:11,15`).
   **Corolario (defecto de premisa de la tarjeta hermana `t_ad3760e5`):** «no reescalar»
   **no** se logra con `limit_type="min"` solo. Una página 7000x5000 con
   `limit_type=min, limit_side_len=64` **sigue** recortada a 4000x2848 por `max_side_len`
   (por defecto 4000). Para ver la página a resolución nativa hay que subir **también**
   `max_side_len` (p. ej. `>=7000`). El criterio de esa tarjeta («más regiones con
   min/64») probablemente pasa (4000 > 960) pero **no prueba** «no reescalar».
4. **El `rect` batch size agrupa los recortes.** `region_batch_size` por defecto en CPU:
   16 para `tiny`, 4 para el resto; con acelerador, el default del adaptador o
   `clamp(12g-28,4,64)` si se da presupuesto (`oar-ocr-0.10.1/src/oarocr/builder_utils.rs:87-114,160-174`;
   `ocr.rs:291-301`). El nº de pasadas de rec es `ceil(N / batch)`, no `N`.

### 11.2 Forma exacta del API

**Python (superficie 1, `VeloceOCR`).** Dos métodos nuevos, ambos con `self` y `image`
en la misma forma que `recognize` (`str`/`bytes`/`PathLike`), liberando el GIL en la
inferencia:

```python
class VeloceOCR:
    def detect_regions(
        self,
        image: str | bytes | PathLike[str],
        *,
        text_det_limit_side_len: int | None = None,      # None = default actual (960)
        text_det_limit_type: str | None = None,          # "min" | "max" | None
        text_det_max_side_len: int | None = None,        # None = default actual (4000)
        text_det_thresh: float | None = None,            # score_threshold (hoy 0.2)
        text_det_box_thresh: float | None = None,        # box_threshold (hoy 0.45/0.4)
        text_det_unclip_ratio: float | None = None,      # hoy 1.4
        text_det_max_candidates: int | None = None,      # hoy 3000
    ) -> list[BoundingBox]: ...

    def recognize_regions(
        self,
        image: str | bytes | PathLike[str],
        boxes: Sequence[BoundingBox],
        *,
        rec_score_threshold: float | None = None,        # filtro de confianza del rec
        region_batch_size: int | None = None,            # recortes por pasada de rec
    ) -> OcrResult: ...
```

Reglas fijas (contrato, no implementación):

* **Tipos reutilizados, ninguno nuevo.** `detect_regions` devuelve `list[BoundingBox]`
  (la `#[pyclass]` existente, AABB `x1,y1,x2,y2`, `src/core/types.rs:312-350`);
  `recognize_regions` devuelve `OcrResult` con **una `TextRegion` por caja de entrada**
  (`box` = la caja dada, `text` = texto reconocido o `""`, `confidence` = score o `0.0`).
* **Caja = AABB.** La salida de detección del crate es un cuadrilátero; se colapsa a su
  `aabb()` igual que ya hace el backend de texto (`src/engines/oar_text.rs:179`) y que
  `TaskPredictor("text_detection")` (`src/tasks/mod.rs:377`). *Trade-off*: se pierde la
  rotación de líneas inclinadas. Alternativa rechazada: una `#[pyclass]` nueva de
  polígono de 4 puntos — duplicaría `BoundingBox` y rompería la regla de una sola
  representación de caja; para texto rotado se usa `recognize` (que conserva el
  cuadrilátero internamente vía `TextCroppingProcessor`, `ocr.rs:868-903`).
* **`detect_regions` usa el modelo de detección del preset**, no el `tiny` fijo de
  `TaskPredictor`. En `VeloceOCR("pp_ocrv6_medium")` corre `pp-ocrv6_medium_det.onnx`
  (`src/core/types.rs:64-70`); en `pp_structurev3`, el `tiny` que embebe
  (`src/core/types.rs:260`).
* **Defaults = comportamiento actual** (`None` → 960 / Max / 4000 y umbrales de hoy):
  cero cambio para quien no pasa nada, y **idénticos** a los de la tarjeta hermana
  `t_ad3760e5` sobre `recognize`. Receta para 7000x5000 a resolución nativa:
  `limit_type="min", limit_side_len=64, max_side_len>=7000` (los tres, por 11.1.3).
* **Validación tipada, sin fallback silencioso.** `limit_type` fuera de `{min,max}`,
  umbrales fuera de rango o `region_batch_size==0` → `PyOcrValueError` antes de cargar
  modelos (misma política que la whitelist de `src/tasks/mod.rs:73-90`).
* **Presets sin par det+rec propio** (`indra`, VLM) → `PyOcrValueError`; el SDK se
  define para los presets de texto (`pp_ocrv6*`) y `pp_structurev3`.
* **Una sola fuente de verdad de los knobs.** El mapeo `opts → TextDetectionConfig`
  debe ser **un** helper de Rust compartido por `detect_regions` y, si se añaden allí,
  por `TaskPredictor("text_detection")`; el significado de `text_det_*` no puede diferir
  entre `recognize` (tarjeta hermana) y `detect_regions`.

**Rust (forma interna, `VeloceOCR` en `src/lib.rs`).** Dos métodos sobre el struct que ya
tiene `engine`/`config`/`provider_effective` (`src/lib.rs:39-46`):

```rust
fn detect_regions(&self, py: Python<'_>, image: &Bound<'_, PyAny>, opts: &Bound<'_, PyDict>)
    -> PyResult<Vec<BoundingBox>>;
fn recognize_regions(&self, py: Python<'_>, image: &Bound<'_, PyAny>, boxes: &Bound<'_, PyAny>, opts: &Bound<'_, PyDict>)
    -> PyResult<OcrResult>;
```

* `detect_regions` construye (una vez, residente) un `TextDetectionPredictor` sobre el
  modelo de detección del preset con `.with_config(TextDetectionConfig{ .. })`
  (`oar-ocr-core-0.10.1/src/predictors/text_detection.rs:95-112`) y devuelve
  `det.bbox.aabb()` por detección.
* `recognize_regions` recorta con `image::imageops::crop_imm` sobre la imagen RGB nativa
  (sin reescalar la página) y pasa los recortes en lotes de `region_batch_size` al
  `TextRecognitionPredictor` del preset; mapea un resultado por caja.

### 11.3 Decisión de reutilización (y alternativa rechazada)

**No se reutiliza `full_page_tiling`/`FullPageTiling`** (`src/core/image_processor.rs:150-201`).
Emite una **malla fija 512 con solapamiento** — responde «cómo trocear la página», no
«cómo recortar estas cajas de texto». Usarla para recortar regiones **cortaría líneas por
la mitad** y dispararía el nº de pasadas de rec (una malla 512x512 con `overlap=64` sobre 7000x5000 son 192 (16x12)
mosaicos frente a un puñado por línea). Sigue siendo la utilidad opt-in de ADR-009, sin
cambios.

**Se reutiliza:** el primitivo de recorte `image::imageops::crop_imm` (ya usado por el
tiling, `src/core/image_processor.rs:197`); el `TextDetectionPredictor` y el
`TextRecognitionPredictor` ya envueltos en `src/tasks/mod.rs`; y `BoundingBox`/`OcrResult`
como tipos de cruce. Lo único nuevo en Rust es el cableado de los knobs y el bucle
recorte→rec; **ninguna** estructura de datos nueva.

Alternativa evaluada y rechazada: **un recorte por caja como función pura nueva en
`image_processor.rs`**. Es la ruta que «reutiliza» el módulo de preprocesamiento, pero
`crop_imm` ya es una línea y el módulo se declara «sin conocer `oar-ocr`»
(`src/core/image_processor.rs:10-12`); un helper propio sólo añade superficie. Se usa
`crop_imm` en línea.

### 11.4 Relación con `TaskPredictor("text_detection")` y con «no reescalar» (`t_ad3760e5`)

* **Con `TaskPredictor("text_detection"): no es lo mismo; lo sustituye para páginas
  grandes.** `TaskPredictor("text_detection")` está **clavado al det `tiny`**
  (`src/storage/registry.rs:187`), con umbrales genéricos (`src/tasks/mod.rs:123-129`) y
  **sin** knobs de reescalado → sobre una página grande reescala a 960 y pierde texto
  fino. `detect_regions` es el **mismo predictor** con (a) el modelo de detección del
  preset y (b) los knobs. Decisión: `TaskPredictor("text_detection")` **no se elimina**
  (compatibilidad); queda como «det suelto a resolución de pipeline», y `detect_regions`
  es la superficie soportada para detección a resolución elegida. Recomendado: añadir a
  `TaskPredictor("text_detection")` los mismos tres knobs para que ambos compartan el
  helper de 11.2 y no haya dos caminos de la misma cosa.
* **Con «no reescalar» (`t_ad3760e5`): complementarios, no sustitutos.** Esa tarjeta
  arregla la etapa de det **dentro de la página completa** (`VeloceOCR.recognize`); y como
  el pipeline **ya recorta por región a resolución nativa** (11.1.1), con los knobs
  `recognize` **ya entrega el objetivo end-to-end** (texto fino recuperado, recortes
  nativos) sin API nueva. Lo que aporta el SDK de regiones es distinto: (1) **las cajas**
  y (2) **rec sobre cajas ajenas** (regiones de layout, otro detector) — cosa que `OAROCR`
  no puede hacer porque siempre detecta sus propias cajas.
  **Regla de uso:** página completa a resolución nativa → `recognize(**text_det_*)` (una
  sesión, una llamada, menos pasadas); necesitas las cajas o das las tuyas →
  `detect_regions` + `recognize_regions`. Ninguna reemplaza a la otra, y ambas comparten
  el **mismo** `TextDetectionConfig`.

### 11.5 Coste: nº de regiones → rec; memoria 7000x5000 nativa; tiempo

**Nº de pasadas de rec.** `ceil(N / region_batch_size)`, con `N` = nº de cajas. Defaults
CPU: 16 (`tiny`) / 4 (resto); acelerador: default del adaptador o `clamp(12g-28,4,64)`
(`oar-ocr-0.10.1/src/oarocr/builder_utils.rs:87-114,160-174`). Ej.: 2000 regiones → 500
pasadas (batch 4), 125 (16), 32 (64). Los recortes se agrupan; **no** hay N *forward*
sueltos.

**Memoria — página 7000x5000 (procedencia: aritmética sobre las fórmulas del crate).**

| Concepto | Tamaño | Base |
| :--- | ---: | :--- |
| Página RGB8 nativa (7000x5000) | **100,1 MiB** (105 000 000 B) | 7000·5000·3 |
| Copia interna del det con `max_side_len=4000` | **32,6 MiB** (4000x2848) | `resize_detection.rs:287-302` |
| Copia interna del det a resolución nativa (`max_side_len>=7000`) | **100,1 MiB** | idem, sin recorte |
| Recortes en vuelo, caja media 800x40, por lote 4/16/64 | 0,37 / 1,46 / 5,86 MiB | 800·40·3·batch |
| Tensor de entrada de rec por lote 4/16/64 | 0,70 / 2,81 / 11,25 MiB | [b,3,48,320]·f32 (`constants.rs:21`) |

Pico ≈ página + mayor copia del det + recortes en vuelo + arena de ORT. Con la página a
resolución nativa: **~200 MiB** sobre CPU (página + copia nativa del det) + arena; con
`max_side_len=4000`: **~133 MiB** + arena. Todo cabe de sobra en cualquier
`max_runtime_seconds` de este proyecto. *No medido en proceso aquí* (el envelope de esta
tarjeta es sólo docs); la medida de pico pertenece a `t_3664c9a8`.

**Tiempo (huella).** El SDK hace det **una** vez + rec sobre `N` regiones = **el mismo
trabajo** que ya hace `recognize` en la misma página. Base **medida** de `recognize` en
`text`/FUNSD, CPU: `pp_ocrv6 tiny 318`, `small 823`, `medium 2138` ms/img
(`benchmarks/reports/text/REPORT.md:21-23`); GPU tiny 419 ms/img (`:54`). **Caveat de
procedencia:** FUNSD son páginas pequeñas (~1k px); para 7000x5000 ese número **no**
aplica. La huella para la página grande es **estimada** (crece ~lineal con los píxeles en
det y con `N` en rec), **no medida**; la medición es de `t_c5468198`/`t_3664c9a8`, y este
bloque no la inventa.

**Cuadre con `max_runtime_seconds`.** Esta tarjeta (diseño) consume 0 cómputo. Las de
implementación/verificación tienen 2400 s / 1800 s: un build incremental + **una** página
7000x5000, `device="cpu"`, una llamada → segundos-a-minutos bajos, dentro del envelope.

### 11.6 Gaps abiertos (no defectos de este diseño)

* El criterio de `t_ad3760e5` no distingue «no reescalar» de «reescalar menos»: conviene
  añadir `text_det_max_side_len>=7000` al caso de aceptación para que la página se vea a
  resolución **nativa** de verdad (11.1.3).
* La medición de pico de memoria y de tiempo de una página 7000x5000 real **no existe
  todavía**; queda para las tarjetas hijas. Este bloque declara su envelope como
  aritmética + estimación, y lo etiqueta como tal.

## 12. Router automático de estructura: layout / tabla / fórmula (`RAUTO`, 2026-11-17)

> **Bloque nuevo; no reescribe §1-§11.** Fija las reglas de disparo que puede implementar
> una tarjeta hija, sobre las piezas que ya existen: `pipeline_profiles()`, `multifeature.recognize`,
> `resolve_pipeline`, los presets de `VeloceOCR` y la composición de `t_17009adc` (en curso).
>
> **Procedencia de citas.** Las de `oar-ocr*` son de primera mano, leídas en
> `C:\Users\vquilon\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\oar-ocr-0.10.1\` y
> `oar-ocr-core-0.10.1\`; las `src/...`, `pyocrust/...`, `tests/...` y `benchmarks/...` son del repo.

### 12.1 Hecho que decide la forma: la cadena layout→tabla→fórmula **ya existe** dentro del preset de estructura

`OARStructure::predict_image` corre, en un solo pipeline y en este orden: `prepare_page` →
`detect_layout_and_regions` (modelo de layout) y luego `complete_page`, que ejecuta el
`TableAnalyzer` **sobre las regiones de layout** y `recognize_formulas` filtrando
`element_type.is_formula()`, y ordena la lectura con `sort_layout_elements_enhanced`.
Evidencia: `oar-ocr-0.10.1/src/oarocr/structure.rs:2728-2737` (`prepare_page`), `:2739-2800`
(`complete_page`: analyzer + sort), `:2085-2100` (`recognize_formulas`:
`.filter(|e| e.element_type.is_formula())`).

**Regla de diseño (la que evita duplicar todo lo demás):** el router **no** vuelve a decidir
«si hay tabla, corre tabla» ni «si hay fórmula, corre fórmula»; eso ya está gateado aguas
arriba por la salida de layout. El router decide **una sola cosa**: si se enciende el preset
de estructura (`pp_structurev3`) o no. Encendido, layout es incondicional (es su primera
etapa) y tabla/fórmula disparan **por región** según su clase, dentro del mismo pipeline.

**Corolario de coste:** la cadena se satisface cargando `pp_structurev3` **una vez**, nunca
encadenando `TaskPredictor("layout_detection")` + `("table_structure_recognition")` +
`("formula_recognition")`.

* Alternativa evaluada —*encadenar los tres `TaskPredictor`*— y por qué pierde: (1) obliga a
  implementar en Python el gate y el pegado layout→región que el preset ya hace (§12.1);
  (2) pierde la salida rica: la tarea suelta `table_structure_recognition` devuelve tokens y
  geometría, **no HTML** (§3.1.2), mientras `StructureResult.to_markdown()` sí (§3.1.4, ADR-003);
  (3) pierde clases que el preset ya trae (clasificación wired/wireless, detección de celdas).
  En sesiones ORT sí sería más barato (3 frentes: layout 1 artefacto, tabla 1, fórmula 1;
  `src/storage/registry.rs:185-206`) frente a los 8 del preset, pero no existe hoy una carga
  perezosa por etapa en `pyocrust` y el coste medido por página (§12.5) no es el cuello en
  este host. Rechazada por código y por contrato, no por aritmética de sesiones.
* Toda esta cadena es ortogonal al SDK de regiones de §11: si el llamante aporta sus propias
  cajas, `recognize_regions` sustituye la detección propia del pipeline y no se toca layout.

### 12.2 Cuatro decisiones; el router es la que **falta** (no duplicar)

| Decisión | Dueño hoy | Entrada | Fuente |
| :--- | :--- | :--- | :--- |
| Intención declarada → preset/tareas | `resolve_pipeline` | `TaskSpec` | `pyocrust/resolver.py:67-117` |
| Features explícitas → ejecuciones | `multifeature.recognize` | `features=[...]` | `pyocrust/multifeature.py:106-143` |
| Flags de **etapa** (orientación doc, unwarping, orientación de línea, `text_type`) | constructor de `VeloceOCR` | bools / `str` | tarjeta `t_17009adc` (en curso) |
| **Imagen → ¿hace falta estructura?** | **nadie** | señal de la imagen | — ← **el router** |

Reglas de no-duplicación (precedencia estricta):

1. **Lo declarado gana.** Si el llamante dio un `TaskSpec` o una lista `features`, el router
   **delega** (a `resolve_pipeline` / a `multifeature`) y no re-deriva nada. Así no hay dos
   implementaciones del mismo mapeo intención→preset.
2. **El router produce, no ejecuta.** Su salida es la lista `features=[...]` que consume el
   **único** ejecutor `multifeature.recognize`. No añade un segundo motor de ejecución.
3. **Los flags de composición viven en un solo sitio** (el constructor de `VeloceOCR`,
   `t_17009adc`). El router **no** los fija; los pasa tal cual. Frontera a cerrar con esa
   tarjeta: `text_type="table"` decide «esta página es una tabla» a nivel de etapa, que
   solaparía con el router — si ese flag llega a existir, la decisión «¿tabla?» pertenece al
   router y `text_type` debe quedar como mero ajuste de preprocesado (gap §12.6).

### 12.3 Reglas de disparo (explícitas y testeables)

La política es una **función pura, sin inferencia**: `route(declared, signals) -> RouteDecision`.
Primera regla que casa, gana. Constantes nombradas (defaults de política, no medidos; §12.6):

```
GEOM_MIN_SIDE_PX   = 64      # lado menor por debajo del cual no cabe estructura
ROUTE_MIN_REGIONS  = 24      # nº de regiones de la sonda que justifica estructura
ROUTE_MIN_DENSITY  = 0.12    # Σ área(cajas) / área(imagen)
```

| # | Condición | Decisión | `reason` |
| :--- | :--- | :--- | :--- |
| `R0` | `declared` es `TaskSpec` o `features` | delegar a `resolve_pipeline` / `multifeature`; el router no decide | `declared` |
| `R1` | `min(W,H) < GEOM_MIN_SIDE_PX` | texto (`pp_ocrv6_tiny`), **sin** estructura (gratis, sin modelos) | `geometry` |
| `R2` | `probe=True` y `n_regions >= 24` **o** `ink_ratio >= 0.12` | estructura (`pp_structurev3`) | `probe` |
| `R2'` | `probe=True` y no cumple `R2` | texto | `probe` |
| `R3` | nada declarado, sin sonda, geometría OK | texto del tamaño que elija `resolve_pipeline(TaskSpec())` (tiny por defecto) | `default-text` |

Notas que hacen las reglas testeables:

* **¿Layout «siempre»? No.** Layout solo existe dentro del preset de estructura; el preset de
  texto nunca lo corre. Con la salida de `R3`/`R1` el contrato imagen→OCR queda **idéntico** (§12.4).
* **¿Tabla/fórmula «a partir de la salida de layout»? Ya gateado aguas arriba** (§12.1). El
  router **no** devuelve un flag «tabla=on/fórmula=on»: para saber si dispararon, se lee el
  propio `StructureResult` (tabla HTML en el Markdown / LaTeX de la fórmula). Añadir un flag
  paralelo sería la segunda copia del mismo concepto que el router debe evitar.
* **La sonda es opt-in, no por defecto.** Un det obligatorio añadiría una sesión al caso común
  y, si la decisión sale «texto», el pipeline de texto **volvería a detectar** (det dos veces);
  además la señal es débil en esquemáticos vectorizados (pocas cajas de texto). Por eso el
  default es `R3` (YAGNI). Alternativa rechazada: sonda obligatoria; pierde porque no se paga
  sola y duplica detección en el camino barato.
* **Lectura de la señal de densidad.** Se toma `ink_ratio` **alto** como indicio de página con
  contenido (no «densidad baja», como enunciaba la tarjeta): una página densa necesita
  estructura; y el OR con `n_regions` cubre también el caso de muchos fragmentos. Lectura
  «densidad baja ⇒ estructura» rechazada por un solo-signal débil.

Ejemplos de aceptación (entrada → salida), los que debe cubrir el test de la tarjeta hija:

| `declared` | `signals` | `features` devueltas | `reason` |
| :--- | :--- | :--- | :--- |
| `TaskSpec(tables=True)` | — | `("pp_structurev3",)` | `declared` |
| `features=["layout"]` | — | `("layout_detection",)` (delegado) | `declared` |
| `None` | `{W:40,H:40}` | `("pp_ocrv6_tiny",)` | `geometry` |
| `None` (probe) | `{n_regions:5, ink_ratio:0.05}` | `("pp_ocrv6_tiny",)` | `probe` |
| `None` (probe) | `{n_regions:31, ink_ratio:0.90}` | `("pp_structurev3",)` | `probe` |
| `None` | — | `("pp_ocrv6_tiny",)` | `default-text` |

> El camino de texto (R1/R2'/R3) devuelve el **id del preset resuelto** (`pp_ocrv6_tiny`), no la
> tarea `text_recognition`: `text_recognition` es tarea (`family=task`) y devuelve `{text, score}`
> (§3.1.2), lo que incumpliría el `OcrResult` sin cambios que exige §12.4 y perdería el tamaño que
> fija R3 (`resolve_pipeline(TaskSpec())`).

Donde vive (sin módulo nuevo): `route()` en `pyocrust/resolver.py` —que ya se documenta como
«pure pipeline recommendations»— y un driver de una línea en `pyocrust/multifeature.py`:
`auto_recognize(image, ...)` = (`probe` opcional) + `route(...)` +
`multifeature.recognize(image, features=decision.features)`.

### 12.4 Qué se añade al resultado y cómo se conserva el contrato actual

* **Router → texto** (R1/R2'/R3): devuelve `OcrResult` **sin cambios**, exactamente el de hoy
  (§3.1.2/§3.1.4). Cero claves nuevas.
* **Router → estructura** (R0/R2): devuelve `StructureResult` con `to_markdown()` (tablas HTML,
  fórmulas LaTeX), `elements` (layout) y `regions` — **tipo que ya existe** (ADR-003,
  §3.1.4). No se crea ni un `#[pyclass]` ni un esquema nuevo.
* **La estructura por región y el orden de lectura ya vienen incluidos**: `StructureResult`
  ordena en `sort_layout_elements_enhanced` (§12.1); la tarea suelta de layout expone
  `is_reading_order_sorted` (`src/tasks/mod.rs:336`, `pyocrust/__init__.pyi:149`). El router no
  añade nada aquí.
* **Explicabilidad fuera del resultado.** El «porqué» no se mezcla en la salida OCR: va en un
  objeto separado `RouteDecision` (`preset`, `size`, `features`, `reason`, `artifacts` leídos de
  `pipeline_profiles()[id]`). Así un consumidor existente ve el **mismo tipo y las mismas claves**
  con router o sin él. Los tiempos **no** se incrustan en el código (envejecerían): viven en la
  tabla de §12.5.

### 12.5 Coste por modelo encendido

Sesiones ORT = nº de `.onnx` del perfil (los `.txt`/`.json` de diccionario/tokenizer no abren
sesión). Artefactos por `pipeline_profiles()`/`registry`: `pp_ocrv6` = 3 (2 sesiones);
`pp_structurev3` = 11 (8 sesiones: det, rec, layout, table_cls, wired/wireless, cell_det,
formulanet — `src/storage/registry.rs:161-173`).

| Se enciende | Artefactos (sesiones) | ms/página medidos (CPU) | Medido en |
| :--- | :--- | ---: | :--- |
| Texto `tiny` / `small` / `medium` | 3 (2) | 318 / 823 / 2138 | `benchmarks/reports/text/REPORT.md:21-23` |
| **Preset estructura** (`pp_structurev3`) | **11 (8)** | layout 2926 · tabla 1128 · fórmula 1028 | `layout/REPORT.md:62`, `table/REPORT.md:22`, `formula/REPORT.md:24` |
| Etapa: orientación de documento | 1 (1) | 4 | `orientation/REPORT.md:21` |
| Etapa: rectificación (unwarping) | 1 (1) | 74 | `rectification/REPORT.md:21` |
| Etapa: orientación de línea | 1 (1) | 2 | `text_line/REPORT.md:21` |
| Etapa: detección de sello | 1 (1) | 217 | `seal/REPORT.md:20` |

* **Caveats de procedencia (no inventados):** las cifras de layout/tabla/fórmula son del
  **mismo preset** `pp_structurev3` sobre **datasets distintos** (`n` = 40/8/10) — se dan por
  feature, **no** son aditivas ni aíslan un modelo. No existe medida de una sonda de detección
  suelta (el banco `text` mide el pipeline det+rec completo) ni de `ram_bytes` (`None` en el
  catálogo). No se extrapolan (§12.6).
* **Cómo el router explica el coste:** por encender estructura pasa de 2 a 8 sesiones residentes;
  el disparo de tabla/fórmula **por región** es el que gatea su *forward*, no su carga. El router
  reporta qué perfil se carga (`artifacts`) y con qué `reason`, y el `reason` apunta a esta tabla.

### 12.6 Gaps abiertos (no defectos de este diseño)

* `GEOM_MIN_SIDE_PX`, `ROUTE_MIN_REGIONS` y `ROUTE_MIN_DENSITY` son **defaults de política**, no
  umbrales medidos: no hay barrido que los calibre. Son el mando de calibración; el barrido que
  los fije es tarjeta hija.
* La frontera router ↔ `text_type` de `t_17009adc` (§12.2) queda sin cerrar hasta que esa tarjeta
  aterrice su semántica.
* La sonda opt-in no tiene coste medido (det aislado) ni prueba de que su señal discrimine
  esquemáticos vectorizados; por eso no es el default.
* El router no cubre el caso PDF con text-layer: ahí la decisión «¿rasterizar y pasar por OCR?»
  es de la tarjeta `t_3d36077e` (API de documentos), que es quien mejor discrimina. Este bloque
  es la política para una **imagen ya rasterizada**.


## 13. API de alto nivel para documentos PDF (text-layer vs render por página) (`PDFDOC`, 2026-11-17)

> **Bloque nuevo; no reescribe §1-§12.** Fija la forma que implementa la tarjeta hija
> `t_a7f78bfa` (hefesto). Se apoya en §3.1.4 (tres superficies), ADR-011 (núcleo Rust +
> fachada Python fina) y §11 (reglas de reuso de tipos).
>
> **Procedencia de citas.** Las de `pdfium-render` 0.9.5 son de **primera mano** (documentación
> oficial, docs.rs, leída hoy). Las de PDFium/`pypdfium2` son de la copia instalada en
> `.venv/Lib/site-packages/pypdfium2*`. Las rutas `src/...`, `Cargo.toml`, `pyocrust/...` son
> del repo.

### 13.1 Hechos verificados hoy (leídos, no inferidos)

1. **No hay ninguna dependencia PDF en el árbol Rust.** `Cargo.toml` declara `pyo3`,
   `oar-ocr`, `oar-ocr-vl` (opt), `image = "0.25"`, `rayon`, `reqwest`, `sha2`; ninguna parsea
   PDF. `image = "0.25"` **ya** está: la usan el preprocesamiento y el *tiling*
   (`src/core/image_processor.rs:14-15`).
2. **El punto de entrada OCR acepta sólo bytes codificados, no un raster crudo.**
   `VeloceOCR.recognize` extrae `str`/`bytes`/`PathLike` y lee bytes (`src/lib.rs:189-201`);
   los motores decodifican con `image::load_from_memory(bytes).into_rgb8()`
   (`src/engines/oar_text.rs:234-239`; igual en `oar_indra.rs:48`, `oar_structure.rs:189`,
   `vlm.rs:415`). Corolario: un raster producido **fuera** del núcleo debe entregarse
   codificado (PNG) y se vuelve a decodificar dentro.
3. **No existe rasterizador PDF pure-Rust; PDFium ya está en el host.** El wheel de
   `pypdfium2` 5.14.0 (BSD-3-Clause / Apache-2.0, metadatos del `dist-info`) trae el binario
   nativo en `.venv/Lib/site-packages/pypdfium2_raw/pdfium.dll` = **7 381 504 B (7,04 MiB,
   Windows x64)**.
4. **PDFium da, por página y en una sola biblioteca, texto con cajas, tamaño y render.** En
   `pypdfium2` (`_helpers/textpage.py:149,160,196,224`; `_helpers/page.py:53-67,190,353`):
   `count_chars`, `get_charbox`, `count_rects`/`get_rect`, `get_text_range`, `get_size`,
   `render(scale=…)`. El bitmap de PDFium es **BGRA/BGRx por defecto** (4 B/px)
   (`_helpers/bitmap.py:211,218`).
5. **`pdfium-render` 0.9.5 es un binding de alto nivel a PDFium y NO incluye PDFium.**
   Licencia **MIT OR Apache-2.0**; enlaza la librería nativa en *runtime* (`libloading` entre
   sus dependencias) o en *build* (`PDFIUM_DYNAMIC_LIB_PATH` / `PDFIUM_STATIC_LIB_PATH`).
   PDFium, al instalarlo, va bajo sus propias licencias (**Apache-2.0 / BSD-3-Clause**).
   Soporta `image` 0.25 (feature), la misma versión que el repo. MSRV ≥ 1.61 sin esa feature.
6. **La API de `pdfium-render` cubre exactamente lo que pide el contrato** (docs.rs 0.9.5):
   `PdfPage::text() -> Result<PdfPageText, PdfiumError>`; `PdfPageText::len() -> i32` (cuenta
   caracteres, incluidos espacios y saltos); `PdfPageText::segments() -> PdfPageTextSegments`;
   `PdfPageTextSegment::text() -> String` y `PdfPageTextSegment::bounds() -> PdfRect` (el
   propio crate documenta que PDFium **fusiona cajas pequeñas en segmentos** con la misma
   línea base y fuente); `PdfPage::width()/height() -> PdfPoints`;
   `PdfPage::render(width: Pixels, height: Pixels, rotation) -> Result<PdfBitmap, PdfiumError>`
   y `render_with_config(&PdfRenderConfig)`;
   `PdfPage::points_to_pixels/pixels_to_points(…, &PdfRenderConfig)` para convertir puntos↔píxeles.
7. **`lopdf`/`pdf-extract` extraen texto SIN cajas y no rasterizan.** El ejemplo propio de
   `lopdf` 0.44 (`extract_text.rs`) hace `doc.extract_text(&[page]) -> Result<String>`:
   devuelve una cadena, no regiones ni coordenadas.

### 13.2 Forma exacta del API

**Python (superficie nueva, fachada fina sobre el núcleo).** Dos funciones libres y una clase:

```python
from pyocrust import parse_document, render_page, PageInfo, TextRegion

pages = parse_document("plano.pdf")                 # todas las páginas
pages = parse_document("plano.pdf", pages=[2, 5])   # sólo las 1-indexadas [2, 5]
png   = render_page("plano.pdf", index=5, dpi=200)  # bytes PNG de UNA página
```

```python
def parse_document(
    path: str | PathLike[str],
    pages: Sequence[int] | None = None,   # None = todas; si no, 1-indexadas
    dpi: int = 200,                        # sólo fija width_px/height_px
    *,
    text_min_chars: int = 64,              # umbral de la regla 13.3
) -> list[PageInfo]: ...

def render_page(
    path: str | PathLike[str],
    index: int,                            # 1-indexada
    dpi: int = 200,
) -> bytes: ...                            # PNG, una página, listo para recognize()
```

`PageInfo` (nueva `#[pyclass]`, atributos de sólo lectura) — es el **único** tipo nuevo:

```python
class PageInfo:
    index: int                        # 1-indexado, como el usuario ve el PDF
    has_text_layer: bool              # regla 13.3
    needs_ocr: bool                   # == not has_text_layer
    width_px: int                     # round(width_pt  * dpi / 72)
    height_px: int                    # round(height_pt * dpi / 72)
    text_regions: list[TextRegion]    # [] si needs_ocr
```

Reglas fijas (contrato, no implementación):

* **Tipos reutilizados, ninguno nuevo salvo `PageInfo`.** `text_regions` usa el `TextRegion`
  existente (texto, confianza y caja, `src/core/types.rs:265-343`): `box` = el AABB del
  segmento, `text` = `segment.text()`, y `confidence = 1.0` porque es extracción **exacta** del
  text-layer, no una puntuación de modelo (se documenta como tal). Mismo espíritu que §11.2.
* **`box` es un AABB en puntos PDF, origen arriba-izquierda, `y` hacia abajo.** Con
  `h = page.height()`: `x1 = rect.left`, `y1 = h − rect.top`, `x2 = rect.right`,
  `y2 = h − rect.bottom`. Es el **único** sistema de coordenadas del API (13.3). Así una caja
  de text-layer y una caja de OCR (ya AABB) son directamente comparables.
* **`dpi` no cambia las cajas.** `parse_document` es *dpi-independiente* en todo salvo
  `width_px`/`height_px`; re-renderizar a otro `dpi` no obliga a re-parsear. *Alternativa
  rechazada:* cajas en píxeles al `dpi` del render — haría que `box` dependiera en silencio de
  `dpi` (dos `dpi` ⇒ dos marcos) y acoplaría el texto (que no se rasteriza) a una resolución
  que no le afecta.
* **Errores tipados, sin *fallback* silencioso.** Índice fuera de rango, `dpi < 1`,
  `text_min_chars < 1`, `pages` con duplicados o no enteros → `PyOcrValueError` antes de abrir
  el documento. Si la librería PDFium no se puede cargar → `PyOcrRuntimeError` (nunca una lista
  vacía ni una página «sin texto» fingida). Misma política que la whitelist de
  `src/tasks/mod.rs:73-90`.
* **Funciones libres, no métodos:** son sin estado (no hay modelo que cargar). Consistente con
  `models_status`/`pipeline_profiles`.

### 13.3 Regla text-layer vs render (la decisión)

```python
n = page.text().len()                     # nº de caracteres que PDFium ve en la capa de texto
has_text_layer = n >= text_min_chars      # text_min_chars por defecto 64
needs_ocr      = not has_text_layer
```

* **`has_text_layer == True` → extraer, sin OCR.** `text_regions` = una `TextRegion` por
  `PdfPageTextSegment` (`segment.text()` + `segment.bounds()`): es **exacto** —el texto sale
  del *content stream*, no de un modelo— y trae coordenadas. `needs_ocr = False`.
* **`has_text_layer == False` → marcar y rasterizar.** `text_regions = []`, `needs_ocr = True`;
  el raster se produce con `render_page(index, dpi)` y entra al OCR (13.5). Es el caso de los
  **escaneos** y del **texto vectorizado como trazos** (esquemáticos): ambos dan `n = 0`.
* **Por qué un umbral y no `n > 0`.** Una página escaneada con un sello de texto (unas decenas
  de caracteres) tiene `n > 0` pero NO es una página de texto; tratarla como text-layer perdería
  el contenido del escaneo. `text_min_chars = 64` es un valor **documentado y sustituible**
  (kwarg), pensado para el corpus objetivo: un esquemático con text-layer tiene miles de
  caracteres y uno vectorizado, 0. **Es heurística, no umbral medido** (ver 13.7).
* **Un solo marco de coordenadas.** Ambas ramas producen AABB en puntos PDF con el mismo origen
  (13.2). PDFium es **una** biblioteca: texto y render salen del mismo modelo de página, así que
  no hay dos convenciones de eje que casar (ese era el riesgo de mezclar un parser pure-Rust de
  texto con un rasterizador aparte).

### 13.4 Crate elegido y su coste (alternativa rechazada)

**Elegido: `pdfium-render` 0.9.x (MIT OR Apache-2.0) + una librería dinámica PDFium
(Apache-2.0 / BSD-3-Clause).** Es **una** dependencia nueva y resuelve las **tres** cosas que el
contrato necesita con **un solo** modelo de página: (1) texto con cajas, (2) tamaño de página,
(3) rasterizado. Mantiene el raster **dentro del proceso** del núcleo, sin viaje a Python ni
codificar/decodificar PNG de por medio. Nada de modelos ni red: es parseo y render.

**Coste, explícito:**

| Concepto | Valor | Base |
| :--- | :--- | :--- |
| Dependencia nueva en `Cargo.toml` | 1 (`pdfium-render`) | — |
| Binario nativo que hay que aportar | PDFium dinámico, **7,04 MiB** en Windows x64 | `pypdfium2_raw/pdfium.dll` medido en el host |
| Enlace | runtime (`libloading`) o build (`PDFIUM_DYNAMIC_LIB_PATH`/`PDFIUM_STATIC_LIB_PATH`) | docs `pdfium-render` 0.9.5 |
| Licencias | `pdfium-render` MIT/Apache-2.0; PDFium Apache-2.0/BSD-3-Clause | docs + metadatos `pypdfium2` |
| Compatibilidad `image` | feature `image` 0.25 = la del repo | `Cargo.toml:34` vs deps de `pdfium-render` |

Que el binario ya exista en `.venv` (por `pypdfium2`) **no** lo convierte en dependencia del
crate: para el *dev loop* se puede apuntar `PDFIUM_DYNAMIC_LIB_PATH` a esa carpeta sin bajar
nada, pero el wheel distribuido debe llevar su propio PDFium por plataforma (un segundo binario
junto a `_pyocrust_core.pyd`).

**Alternativa rechazada: text-layer pure-Rust (`lopdf`/`pdf-extract`/`pdf-inspector`) + render
en Python (`pypdfium2`).** *Motivo real, no de gusto:* `lopdf`/`pdf-extract` dan texto **sin
cajas** (13.1.7) y **no rasterizan**, así que la rama `needs_ocr` seguiría necesitando PDFium
**en Python** de todos modos → dos bibliotecas, y el raster cruzaría a Python y volvería al
núcleo como PNG (13.1.2), con su codifica/decodifica extra. `pdf-inspector` (pure Rust,
`extract_text_with_positions` + `detect_pdf`) sí cubre la rama de texto —clasifica
texto/escaneado y da posiciones— pero **tampoco rasteriza**, y su propia documentación avisa de
que los `TextItem` van con origen abajo-izquierda y `y` hacia arriba mientras las cajas de
región/render van con origen arriba-izquierda: mezclar dos bibliotecas obliga a casar dos
marcos. Con `pdfium-render`, **una** biblioteca da texto, cajas y render en el mismo marco.

También evaluada: **fachada Python pura sobre `pypdfium2`** (0 dependencias nuevas; el mismo
PDFium por debajo; funciona hoy). Se rechaza **sólo** porque contradice el requisito explícito
«API en Rust» y paga el mismo PNG de ida y vuelta; queda como salida si esa exigencia se
revierte.

### 13.5 Dónde vive y composición con el pipeline OCR

**Dentro de pyocrust, en el núcleo Rust.** Módulo nuevo `src/documents.rs` con la `#[pyclass]`
`PageInfo` y las funciones `parse_document`/`render_page`; registrado en `_pyocrust_core`
(`src/lib.rs:349-368`) y re-exportado en `pyocrust/__init__.py` (+`__all__`) y
`pyocrust/__init__.pyi`. Es la forma «núcleo Rust + fachada Python fina»
(`pyocrust/__init__.py:1-11`, ADR-011) y una superficie más junto a las tres de §3.1.4. **No**
es un *entry*, módulo ni servidor aparte: el raster tiene que nacer en el **mismo proceso** que
el OCR.

**Composición (objetivo del encargo).** Para una página `needs_ocr`:

```python
png = render_page("plano.pdf", index=5, dpi=200)
res = VeloceOCR("pp_ocrv6").recognize(png)     # entra al OCR como cualquier imagen
```

La página rasterizada entra **al mismo `recognize`** que hoy; los indicadores de composición
(orientación / desinclinado / **unwarping**) los resuelve el preprocesamiento de `oar-ocr`
**sin cambios** — este diseño **no** añade una etapa de composición nueva. `pp_structurev3`,
`indra` y el VLM usan el mismo `render_page`; sólo cambia el preset de `recognize`. Cuando el
raster nace en el núcleo no hay que codificar a PNG ni re-decodificar: se entrega el `RgbImage`
directamente al motor. (La superficie pública mínima `render_page -> PNG -> recognize` reutiliza
el decodificador existente; el atajo en proceso es implementación de `t_a7f78bfa`.)

### 13.6 Envelope de memoria y tiempo (con procedencia)

**Memoria por página (procedencia: aritmética sobre los formatos documentados).** Página de
ejemplo 7000×5000, como en §11.5:

| Concepto | Tamaño | Base |
| :--- | ---: | :--- |
| Text-layer (rama sin OCR) | despreciable | nº de caracteres + nº de segmentos (miles × decenas de B) |
| Bitmap de PDFium (BGRA/BGRx, 4 B/px) | **133,5 MiB** (140 000 000 B) | 7000·5000·4; formato por defecto (13.1.4) |
| Copia RGB8 para el OCR (3 B/px) | **100,1 MiB** (105 000 000 B) | 7000·5000·3; `into_rgb8()` (13.1.2) |
| PNG intermedio (si se usa `render_page`) | +buffer de codificación | encoder de `image` |

Pico de la rama OCR ≈ bitmap BGRA + copia RGB ≈ **~234 MiB** (+ la arena de ORT del OCR). La
cifra del encargo («~105 MB») es **sólo** la copia RGB; el pico honesto es ~2,2× ese valor
porque el bitmap nativo de PDFium es de 4 B/px, no 3. **Una página a la vez, nunca todas**: el
envelope no se multiplica por el nº de páginas (de ahí que `parse_document` sea
metadatos-only y el raster salga de `render_page` página a página).

**Tiempo.** Text-layer: **~ms/página** (construir la *text page* de PDFium y recorrer sus
segmentos). Render a `dpi`: rasterización de PDFium, **estimada, no medida** —este bloque es
sólo docs—: para una página grande es del orden de décimas de segundo a `dpi` moderado, pero
**este documento no lo inventa**; la medición pertenece a `t_a7f78bfa`. La huella de `recognize`
sobre páginas pequeñas de FUNSD está medida en `benchmarks/reports/text/REPORT.md` y **no**
aplica a 7000×5000 (§11.5).

**Cuadre con `max_runtime_seconds`.** Esta tarjeta (diseño) consume 0 cómputo. La hija tiene
2400 s: un build incremental (`maturin develop`, una vez) + parsear y rasterizar **una** página
+ un `recognize` caben de sobra.

### 13.7 Gaps abiertos (no defectos de este diseño)

* **El gate de licencias no clasifica binarios nativos.** `src/storage/license.rs` es por
  artefacto del registro de **pesos**; PDFium (Apache-2.0/BSD-3-Clause, permisiva) no tiene
  entrada ahí. La hija debe declararla en el gate en vez de dejarla fuera de la contabilidad.
* **`text_min_chars = 64` es heurística**, no un umbral ajustado contra el corpus real del
  usuario; conviene revisarlo con un PDF mixto de verdad (la hija ya prueba ese caso).
* **No hay medición** de pico de memoria ni de tiempo de render de una página grande; queda
  para `t_a7f78bfa`. Este bloque declara su envelope como aritmética + estimación, y lo etiqueta.

## 14. Estado implementado: parametrización de detección y modo de regiones (2026-11-17)

> **Bloque nuevo; no reescribe §1-§13.** Reconciliación de los bloques de diseño `RDET`
> (§11) y de los knobs de detección/composición contra el **árbol real**, tras las tarjetas
> `t_ad3760e5` (knobs en el constructor) y `t_3664c9a8` (SDK de regiones). Documenta **lo
> implementado**, no lo planeado. Procedencia: rutas `src/...`, `pyocrust/...`, `tests/...`
> de este repo, leídas hoy; las de `oar-ocr*` donde §11 las fija.

### 14.1 Superficie real (firmas leídas del árbol, no inferidas)

Constructor `VeloceOCR.__new__` (`src/lib.rs:61-98`). Los siete `text_det_*` son `None` por
defecto; los tres flags de composición y `text_type` vienen de `t_17009adc`:

| kwargs Python | default real | efecto | dónde |
| :--- | :--- | :--- | :--- |
| `text_det_limit_side_len` | `None` → `960` | lado objetivo del reescalado | `src/lib.rs:67`; `src/engines/oar_text.rs:91-93` |
| `text_det_limit_type` | `None` → `"max"` | limita lado corto (`"min"`) o largo (`"max"`) | `src/lib.rs:68`; `src/engines/oar_text.rs:94-96` |
| `text_det_max_side_len` | `None` → `4000` | tope **incondicional** del lado largo | `src/lib.rs:69`; `src/engines/oar_text.rs:97-99` |
| `text_det_thresh` | `None` → `0.2` | umbral de score de detección | `src/lib.rs:70`; `src/engines/oar_text.rs:100-102` |
| `text_det_box_thresh` | `None` → `0.45` (`0.4` en `tiny`) | umbral de caja | `src/lib.rs:71`; `src/engines/oar_text.rs:83-86,103-105` |
| `text_det_unclip_ratio` | `None` → `1.4` | expansión del cuadrilátero | `src/lib.rs:72`; `src/engines/oar_text.rs:106-108` |
| `text_det_max_candidates` | `None` → `3000` | nº máx. de cajas | `src/lib.rs:73`; `src/engines/oar_text.rs:109-111` |
| `use_doc_orientation` | `True` | endereza 90/180/270 antes de detectar | `src/lib.rs:74,117-118` |
| `use_doc_unwarping` | `True` | rectificación UVDoc (páginas curvadas) | `src/lib.rs:75,119` |
| `use_textline_orientation` | `True` | gira el recorte de línea boca abajo | `src/lib.rs:76,120` |
| `text_type` | `"general"` | `"general"`\|`"table"`\|`"seal"` (preprocesado y tipo de caja) | `src/lib.rs:77,121-128` |
| `rec_score_threshold` (method) | `None` → `0.0` | filtro de confianza del rec | `src/lib.rs:318-326` |
| `region_batch_size` (method) | `None` → `16` (`tiny`) / `4` resto | recortes por pasada de rec | `src/lib.rs:327-335`; `src/regions.rs:62-65` |

Métodos nuevos:

* `VeloceOCR.detect_regions(image, *, text_det_*) -> list[BoundingBox]` (`src/lib.rs:260-298`).
  Los mismos siete kwargs; `None` hereda el valor del constructor vía
  `TextDetectionOptions::or` (`src/engines/oar_text.rs:65-75`, usado en `src/regions.rs:74`).
  Usa el modelo de detección **del preset** y devuelve el AABB de cada detección
  (`src/regions.rs:83-87`).
* `VeloceOCR.recognize_regions(image, boxes, *, rec_score_threshold=None, region_batch_size=None)
  -> OcrResult` (`src/lib.rs:308-339`). Recorta la imagen nativa con `crop_imm` y devuelve
  **una `TextRegion` por caja de entrada, en el mismo orden** (`src/regions.rs:92-142`;
  recorte con clamp a la página en `src/regions.rs:194-204`).

En la ruta del constructor, los `text_det_*` y los flags de composición **sólo los consume
`PpOcrV6`** (`src/lib.rs:99-116`); en los demás presets el pipeline se construye sin ellos.
En cambio `detect_regions` **sí** aplica sus `text_det_*` al detector del preset, también en
`pp_structurev3` (que usa su `tiny` de detección; `src/regions.rs:145-161`). El SDK de
regiones existe sólo para presets con par det+rec propio (`pp_ocrv6*`, `pp_structurev3`;
`src/regions.rs:47-51`).

### 14.2 Defaults reales = comportamiento de hoy (cero cambio)

`TextDetectionOptions::default()` es todos-`None` (`src/engines/oar_text.rs:41-57`); `to_config`
parte del histórico (**0.2 / 0.4 tiny / 0.45 resto / 1.4 / 3000**, `:80-90`) y sólo pisa los
campos `Some` (`:91-111`). `limit_side_len`/`limit_type`/`max_side_len` quedan `None`, así que el
adaptador de detección de `oar-ocr` pone `960/Max/4000` (§11.1.3) — **idéntico** a lo que hacía
`recognize` antes de estos knobs. Fijado por los tests unitarios de `src/engines/oar_text.rs:394-445`
(`detection_options_default_is_todays_behaviour`, `detection_options_or_pisa_solo_los_campos_no_none`).

### 14.3 Errores tipados (sin fallback mudo)

Un solo helper `detection_options` (`src/lib.rs:404-478`) valida antes de decodificar o cargar
modelos: `limit_type∉{min,max}`, umbrales ∉ `[0,1]`, `unclip_ratio<0`, `max_candidates<1`, lados
fuera de `1..u32::MAX` → `PyOcrValueError`. Es el **mismo** helper en el constructor (`:101-109`)
y en `detect_regions` (`:287-295`): el significado de `text_det_*` no puede diferir entre
`recognize` y `detect_regions` (§11.2). `rec_score_threshold∉[0,1]` y `region_batch_size<1` →
`PyOcrValueError` (`:318-335`); un preset sin par det+rec → `PyOcrValueError` con la lista de
presets soportados (`:344-353`).

El contrato está en `pyocrust/__init__.pyi:320-442` (stubs): cada parámetro con su default real
y la validación. Verificado contra el `.pyd` instalado por introspección
(`inspect.signature(VeloceOCR.detect_regions)` coincide con el stub).

### 14.4 Ejemplo: página grande / PDF vectorial a alta resolución (copiar y ejecutar)

```python
from pyocrust import VeloceOCR, render_page

# PDF vectorial (o escaneado) -> raster grande. render_page necesita PDFium (§13):
# un pdfium.dll junto al módulo nativo, o PYOCRUST_PDFIUM_LIB apuntando al suyo.
png = render_page("plano.pdf", index=1, dpi=600)      # ~5000x7000 px para un A4

RECETA = dict(text_det_limit_type="min", text_det_limit_side_len=64,
              text_det_max_side_len=7000)             # los TRES; con min/64 solo, el tope de 4000 recorta
engine = VeloceOCR("pp_ocrv6_medium", **RECETA)

boxes = engine.detect_regions(png, **RECETA)          # cajas AABB a resolución nativa
result = engine.recognize_regions(png, boxes)         # una TextRegion por caja, mismo orden
print(len(boxes), [r.text for r in result.regions[:3]])
```

Si no se necesitan las cajas, `VeloceOCR("pp_ocrv6_medium", **RECETA).recognize(png)` entrega el
objetivo end-to-end de una sola vez (el pipeline ya recorta por región a resolución nativa, §11.1.1).

### 14.5 Verificación y divergencias

| Qué | Evidencia (corrida real) |
| :--- | :--- |
| Defaults = histórico | tests unitarios `src/engines/oar_text.rs:394-445`; verdes en el handoff de `t_ad3760e5`/`t_3664c9a8` |
| Validación tipada del constructor | `tests/test_text_det_options.py` — 10/10 valores inválidos → `PyOcrValueError` |
| Criterio de aceptación del SDK de regiones | `tests/test_regions_sdk.py:140-174` — ≥40 cajas, 1:1 por caja, paridad ≥90%, ≥40 líneas del espectro; 6 passed |
| Rechazo de valores inválidos en los métodos | `tests/test_regions_sdk.py:177-201`; `tests/test_text_det_options.py` |
| El ejemplo de 14.4 corre | sonda directa en este host sobre `tests/data/mixed_text_and_scan.pdf` (2 páginas, `needs_ocr=[False,True]`) y sobre una página sintética: `render_page(dpi=600)` → `detect_regions` 6 cajas → `recognize_regions` 6 regiones con texto real |

* **Gap cerrado de §11.6.** «Añadir `text_det_max_side_len>=7000` al caso de aceptación» está
  hecho: `tests/test_regions_sdk.py:39-43` fija los tres knobs (`RECETA_NATIVA`) y `:145-146`
  los usa.
* **Nota ajena, no verificada.** `tests/test_text_det_parity.py` (fichero **no rastreado**, de
  otra tarjeta) falla hoy con 0 regiones tanto en default como en nativo. Hipótesis: se escribió
  contra los defaults anteriores al flip de composición (`use_doc_orientation/unwarping/
  textline_orientation = True`, `src/lib.rs:74-76`, cambio de `t_17009adc`). No comprobado;
  referencia: comentario 593 de `t_3664c9a8`. No es defecto de los knobs ni del SDK de regiones
  (cambios aditivos).
* **Sin medir.** Pico de memoria y tiempo de una página 7000x5000 reales siguen siendo estimación
  (§11.5); la pata GPU **no** se ha ejercitado (el `.pyd` instalado es release sin providers
  aceleradores), así que el gate «medir pico antes de GPU» no se ha disparado.
* Documentado además en `README.md` / `README.es.md` (sección «Detection options and region mode
  (`RDET`)» / «Opciones de detección y modo de regiones») y en `pyocrust/__init__.pyi`.


## 15. Contrato de entrada multi-flujo: imagen, PDF y sesión (`ENTRY`, 2026-11-17)

> **Bloque nuevo; no reescribe §§1–14. Diseño propuesto, no implementación.** Cierra la costura
> entre las entradas Python de imagen/PDF, el router y los motores Rust. Las firmas de abajo
> son normativas para la implementación posterior; las citas describen sólo el árbol observado.
>
> **Aclaración de revisión (2026-11-17):** sólo `PipelineChoice.id` es ejecutable (`tasks` es
> informativo); `tiled` delega el flujo completo en la entrada Rust normativa
> `VeloceOCR.recognize_tiled(...)`, pendiente de implementación (`pyocrust/__init__.pyi:403-417,435-442`; `src/lib.rs:230-243,272-339`).

### 15.1 Base observada y límites de compatibilidad

- `TaskSpec` expresa intención declarativa; `resolve_pipeline` la resuelve sin ejecutar modelos,
  y `route` devuelve un `RouteDecision` con preset/features y motivo (`pyocrust/resolver.py:12-37,68-89,132-147,169-207`).
- `multifeature.recognize` recibe una imagen y una secuencia de features; una feature devuelve
  su salida sin envoltorio y varias producen un `dict` etiquetado. `_run_features` construye
  `VeloceOCR`/`TaskPredictor` por llamada si no se le pasa una caché
  (`pyocrust/multifeature.py:117-173,176-204`). `auto_recognize` también recibe imagen y devuelve
  `(salida, RouteDecision)` (`pyocrust/multifeature.py:255-286`).
- `parse_document(path, pages=None, dpi=200, *, text_min_chars=64)` selecciona todas las
  páginas si `pages` es `None`; `render_page(path, index, dpi=200)` rasteriza una página
  (`src/documents.rs:176-199,221-276,279-343`).
- El motor público de preset es `VeloceOCR`; el predictor de tarea es `TaskPredictor`.
  Ambos aceptan `license_commercial_use` y `license_acknowledge`; sus constructores verifican
  el gate antes de crear el motor (`src/lib.rs:60-98,151-158`; `src/tasks/mod.rs:39-69`).
- `OcrResult` es la salida de texto y `StructureResult` conserva la estructura sin aplanar
  (`src/core/types.rs:391-419,482-509`). La extracción PDF ya produce `TextRegion` exactas
  (`src/documents.rs:241-273`).
- El default histórico de detección es 960/Max/4000 cuando los knobs son `None`
  (`DESIGN.md:1844-1851`; `pyocrust/__init__.pyi:320-342`). `full_page_tiling_boxes` genera
  geometría y `Tile::global_x/global_y` traslada coordenadas; ADR-009 mantiene el mosaico
  opt-in para no romper la geometría del pipeline general (`src/core/image_processor.rs:3-12,26-54,150-182`).

`VeloceOCR` y `TaskPredictor` conservan sus firmas y defaults actuales. La política nueva de
resolución sólo rige estas entradas nuevas y `Session`; no cambia el comportamiento de llamadas
existentes (`src/lib.rs:61-78`; `DESIGN.md:1844-1851`).

### 15.2 Firmas públicas nuevas

Tipos de apoyo (dataclasses congeladas, exportadas desde `pyocrust`; no modifican las salidas
nativas existentes):

```python
Resolution = Literal["default", "balanced", "native", "tiled"]
ImageOutput = OcrResult | StructureResult

@dataclass(frozen=True)
class PageRun:
    index: int                                  # 1-indexado
    source: Literal["text_layer", "ocr"]
    output: ImageOutput
    route_decision: RouteDecision | None        # sólo si auto_route y se ejecutó OCR
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class DocumentResult:
    pages: tuple[PageRun, ...]                  # orden de `pages` o del PDF
```

La firma completa del bloque de detección —idéntica en las entradas de imagen, documento y
sesión— es: `resolution: Resolution = "balanced"`, `tile_size: int | None = None`,
`tile_overlap: int | None = None` y estos escapes explícitos, todos `None` por defecto:

```python
text_det_limit_side_len: int | None = None,
text_det_limit_type: Literal["min", "max"] | None = None,
text_det_max_side_len: int | None = None,
text_det_thresh: float | None = None,
text_det_box_thresh: float | None = None,
text_det_unclip_ratio: float | None = None,
text_det_max_candidates: int | None = None,
```

Son los siete knobs que ya acepta `VeloceOCR`; los parámetros y sus límites existentes están en
`pyocrust/__init__.pyi:320-442` y `src/lib.rs:61-98,404-478`.

```python
def recognize_image(
    image: str | bytes | PathLike[str],
    *,
    task: TaskSpec | None = None,
    resolution: Resolution = "balanced",
    tile_size: int | None = None,
    tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None,
    text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None,
    text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None,
    device: str = "cpu",
    custom_path: str | None = None,
    license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> ImageOutput: ...

def recognize_document(
    path: str | PathLike[str],
    pages: Sequence[int] | None = None,
    *,
    task: TaskSpec | None = None,
    page_tasks: Mapping[int, TaskSpec] | None = None,
    auto_route: bool = False,
    probe: bool = False,
    dpi: int = 600,
    text_min_chars: int = 64,
    resolution: Resolution = "balanced",
    tile_size: int | None = None,
    tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None,
    text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None,
    text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None,
    device: str = "cpu",
    custom_path: str | None = None,
    license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> DocumentResult: ...

class Session:
    def __init__(
        self,
        *,
        device: str = "cpu",
        custom_path: str | None = None,
        resolution: Resolution = "balanced",
        tile_size: int | None = None,
        tile_overlap: int | None = None,
        text_det_limit_side_len: int | None = None,
        text_det_limit_type: Literal["min", "max"] | None = None,
        text_det_max_side_len: int | None = None,
        text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None,
        text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
        license_commercial_use: bool = True,
        license_acknowledge: bool = False,
    ) -> None: ...

    def __enter__(self) -> Session: ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...
    def recognize_image(self, image: str | bytes | PathLike[str], *, task: TaskSpec | None = None) -> ImageOutput: ...
    def iter_document_pages(
        self,
        path: str | PathLike[str],
        pages: Sequence[int] | None = None,
        *,
        task: TaskSpec | None = None,
        page_tasks: Mapping[int, TaskSpec] | None = None,
        auto_route: bool = False,
        probe: bool = False,
        dpi: int = 600,
        text_min_chars: int = 64,
    ) -> Iterator[PageRun]: ...
    def purge(self) -> None: ...

def available_features(
    *, license_commercial_use: bool = True, license_acknowledge: bool = False,
) -> list[str]: ...
```

`task` es intención estructurada (`TaskSpec`), no una cadena de features. `page_tasks` permite
asignar un flujo explícito distinto a cada índice 1-indexado. `auto_route=True` es excluyente
con `task` y `page_tasks`; sin `task`, se usa `TaskSpec()`. Si hay `page_tasks`, sus claves deben ser
páginas seleccionadas. `auto_route=True` calcula una decisión por cada página que necesita OCR;
`probe=True` añade la sonda de detección sólo en ese modo. `recognize_image` devuelve únicamente
la salida. La API existente `auto_recognize(image, ...)` conserva su retorno
`(salida, RouteDecision)` y sus flags de licencia (`pyocrust/multifeature.py:255-286`).

Los flags superiores de licencia `None` heredan los valores de `task` (o `TaskSpec()` si no se
pasa); un bool explícito sustituye ese campo. En `page_tasks`, la misma política superior se
aplica a cada `TaskSpec`. No se ignora ningún flag. `Session` fija ambos valores en su constructor;
los `TaskSpec` usados dentro deben declarar la misma política, o se rechazan con
`PyOcrValueError`. `available_features` devuelve IDs canónicos, ordenados, tomados de
`pipeline_profiles()` y filtrados con la misma regla declarada (`src/storage/catalog.rs:199-221`).

Errores observables:

| Condición | Error/aviso |
| :--- | :--- |
| Contenido no aceptado como PDF / imagen | `IncompatiblePdfError(PyOcrValueError)` / `IncompatibleImageError(PyOcrValueError)`; mensaje literal empieza «el contenido no es un PDF compatible» / «el contenido no es una imagen compatible». Son tipos nuevos, distintos entre sí. |
| Ruta inaccesible, PDFium/backend/modelo no disponible | `PyOcrRuntimeError` con causa; no se disfraza de incompatibilidad de contenido (`src/core/error.rs:176-199`; `src/documents.rs:163-174`). |
| `pages`, `page_tasks`, `dpi`, `text_min_chars`, enum/knobs inválidos; `tiled` con un flujo de estructura; `page_tasks` junto a `auto_route` | `PyOcrValueError`. `pages=None` conserva «todas» y los índices explícitos son 1-indexados, únicos y dentro de rango (`src/documents.rs:176-199`). |
| Licencia no permite cualquiera de las features requeridas por la corrida | `PyOcrValueError` antes de probe, raster, primera página o construcción de motor. |
| La asignación/reserva necesaria para cumplir la resolución solicitada falla | `ResolutionError(PyOcrRuntimeError)`; nunca degradación automática. El mensaje incluye dimensiones y opciones para recuperar (`resolution="balanced"`, `resolution="tiled"` o el `text_det_*` pertinente). |
| La detección reduce dimensiones respecto de la imagen de entrada | `warnings.warn(..., RuntimeWarning, stacklevel=2)` antes de inferir; el texto indica dimensiones antes/después y el flag exacto que evita/eleva el tope. En PDF se conserva además en `PageRun.warnings`. |

El tipo de origen se decide por contenido, no por sufijo: `recognize_image` valida los bytes con el
decodificador de imagen (`src/lib.rs:356-379`); `recognize_document` entrega el path al lector
PDFium (`src/documents.rs:163-174,221-233`). La extensión no participa. La superficie de PDF
acepta `str | PathLike[str]` (no bytes), acorde a las primitivas existentes (`src/documents.rs:325-343`).
Un PDF con nombre `.png` sigue siendo PDF para `recognize_document`; el mismo contenido pasado a
`recognize_image` produce `IncompatibleImageError`. Un PNG con nombre `.pdf` produce
`IncompatiblePdfError` en `recognize_document`. Fallos de lectura se mantienen como errores de
runtime, separados de «formato no compatible».

### 15.3 Resultado por entrada y recorrido por página

- Imagen: una salida de preset, nunca una lista de páginas ni un contenedor adicional. El tipo es
  `OcrResult` para `pp_ocrv6_<size>` (también con `resolution="tiled"`) o `StructureResult`
  para `pp_structurev3`; las recomendaciones de `PipelineChoice.tasks` no agregan salidas
  (`src/core/types.rs:391-419,482-509`; §15.7).
- PDF: `DocumentResult.pages` contiene un `PageRun` por página seleccionada, en orden de selección
  (`pages=None` equivale a todas). `source="text_layer"` lleva `OcrResult` con las regiones
  extraídas exactamente y no llama al OCR; ocurre incluso si el `TaskSpec` pide estructura. Para
  forzar el pipeline completo sobre esa página se usa `render_page` + `recognize_image`
  (`src/documents.rs:176-199,241-273`; §13.3 y §13.5).
- `source="ocr"` lleva `OcrResult` o `StructureResult`, según el único `choice.id` resuelto
  para esa página; en modo automático, `route_decision` de ese `PageRun` es la decisión de esa
  página, y en modo explícito es `None`. Una página no hereda la decisión de su vecina.
- `recognize_document` consume el iterador de `Session.iter_document_pages` y materializa el
  `DocumentResult`; la variante con estado deja que la persona consumidora obtenga cada `PageRun`
  sincrónicamente, llame otras utilidades de `pyocrust` entre páginas y luego solicite la siguiente.
  El iterador mantiene como máximo la página/raster activo; ni PDF, imágenes ni resultados se
  retienen en la caché del estado.

### 15.4 Política de resolución, aviso y mosaicos

`resolution="balanced"` es el default nuevo: una pasada de detección con `limit_type="min"`,
`limit_side_len=64` y `max_side_len=4000`, el comportamiento de pipeline declarado para Paddle.
No se activa tiling por defecto. El PDF usa `dpi=600` por defecto: `dpi` es el único mando de
render; la política de detección es independiente. A 600 dpi una A4 ronda 4960×7016 px
(§14.4); el render a alta resolución cuesta memoria, pero evita el default de 200 dpi
(§13.2, §13.6 y `src/documents.rs:306-319`).

| Valor | Semántica efectiva |
| :--- | :--- |
| `"default"` | Compatibilidad histórica: `960/Max/4000`; no es el default nuevo. |
| `"balanced"` | `min/64/4000`, compatible con el pipeline Paddle; puede reducir un lado mayor que 4000 y por ello avisa. |
| `"native"` | `min/64`; el `text_det_max_side_len` efectivo se fija al lado mayor real de la imagen/página. Sin tope artificial ni reducción automática; expone el coste de memoria/tiempo. |
| `"tiled"` | Opt-in, sólo OCR de texto: 2048 px por mosaico, solape 256 px (12,5%). Parámetros de calibración pendientes de medirse con el fixture de esquemáticos; 512/64 de ADR-009 no es el tamaño de contexto para detección. |

Los `text_det_*` explícitos sustituyen el valor correspondiente del modo elegido; no se aceptan
knobs reconocidos pero ignorados. Toda reducción efectiva, incluida una impuesta por un escape
`text_det_*`, emite `RuntimeWarning` con el nombre y valor del flag. En `balanced` sobre una página
mayor de 4000 se recomienda `resolution="native"` o un `text_det_max_side_len` suficiente; en
`default` la advertencia recomienda `resolution="balanced"` o `"native"`. `native` junto a un
`text_det_max_side_len` menor que el lado de entrada es contradictorio y se rechaza, no se
interpreta como permiso para recortar. La API no inventa un presupuesto global de memoria: valida
el cálculo de dimensiones y reserva los buffers requeridos antes de inferir; si no puede hacerlo,
lanza `ResolutionError` con el modo y los flags alternativos. No baja la resolución para evitar
ese error. El caso 7000×5000 necesita aproximadamente 100,1 MiB para una copia RGB8 de página,
antes de buffers del detector/ORT; el render PDF añade el bitmap y conversión descritos en
§13.6. Es un default deliberadamente más lento/costoso que 960.

En `"tiled"` se reutiliza la geometría de `full_page_tiling_boxes` y los offsets de
`Tile::global_x/global_y` (`src/core/image_processor.rs:26-53,150-182`). La ejecución de
extremo a extremo pertenece a Rust: la entrada normativa `VeloceOCR.recognize_tiled(...)`
recibe la imagen, `tile_size`, `tile_overlap` y los `text_det_*`; trocea, detecta con el
preset seleccionado, traslada las cajas a coordenadas globales, aplica la propiedad por
centro y reconoce los recortes nativos para recomponer un `OcrResult` global. `_run` delega
en esa entrada cuando `resolution="tiled"`; Python no recorre los mosaicos (§15.7). Este
símbolo es un contrato de diseño pendiente de implementación: el binding actual expone por
separado `recognize`, `detect_regions` y `recognize_regions`, sin una entrada tiled
(`pyocrust/__init__.pyi:403-417,435-442`; `src/lib.rs:230-243,272-339`).
La recomposición deduplica con una regla determinista de **propiedad por centro**: cada
detección global se conserva sólo si su centro cae en la zona de propiedad no solapada de
ese mosaico; los límites de propiedad particionan los solapes entre vecinos, con desempate
estable por índice de mosaico. No se usa IoU como decisión ambigua. El modo se rechaza para
`pp_structurev3`/salidas de layout, tabla o fórmula: ADR-009 mantiene el mosaico fuera del
pipeline general porque rompe la coherencia geométrica (`src/core/image_processor.rs:3-12`).
`tile_size` y `tile_overlap` sólo son válidos con `resolution="tiled"`; si se omiten, sus
efectivos son 2048/256, y se valida `0 <= tile_overlap < tile_size`.

### 15.5 Estado Python y vida de los modelos

`Session` sólo cachea runners/modelos. El constructor fija de manera inmutable `device`,
`custom_path`, política de resolución/knobs y flags de licencia. `__enter__` activa una sesión con
caché vacía; los motores se cargan perezosamente al primer uso. `iter_document_pages` procesa una
página por vez. La caché no incluye documentos, rasteres ni salidas; su clave separa al menos la
feature y los knobs efectivos. Así se elimina la reconstrucción por feature/llamada que hace hoy
`_run_features` sin caché (`pyocrust/multifeature.py:117-165`).

`purge()` libera todos los runners/modelos ya residentes y devuelve `None`; mantiene la sesión
abierta y reutilizable, de modo que la próxima operación vuelve a cargarlos. `__exit__` purga y
cierra aun si el bloque `with` sale con excepción. Usar métodos después de `__exit__` da
`PyOcrRuntimeError`. La sesión no es thread-safe; `purge()` y lecturas son síncronos y sólo se
invocan entre operaciones. Es el estado de modelos pedido, no un estado de documento o de cursor
compartido.

### 15.6 Licencia: preflight agregado y catálogo disponible

Antes de la primera sonda, raster o construcción de predictor, `_run` resuelve el plan
ejecutable completo. Para cada página que necesita OCR, la especificación efectiva es
`page_tasks[i]` si existe; en otro caso `task`, o `TaskSpec()` si tampoco se pasó `task`.
`resolve_pipeline` convierte esa especificación en un único perfil ejecutable, `choice.id`;
`PipelineChoice.tasks` son recomendaciones informativas y no se ejecutan ni se incluyen en el
preflight (`pyocrust/resolver.py:68-89,115-118`; §15.7). Con `auto_route=True`, el conjunto
incluye los perfiles candidatos del router y sólo incluye `text_detection` si se solicita
`probe=True`. Se valida el conjunto completo de páginas/candidatos antes de la primera sonda,
raster o construcción de predictor; si una licencia no permite un perfil ejecutable, la
corrida falla antes de cargar modelos. El contrato exige pasar los flags efectivos a cada
`VeloceOCR`/`TaskPredictor` que se ejecute, incluida la sonda; la ruta heredada `_probe` actual
no los recibe y su integración debe propagarlos (`pyocrust/multifeature.py:84-115,246-252`).
Sigue vigente el gate de licencia del constructor individual (`src/lib.rs:151-158`;
`src/tasks/mod.rs:52-69`). La licencia agregada mantiene *default-deny*: `Unknown` nunca permite
uso, el uso comercial requiere permiso y la atribución requerida exige aceptación
(`src/storage/license.rs:148-176,193-223`).

`available_features(license_commercial_use=True, license_acknowledge=False)` devuelve, sin
cargar modelos ni inferir, la lista ordenada de IDs de `pipeline_profiles()` cuyas filas permiten
la política declarada. Las filas ya exponen licencia, permiso comercial y aceptación de
atribución (`src/storage/catalog.rs:199-221`). El helper es informativo, no reemplaza el preflight:
si la política cambia entre consulta y corrida, la corrida vuelve a validar.

### 15.7 Convergencia: función Python → `run` → primitiva Rust

`_run` es el único núcleo privado: valida el plan completo/licencia, normaliza una página raster,
resuelve el runner y usa la caché opcional de `Session`. No se publica `run(source, ...)` ni una
firma polimórfica PDF/imagen.

La conversión normativa por página es: `page_tasks[i]` si la página tiene override; si no,
`task`; si tampoco existe, `TaskSpec()`. `resolve_pipeline` produce `PipelineChoice` y su
`id` es el único preset ejecutable de ese `TaskSpec`; `PipelineChoice.tasks` son recomendaciones
informativas, no una secuencia de `TaskPredictor`. `pp_ocrv6_<size>` produce `OcrResult` y
`pp_structurev3` produce `StructureResult`; `output_format` orienta la selección del perfil,
pero no transforma su salida (`pyocrust/resolver.py:40-50,97-118`; `src/lib.rs:230-243`).
`TaskPredictor.predict` no ejecuta `PipelineChoice.tasks`: la sonda opt-in de `auto_route` y las
features que la ruta heredada devuelve como tareas siguen siendo caminos de ejecución distintos
(`pyocrust/multifeature.py:246-286`; `pyocrust/resolver.py:68-89`).

| Función Python | Plan ejecutable | Núcleo `_run` | Primitiva Rust |
| :--- | :--- | :--- | :--- |
| `recognize_image(image, task=...)` | resuelve `task` (o `TaskSpec()`) a `choice.id`; excluye `choice.tasks` | `_run(image, plan, settings, cache=None)` | `VeloceOCR.recognize` para `balanced`/`native`; `VeloceOCR.recognize_tiled` para `tiled` (entrada Rust de diseño; devuelve `OcrResult`). (`src/lib.rs:230-243`; tiled: §15.4). |
| `auto_recognize(image, ...)` existente | conserva su plan/decisión del router | preflight → sonda opcional → `route` → `_run` | `TaskPredictor.predict` para la sonda solicitada; `VeloceOCR.recognize`/`TaskPredictor.predict` según la ruta existente (`pyocrust/multifeature.py:246-286`; `src/tasks/mod.rs:240-245`). |
| `recognize_document(path, ...)` | si `auto_route`: perfiles candidatos/ruta por página; si no: `page_tasks[i]` > `task` > `TaskSpec()`; text-layer no ejecuta pipeline | parsea/preflight; crea `PageRun` para cada página | `parse_document`; páginas OCR: `render_page` → `_run` → `VeloceOCR.recognize` o, en tiled, `VeloceOCR.recognize_tiled`; resultado por preset (`src/documents.rs:221-343`; §15.3). |
| `Session.recognize_image` | mismo `choice.id` que la llamada sin estado | `_run(..., cache=session._runners)` | mismas entradas Rust; en tiled, `VeloceOCR.recognize_tiled`. |
| `Session.iter_document_pages` | mismo override por página y exclusión de recomendaciones | preflight una vez; avanza `_run` por página con `cache=session._runners` | mismas primitivas PDF/imagen; en tiled, entrada Rust end-to-end con geometría reutilizada. |
| `available_features(...)` | no crea plan ni carga modelo | consulta pura del catálogo y filtro de licencia | `pipeline_profiles()` (sin `VeloceOCR`, `TaskPredictor`, render ni inferencia; `src/storage/catalog.rs:199-221`). |

El flujo PDF no comparte una salida universal: el documento agrega `PageRun`, pero cada `output`
conserva el esquema del pipeline elegido para esa página. Así el contrato público impone tipo de
origen, cardinalidad y errores distinguibles, mientras imagen y PDF convergen únicamente después
de validar su contenido.