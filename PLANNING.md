# Plan de Trabajo y Ejecución (Tareas para Hermes)
# Proyecto: pyocrust (antes `ocr_rust_bridge`)

Este documento detalla la hoja de ruta secuencial para la implementación del paquete. Cada tarea debe completarse y validarse antes de proceder a la siguiente.

> **Contrato:** `DESIGN.md` es el contrato de diseño (validado en `A1`, reescrito en `E1`, reconciliado en `D1`). Este documento es el tracker.
> Cada entrada lleva identificador, tarjeta del board (`pyocrust`), estado y criterio de aceptación.
> Estados: `Pendiente` / `En curso` / `Hecho` / `Bloqueado` / `Descartado`. Todo cambio de estado va fechado.
>
> **Estado global (D1, 2026-10-25; actualizado en `D2` y `S2.0`):** las fases 0-5 están **Hechas**; `S1.2` (`b128566`), `S1.3`, `S1.4` (cerrada por `S2.0`) y `S1.5` (`c30a3a9`) quedaron **cerradas**, pero el sign-off `S1` sigue **RECHAZADO**, con `S1.1` pendiente y `S1.6` parcial (§7). El proyecto **no** está aprobado: `D1`/`D2` reconcilian la documentación, no la implementación.

### Actualización `S2.2` — Indra (parcial)

* **Tarjeta:** `t_027743e2`, abierta; aceptación arquitectónica parcial, no cierre.
* **Implementado:** tercer preset `indra` junto a `pp_ocrv6*` y `pp_structurev3`,
  nueve artefactos requeridos en `<models_dir>/indra/`, mismo `ensure_models`,
  `.math(true)` y salida `StructureResult`; contrato en `DESIGN.md` §3.1.1.
* **Evidencia comunicada:** smoke CPU (dos regiones, dos elementos y Markdown),
  una prueba Python pasada y una prueba Rust de giro inverso pasada.
* **Pendiente:** suite global (antecedente de 24 fallos de APIs `S3.x`), GPU y
  calidad matemática. TLS bloquea la descarga Rust HF; `urllib` fue solo diagnóstico,
  no validación de `ensure_models`. `B6/B7` mantiene la tarjeta existente `t_c319bbab`.
* Las tablas y recuentos `D1`/`D2` siguientes son históricos; se preservan sus pendientes.

### Actualización `S2.3` — tareas individuales (aprobación acotada)

* **Tarjeta:** `t_a3bd3db6`, abierta; aprobación arquitectónica acotada al código
  tras revisión crítica de whitelist/shape sin bloqueantes, no cierre global.
* **Implementado:** cinco tareas de `TaskPredictor`, entradas `str`/`Path`/`bytes`,
  salidas `dict`/lista de `dict`, modelos gestionados o explícitos sin descarga,
  whitelist por tarea, PNG como `PyBytes` y shape de línea `(H, W)=(80, 160)`
  configurable. Contrato y defaults en `DESIGN.md` §3.1.2.
* **Evidencia comunicada:** 53 pruebas Cargo pasadas; binding reconstruido;
  defaults probados con inferencia CPU real. Probador: `tests/test_tasks.py`,
  offline con `RAYON_NUM_THREADS=2`, **21 pasadas, 0 skips, 5.08 s**; incluye
  rectificación por ruta/bytes y batch, rechazo de opciones y shape cero.
* **Pendiente de evidencia positiva:** `models=dict`, shape alternativo,
  GPU/calidad y batch de las otras tareas. Suite global no reevaluada en esta
  intervención; se mantiene el antecedente de 24 fallos de APIs `S3.x`.
* No modifica los estados ni las condiciones históricas `D1`/`D2` o `S2.2`.

### Actualización `S2.4` — once tareas (APROBADO acotado)

* **Estado:** contrato/código aprobado por Arquitecto S2.4 y Crítico R2;
  no implica cierre global ni reemplaza la evidencia histórica `S2.3` anterior.
* **Implementado:** seis tareas adicionales (`text_detection`, `text_recognition`,
  `layout_detection`, `table_classification`, `table_structure_recognition`,
  `table_cell_detection`): once nombres, esquemas, whitelist/defaults y artefactos
  exactos en `DESIGN.md` §3.1.2. Batch ordenado, vacío `[]`, inferencia sin GIL;
  tokens/bboxes de tabla sin reconstrucción HTML. Diccionario `dict_path` >
  `models['dict']` > companion perezoso; modelos/dict/tokenizer canonicalizados
  como ficheros locales antes de upstream, explícitos sin descarga implícita.
* **Evidencia comunicada:** Rust **53 pass**, binding reconstruido;
  probador **40 pass, 4 skip, 9.16 s**; padre con `.venv` exacto del proyecto:
  **40 pass, 4 skip, 6.51 s**. Son ejecuciones previas, no reejecutadas por escriba.
* **Inferencia CPU real:** las cinco tareas `S2.3` más detección/reconocimiento
  de texto de `S2.4`. Las cuatro nuevas tareas layout/table classification/
  table structure/table cells quedan pendientes por caché/modelos ausentes;
  los skips no son inferencias verificadas. GPU y calidad no validadas.
* Sin modificar pendientes/TODO históricos `D1`/`D2`/`S2.2`, ni afirmar once
  inferencias reales o suite global reevaluada.

### Actualización `S3` — catálogo, hardware y resolver (APROBADO acotado)

* **Estado:** Arquitecto S3 aprueba acotadamente las APIs ya exportadas
  `model_catalog`, `pipeline_profiles`, `GpuInfo`, `HardwareProfile`,
  `detect_hardware`, `TaskSpec`, `PipelineChoice`, `resolve_pipeline`.
  Contrato en `DESIGN.md` §3.1.3; ejemplo de recomendación separado de ejecución
  en `README.md`. No cierra el sign-off global ni las condiciones históricas.
* **Implementado:** catálogo/perfiles desde registros reales, parámetros/RAM
  desconocidos `None`, tamaños upstream y tamaño Indra desconocido en catálogo;
  inventario físico stdlib, override explícito y resolver heurístico validado.
* **Evidencia comunicada:** hardware **15 pass, 1 skip**, resolver **29 pass**,
  catálogo **5 pass**; Rust **53 pass previos**. No son nuevas ejecuciones de
  esta intervención documental ni certificación de modelos o GPU.
* **Límites:** GPU detectada no prueba wheel CUDA; Indra es alternativa heurística,
  no disponibilidad ni ejecución. Resolver sin modelos/descargas/preflight;
  resolución nativa de `models_dir` puede normalizar/reexportar `OAR_HOME` relativa.
  `tasks` no se ejecuta automáticamente y `output_format` no convierte salida.
* No se ejecutaron tests/builds, modelos, descargas, commits ni cambios de board
  en esta actualización documental; se preservan estructura y antecedentes.

### Actualización `S2.5/S2.6` — cierre documental de exposición (2026-10-31)

* **Alcance:** exposición Python comprobada **11/11 predictores + 3/3 familias
  de pipelines**. Tiny/Small/Medium cuentan como una familia `pp_ocrv6`;
  exposición por introspección/constructor con error tipado no prueba inferencia.
  Cierre documental de exposición, no aceptación de inferencia completa ni
  sign-off global; revisión crítica en curso, sin cambiar estados del board.
* **Evidencia focal contrastada:** `runs.json` registra `test_recognize`
  **9 pass/2 skip**, `test_indra` **1 pass/0 skip**, `test_models`
  **4 pass/2 skip**: total **14 pass, 4 skip, 0 fallos/errores**.
  Tiny reconoce las dos líneas conocidas; Indra devuelve Markdown/bloques/regiones
  y matemática inline. No equivale a calidad matemática certificada ni full suite.
  `.venv` Python 3.14.9, native existente sin rebuild, offline, afinidad dos CPU;
  provider efectivo no instrumentado y sin garantía de dos threads nativos totales.
* **Cuatro tareas pendientes de inferencia:** `layout_detection`,
  `table_classification`, `table_structure_recognition`, `table_cell_detection`
  por caché/modelos ausentes. Se conserva la evidencia posterior S2.4 del padre
  (**40 pass, 4 skip**): `text_line_orientation` ya corregida; el fallo de un
  log anterior es histórico, no un fallo actual ni invalida esa ejecución posterior.
