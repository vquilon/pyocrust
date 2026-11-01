# Documento de Diseño de Arquitectura: Wrapper Multidisciplinar OCR en Rust
# Sistema: pyocrust (antes `ocr_rust_bridge`)

> **Estado del documento:** contrato de diseño de la versión 1, **reconciliado con
> el árbol real en `D1` y `D2` (2026-10-25)**. Validado por el dictamen de arquitectura de
> la tarjeta `A1` (veredicto: **CAMBIOS OBLIGATORIOS**) y contrastado con las
> fuentes de `oar-ocr` `0.10.1` y con la intención de producto de `DECISIONS.md`.
> Toda decisión impuesta por `A1` queda registrada como ADR numerado en §4.
>
> **Aviso de estado del proyecto (D1, 2026-10-25; actualizado en `D2`, 2026-10-25):**
> el sign-off final (`S1`, tarjeta `t_d005409b`) sigue **RECHAZADO**. El código que
> describe este documento existe, compila y pasa sus tests; `S1` impuso **7
> condiciones**, de las que quedan **6 abiertas** (§9.2): `S1.2` la cerró el commit
> `b128566` (`t_ab6ff8d0`, ver §9.1). Este documento describe el estado **real**, no
> el deseado: cada ADR lleva su estado de cumplimiento verificado en §9.1.

## 1. Objetivo General

Diseñar y desarrollar un wrapper nativo en Rust utilizando **PyO3** y **Maturin** que encapsule librerías de reconocimiento de caracteres (OCR) y fórmulas matemáticas del ecosistema de Rust (partiendo de `oar-ocr`). El paquete final debe ser unificado, multiplataforma, altamente eficiente en el manejo de memoria/hilos, con soporte dinámico para GPU/CPU y capaz de integrarse de forma transparente en un software existente en Python.

### 1.1 Alcance de la versión 1

| Ámbito | Entra en v1 | Fuera de v1 (hito posterior) |
| :--- | :--- | :--- |
| Texto (OCR) | PP-OCRv6 en tamaños `Tiny`, `Small`, `Medium` vía `OAROCRBuilder` | PP-OCRv4 y PP-OCRv5 |
| Estructura | PP-StructureV3 vía `OARStructureBuilder`: layout, tablas (HTML) y fórmulas (LaTeX). **Estado real (`D2`, commit `b128566`):** el backend carga los 9 artefactos y `recognize` **no aplana**: devuelve el Markdown del documento (tablas HTML + fórmulas LaTeX), los elementos de layout (`LayoutRegion`) y las regiones OCR, y todo ello cruza a Python (ADR-003 **cumplido**) | — |
| Motor de inferencia | **ONNX Runtime** exclusivamente | **Candle** y `oar-ocr-vl` (VLM ~0.9B), pospuestos a v2 (ADR-001) |
| Distribución de modelos | `auto-download` (ModelScope → `$OAR_HOME`) + descargador Hugging Face resiliente (ADR-007). **Estado real (D1):** el descargador está implementado pero no conectado al pipeline (§9.1 ADR-007) | otros repositorios |
| Plataforma de ejecución | CPU y GPU (features `cuda`, `directml`), Python 3.10+ (abi3) | `tensorrt`, `openvino`, `coreml`, `webgpu` |

`oar-ocr` `0.10.1` cubre además PP-OCRv4/v5, UniMERNet y PP-FormulaNet (fórmulas), SLANet/SLANet+/SLANeXt + RT-DETR (tablas), PP-DocLayoutV2/V3 (layout) y PP-LCNet/UVDoc (orientación y rectificación). El árbol actual expone tres familias de presets: `pp_ocrv6*`, `pp_structurev3` e `indra`; `S2.2` sigue parcial (§3.1.1).

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
│   │   │                       # enums OcrTask, OcrSize, ModelSpec y el enum Rust OcrOutput; struct ModelPaths
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
│   ├── hardware.py             # Inventario físico y dataclasses GPU/RAM (S3.1)
│   ├── resolver.py             # TaskSpec, PipelineChoice, resolve_pipeline (S3.1)
│   └── py.typed                # Marcador PEP 561
└── tests/
    ├── conftest.py             # Utilidades comunes: PNG sintético con la stdlib y localización
    │                           # de los modelos reales en disco
    ├── test_config.py          # Niveles de prioridad en la resolución de rutas
    ├── test_tiling.py          # Troceado con solapamiento
    ├── test_recognize.py       # recognize end-to-end (carga directa, env var y caché)
    ├── test_indra.py           # Smoke Indra (S2.2)
    └── data/sample_text.png    # Imagen real de dos líneas para los tests de reconocimiento
