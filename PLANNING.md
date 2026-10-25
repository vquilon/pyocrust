# Plan de Trabajo y Ejecución (Tareas para Hermes)
# Proyecto: pyocrust (antes `ocr_rust_bridge`)

Este documento detalla la hoja de ruta secuencial para la implementación del paquete. Cada tarea debe completarse y validarse antes de proceder a la siguiente.

> **Contrato:** `DESIGN.md` es el contrato de diseño (validado en `A1`, reescrito en `E1`, reconciliado en `D1`). Este documento es el tracker.
> Cada entrada lleva identificador, tarjeta del board (`pyocrust`), estado y criterio de aceptación.
> Estados: `Pendiente` / `En curso` / `Hecho` / `Bloqueado` / `Descartado`. Todo cambio de estado va fechado.
>
> **Estado global (D1, 2026-10-25; actualizado en `D2`):** las fases 0-5 están **Hechas**; `S1.2` (`b128566`), `S1.3` y `S1.5` (`c30a3a9`) quedaron **cerradas**, pero el sign-off `S1` sigue **RECHAZADO**, con `S1.1` pendiente y `S1.4`/`S1.6` parciales (§7). El proyecto **no** está aprobado: `D1`/`D2` reconcilian la documentación, no la implementación.

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

## 6. Qué quedó fuera de alcance y por qué

| Punto | Estado | Motivo | Cómo se documenta |
| :--- | :--- | :--- | :--- |
| `StructureResult` / `to_markdown()` (ADR-003) | **Implementado (`D2`, `b128566`)** | `I4` lo aplanó y `S1` lo marcó bloqueante; lo implementó `t_ab6ff8d0` | `DESIGN.md` ADR-003 y §9.1; `S1.2` cerrada en §7 |
| Preflight conectado al constructor | **Implementado (`b128566`)** | `VeloceOCR::new` invoca `preflight_paths(...).ensure_ready()` (`src/lib.rs:60`) | `DESIGN.md` §7.2; mitad preflight de `S1.4` resuelta en §7 |
| Descargador HF conectado al pipeline | No implementado | el módulo existe y se testea, pero nadie lo llama; descarga `oar-ocr` | `DESIGN.md` ADR-007 y §7.3 |
| `rayon` en uso real | No implementado | no hay bucle de preprocesamiento que paralelizar | `DESIGN.md` ADR-008 y §9.1 |
| Tarea `Formula` / LaTeX accesible desde Python | No implementado | `OcrTask` no tiene la variante y `recognize` devuelve `OcrResult` | `tests/test_recognize.py:144-155` (`skip` con motivo) |

## 7. Trabajo pendiente tras `S1` (RECHAZADO)

Condiciones abiertas del dictamen `S1` (comentario de `t_d005409b`, 2026-10-25). Copia fiel de `DESIGN.md` §9.2; son trabajo de **código** y no entran en `D1` ni en `D2`.

| Id | Condición | Gravedad | Estado (D2) | Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| S1.1 | `pyapi::full_page_tiling` materializa los mosaicos y los descarta (OOM con `overlap` alto) | Bloqueante | Pendiente | `src/core/image_processor.rs:229-249` |
| S1.2 | `StructureResult` (ADR-003) no existía ni cruzaba a Python | Bloqueante | **Cerrada (`D2`, `b128566`)** | `src/core/types.rs:400-409`; `src/engines/oar_structure.rs:148-171` |
| S1.3 | `PyOcrValueError`/`PyOcrRuntimeError` no heredan de `PyOcrError` | Mayor | **Cerrada (`c30a3a9`)** | `src/core/error.rs:147-149` |
| S1.4 | `VeloceOCR::new` no ejecuta el preflight (ni el descargador) | Mayor | Parcial (`D2`) | `src/lib.rs:58-62` (preflight sí, descargador no) |
| S1.5 | `OAR_HOME` relativa rompe la autodescarga de `oar-ocr` | Mayor | **Cerrada (`c30a3a9`)** | `src/storage/config.rs:115-126,144-155` |
| S1.6 | `VeloceOCR::new` retiene el GIL durante la carga | Menor | Parcial (`D2`) | `src/lib.rs:35-65` |
| S1.7 | Retirar de `DESIGN.md` las capacidades de VRAM inexistentes | Menor | **Hecho en `D1`** | `DESIGN.md` §3.3 y ADR-005 |

`S1.2` la resolvió `arquitecto` por la opción A (implementar `StructureResult`) y la cerró `t_ab6ff8d0` (`b128566`, `D2`); `S1.3` y `S1.5` las cerró `c30a3a9`, que aterrizó mientras `D2` corría.

> **Nota (`D2`).** Quedan `S1.1` (pendiente) y `S1.4`/`S1.6` (parciales): el descargador sigue sin conectar (`src/storage/models.rs`, `src/storage/download.rs`) y las rutas/preflight aún retienen el GIL (`src/lib.rs:35-60`). Debe re-verificarlas quien las posee.

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