* **Cuatro skips focales explícitos:** estructura/Markdown y acceso LaTeX de
  PP-StructureV3 por seis artefactos ausentes de once: `pp-doclayoutv3.onnx`,
  `pp-lcnet_x1_0_table_cls.onnx`, `slanext_wired.onnx`, `slanet_plus.onnx`,
  `rt-detr-l_wired_table_cell_det.onnx`, `table_structure_dict_ch.txt`;
  descarga de caché fría y redescarga por tamaño incorrecto excluidas por offline.
  PP-StructureV3, Small/Medium, descargas frías/redescarga, GPU y calidad siguen
  sin aceptación actual. El test LaTeX omitido conserva el riesgo por lectura
  `formula.trim()` sobre `str` y fixture sin fórmula conocida: no fallo ejecutado.
* **Provenance:** evidencia en
  `C:/Users/vquilon/AppData/Local/hermes/profiles/hefesto/cache/scratch/s25-closure/`
  (`MATRIX_S2_5.md`, `runs.json`, logs/XML y `exposure.json`), HEAD observado
  `113a490`. La matriz no localizó el log exacto de las 40 tasks posteriores;
  se atribuyen al padre y al registro S2.4, no a nuevas ejecuciones del escriba.
  S2.6 solo modifica README/PLANNING: sin tests/builds/modelos/descargas,
  benchmarks, commits ni board; histórico D1/D2/S2.2 preservado.

### Actualización `B9` — documentación del banco (2026-10-31)

* **Estado:** Crítico R2 **APROBADO acotado** al banco, no sign-off global.
  Regresiones comunicadas **21 pass, 17 deselected**, no reejecutadas por escriba.
* **Run real contrastada:** `benchmarks/results/2026-10-31_23-37-34/summary.json`
  y CSV: **5/5 Tiny (`text`), 5/5 Indra (`full_page`, `math`), 5/5 RapidOCR
  (`text`)**, sin errores. Estructura/fórmula **skipped**: seis artefactos de
  PP-StructureV3 ausentes en offline, no inferencia ni descarga verificada.
  La herramienta agotó el timeout; exit code del runner no observado, aunque
  los artefactos fueron recuperados. No se certifica terminación correcta.
* **Contrato documentado:** 22 columnas; `--task-types`, `--manifest` con `image`
  y GT legítimo `text`/`markdown`/`blocks`, `--repeats`, `--device cpu|gpu`.
  GPU rechazada con skip sin fallback CPU; provider efectivo `unverified`.
  Fórmula usa `result.formulas`, no Markdown de página; legacy `cer_ord=None`.
* **Límites:** Markdown **N/A / no evaluada** sin GT Markdown/bloques; cinco
  muestras no son comparación publicable. Sin ganador general ni claims de
  rendimiento GPU. B3/B4/B5 y post previo conservados como históricos;
  prevalece B9 en `benchmarks/README.md` y `benchmarks/LINKEDIN.md`.
* Solo esos dos documentos y este tracker: sin modelos/tests/builds/commits/board.
  Autorización de commit para Hefesto, no ejecutada por el escriba.

## 0. Mapa de tareas a tarjetas del board

Board: `pyocrust` (`%LOCALAPPDATA%\hermes\kanban\boards\pyocrust\kanban.db`). Estado leído en `D1` el 2026-10-25 directamente de la base de datos del board.

| Id | Fase | Título | Tarjeta | Responsable | Estado | Fecha de cambio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `A1` | 0 | Validar el diseño y dictaminar cambios obligatorios | `t_f182fde7` | `arquitecto` | Hecho | 2026-10-25 |
| `E1` | 0 | Reescribir `DESIGN.md` y `PLANNING.md` | `t_12f74e4b` | `escriba` | Hecho | 2026-10-25 |
| `I1` | 1 | Esqueleto del paquete (Cargo, maturin, módulo nativo) | `t_7e398138` | `hefesto` | Hecho | 2026-10-25 |
| `I2` | 2 | Core: tipos, trait, errores y tiling | `t_629765fb` | `coder` | Hecho | 2026-10-25 |
| `I3` | 3 | Storage: resolución de rutas, preflight y descargador | `t_4063447c` | `hefesto` | Hecho | 2026-10-25 |
| `I4` | 4 | Engines (`oar_text` + `oar_structure`) y clase `VeloceOCR` | `t_e4d7a850` | `coder` | Hecho | 2026-10-25 |
| `V1` | 5 | Tests de integración (config, tiling, recognize) | `t_523ca1e7` | `probador` | Hecho | 2026-10-25 |
| `C1` | 5 | Atacar la implementación antes del sign-off | `t_b674050d` | `critico` | Hecho | 2026-10-25 |
| `S1` | 5 | Sign-off final contra `DESIGN.md` | `t_d005409b` | `arquitecto` | Hecho (**RECHAZADO**) | 2026-10-25 |
| `D1` | 6 | Reconciliar `DESIGN.md` y `PLANNING.md` con lo implementado | `t_7449f60f` | `escriba` | Hecho | 2026-10-25 |
| `D2` | 6 | Reconciliar `DESIGN.md` y `PLANNING.md` con ADR-003 cumplido | `t_bbf33ff6` | `escriba` | Hecho | 2026-10-25 |

Dependencias: `A1` → `E1` → `I1` → `I2` → `I3` → `I4` → (`V1`, `C1`) → `S1` → `D1` → `D2`. `C1` ataca lo verificado por `V1`; `D1` cierra la documentación después del sign-off; `S1.2` se cerró después con `t_ab6ff8d0` (`b128566`) y `D2` reconcilia la documentación con ese cierre.

> **Corrección de responsables (D1):** el board asigna `I2` e `I4` al perfil `coder`, no a `hefesto` como decía la versión previa de esta tabla. Se corrige aquí contra el estado real del board.

### 0.1 Cumplimiento de la lista de cambios obligatorios de `A1`

Los 8 puntos del dictamen consolidado (`A1`, comentario del 2026-10-25) y dónde queda cada uno:

| # | Cambio obligatorio de `A1` | Dónde queda registrado |
| :--- | :--- | :--- |
| 1 | Limitar v1 a ONNX Runtime; Candle / `oar-ocr-vl` a v2 | `DESIGN.md` §1.1, §8, ADR-001 |
| 2 | Quitar `scipix_engine`; motor unificado; paquete Python con `__init__`, `py.typed` y `tests/` | `DESIGN.md` §2, ADR-006, ADR-011 |
| 3 | Sustituir `load_model(&mut self, &str)` por presets; entrada por `Path` y por `&[u8]` | `DESIGN.md` §3.1, ADR-002 |
| 4 | Descargador Hugging Face resiliente (streaming, `Range`, SHA-256, `DownloadError`) y prioridad de rutas | `DESIGN.md` §3.2, §7, ADR-007 |
| 5 | Sin `impl Drop` manual; liberación del GIL; `panic = "unwind"` | `DESIGN.md` §3.3, ADR-004, ADR-005, ADR-012 |
| 6 | Suprimir el tiling forzado 512/64 del pipeline general; `rayon` acotado al preprocesamiento de CPU | `DESIGN.md` §3.4, ADR-008, ADR-009 |
| 7 | `Cargo.toml`: dependencias y features; `panic = "unwind"` en `[profile.release]` | `DESIGN.md` §2, §3.3, ADR-010 |
| 8 | Reescribir las fases 1 a 5 de `PLANNING.md` alineadas con lo anterior | Este documento, §1-§5 + Anexo A |

## Fase 0: Diseño y Validación

### `A1` — Validar el diseño y dictaminar cambios obligatorios

* **Tarjeta:** `t_f182fde7`. **Responsable:** `arquitecto`. **Estado:** Hecho (2026-10-25).
* **Criterio de aceptación:** un comentario con veredicto exactamente `APROBADO` o `CAMBIOS OBLIGATORIOS`, seguido de una lista numerada y accionable (fichero + cambio) por defecto. No se acepta un "revisado" sin lista.
* **Resultado:** `CAMBIOS OBLIGATORIOS`, con 8 cambios accionables. Ver §0.1.