```

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

### 3.1.1 Contrato actual de Indra (`S2.2`, parcial)

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
  size_bytes: int | None, env_vars: list[str]}`. Incluye el registro upstream
  y companions Indra; `params=None` siempre, tamaño desde `find(name)` para
  upstream y `None` para Indra (no sustituido por los tamaños HF de storage).
  `env_vars`: `OAR_HOME`, `OCR_MODELS_CACHE_DIR`, `PYOCRUST_OFFLINE`,
  `CUDA_LAUNCH_BLOCKING`, `RUST_LOG`; no promete controles `OAR_VL_*` para Indra ONNX.
* `pipeline_profiles() -> dict[str, dict]`, indexado por ID:
  `{id: str, family: str, quality: str, output_format: str,
  disk_bytes: int | None, ram_bytes: int | None, artifacts: list[str], description: str}`.
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

### 3.1.4 API pública: dos superficies (`S2.3`-`S2.6`)

`pyocrust` expone dos superficies de inferencia, además de las consultas de
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
inferencia.

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

*Comportamiento de descarga:* la v1 tenía previstos **dos** caminos: (1) `auto-download` de `oar-ocr` desde ModelScope hacia `$OAR_HOME`; (2) descargador propio desde Hugging Face cuando ModelScope no es alcanzable o el entorno es corporativo/offline, con el contrato de §7.3. Si el fichero existe y su tamaño/hash es correcto, **no** se hace ninguna petición de red.

> **Estado real (D1).** Solo el camino (1) está activo: `oar-ocr` trae
> `auto-download` (`Cargo.toml:20`) y es quien descarga cuando falta un artefacto.
> El camino (2) está **implementado y testeado** (`src/storage/download.rs`) pero
> **no se invoca en runtime**: no hay ninguna llamada a `fetch` en `src/lib.rs` ni
> en `src/engines/`. ADR-007 queda **parcial** (§9.1) y es el defecto que `S1`
> marcó como condición 4.

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
| `rayon` | Declarado en `Cargo.toml:26` pero **sin uso** en `src/`: aún no existe el bucle de preprocesamiento que paralelizar (ADR-008, parcial) |

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
* **Estado (D1, 2026-10-25).** **Parcial.** `rayon` está declarado (`Cargo.toml:26`) pero **no se usa** en `src/`: aún no existe el bucle de preprocesamiento que debía acotarse. No es hoy un defecto funcional (la regla se respeta por ausencia de uso), pero la dependencia es peso muerto.

### ADR-009: preprocesamiento — escalado nativo por defecto, tiling opt-in

* **Contexto.** `DECISIONS.md` §5 exige `FullPageTiling` con mosaicos de 512x512 y solapamiento de 64px para no truncar fórmulas en las líneas de corte. `A1` lo declaró contraproducente para el pipeline general: trocear rompe la relación de aspecto y la coherencia geométrica que esperan los modelos de layout y tablas, que ya escalan con `limit_side_len`.
* **Decisión.** El pipeline general aplica `ScaleDown` (escalado nativo de `oar-ocr`). `FullPageTiling` se conserva como **función pura opt-in** sobre `image::RgbImage`, sin I/O y sin conocer `oar-ocr`, con solapamiento configurable (64px por defecto) y test propio (tarjeta `I2`).
* **Consecuencias.** Nadie pierde la herramienta; se pierde solo el troceado forzado. Una imagen menor que un mosaico produce un único mosaico, y un solapamiento mayor o igual al tamaño del mosaico debe rechazarse con error, no producir un bucle degenerado (criterio que verifica `C1`).
* **Coste (respuesta a `DECISIONS.md` §5).** El usuario que necesite troceado debe invocarlo explícitamente.
* **Estado (D1, 2026-10-25).** Cumplido **con defecto**: las funciones puras y el rechazo de `overlap >= tile_size` están implementados y testeados, pero el adaptador PyO3 materializa los mosaicos que descarta (`S1.1`, bloqueante; §3.4).

### ADR-010: dependencias y features de `Cargo.toml`

* **Contexto.** Alternativas: reimplementar lo que `oar-ocr` ya hace, o apoyarse en sus features.
* **Decisión.** Dependencias: `pyo3` con `extension-module` y `abi3-py310`; `oar-ocr` `0.10.1` con `auto-download` y `simd`, y `cuda`/`directml` como features opcionales; `image`; `rayon` (ADR-008); `reqwest` con `stream` y TLS (ADR-007); `sha2` para el SHA-256 del descargador. `[profile.release]` con `panic = "unwind"` (ADR-004).
* **Consecuencias.** El binario por defecto es CPU; la GPU se activa compilando con `--features cuda` o `--features directml`.
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

## 5. Riesgos Conocidos

