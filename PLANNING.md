# Plan de Trabajo y Ejecución (Tareas para Hermes)
# Proyecto: pyocrust (antes `ocr_rust_bridge`)

Este documento detalla la hoja de ruta secuencial para la implementación del paquete. Cada tarea debe completarse y validarse antes de proceder a la siguiente.

> **Contrato:** `DESIGN.md` es el contrato de diseño (validado en `A1`, reescrito en `E1`). Este documento es el tracker.
> Cada entrada lleva identificador, tarjeta del board (`pyocrust`), estado y criterio de aceptación.
> Estados: `Pendiente` / `En curso` / `Hecho` / `Bloqueado` / `Descartado`. Todo cambio de estado va fechado.

## 0. Mapa de tareas a tarjetas del board

Board: `pyocrust` (`~/.hermes/kanban/boards/pyocrust/kanban.db`). Estado leído el 2026-10-25.

| Id | Fase | Título | Tarjeta | Responsable | Estado | Fecha de cambio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `A1` | 0 | Validar el diseño y dictaminar cambios obligatorios | `t_f182fde7` | `arquitecto` | Hecho | 2026-10-25 |
| `E1` | 0 | Reescribir `DESIGN.md` y `PLANNING.md` | `t_12f74e4b` | `escriba` | En curso | 2026-10-25 |
| `I1` | 1 | Esqueleto del paquete (Cargo, maturin, módulo nativo) | `t_7e398138` | `hefesto` | Pendiente | — |
| `I2` | 2 | Core: tipos, trait, errores y tiling | `t_629765fb` | `hefesto` | Pendiente | — |
| `I3` | 3 | Storage: resolución de rutas y preflight | `t_4063447c` | `hefesto` | Pendiente | — |
| `I4` | 4 | Engines (`oar_text` + `oar_structure`) y clase `VeloceOCR` | `t_e4d7a850` | `hefesto` | Pendiente | — |
| `V1` | 5 | Tests de integración (config, tiling, recognize) | `t_523ca1e7` | `probador` | Pendiente | — |
| `C1` | 5 | Atacar la implementación antes del sign-off | `t_b674050d` | `critico` | Pendiente | — |
| `S1` | 5 | Sign-off final contra `DESIGN.md` | `t_d005409b` | `arquitecto` | Pendiente | — |
| `D1` | 6 | Reconciliar `DESIGN.md` y `PLANNING.md` con lo implementado | `t_7449f60f` | `escriba` | Pendiente | — |

Dependencias: `A1` → `E1` → `I1` → `I2` → `I3` → `I4` → (`V1`, `C1`) → `S1` → `D1`. `C1` ataca lo verificado por `V1`; `D1` cierra la documentación después del sign-off.

## 0.1 Cumplimiento de la lista de cambios obligatorios de `A1`

Los 8 puntos del dictamen consolidado (`A1`, comentario del 2026-10-25) y dónde queda cada uno:

| # | Cambio obligatorio de `A1` | Dónde queda registrado |
| :--- | :--- | :--- |
| 1 | Limitar v1 a ONNX Runtime; Candle / `oar-ocr-vl` a v2 | `DESIGN.md` §1.1, §8, ADR-001 |
| 2 | Quitar `scipix_engine`; motor unificado; paquete Python con `__init__`, `py.typed` y `tests/` | `DESIGN.md` §2, ADR-006, ADR-011 |
| 3 | Sustituir `load_model(&mut self, &str)` por presets; entrada por `Path` y por `&[u8]` | `DESIGN.md` §3.1, ADR-002 |
| 4 | Descargador Hugging Face resiliente (streaming, `Range`, SHA-256, `DownloadError`) y prioridad de rutas | `DESIGN.md` §3.2, §7, ADR-007 |
| 5 | Sin `impl Drop` manual; `py.allow_threads()`; `panic = "unwind"` | `DESIGN.md` §3.3, ADR-004, ADR-005, ADR-012 |
| 6 | Suprimir el tiling forzado 512/64 del pipeline general; `rayon` acotado al preprocesamiento de CPU | `DESIGN.md` §3.4, ADR-008, ADR-009 |
| 7 | `Cargo.toml`: dependencias y features; `panic = "unwind"` en `[profile.release]` | `DESIGN.md` §2, §3.3, ADR-010 |
| 8 | Reescribir las fases 1 a 5 de `PLANNING.md` alineadas con lo anterior | Este documento, §1-§5 + Anexo A |