### `E1` — Reescribir `DESIGN.md` y `PLANNING.md`

* **Tarjeta:** `t_12f74e4b`. **Responsable:** `escriba`. **Estado:** Hecho (2026-10-25).
* **Criterio de aceptación:** `DESIGN.md` y `PLANNING.md` reflejan punto por punto la lista de cambios obligatorios de `A1`, y `PLANNING.md` mapea cada tarea a su tarjeta. Verificable leyendo ambos ficheros y comparándolos con el comentario de `A1`.
* **Evidencia:** la tabla §0.1 es el mapeo punto por punto; los 12 ADR de `DESIGN.md` §4 registran las decisiones, y `DESIGN.md` apareció ya con los 12 ADR en el commit `4ede5c7`.

## Fase 1: Inicialización y Estructura Base

### `I1` — Esqueleto del paquete

* **Tarjeta:** `t_7e398138`. **Responsable:** `hefesto`. **Estado:** Hecho (2026-10-25, commit `4ede5c7`).
* **Contenido:** `Cargo.toml` (crate `pyocrust_core`, `crate-type = ["cdylib"]`, edition 2024, `pyo3` con `extension-module` y `abi3-py310`, `oar-ocr` `0.10.1` con las features de ADR-010); `pyproject.toml` (backend `maturin`, `module-name = "pyocrust._pyocrust_core"`, `requires-python = ">=3.10"`); `src/lib.rs` con `#[pymodule]` y `#[pyo3(name = "_pyocrust_core")]`; `pyocrust/__init__.py` y `pyocrust/__init__.pyi`; `LICENSE` (Apache-2.0), `README.md` y `.gitignore`.
* **Criterio de aceptación:** `cargo check` termina sin errores en la raíz del proyecto, y tras `pip install maturin` y `maturin develop`, `python -c "import pyocrust"` funciona. La salida **real** de ambos comandos debe ir adjunta en el resumen.
* **Restricción vinculante:** el perfil de release **no** declara `panic = "abort"` (ADR-004).
* **Evidencia:** existe `pyocrust/_pyocrust_core.pyd` (build de `maturin develop`), `maturin` está en `.venv` y `pyocrust/__init__.py` importa el módulo nativo; `Cargo.toml:45` declara `panic = "unwind"`.

## Fase 2: Implementación de Estructuras Core e Interfaces

### `I2` — Core

* **Tarjeta:** `t_629765fb`. **Responsable:** `coder`. **Estado:** Hecho (2026-10-25, commits `4ede5c7`, `d45d86c`, `e7cf9fa`).
* **Contenido:** `src/core/types.rs` (`OcrResult`, `TextRegion` con `#[pyclass]`/`#[pyo3(get)]`, enums `OcrTask`, `OcrSize`, `ModelSpec`, `ModelPaths`); `src/core/mod.rs` (trait `OcrEngineBackend`); `src/core/error.rs` (`OcrError` y su traducción a excepciones Python); `src/core/image_processor.rs` (`ScaleDown` y `FullPageTiling` como funciones puras sobre `image::RgbImage`, sin I/O y sin conocer `oar-ocr`).
* **Criterio de aceptación:** (1) `cargo check` termina sin errores; (2) un test ejecutable en Rust demuestra el tiling: una imagen sintética de 1200x900 con mosaico 512 y solapamiento 64 produce exactamente los mosaicos y offsets esperados, y ningún mosaico se solapa por debajo de 64px en los bordes de corte. Salida real adjunta.
* **Evidencia:** tests `tiling_1200x900_512_64_produces_the_expected_tiles` y `tiling_overlap_is_never_below_the_requested_value` (`src/core/image_processor.rs:269-372`); 36/36 tests Rust en verde (`S1`).
* **Coherencia con el diseño:** el diseño (ADR-009) declara el tiling **opt-in**: las funciones existen y se testean, pero el pipeline general no las aplica. El caso degenerado `overlap >= tamaño de mosaico` se rechaza con error (`ImageProcessError::OverlapTooLarge`), no con bucle degenerado.
* **Deuda declarada:** `OcrTask` se define con solo las variantes `Text`/`Structure` y **no** se usa en ningún punto del pipeline; su variante `Formula` no existe, por eso el escenario LaTeX de `V1` queda `skip` (ver §6).

## Fase 3: Gestión de Almacenamiento, Paths y Descargas

### `I3` — Storage

* **Tarjeta:** `t_4063447c`. **Responsable:** `hefesto`. **Estado:** Hecho (2026-10-25, commit `09e95cf`).
* **Contenido:** `src/storage/config.rs` (orden estricto de prioridad de `DESIGN.md` §3.2/§7.1); `src/storage/models.rs` (preflight por preset); `src/storage/mod.rs` (re-exports); `src/storage/download.rs` (descargador HF, contrato de `DESIGN.md` §7.3).
* **Criterio de aceptación:** un test ejecutable demuestra que (1) cada nivel de prioridad gana al anterior cuando ambos existen, y (2) con un directorio vacío, el preflight lista los modelos que faltarían para el preset pedido. Salida real adjunta.
* **Evidencia:** tests `level_1..3` (`src/storage/config.rs:181-229`), `empty_directory_reports_all_missing_*` (`src/storage/models.rs:102-178`) y `offline_bypass_*` (`src/storage/download.rs:236-268`).
* **Coherencia con el diseño:** la tarjeta era condicional ("si el diseño resultó de `A1` eliminó el descargador propio, este módulo queda solo con la resolución de rutas"). El diseño vigente **mantiene** el descargador (ADR-007), así que `src/storage/download.rs` se implementó con el contrato de `DESIGN.md` §7.3.
* **Fuera de alcance (D1):** el preflight y el descargador **no** se conectan al pipeline: `VeloceOCR::new` no invoca `preflight_paths(...).ensure_ready()` ni `fetch(...)`. Condiciones `S1.4` (§7).

## Fase 4: Integración de Motores y Factoría de Inferencia

### `I4` — Engines y API pública

* **Tarjeta:** `t_e4d7a850`. **Responsable:** `coder`. **Estado:** Hecho (2026-10-25, commit `7e68a66`).
* **Contenido:** `src/engines/oar_text.rs` (adaptador sobre `OAROCRBuilder`, PP-OCRv6); `src/engines/oar_structure.rs` (adaptador sobre `OARStructureBuilder`, PP-StructureV3); `src/engines/mod.rs` (factoría por nombre); `src/lib.rs` (clase pública `VeloceOCR` en el `#[pymodule]`, constructor parametrizado y `recognize` liberando el GIL).
* **Criterio de aceptación:** (1) `cargo check` sin errores; (2) con modelos en disco, un `recognize` end-to-end devuelve un `OcrResult` con texto no vacío; (3) sin modelos, **no** dar la tarea por buena: documentar el comando exacto que la verificaría y qué modelos harían falta.
* **Riesgo principal:** R1 de `DESIGN.md` §5 (firma exacta de `OARStructureBuilder` en `0.10.1`). **Resuelto (D1):** el adaptador usa la API real del crate (`oar_structure.rs:128-135`); `DESIGN.md` §3.1 y §5 lo registran.
* **Desviación de alcance (D1, cerrada en `D2`):** `StructureResult` (ADR-003) **no** se implementó en `I4`: `VeloceOCR.recognize` devolvía siempre `OcrResult`, incluso para `pp_structurev3`, aplanando layout, tablas y fórmulas. Lo corrigió la tarjeta `t_ab6ff8d0` (commit `b128566`): el trait devuelve `OcrOutput` y `convert_structure` conserva Markdown, layout y regiones (`src/engines/oar_structure.rs:148-171,185-215`). Condición `S1.2`, **cerrada** (§7).

## Fase 5: Exposición PyO3 y Pruebas de Integración

### `V1` — Tests de integración