| Id | Riesgo | Impacto | Mitigación | Estado (D1) |
| :--- | :--- | :--- | :--- | :--- |
| R1 | La firma exacta de `OARStructureBuilder` en `0.10.1` difiere de la documentada (docstring antiguo con firmas de dos parámetros frente a métodos específicos) | `src/engines/oar_structure.rs` no compila | Contrastar la API real del crate antes de escribir el adaptador; documentar la desviación | **Cerrado.** API real contrastada y usada (`src/engines/oar_structure.rs:130-137`, §3.1) |
| R2 | ModelScope inalcanzable (firewall corporativo, CI) | Sin modelos no hay inferencia | Descargador HF de ADR-007; bypass de red si el modelo ya está en disco | **Parcial.** El descargador HF existe pero no está conectado; hoy solo actúa `auto-download` |
| R3 | Peso de PP-StructureV3 (9 artefactos) y VRAM en GPU de 16 GB | Fallo de carga o OOM | Caché en `$OAR_HOME`; presets `Tiny`/`Small` para texto | Abierto |
| R4 | `maturin` no está instalado en el intérprete activo | No se puede construir el paquete | `pip install maturin` antes de `maturin develop` | **Cerrado.** `maturin` instalado en `.venv`; `maturin develop` ejecutado |
| R5 | Acoplamiento circular entre `config.rs` (rutas) y `download.rs` (descarga) | Módulos difíciles de testear | `download.rs` recibe rutas ya resueltas; no consulta el entorno | Cumplido: `fetch(url, dest, sha256_hex)` no lee variables de entorno |
| R6 | `pyapi::full_page_tiling` materializa y descarta los mosaicos | OOM con `overlap` alto | Reducir el adaptador a puro cálculo de geometría | **Abierto** (`S1.1`, bloqueante) |
| R7 | `OAR_HOME` relativa no se reexporta absoluta | La autodescarga de `oar-ocr` falla | Rechazar la relativa o reexportar la normalizada | **Cerrado (`c30a3a9`):** se reexporta absoluta (`src/storage/config.rs:115-126,144-155`) |

## 6. Estado Actual

Actualizado en `D1` (2026-10-25) leyendo el árbol real y el board `pyocrust`.

| Elemento | Estado | Evidencia |
| :--- | :--- | :--- |
| `DESIGN.md` | Reconciliado en `D1` | Este documento |
| `PLANNING.md` | Reconciliado en `D1` | Mapea cada tarea a su tarjeta con estado real |
| Crate `pyocrust_core` | Existe y compila | `Cargo.toml`, `src/**`; `cargo test` = **36/36 OK** (recuento de `S1`) |
| Paquete `pyocrust` | Existe e importa | `pyocrust/__init__.py`; `maturin develop` ejecutado (`pyocrust/_pyocrust_core.pyd`) |
| Suite de integración (Python) | **31 pasados, 2 `skip`, 1 `xfail`** | `pytest tests/ -q` — recuento de `S1` |
| Sign-off `S1` | **RECHAZADO**, 7 condiciones (`S1.2`/`S1.3`/`S1.5` cerradas) | §9.2 |
| ADR cumplidos | **10 de 12** (uno con defecto), 2 parciales | §9.1 |

Lo que este documento **no** sabe:

* el contenido del árbol de `oar-ocr` `0.10.1` no está descargado en el host: las citas internas de §3 y §4 atribuidas a `A1` siguen siendo de segunda mano;
* **no** se ha medido rendimiento real de ningún pipeline (no hay benchmark);
* la verificación de los defectos abiertos de §9.2 es la de `S1`/`C1`, no una re-ejecución propia de `D1`.

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

> **Desviación (D1), corregida (`D2`, `b128566`).** El preflight está implementado y
> **conectado**: `VeloceOCR::new` invoca `preflight_paths(&paths).ensure_ready()`
> (`src/lib.rs:60`) antes de crear el motor, así que ante modelos ausentes el usuario
> recibe `MissingModelArtifacts` con la lista de ficheros. De `S1.4` queda abierta
> solo la conexión del descargador (§7.3).

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

> **Desviación (D1), vigente en `D2`.** `fetch` no se llama desde ninguna ruta de
> ejecución (`src/lib.rs`, `src/engines/`): el módulo es código muerto en runtime. El
> bypass offline y la verificación no protegen hoy ninguna descarga real porque es
> `oar-ocr` quien descarga. ADR-007 **parcial**; la mitad del descargador de `S1.4`
> sigue abierta (el preflight sí se conectó, §7.2).

## 8. Notas de Evolución

