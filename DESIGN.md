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