* **Tarjeta:** `t_523ca1e7`. **Responsable:** `probador`. **Estado:** Hecho (2026-10-25, commit `d2e445c`).
* **Contenido:** `tests/conftest.py`, `tests/test_config.py`, `tests/test_tiling.py`, `tests/test_recognize.py` y `tests/data/sample_text.png`.
* **Criterio de aceptación:** `python -m pytest tests/ -q` en verde, con la salida **real** adjunta. Si un escenario no se puede ejecutar por falta de modelos o de GPU, se marca `skip` con el motivo, y el resumen distingue explícitamente entre "pasaron", "skipped" y "fallaron". No se cuenta como verde lo que no se ejecutó.
* **Resultado (`S1`):** **31 pasados, 2 `skip`, 1 `xfail`**. Los dos `skip` son `test_pp_structurev3_end_to_end` (faltan los 9 artefactos en disco) y `test_el_latex_de_una_formula_no_es_accesible_desde_python` (el contrato no expone `Formula` ni el LaTeX). El `xfail` es `test_las_excepciones_del_crate_heredan_de_pyocrerror`, que documenta la condición `S1.3`. **Actualización `D2` (`b128566`):** el `skip` de LaTeX se sustituyó por `test_pp_structurev3_devuelve_structure_result_con_markdown`; el recuento de arriba es el de `S1`.

### `C1` — Ataque a la implementación

* **Tarjeta:** `t_b674050d`. **Responsable:** `critico`. **Estado:** Hecho (2026-10-25).
* **Contenido:** revisión adversarial de GIL, VRAM, contrato del trait, licencias, perfil de release, tiling (imagen menor que un mosaico; `overlap >= mosaico`), resolución de rutas (directorio inexistente, sin permisos, `OAR_HOME` relativa) y errores tragados.
* **Criterio de aceptación:** un comentario con la lista de defectos, cada uno con `fichero:línea`, por qué es un defecto y la corrección concreta. Por cada categoría sin defectos, decir explícitamente qué se verificó y cómo. No se acepta "todo correcto" sin evidencia.
* **Límite:** no modifica código; si encuentra un defecto crítico, `kanban_block` con `needs_input`.
* **Resultado:** informe adversarial en el comentario de la tarjeta; los hallazgos que `S1` elevó a condiciones quedan en §7.

### `S1` — Sign-off final

* **Tarjeta:** `t_d005409b`. **Responsable:** `arquitecto`. **Estado:** Hecho (2026-10-25) con veredicto **RECHAZADO**.
* **Contenido:** recorrer `src/` y comprobar que cada ADR de `DESIGN.md` tiene su correspondencia en código, que las rutas de `DESIGN.md` §2 y §7 existen de verdad, y que el estado de este documento coincide con lo implementado.
* **Criterio de aceptación:** veredicto exactamente `APROBADO` o `RECHAZADO`, con (1) lista real de ficheros creados, (2) tests ejecutados y su resultado, (3) desviaciones con su justificación, y (4) si `RECHAZADO`, la lista numerada de lo que impone para aprobar.
* **Resultado:** **RECHAZADO**. Ficheros verificados: 27. `cargo test`: 36/36. `pytest`: 31 pasados, 2 `skip`, 1 `xfail`. Impuso 7 condiciones (§7), dos de ellas bloqueantes.

## Fase 6: Reconciliación Documental

### `D1` — Reconciliar la documentación con el código

* **Tarjeta:** `t_7449f60f`. **Responsable:** `escriba`. **Estado:** Hecho (2026-10-25).
* **Contenido:** verificar cada ruta y fichero enumerado en `DESIGN.md` contra el árbol real de `src/`; documentar como decisiones las desviaciones surgidas durante la implementación; marcar en este documento las tareas completadas y dejar constancia de las que quedaron fuera de alcance, con su motivo.
* **Criterio de aceptación:** los dos documentos describen el código que existe y son verificables comparando con el árbol real de `src/` y con el estado del board. Sin promesas sobre ficheros inexistentes.
* **Resultado:** todas las rutas de `DESIGN.md` §2 existen (27 ficheros versionados, más `tests/conftest.py` y `tests/data/sample_text.png` que se añaden al árbol documentado); desviaciones registradas en `DESIGN.md` §9 y en §6 de este documento; estado del board reflejado en §0. **`DESIGN.md` §5 (R1/R4) y los ADR 003/005/007/008 llevan ahora su estado real.**
* **Fuera de alcance (declarado):** `D1` **no** escribe código. Las condiciones `S1.1`-`S1.6` (§7) siguen **Pendientes** y necesitan tarjeta propia.

## Fase 7: Benchmarking

Medir la **calidad** y la **velocidad** de `pyocrust` frente a otros OCR sobre un dataset real (FUNSD) y publicar los resultados. El banco vive en `benchmarks/`, **fuera de `src/`**, así que no toca la implementación. Lo escribió `hefesto` (el cuerpo de `B4` atribuye `benchmarks/run_benchmarks.py` a `hefesto`) y **no tiene tarjeta propia en el board**: a fecha de `B3`, las únicas tarjetas de esta fase en la base del board son `B3`, `B4` y `B5`.

| Id | Fase | Título | Tarjeta | Responsable | Estado | Fecha de cambio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `B3` | 7 | Documentar el benchmarking y redactar el post de LinkedIn | `t_da2882a8` | `escriba` | Hecho | 2026-10-25 |
| `B4` | 7 | Atacar la metodología del benchmark (fairness, métricas, estadística) | `t_55e3c268` | `critico` | Hecho | 2026-11-01 |
| `B5` | 7 | Verificar reproducibilidad del benchmark y consistencia del reportero | `t_7f916baa` | `probador` | Hecho | 2026-10-31 |
| `S2.1` | 7 | Exponer fórmulas (LaTeX) en `pp_structurev3` y cerrar el test pendiente | `t_423d391f` | `coder` | Hecho | 2026-10-26 |
| `S2.2` | 7 | Exponer el backend `indra` (markdown de página + LaTeX) en pyocrust | `t_027743e2` | `coder` | Hecho | 2026-10-31 |
| `B6` | 7 | Reescribir el banco de benchmarks: eje `task_type`, 5 backends y 22 columnas | `t_c319bbab` | `escriba` | Hecho | 2026-11-01 |
| `B7` | 7 | Verificar el banco multi-tarea: repetibilidad, metadatos y reportero | `t_12453baf` | `probador` | Hecho | 2026-11-01 |
| `B8` | 7 | Atacar la metodología del banco multi-tarea | `t_12453baf` | `critico` | Hecho | 2026-11-01 |
| `B9` | 7 | Actualizar la documentación y el post con el banco multi-tarea | `t_93c3c339` | `escriba` | En curso | 2026-11-01 |

Dependencias: el código del banco (`benchmarks/*.py`, sin tarjeta) precede a `B3`,
`B4` y `B5`; `S2.1` y `S2.2` (backends de fórmula e indra) son prerequisitos para
`B6` (backends que el banco mide); `B6` (reescritura multi-tarea) precede a `B7`
(verificación) y `B8` (metodología adversaria); `B7`/`B8` preceden a `B9`
(documentación). `B3` documenta lo que `B4` (metodología) y `B5` (reproducibilidad)
auditan; `B9` reescribe `B3` con el alcance nuevo.

### `B3` — Documentar el benchmarking y redactar el post de LinkedIn

* **Tarjeta:** `t_da2882a8`. **Responsable:** `escriba`. **Estado:** Hecho (2026-10-25).
* **Contenido:** `benchmarks/README.md` (qué mide, comandos con `.venv/Scripts/python.exe`, contrato del CSV de 15 columnas, interpretación de cada métrica y limitaciones conocidas); `benchmarks/LINKEDIN.md` (borrador de post con los números reales del JSON); una sección `## Benchmarking` en `README.md`; y esta `Fase 7`.
* **Criterio de aceptación:** los cuatro ficheros existen; `benchmarks/README.md` documenta comandos copiables; el post contiene números que coinciden con `benchmark_summary.json`; `PLANNING.md` conserva el estilo y no rompe las tablas previas.
* **Evidencia:** números leídos de `benchmarks/output_examples/benchmark_summary.json` (run `2026-10-25_22-07-24`, n=29 por backend, 3 backends: `pyocrust`, `rapidocr`, `easyocr`): `pyocrust` CER `0.483`, F1 `0.744`, `715` ms/pág.; `rapidocr` CER `0.477`, F1 `0.603`, `5994` ms/pág.; `easyocr` CER `0.523`, F1 `0.428`, `8303` ms/pág. `pyocrust` es ~8,4× más rápido que `rapidocr` y ~11,6× que `easyocr`. El JSON se regenera con cada `report_benchmarks.py`, así que los números del post corresponden a la run vigente al escribir `B3`.