## Fase 0: Diseño y Validación

### `A1` — Validar el diseño y dictaminar cambios obligatorios

* **Tarjeta:** `t_f182fde7`. **Responsable:** `arquitecto`. **Estado:** Hecho (2026-10-25).
* **Criterio de aceptación:** un comentario con veredicto exactamente `APROBADO` o `CAMBIOS OBLIGATORIOS`, seguido de una lista numerada y accionable (fichero + cambio) por defecto. No se acepta un "revisado" sin lista.
* **Resultado:** `CAMBIOS OBLIGATORIOS`, con 8 cambios accionables. Ver §0.1.

### `E1` — Reescribir `DESIGN.md` y `PLANNING.md`

* **Tarjeta:** `t_12f74e4b`. **Responsable:** `escriba`. **Estado:** En curso (2026-10-25).
* **Criterio de aceptación:** `DESIGN.md` y `PLANNING.md` reflejan punto por punto la lista de cambios obligatorios de `A1`, y `PLANNING.md` mapea cada tarea a su tarjeta. Verificable leyendo ambos ficheros y comparándolos con el comentario de `A1`.
* **Evidencia:** la tabla §0.1 de este documento es el mapeo punto por punto.

## Fase 1: Inicialización y Estructura Base

### `I1` — Esqueleto del paquete

* **Tarjeta:** `t_7e398138`. **Responsable:** `hefesto`. **Estado:** Pendiente.
* **Contenido:** `Cargo.toml` (crate `pyocrust_core`, `crate-type = ["cdylib"]`, edition 2024, `pyo3` con `extension-module` y `abi3-py310`, `oar-ocr` `0.10.1` con las features de ADR-010); `pyproject.toml` (backend `maturin`, `module-name = "pyocrust._pyocrust_core"`, `requires-python = ">=3.10"`); `src/lib.rs` con `#[pymodule]` y `#[pyo3(name = "_pyocrust_core")]`; `pyocrust/__init__.py` y `pyocrust/__init__.pyi`; `LICENSE` (Apache-2.0), `README.md` y `.gitignore`.
* **Criterio de aceptación:** `cargo check` termina sin errores en la raíz del proyecto, y tras `pip install maturin` y `maturin develop`, `python -c "import pyocrust"` funciona. La salida **real** de ambos comandos debe ir adjunta en el resumen.
* **Restricción vinculante:** el perfil de release **no** declara `panic = "abort"` (ADR-004).

## Fase 2: Implementación de Estructuras Core e Interfaces

### `I2` — Core

* **Tarjeta:** `t_629765fb`. **Responsable:** `hefesto`. **Estado:** Pendiente.
* **Contenido:** `src/core/types.rs` (`OcrResult`, `TextRegion` con `#[pyclass]`/`#[pyo3(get)]`, enums `OcrTask`, `OcrSize`, `ModelSpec`, `ModelPaths`); `src/core/mod.rs` (trait `OcrEngineBackend`); `src/core/error.rs` (`OcrError` y su traducción a excepciones Python); `src/core/image_processor.rs` (`ScaleDown` y `FullPageTiling` como funciones puras sobre `image::RgbImage`, sin I/O y sin conocer `oar-ocr`).
* **Criterio de aceptación:** (1) `cargo check` termina sin errores; (2) un test ejecutable en Rust demuestra el tiling: una imagen sintética de 1200x900 con mosaico 512 y solapamiento 64 produce exactamente los mosaicos y offsets esperados, y ningún mosaico se solapa por debajo de 64px en los bordes de corte. Salida real adjunta.
* **Coherencia con el diseño:** el diseño (ADR-009) declara el tiling **opt-in**: estas funciones existen y se testean, pero el pipeline general no las aplica. Añadir al test el caso degenerado `overlap >= tamaño de mosaico`, que debe rechazarse con error en lugar de producir un bucle degenerado (lo comprueba también `C1`).

## Fase 3: Gestión de Almacenamiento, Paths y Descargas

### `I3` — Storage