* **v2 — Candle y `oar-ocr-vl`.** Entrarán bajo una feature opcional `vl`, nunca por defecto: requieren CUDA Toolkit completo y kernels de Flash Attention, que multiplican el tiempo de compilación (ADR-001).
* **v2 — paralelismo inter-página.** Solo si una medición lo justifica, y siempre con `intra_threads = 1` para no pelearse con el pool intra-op de ORT (ADR-008).
* **Features de aceleración adicionales.** `tensorrt`, `openvino`, `coreml` y `webgpu` existen en `oar-ocr`; se añaden cuando haya un objetivo de despliegue que los pida, no antes.
* **Gestión explícita de VRAM.** Si la liberación por RAII resulta insuficiente en producción, el camino es un `close()`/context manager que suelte el último `Arc`, **no** un `Drop` manual con llamadas a CUDA (ADR-005).
* **Cierre de las condiciones de `S1`.** `S1.2` (`b128566`) y `S1.3` y `S1.5` (`c30a3a9`) quedaron cerradas; siguen abiertas `S1.1` (pendiente) y `S1.4`/`S1.6` (parciales). Son código, no documentación, y necesitan tarjeta propia.

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
| ADR-007 | Descargador HF resiliente | **Parcial** | `src/storage/download.rs:99-196` cumple el contrato, pero `fetch` no se llama en runtime |
| ADR-008 | `rayon` solo en preprocesamiento CPU | **Parcial** | `rayon` en `Cargo.toml:26`, sin uso en `src/` |
| ADR-009 | Tiling opt-in | Cumplido con defecto | `src/core/image_processor.rs:147-185`; adaptador con defecto de memoria (`S1.1`) |
| ADR-010 | Dependencias y features | Cumplido | `Cargo.toml:13-36,45` |
| ADR-011 | Nomenclatura | Cumplido | `pyproject.toml:23`; `src/lib.rs:106` |
| ADR-012 | Sesiones con `Arc`, sin `Drop` | Cumplido | `src/engines/oar_text.rs:50`; `src/engines/oar_structure.rs:32` |

### 9.2 Condiciones abiertas del sign-off `S1` (tarjeta `t_d005409b`, RECHAZADO)

`S1` cerró como **RECHAZADO** con 7 condiciones (comentario del 2026-10-25). Estado a día de `D2`:

| Id | Condición | Gravedad | Estado | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| S1.1 | `pyapi::full_page_tiling` materializa los mosaicos y los descarta (OOM con `overlap` alto) | Bloqueante | **Pendiente** | `src/core/image_processor.rs:229-249` |
| S1.2 | `StructureResult` (ADR-003) no existía ni cruzaba a Python | Bloqueante | **Cerrada (`D2`, `b128566`)** | `src/core/types.rs:400-409`; `src/engines/oar_structure.rs:148-171` |
| S1.3 | `PyOcrValueError`/`PyOcrRuntimeError` no heredan de `PyOcrError` | Mayor | **Cerrada (`c30a3a9`)** | `src/core/error.rs:147-149` (base `PyOcrError`) |
| S1.4 | `VeloceOCR::new` no ejecuta el preflight (ni el descargador) | Mayor | **Parcial (`D2`)** | `src/lib.rs:58-62` (preflight sí, descargador no) |
| S1.5 | `OAR_HOME` relativa rompe la autodescarga de `oar-ocr` | Mayor | **Cerrada (`c30a3a9`)** | `src/storage/config.rs:115-126,144-155` |
| S1.6 | `VeloceOCR::new` retiene el GIL durante la carga | Menor | **Parcial (`D2`)** | `src/lib.rs:35-65` (el motor se crea con `py.detach`, `:62`) |
| S1.7 | Retirar de `DESIGN.md` las capacidades de VRAM inexistentes | Menor | **Hecho en `D1`** | §3.3 y ADR-005 corregidos |

`S1.2` la cerró el código de `t_ab6ff8d0` (`b128566`) y `S1.3`/`S1.5`, el de `c30a3a9`. Las restantes (`S1.1`, `S1.4`, `S1.6`) son trabajo de código y **no** se abordan en esta tarjeta (`D2` no escribe código). Requieren tarjeta propia con el perfil que decida `arquitecto`.

> **Nota de `D2` sobre las demás condiciones.** Mientras `D2` corría aterrizó el commit `c30a3a9`
> (`S1.3`-`S1.6`), que cierra la jerarquía de excepciones (`src/core/error.rs:147-149`) y la
> reexportación absoluta de `OAR_HOME` (`src/storage/config.rs:115-126,144-155`); el mismo árbol trae ya
> el preflight conectado (`src/lib.rs:60`, de `b128566`) y el GIL liberado al crear el motor
> (`src/lib.rs:62`). `S1.4` y `S1.6` quedan **parciales** (descargador sin conectar; rutas y preflight
> retienen el GIL) y debe re-verificarlas quien las posee.

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
| Estado del proyecto | §1.1/§6 sin sign-off | `S1` RECHAZADO con 7 condiciones | §6 y §9.2 |