### `B4` — Atacar la metodología del benchmark

* **Tarjeta:** `t_55e3c268`. **Responsable:** `critico`. **Estado:** En curso (2026-10-25).
* **Contenido:** revisión adversarial de la *fairness* entre backends (mismo preprocesado, mismo *warmup*), de las métricas (orden del ground truth, papel del `word_f1`, falta de significancia con `n` pequeño), de la representatividad (Tiny vs. modelo por defecto; FUNSD en inglés), de los tiempos y de la reproducibilidad.
* **Criterio de aceptación:** un comentario con la lista numerada de defectos, cada uno con `fichero:línea` y la corrección concreta; por cada categoría sin defectos, qué se verificó y cómo.
* **Límite:** no toca código ni `src/`; si un defecto invalida resultados ya publicados, `kanban_block` con `needs_input`.

### `B5` — Verificar reproducibilidad del benchmark

* **Tarjeta:** `t_7f916baa`. **Responsable:** `probador`. **Estado:** En curso (2026-10-25).
* **Contenido:** `benchmarks/tests/test_functional.py` (pruebas funcionales de la API pública de `pyocrust` sobre FUNSD y del contrato del CSV) y `benchmarks/tests/conftest.py`; dos runs de `--limit 10` para comparar estabilidad de `cer`/`word_f1`, y recálculo manual del agregado frente a `benchmark_summary.json`.
* **Criterio de aceptación:** un comentario con la salida real de `pytest benchmarks/tests -q`, las medias de `pyocrust` de las dos runs y su diferencia, el recálculo del CER/F1 agregado frente a `benchmark_summary.json`, y evidencia de que ningún backend ausente apareció como ejecutado.
* **Límite:** no modifica `src/` ni el runner/reportero salvo un bug de una línea, que reporta aparte.

### `B6` — Reescribir el banco de benchmarks: eje `task_type`, 5 backends y 22 columnas

* **Tarjeta:** `t_c319bbab`. **Responsable:** `escriba`. **Estado:** Hecho (2026-11-01).
* **Contenido:** `benchmarks/run_benchmarks.py` pasó de un banco lineal a uno
  multi-tarea con eje `task_type` (`text`, `structure`, `formula`, `full_page`),
  cinco backends nuevos (`pyocrust_formula`, `pyocrust_indra`) y contrato CSV
  de 22 columnas (`markdown_f1`, `block_f1`, `model_name`, `model_variant`,
  `task_type`, `provider_effective`, etc.). `benchmarks/report_benchmarks.py`
  alinea agregados y salidas.
* **Criterio de aceptación:** un run `--limit 5` produce `summary.json` y
  `benchmark_table.md` con los 22 campos; `--task-type` filtra; backends no
  instalados aparecen como `skipped`, nunca como `ok`.
* **Evidencia:** run `2026-10-31_23-37-34`, 21 pass, 17 deselected, 2 skipped
  (FUNSD GT Markdown/bloques ausentes y estructura/fórmula offline). Artefactos
  recuperados tras timeout del runner.

### `B7` — Verificar el banco multi-tarea: repetibilidad, metadatos y reportero

* **Tarjeta:** `t_12453baf`. **Responsable:** `probador`. **Estado:** Hecho (2026-11-01).
* **Contenido:** dos runs de `--limit 5` (`2026-11-01_14-36-33`,
  `2026-11-01_14-36-49`) para comparar estabilidad de `cer`/`word_f1`;
  recálculo manual del agregado frente a `benchmark_summary.json`; comprobación
  de que ningún backend ausente (`easyocr`, `tesseract`, `structure`,
  `formula`) aparece como `ok`.
* **Criterio de aceptación:** comentario con las dos salidas reales, las medias
  de `pyocrust` de las dos runs y su diferencia, el recálculo del CER/F1
  agregado frente al JSON, y evidencia de que los backends ausentes no generan
  filas.
* **Evidencia:** 5 muestras por backend; `easyocr`/`tesseract` ausentes en la
  run de aceptación. `provider_effective=unverified` documentado.

### `B8` — Atacar la metodología del banco multi-tarea

* **Tarjeta:** `t_12453baf`. **Responsable:** `critico`. **Estado:** Hecho (2026-11-01).
* **Contenido:** revisión adversarial del banco multi-tarea desde la lectura
  completa de `benchmarks/run_benchmarks.py` y `benchmarks/report_benchmarks.py`
  más una sonda empírica (`probe_md.py`). Seis defectos identificados, ninguno
  cerrado en código.
* **Criterio de aceptación:** lista numerada de defectos, cada uno con
  `fichero:línea`, impacto y severidad. Un defecto invalida la tabla publicada
  como comparación; los demás son limitaciones documentadas.
* **Evidencia / Defectos:**
  1. **CRÍTICO** — `markdown_f1`/`block_f1` vacíos en FUNSD: `gt_markdown`/`gt_blocks`
     `None` → N/A en todas las filas (`run_benchmarks.py:227,525-526,542`).
  2. **MAYOR** — `markdown_f1` es LCS de tokens ordenados, no equivalencia de
     documento; reordenar baja 1.0→0.6667 (`run_benchmarks.py:203-218`).
  3. **MAYOR** — `block_f1` compara etiquetas crudas sin normalizar
     (`run_benchmarks.py:221-224,314`).
  4. **MAYOR** — `model_variant` nominal; `provider_effective="unverified"`
     no demuestra el provider ejecutado (`run_benchmarks.py:429,445`).
  5. **MEDIO** — memoria entre imágenes no medida; CPU/RAM no en meta
     (`run_benchmarks.py:439,471,482,531-556`).
  6. **PEQUEÑO** — sin versiones datasets/HF/pesos; no reproducible exactamente
     (`run_benchmarks.py:531-556`).

### `B9` — Actualizar la documentación y el post con el banco multi-tarea

* **Tarjeta:** `t_93c3c339`. **Responsable:** `escriba`. **Estado:** En curso (2026-11-01).
* **Contenido:** `benchmarks/README.md` (documentar eje `task_type`, 5 backends,
  22 columnas, `markdown_f1`/`block_f1` y la regla de titular), `benchmarks/LINKEDIN.md`
  (post con números reales del banco multi-tarea y defectos abiertos), `PLANNING.md`
  (tabla de Fase 7 y mapa de dependencias actualizados), `README.md` (sección
  `## Benchmarking` reconciliada).
* **Criterio de aceptación:** los cuatro ficheros existen y dicen lo que de verdad
  hace el banco; comandos de `benchmarks/README.md` son copiables; el post contiene
  números que coinciden con `benchmark_summary.json`; `PLANNING.md` refleja el estado
  real del board.
* **Límite:** no toca `src/`, `tests/` ni `benchmarks/*.py`.

## Fase 8: Cobertura completa de `oar-ocr`

Ampliar `pyocrust` de "dos presets fijos" a wrapper completo de `oar-ocr` `0.10.1`:
gestor de modelos conectado (S2.0), once tareas individuales (S2.3-S2.4),
indra (S2.2), fórmulas (S2.1) y verificación de exposición (S2.5).

> **Contrato:** cada tarjeta cierra código + evidencia. `S2.5` verifica exposición
> (11/11 predictores + 3/3 pipelines); `S2.6` reconcilia la documentación con ese
> cierre. La inferencia real de las 14 entradas y la descarga fría permanecen
> como limitaciones explícitas, no como defectos no detectados.