* **Tarjeta:** `t_4063447c`. **Responsable:** `hefesto`. **Estado:** Pendiente.
* **Contenido:** `src/storage/config.rs` (orden estricto de prioridad de `DESIGN.md` §3.2/§7.1); `src/storage/models.rs` (preflight por preset); `src/storage/mod.rs` (re-exports).
* **Criterio de aceptación:** un test ejecutable demuestra que (1) cada nivel de prioridad gana al anterior cuando ambos existen, y (2) con un directorio vacío, el preflight lista los modelos que faltarían para el preset pedido. Salida real adjunta.
* **Coherencia con el diseño:** la tarjeta era condicional ("si el diseño resultó de `A1` eliminó el descargador propio, este módulo queda solo con la resolución de rutas"). El diseño vigente **mantiene** el descargador (ADR-007), así que `src/storage/download.rs` se implementa con el contrato de `DESIGN.md` §7.3.

## Fase 4: Integración de Motores y Factoría de Inferencia

### `I4` — Engines y API pública

* **Tarjeta:** `t_e4d7a850`. **Responsable:** `hefesto`. **Estado:** Pendiente.
* **Contenido:** `src/engines/oar_text.rs` (adaptador sobre `OAROCRBuilder`, PP-OCRv6); `src/engines/oar_structure.rs` (adaptador sobre `OARStructureBuilder`, PP-StructureV3); `src/engines/mod.rs` (factoría por nombre); `src/lib.rs` (clase pública `VeloceOCR` en el `#[pymodule]`, constructor parametrizado y `recognize` liberando el GIL).
* **Criterio de aceptación:** (1) `cargo check` sin errores; (2) con modelos en disco, un `recognize` end-to-end devuelve un `OcrResult` con texto no vacío; (3) sin modelos, **no** dar la tarea por buena: documentar el comando exacto que la verificaría y qué modelos harían falta.
* **Riesgo principal:** R1 de `DESIGN.md` §5 (firma exacta de `OARStructureBuilder` en `0.10.1`). Si el código no compila por eso, contrastar la API real del crate y documentar la desviación, nunca inventar un wrapper que no compila.

## Fase 5: Exposición PyO3 y Pruebas de Integración

### `V1` — Tests de integración

* **Tarjeta:** `t_523ca1e7`. **Responsable:** `probador`. **Estado:** Pendiente.
* **Contenido:** `tests/test_config.py`, `tests/test_tiling.py`, `tests/test_recognize.py`.
* **Criterio de aceptación:** `python -m pytest tests/ -q` en verde, con la salida **real** adjunta. Si un escenario no se puede ejecutar por falta de modelos o de GPU, se marca `skip` con el motivo, y el resumen distingue explícitamente entre "pasaron", "skipped" y "fallaron". No se cuenta como verde lo que no se ejecutó.

### `C1` — Ataque a la implementación

* **Tarjeta:** `t_b674050d`. **Responsable:** `critico`. **Estado:** Pendiente.
* **Contenido:** revisión adversarial de GIL, VRAM, contrato del trait, licencias, perfil de release, tiling (imagen menor que un mosaico; `overlap >= mosaico`), resolución de rutas (directorio inexistente, sin permisos, `OAR_HOME` relativa) y errores tragados.
* **Criterio de aceptación:** un comentario con la lista de defectos, cada uno con `fichero:línea`, por qué es un defecto y la corrección concreta. Por cada categoría sin defectos, decir explícitamente qué se verificó y cómo. No se acepta "todo correcto" sin evidencia.
* **Límite:** no modifica código; si encuentra un defecto crítico, `kanban_block` con `needs_input`.

### `S1` — Sign-off final

* **Tarjeta:** `t_d005409b`. **Responsable:** `arquitecto`. **Estado:** Pendiente.
* **Contenido:** recorrer `src/` y comprobar que cada ADR de `DESIGN.md` tiene su correspondencia en código, que las rutas de `DESIGN.md` §2 y §7 existen de verdad, y que el estado de este documento coincide con lo implementado.
* **Criterio de aceptación:** veredicto exactamente `APROBADO` o `RECHAZADO`, con (1) lista real de ficheros creados, (2) tests ejecutados y su resultado, (3) desviaciones con su justificación, y (4) si `RECHAZADO`, la lista numerada de lo que impone para aprobar.

## Fase 6: Reconciliación Documental

### `D1` — Reconciliar la documentación con el código