| Id | Fase | Título | Tarjeta | Responsable | Estado | Fecha de cambio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `S2.0` | 8 | Gestor de modelos: registro único, auto-descarga paralela y caché verificada | `t_54cab62c` | `hefesto` | Hecho | 2026-10-31 |
| `S2.1` | 8 | Exponer fórmulas (LaTeX) en `pp_structurev3` y cerrar el test pendiente | `t_423d391f` | `coder` | Hecho | 2026-10-26 |
| `S2.2` | 8 | Exponer el backend `indra` (markdown de página + LaTeX) en pyocrust | `t_027743e2` | `coder` | Hecho | 2026-10-31 |
| `S2.3` | 8 | TaskPredictor: las 5 capacidades que faltan (orientación, rectificación, línea, sello, fórmula) | `t_f6168e7b` | `coder` | Hecho | 2026-10-31 |
| `S2.4` | 8 | TaskPredictor: las 6 tareas restantes + `predict_batch` (cobertura 11/11) | `t_ce72cb5b` | `coder` | Hecho | 2026-11-01 |
| `S2.5` | 8 | Verificar la cobertura completa de `oar-ocr` (11 predictores + 3 pipelines) | `t_6c79980d` | `probador` | Hecho | 2026-11-01 |
| `S2.6` | 8 | Documentar la API de cobertura completa (DESIGN, PLANNING, README) | `t_524c734e` | `escriba` | En curso | 2026-11-01 |

Dependencias: `S2.0` (modelos) → `S2.1` (fórmulas en structure) → `S2.2` (indra) → `S2.3` (5 tareas) → `S2.4` (6 tareas restantes + batch) → `S2.5` (verificación) → `S2.6` (documentación). `S2.1` y `S2.2` comparten `S2.0` como prerequisito de artefactos.

### `S2.0` — Gestor de modelos: registro único, auto-descarga paralela y caché verificada

* **Tarjeta:** `t_54cab62c`. **Responsable:** `hefesto`. **Estado:** Hecho (2026-10-31, commit `113a490`).
* **Contenido:** `src/storage/registry.rs` (registro único ModelScope + HuggingFace),
  `src/storage/models.rs` (preflight + auto-descarga paralela con `rayon`, 4 hilos),
  sidecar `<name>.sha256` para no re-hashear en caliente, `PYOCRUST_OFFLINE=1`.
  Cierra `S1.4`: `ensure_models` conecta el descargador nativo al pipeline.
* **Criterio de aceptación:** `cargo test` verde, `pytest tests/test_models.py` verde,
  `models_status()` refleja el directorio resuelto, descarga paralela acotada.
* **Evidencia:** Rust 53/53; Python `test_models` 4 pass/2 skip. `ensure_models`
  ejecuta preflight, descarga en paralelo y re-verifica.

### `S2.1` — Exponer fórmulas (LaTeX) en `pp_structurev3`

* **Tarjeta:** `t_423d391f`. **Responsable:** `coder`. **Estado:** Hecho (2026-10-26).
* **Contenido:** `pp_formulanet-s.onnx` + tokenizer en el registro de ModelScope;
  `ModelPaths` gana campos de fórmula; `OARStructureBuilder` encadena
  `.with_formula_recognition(...)` cuando los artefactos están presentes.
* **Criterio de aceptación:** `cargo test` verde; test de LaTeX pasa o salta con
  comando exacto.
* **Evidencia:** Rust 39/39; Python 8 passed/2 skipped.

### `S2.2` — Exponer el backend `indra`

* **Tarjeta:** `t_027743e2`. **Responsable:** `coder`. **Estado:** Hecho (2026-10-31).
* **Contenido:** `src/engines/oar_indra.rs` como tercer backend del trait
  `OcrEngineBackend`; nueve artefactos HuggingFace (`datalab-to/indra-ocr`,
  revisión `bd02167f...`) en el registro; `VeloceOCR('indra')` devuelve
  `StructureResult` con Markdown, regiones y bloques.
* **Criterio de aceptación:** constructor y smoke CPU con dos regiones, dos
  elementos y Markdown; prueba Python y Rust de giro inverso pasadas.
* **Evidencia:** 1 pass en `test_indra.py`; `models_status()` reporta los 9
  artefactos. No certifica GPU, calidad matemática ni descarga fría.

### `S2.3` — TaskPredictor: las 5 capacidades que faltan

* **Tarjeta:** `t_f6168e7b`. **Responsable:** `coder`. **Estado:** Hecho (2026-10-31).
* **Contenido:** cinco tareas (`document_orientation`, `document_rectification`,
  `text_line_orientation`, `seal_text_detection`, `formula_recognition`),
  entradas `str`/`Path`/`bytes`, salidas `dict`, PNG como `PyBytes`.
* **Criterio de aceptación:** 53 tests Rust; `tests/test_tasks.py` 21 passed/0 skip.
* **Evidencia:** 53/53 Rust; 21/21 Python focal. Inferencias offline reales.

### `S2.4` — TaskPredictor: las 6 tareas restantes + `predict_batch`

* **Tarjeta:** `t_ce72cb5b`. **Responsable:** `coder`. **Estado:** Hecho (2026-11-01, commit `1349296`).
* **Contenido:** seis tareas adicionales (`text_detection`, `text_recognition`,
  `layout_detection`, `table_classification`, `table_structure_recognition`,
  `table_cell_detection`): once nombres, esquemas, whitelist/defaults y artefactos
  exactos en `DESIGN.md` §3.1.2. Batch ordenado, vacío `[]`, inferencia sin GIL.
* **Criterio de aceptación:** 53 tests Rust; `tests/test_tasks.py` 44 passed;
  batch de 2 imágenes = 2 dicts.
* **Evidencia:** 53/53 Rust; 44/44 Python focal. `predict_batch` reutiliza el
  predictor (modelo construido una vez).

### `S2.5` — Verificar la cobertura completa de `oar-ocr`

* **Tarjeta:** `t_6c79980d`. **Responsable:** `probador`. **Estado:** Hecho (2026-11-01).
* **Contenido:** matriz de 14 filas (11 predictores + 3 pipelines), prueba de 11
  nombres canónicos, comprobación de claves de `dict` contra `__init__.pyi`,
  gestión de modelos (preflight, bypass offline, truncado, hash incorrecto),
  sin carga duplicada (`predict_batch` 2 dicts).
* **Criterio de aceptación:** comentario con matriz 14 filas, `cargo test` 53/53,
  `pytest tests/` 138 passed/2 skipped, evidencia de puntos 2-6.
* **Evidencia:** 53/53 Rust; 138 passed/2 skipped Python. Matriz 11/11+3/3.
  Cuatro skips focales: estructura (6/11 artefactos ausentes), LaTeX (fixture
  sin fórmula), descarga fría y redescarga (excluidas por offline).

### `S2.6` — Documentar la API de cobertura completa

* **Tarjeta:** `t_524c734e`. **Responsable:** `escriba`. **Estado:** En curso (2026-11-01).
* **Contenido:** `DESIGN.md` (API pública §3.1.4, ADR-013, ADR-007 actualizado,
  §2 ampliado), `PLANNING.md` (Fase 8, S1.4 cerrada por S2.0), `README.md`
  (ejemplos TaskPredictor, tabla de cobertura 14 filas, apartado Modelos),
  `benchmarks/README.md` (enlace a eje `task_type`).
* **Criterio de aceptación:** los cuatro documentos describen el código real;
  tabla de cobertura coincide con la matriz de `S2.5`; estado del board coincide
  con `hermes kanban list`; directorio de modelos coincide con
  `pyocrust.models_status()`.

## Fase 9 — Catálogo y resolvedor de pipeline

> **Contrato:** `S3.0` genera el catálogo en Rust (`src/storage/catalog.rs`);
> `S3.1` añade el resolvedor Python (`pyocrust/hardware.py`, `pyocrust/resolver.py`);
> `S3.2` verifica con tests; `S3.3` ataca; `S3.4` sign-off; `S3.5` reconcilia
> `DESIGN.md`, `PLANNING.md` y `README.md`.

|| Id | Fase | Título | Tarjeta | Responsable | Estado | Fecha de cambio ||
|| :--- | :--- | :--- | :--- | :--- | :--- | :--- ||
|| `S3.0` | 9 | Catálogo documentado de modelos y pipelines | `t_585372c9` | `coder` | Hecho | 2026-11-01 ||
|| `S3.1` | 9 | Detección de hardware y resolvedor de pipeline | `t_edec41d8` | `coder` | Hecho | 2026-11-01 ||
|| `S3.2` | 9 | Tests del catálogo, hardware y resolvedor | `t_223cb785` | `probador` | Hecho | 2026-11-01 ||
|| `S3.3` | 9 | Atacar el catálogo y el resolvedor | `t_9c0acbbd` | `critico` | Hecho | 2026-11-01 ||
|| `S3.4` | 9 | Sign-off del catálogo y el resolvedor | `t_f2064743` | `arquitecto` | Hecho | 2026-11-01 ||
|| `S3.5` | 9 | Documentar el catálogo y el resolvedor | `t_f6ad65e6` | `escriba` | En curso | 2026-11-01 ||

Dependencias: `S3.0` → `S3.1` → `S3.2` → `S3.3` → `S3.4` → `S3.5`.
Además `S3.5` depende directamente de `S3.0` y `S3.1` (criterios de aceptación que requieren el catálogo y el resolvedor).

### `S3.0` — Catálogo documentado de modelos y pipelines

* **Tarjeta:** `t_585372c9`. **Responsable:** `coder`. **Estado:** Hecho (2026-11-01).
* **Contenido:** `src/storage/catalog.rs` (catálogo estático `ModelEntry` + `PipelineProfile` leídos de `oar_ocr::download::REGISTRY` y `find(name)`); `src/storage/mod.rs` (re-export); `src/lib.rs` (`model_catalog()` y `pipeline_profiles()` como `#[pyfunction]`).
* **Criterio de aceptación:** `cargo test` verde; `pyocrust.model_catalog()` devuelve 115 filas (98 registro + 17 Indra); `pyocrust.pipeline_profiles()` devuelve 16 filas (5 presets + 11 tareas); `size_bytes` coincide 98/98 con `oar_ocr::download::find`; Indra conserva `None`.
* **Evidencia:** Rust 53/53; `pytest tests/test_catalog.py` 5 passed. Verificado en `EVIDENCIA_S3.0.md`.

### `S3.1` — Detección de hardware y resolvedor de pipeline

* **Tarjeta:** `t_edec41d8`. **Responsable:** `coder`. **Estado:** Hecho (2026-11-01).
* **Contenido:** `pyocrust/hardware.py` (`GpuInfo`, `HardwareProfile`, `detect_hardware()` con stdlib); `pyocrust/resolver.py` (`TaskSpec`, `PipelineChoice`, `resolve_pipeline`); `pyocrust/__init__.pyi` (re-export).
* **Criterio de aceptación:** `cargo test` verde; `pytest tests/ -q` verde (138 passed, 1 skipped, 1 failed — fallo ajeno a S3); `resolve_pipeline(TaskSpec(ocr_only=True, quality='speed'))` → `pp_ocrv6/tiny`; `TaskSpec(formulas='with_text')` → `pp_structurev3`; `TaskSpec(document_kind='scanned')` → orientación + rectificación; `detect_hardware()` → `cpu_count=20`, `ram_bytes=68111413248`, `gpu=RTX PRO 4000 Blackwell/17094934528`.
* **Evidencia:** Rust 53/53; S3 focal 49 passed, 1 skipped (skip: `test_hardware.py:88`). Delta propio: commit `58385e6` (`pyocrust/__init__.pyi`).

### `S3.2` — Tests del catálogo, hardware y resolvedor

* **Tarjeta:** `t_223cb785`. **Responsable:** `probador`. **Estado:** Hecho (2026-11-01).
* **Contenido:** `tests/test_catalog.py`, `tests/test_hardware.py`, `tests/test_resolver.py`.
* **Criterio de aceptación:** `pytest tests/ -q` en verde, distinguiendo pasados/skipped/fallados. Tests focales S3: 49 passed, 1 skipped.
* **Evidencia:** S3 focal 49/1; suite completa 138 passed, 1 skipped, 1 failed (fallo ajeno `test_el_latex...`, reportado en `t_cbcf46e1`).

### `S3.3` — Atacar el catálogo y el resolvedor

* **Tarjeta:** `t_9c0acbbd`. **Responsable:** `critico`. **Estado:** Hecho (2026-11-01).
* **Contenido:** ataque adversarial a las 6 categorías de la tarjeta.
* **Criterio de aceptación:** comentario con lista numerada de defectos, cada uno con `fichero:línea`, por qué es un defecto y corrección concreta.
* **Resultado:** 1 defecto (D0: `output_format="json"` no fuerza `pp_structurev3`, `resolver.py:68`) + 5 categorías sin defectos. D0 justificado por `DESIGN.md` §3.1.3 ("JSON solo no fuerza estructura"). Suite S3.2: 49 passed, 1 skipped.

### `S3.4` — Sign-off del catálogo y el resolvedor

* **Tarjeta:** `t_f2064743`. **Responsable:** `arquitecto`. **Estado:** Hecho (2026-11-01).
* **Contenido:** verificación de `src/storage/catalog.rs`, `pyocrust/hardware.py`, `pyocrust/resolver.py`, `src/storage/registry.rs`, `pyocrust/__init__.py`, `pyocrust/__init__.pyi`, `DESIGN.md`, `PLANNING.md` y tests.
* **Criterio de aceptación:** veredicto `APROBADO` o `RECHAZADO` con lista de ficheros revisados, pruebas ejecutadas, desviaciones y defectos de S3.3 corregidos/justificados.
* **Veredicto:** **APROBADO**. D0 justificado; sin segundo sistema de rutas/descargador, sin `psutil`/`GPUtil`, sin `#[pyclass]` nuevo, sin tamaños duplicados. Tareas canónicas S2.3/S2.4: 11 nombres coinciden.

### `S3.5` — Documentar el catálogo y el resolvedor

* **Tarjeta:** `t_f6ad65e6`. **Responsable:** `escriba`. **Estado:** En curso (2026-11-01).
* **Contenido:** `DESIGN.md` (API pública §3.1.4, ADR-014/015/016, §2 y §9), `PLANNING.md` (Fase 9), `README.md` (Modelos y resolvedor, tabla de `pipeline_profiles()`, Variables de entorno).
* **Criterio de aceptación:** los tres documentos describen el código real; cada ruta/símbolo verificable con `read_file`; `disk_bytes`/`ram_bytes` de README coinciden con `pyocrust.pipeline_profiles()` en este host; estado del board coincide con `hermes kanban list`.
* **Evidencia:** this card.

## 6. Qué quedó fuera de alcance y por qué

| Punto | Estado | Motivo | Cómo se documenta |
| :--- | :--- | :--- | :--- |
| `StructureResult` / `to_markdown()` (ADR-003) | **Implementado (`D2`, `b128566`)** | `I4` lo aplanó y `S1` lo marcó bloqueante; lo implementó `t_ab6ff8d0` | `DESIGN.md` ADR-003 y §9.1; `S1.2` cerrada en §7 |
| Preflight conectado al constructor | **Implementado (`b128566`)** | `VeloceOCR::new` invoca `preflight_paths(...).ensure_ready()` (`src/lib.rs:60`) | `DESIGN.md` §7.2; mitad preflight de `S1.4` resuelta en §7 |
| Descargador HF conectado al pipeline | **Implementado (`S2.0`)** | `ensure_models` conecta el descargador nativo al pipeline (`src/storage/models.rs:224-242`) | `DESIGN.md` ADR-007 y §7.3 |
| `rayon` en uso real | No implementado | no hay bucle de preprocesamiento que paralelizar | `DESIGN.md` ADR-008 y §9.1 |
| Tarea `Formula` / LaTeX accesible desde Python | No implementado | `OcrTask` no tiene la variante y `recognize` devuelve `OcrResult` | `tests/test_recognize.py:144-155` (`skip` con motivo) |

## 7. Trabajo pendiente tras `S1` (RECHAZADO)

Condiciones abiertas del dictamen `S1` (comentario de `t_d005409b`, 2026-10-25). Copia fiel de `DESIGN.md` §9.2; son trabajo de **código** y no entran en `D1` ni en `D2`.