* **Tarjeta:** `t_7449f60f`. **Responsable:** `escriba`. **Estado:** Pendiente.
* **Contenido:** verificar cada ruta y fichero enumerado en `DESIGN.md` contra el árbol real de `src/`; documentar como decisiones las desviaciones surgidas durante la implementación (por ejemplo, la firma real de `OARStructureBuilder`); marcar en este documento las tareas completadas y dejar constancia de las que quedaron fuera de alcance, con su motivo.
* **Criterio de aceptación:** los dos documentos describen el código que existe y son verificables comparando con el árbol real de `src/` y con el estado del board. Sin promesas sobre ficheros inexistentes.

## Divergencias entre el diseño vigente y los cuerpos de las tarjetas

Puntos donde el cuerpo de una tarjeta del board y `DESIGN.md` no dicen lo mismo. Se registran aquí para que `D1` los cierre y para que nadie los resuelva por su cuenta.

| Punto | Dice la tarjeta | Dice `DESIGN.md` | Resolución |
| :--- | :--- | :--- | :--- |
| Nombre del módulo nativo | `I1`: `module-name = "pyocrust._pyocrust_core"` | `A1` propuso `pyocrust._core` | Manda `I1` (decisión de orquestación posterior y explícita). ADR-011 |
| Ubicación del paquete Python | `I1`: `pyocrust/` en la raíz, compartiendo nombre con el repositorio | `A1` propuso `python/pyocrust/` | Manda `I1`. §2 de `DESIGN.md` |
| Tiling | `I2`: implementar `ScaleDown` y `FullPageTiling` (512/64) como funciones puras | ADR-009: el pipeline general no aplica el tiling; la utilidad existe como opt-in | Coexisten: la utilidad se implementa y se testea; no se aplica por defecto |
| Descargador | `I3`: condicional a que el diseño lo mantenga | ADR-007: se mantiene con contrato estricto | Se implementa (§7.3 de `DESIGN.md`) |
| Estructura de módulos | `I2`-`I4`: `core/`, `storage/`, `engines/` | `A1` propuso fusionar en `src/engine.rs` + `src/types.rs` | Manda el board. ADR-006 |
| Trait `OcrEngineBackend` | `I2`: se implementa | `A1`: eliminar la jerarquía de traits | Se conserva **un** trait con dos implementaciones reales. ADR-006 |
| Nombre del identificador de preset | `I2`: `OcrSize`, `ModelSpec` | `A1`: `PpOcrV6Size`, `PipelinePreset` | Manda `I2` (implementa). ADR-002 |

## Anexo A: borrador inicial superado (`E1`)

Se conserva como rastro de lo que decía la primera versión de este documento antes del dictamen de `A1`. Se marca cada bloque con el motivo por el que fue sustituido. **Nada de esto debe ejecutarse tal cual.**

* **Fase 1 (tareas 1.1-1.4).** Superado en parte: `reqwest` entraba en las dependencias base de 1.2; ahora solo existe como dependencia del descargador HF (ADR-007). El esqueleto de carpetas de 1.4 (`src/core`, `src/storage`, `src/engines`) se mantiene. Tarea viva: `I1`.
* **Fase 2 (tareas 2.1-2.3).** Superado: 2.2 definía `load_model(&mut self, &str)` (inválido, ADR-002) y 2.3 exigía el tiling como etapa obligatoria del pipeline (ADR-009 lo deja opt-in). Tareas vivas: `I2`.
* **Fase 3 (tareas 3.1-3.2).** Superado en parte: 3.2 desarrollaba la descarga con `reqwest::blocking` sin contrato de integridad; lo sustituye §7.3 de `DESIGN.md`. 3.1 (prioridad de rutas) se mantiene, con el nivel 3 cambiado de `~/.cache/ocr_rust_bridge/` a `~/.oar`. Tarea viva: `I3`.
* **Fase 4 (tareas 4.1-4.3).** Superado en parte: el adaptador único de 4.1 (`oar_engine.rs`) se divide en `oar_text.rs` y `oar_structure.rs`; la factoría de 4.2 se mantiene sin placeholders; 4.3 (`Arc` para GPU) se mantiene (ADR-012). Tarea viva: `I4`.
* **Fase 5 (tareas 5.1-5.4).** Superado en parte: 5.1 exponía `UniversalOCR` (ahora `VeloceOCR`); 5.3 y 5.4 (compilar con `maturin develop` y probar los tres escenarios) siguen siendo válidos y pasan a `I1`, `V1`. Tarea viva: `V1`.