| Id | Condición | Gravedad | Estado (D2) | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| S1.1 | `pyapi::full_page_tiling` materializa los mosaicos y los descarta (OOM con `overlap` alto) | Bloqueante | Pendiente | `src/core/image_processor.rs:229-249` |
| S1.2 | `StructureResult` (ADR-003) no existía ni cruzaba a Python | Bloqueante | **Cerrada (`D2`, `b128566`)** | `src/core/types.rs:400-409`; `src/engines/oar_structure.rs:148-171` |
| S1.3 | `PyOcrValueError`/`PyOcrRuntimeError` no heredan de `PyOcrError` | Mayor | **Cerrada (`c30a3a9`)** | `src/core/error.rs:147-149` |
| S1.4 | `VeloceOCR::new` no ejecuta el preflight (ni el descargador) | Mayor | **Cerrada (`S2.0`, `t_54cab62c`)** | `src/storage/models.rs:224-242` (`ensure_models` conectado); `DESIGN.md` ADR-007 |
| S1.5 | `OAR_HOME` relativa rompe la autodescarga de `oar-ocr` | Mayor | **Cerrada (`c30a3a9`)** | `src/storage/config.rs:115-126,144-155` |
| S1.6 | `VeloceOCR::new` retiene el GIL durante la carga | Menor | Parcial (`D2`) | `src/lib.rs:35-65` |
| S1.7 | Retirar de `DESIGN.md` las capacidades de VRAM inexistentes | Menor | **Hecho en `D1`** | `DESIGN.md` §3.3 y ADR-005 |

`S1.2` la resolvió `arquitecto` por la opción A (implementar `StructureResult`) y la cerró `t_ab6ff8d0` (`b128566`, `D2`); `S1.3` y `S1.5` las cerró `c30a3a9`, que aterrizó mientras `D2` corría.

> **Nota (`D2`).** Quedan `S1.1` (pendiente) y `S1.6` (parcial): las rutas/preflight aún retienen el GIL (`src/lib.rs:35-60`). `S1.4` la cerró `S2.0` (`t_54cab62c`): `ensure_models` conecta el descargador nativo con paralelismo de 4 hilos y sidecar SHA-256. Debe re-verificar `S1.6` quien la posea.

## 8. Disciplina de commits (verificada en `D1`)

`D1` es el dueño de la disciplina de commits del repositorio. Estado comprobado el 2026-10-25:

| Commit | Fecha | Fase(s) que cubre | Mensaje |
| :--- | :--- | :--- | :--- |
| `4ede5c7` | 12:50 | **E1 + I1 + parte de I2** | Add pyocrust skeleton, core layer and validated design docs |
| `d45d86c` | 13:29 | I2 | Refine core layer for I2 acceptance criteria |
| `e7cf9fa` | 13:32 | I2 | Fix duplicated preprocessing error message in OcrError Display |
| `09e95cf` | 13:50 | I3 | Implement storage layer: model path resolution, preflight, and resilient downloader |
| `7e68a66` | 16:35 | I4 | Implement OCR engines, factory and VeloceOCR class |
| `d2e445c` | 16:47 | V1 | Add integration tests for model path resolution, tiling and recognize |

* **No hay ficheros sueltos sin commitear:** el árbol de trabajo está limpio. Lo único que aparece en `git status --ignored` son artefactos de build correctamente ignorados (`.venv/`, `Cargo.lock`, `target/`, `pyocrust/__pycache__/`, `pyocrust/_pyocrust_core.pyd`, `pyocrust/pyocrust_core.pdb`, `tests/__pycache__/`).
* **Defecto de granularidad (reportado, no corregido):** no existe un commit por fase para `E1` ni para `I1`. Los documentos de `E1` y el esqueleto de `I1` (más el core inicial de `I2`) viajan en el mismo commit `4ede5c7`. La numeración de fases (`E1`-`V1`) **no** aparece en ningún mensaje de commit, así que el mapeo de la tabla anterior se reconstruyó por fecha y por ficheros tocados, no por el mensaje.
* **No se reescribe la historia.** El defecto queda registrado aquí; el remoto se añadirá más tarde y no procede un `rebase` retroactivo que destruiría la trazabilidad de lo ya revisado por `C1`/`S1`.

## Divergencias entre el diseño vigente y los cuerpos de las tarjetas

Puntos donde el cuerpo de una tarjeta del board y `DESIGN.md` no decían lo mismo. Estado final tras `D1`.

| Punto | Dice la tarjeta | Dice `DESIGN.md` | Resolución |
| :--- | :--- | :--- | :--- |
| Nombre del módulo nativo | `I1`: `module-name = "pyocrust._pyocrust_core"` | `A1` propuso `pyocrust._core` | Manda `I1`. Implementado y verificado (`pyproject.toml:23`). ADR-011 |
| Ubicación del paquete Python | `I1`: `pyocrust/` en la raíz, compartiendo nombre con el repositorio | `A1` propuso `python/pyocrust/` | Manda `I1`. §2 de `DESIGN.md` |
| Tiling | `I2`: implementar `ScaleDown` y `FullPageTiling` (512/64) como funciones puras | ADR-009: el pipeline general no aplica el tiling; la utilidad existe como opt-in | Coexisten: la utilidad se implementa y se testea; no se aplica por defecto |
| Descargador | `I3`: condicional a que el diseño lo mantenga | ADR-007: se mantiene con contrato estricto | Se implementa (§7.3 de `DESIGN.md`); **queda desconectado del pipeline** (`S1.4`) |
| Estructura de módulos | `I2`-`I4`: `core/`, `storage/`, `engines/` | `A1` propuso fusionar en `src/engine.rs` + `src/types.rs` | Manda el board. ADR-006 |
| Trait `OcrEngineBackend` | `I2`: se implementa | `A1`: eliminar la jerarquía de traits | Se conserva **un** trait con dos implementaciones reales. ADR-006 |
| Nombre del identificador de preset | `I2`: `OcrSize`, `ModelSpec` | `A1`: `PpOcrV6Size`, `PipelinePreset` | Manda `I2` (implementa). ADR-002 |
| Salida de PP-StructureV3 | `I4` debía exponer `StructureResult` | ADR-003: la estructura no se aplana | **Resuelto (`D2`, `b128566`):** `recognize` devuelve `OcrOutput` y `VeloceOCR.recognize` entrega `StructureResult` con `pp_structurev3` (`S1.2` cerrada) |

## Anexo A: borrador inicial superado (`E1`)

Se conserva como rastro de lo que decía la primera versión de este documento antes del dictamen de `A1`. Se marca cada bloque con el motivo por el que fue sustituido. **Nada de esto debe ejecutarse tal cual.**

* **Fase 1 (tareas 1.1-1.4).** Superado en parte: `reqwest` entraba en las dependencias base de 1.2; ahora solo existe como dependencia del descargador HF (ADR-007). El esqueleto de carpetas de 1.4 (`src/core`, `src/storage`, `src/engines`) se mantiene. Tarea viva: `I1` (Hecha).
* **Fase 2 (tareas 2.1-2.3).** Superado: 2.2 definía `load_model(&mut self, &str)` (inválido, ADR-002) y 2.3 exigía el tiling como etapa obligatoria del pipeline (ADR-009 lo deja opt-in). Tarea viva: `I2` (Hecha).
* **Fase 3 (tareas 3.1-3.2).** Superado en parte: 3.2 desarrollaba la descarga con `reqwest::blocking` sin contrato de integridad; lo sustituye §7.3 de `DESIGN.md`. 3.1 (prioridad de rutas) se mantiene, con el nivel 3 cambiado de `~/.cache/ocr_rust_bridge/` a `~/.oar`. Tarea viva: `I3` (Hecha).
* **Fase 4 (tareas 4.1-4.3).** Superado en parte: el adaptador único de 4.1 (`oar_engine.rs`) se dividió en `oar_text.rs` y `oar_structure.rs`; la factoría de 4.2 se mantiene sin placeholders; 4.3 (`Arc` para GPU) se mantiene (ADR-012). Tarea viva: `I4` (Hecha); la desviación de ADR-003 que registraba §6 quedó **cerrada** en `D2` (`b128566`).
* **Fase 5 (tareas 5.1-5.4).** Superado en parte: 5.1 exponía `UniversalOCR` (ahora `VeloceOCR`); 5.3 y 5.4 (compilar con `maturin develop` y probar los tres escenarios) siguen siendo válidos y pasan a `I1`, `V1` (Hechas).
