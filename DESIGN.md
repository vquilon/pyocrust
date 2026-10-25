# Documento de Diseño de Arquitectura: Wrapper Multidisciplinar OCR en Rust
# Sistema: pyocrust (antes `ocr_rust_bridge`)

> **Estado del documento:** contrato de diseño de la versión 1. Validado por el
> dictamen de arquitectura de la tarjeta `A1` (veredicto: **CAMBIOS OBLIGATORIOS**)
> y contrastado con las fuentes de `oar-ocr` `0.10.1` y con la intención de
> producto de `DECISIONS.md`. Toda decisión impuesta por `A1` queda registrada
> como ADR numerado en §4; toda desviación respecto a `DECISIONS.md` queda
> registrada con su motivo y su coste, sin borrar la decisión original.

## 1. Objetivo General

Diseñar y desarrollar un wrapper nativo en Rust utilizando **PyO3** y **Maturin** que encapsule librerías de reconocimiento de caracteres (OCR) y fórmulas matemáticas del ecosistema de Rust (partiendo de `oar-ocr`). El paquete final debe ser unificado, multiplataforma, altamente eficiente en el manejo de memoria/hilos, con soporte dinámico para GPU/CPU y capaz de integrarse de forma transparente en un software existente en Python.

### 1.1 Alcance de la versión 1

| Ámbito | Entra en v1 | Fuera de v1 (hito posterior) |
| :--- | :--- | :--- |
| Texto (OCR) | PP-OCRv6 en tamaños `Tiny`, `Small`, `Medium` vía `OAROCRBuilder` | PP-OCRv4 y PP-OCRv5 |
| Estructura | PP-StructureV3 vía `OARStructureBuilder`: layout, tablas (HTML) y fórmulas (LaTeX) | — |
| Motor de inferencia | **ONNX Runtime** exclusivamente | **Candle** y `oar-ocr-vl` (VLM ~0.9B), pospuestos a v2 (ADR-001) |
| Distribución de modelos | `auto-download` (ModelScope → `$OAR_HOME`) + descargador Hugging Face resiliente (ADR-007) | otros repositorios |
| Plataforma de ejecución | CPU y GPU (features `cuda`, `directml`), Python 3.10+ (abi3) | `tensorrt`, `openvino`, `coreml`, `webgpu` |

`oar-ocr` `0.10.1` cubre además PP-OCRv4/v5, UniMERNet y PP-FormulaNet (fórmulas), SLANet/SLANet+/SLANeXt + RT-DETR (tablas), PP-DocLayoutV2/V3 (layout) y PP-LCNet/UVDoc (orientación y rectificación). La v1 expone dos de esas capacidades; el resto queda accesible sin cambios de arquitectura porque el motor ONNX ya las trae.

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
| `maturin` | **no instalado** en el intérprete activo | verificado por el orquestador |
| `panic = "abort"` en la referencia | `xycutppy/Cargo.toml:33` bajo `[profile.release]` (`xycutppy/Cargo.toml:28`) | verificado leyendo el fichero |

> Las citas `fichero:línea` sobre el interior del crate `oar-ocr` que aparecen en
> §3 y §4 provienen del dictamen `A1` (comentario del 2026-10-25). Este documento
> **no** ha verificado por su cuenta el árbol de `oar-ocr`, que no está descargado
> en el host. Son, por tanto, cita de segunda mano y así se marcan.

## 2. Arquitectura de Código y Estructura de Carpetas

El borrador inicial partía del patrón **Factoría** y del desacoplamiento mediante **Traits (Interfaces)** para permitir la incorporación de futuras librerías de Rust bajo la misma API de Python sin romper compatibilidad. `A1` declaró esa jerarquía sobre-ingeniería para un único backend real: se conserva un solo punto de extensión (el trait del core, con dos implementaciones reales) y se elimina todo lo que no tenía implementación (placeholder `scipix_engine`, adaptadores por crate, factoría con un único producto). Ver ADR-006.

```text
pyocrust/
├── Cargo.toml                  # Crate pyocrust_core: pyo3, oar-ocr, image, rayon, reqwest.
│                               # [profile.release] con panic = "unwind" (ADR-004, ADR-010)
├── pyproject.toml              # Backend Maturin; module-name = "pyocrust._pyocrust_core" (ADR-011)
├── DECISIONS.md                # Intención de producto. Entrada de diseño; no se reescribe
├── DESIGN.md                   # Este documento
├── PLANNING.md                 # Fases y mapeo de cada tarea a su tarjeta del board
├── LICENSE                     # Apache-2.0 (coincide con la licencia de oar-ocr)
├── README.md                   # Uso, build con maturin y estructura
├── .gitignore                  # target/, Cargo.lock, .env, __pycache__/
├── src/
│   ├── lib.rs                  # Registro del módulo PyO3 y clase pública VeloceOCR
│   ├── core/
│   │   ├── mod.rs              # Re-exports y trait OcrEngineBackend (ADR-002, ADR-006)
│   │   ├── types.rs            # Pyclasses TextRegion, OcrResult, StructureResult;
│   │   │                       # enums OcrTask, OcrSize, ModelSpec, ModelPaths
│   │   ├── error.rs            # OcrError y su traducción a excepciones Python
│   │   └── image_processor.rs  # ScaleDown y FullPageTiling: funciones puras sobre RgbImage,
│   │                           # sin I/O y sin conocer oar-ocr (ADR-009)
│   ├── storage/
│   │   ├── mod.rs              # Re-exports
│   │   ├── config.rs           # Resolución de rutas por prioridad estricta. Sin descarga
│   │   ├── models.rs           # Preflight: ficheros esperados por preset y cuáles faltan
│   │   └── download.rs         # Descargador Hugging Face resiliente (ADR-007)
│   └── engines/
│       ├── mod.rs              # Factoría: nombre de motor -> backend
│       ├── oar_text.rs         # Adaptador sobre OAROCRBuilder (PP-OCRv6)
│       └── oar_structure.rs    # Adaptador sobre OARStructureBuilder (PP-StructureV3)
├── pyocrust/                   # Paquete Python importable. Comparte nombre con el repositorio
│   ├── __init__.py             # Fachada pública de alto nivel
│   ├── __init__.pyi            # Stubs de tipos
│   └── py.typed                # Marcador PEP 561
└── tests/
    ├── test_config.py          # Niveles de prioridad en la resolución de rutas
    ├── test_tiling.py          # Troceado con solapamiento
    └── test_recognize.py       # recognize end-to-end (carga directa, env var y caché)
```

| Ruta | Estado | Nota |
| :--- | :--- | :--- |
| `DECISIONS.md`, `DESIGN.md`, `PLANNING.md` | Existe | Documentación; `DESIGN.md` y `PLANNING.md` se reescriben en `E1` |
| `src/**`, `pyocrust/**`, `tests/**` | Planificado | Los crea `I1`-`I4` y `V1` |
| `Cargo.toml`, `pyproject.toml`, `LICENSE`, `README.md`, `.gitignore` | Planificado | Los crea `I1` |

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
| Preset PP-StructureV3 | 8 ficheros: layout det, OCR det, OCR rec, OCR dict, table classification, wired table structure, wireless table structure, wired cell detection + table dict | `oar-ocr/src/oarocr/structure.rs:345-360` (cita `A1`) |

Además, los builders consumen el builder y devuelven pipelines inmutables listos para inferencia (`OAROCR`, `OARStructure`): no existe un ciclo de vida con carga mutable tardía.

Contrato adoptado (nombres fijados por la tarjeta `I2`, que es la que implementa):

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OcrSize { Tiny, Small, Medium }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ModelSpec { PpOcrV6(OcrSize), PpStructureV3 }

/// Rutas locales ya resueltas por `storage::config` para un `ModelSpec`.
pub struct ModelPaths { /* ... */ }

pub trait OcrEngineBackend: Send + Sync {
    /// Construye el pipeline desde rutas locales resueltas.
    /// 3 artefactos para PP-OCRv6; 8 para PP-StructureV3.
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError>;
    fn recognize(&self, image: &[u8]) -> Result<OcrResult, OcrError>;
}
```

Reglas del contrato:

| Regla | Detalle |
| :--- | :--- |
| Entrada | Ruta de fichero (`str`/`Path`) **y** buffer en memoria (`&[u8]`) |
| Carga | Una sola vez, en el constructor. El modelo queda residente; no hay recarga por llamada |
| Errores | `Result<_, OcrError>` tipado. Prohibido `Result<_, String>` y prohibido `unwrap()` en rutas de datos |
| Salida de texto | `OcrResult` con `TextRegion` (texto, confianza y caja) |
| Salida de estructura | `StructureResult` con `to_markdown()` (tablas HTML, fórmulas LaTeX, jerarquía documental). **No** se aplana a `OcrResult` (ADR-003) |

Firmas reales de estructura verificadas en `0.10.1` (cita `A1`):

| Elemento | Firma | Cita |
| :--- | :--- | :--- |
| Builder de preset | `OARStructureBuilder::pp_structurev3() -> Self` | `oar-ocr/src/oarocr/structure.rs:345` |
| Construcción | `fn build(mut self) -> Result<OARStructure, OCRError>` | `oar-ocr/src/oarocr/structure.rs:807` |
| Inferencia por ruta | `fn predict(&self, image_path: impl Into<PathBuf>) -> Result<StructureResult, OCRError>` | `oar-ocr/src/oarocr/structure.rs:2682` |
| Inferencia por buffer | `fn predict_image(&self, image: image::RgbImage) -> Result<StructureResult, OCRError>` | `oar-ocr/src/oarocr/structure.rs:2979` |
| A Markdown | `fn to_markdown(&self) -> String` | `oar-ocr-core-0.10.1/src/domain/structure.rs:471` |

> Nota de discrepancia: el docstring antiguo de `src/lib.rs:50-51` usaba firmas de dos parámetros (`with_table_cell_detection(model, cell_type)`), mientras que las fuentes de `0.10.1` usan métodos específicos desacoplados (`with_wired_table_structure`, `with_wireless_table_structure`, `with_wired_table_cell_detection`; `oar-ocr/src/oarocr/structure.rs:689-716`, cita `A1`). Manda la fuente, no el docstring.

### 3.2 Estrategia de Resolución de Modelos (Paths) y Autodescarga

El componente `OcrConfig` resuelve la ubicación física del modelo en disco con el siguiente orden estricto de prioridad:

1. **Parámetro explícito (`custom_path`)**: suministrado directamente en Python al instanciar la clase.
2. **Variable de Entorno**: `OAR_HOME` (estándar de `oar-ocr`) o `OCR_MODELS_CACHE_DIR` (directorio compartido definido a nivel de sistema).
3. **Ruta por Defecto (Fall-back)**: `~/.oar` (caché estándar de `oar-ocr`).

| Nivel | Fuente | Gana a |
| :--- | :--- | :--- |
| 1 | parámetro `custom_path` | niveles 2 y 3 |
| 2 | `OAR_HOME` / `OCR_MODELS_CACHE_DIR` | nivel 3 |
| 3 | `~/.oar` | — |

*Comportamiento de descarga:* si el fichero no existe en la ruta resuelta, se dispara la descarga. La v1 tiene **dos** caminos, en este orden: (1) `auto-download` de `oar-ocr` desde ModelScope hacia `$OAR_HOME`; (2) descargador propio desde Hugging Face cuando ModelScope no es alcanzable o el entorno es corporativo/offline. El contrato detallado del descargador está en §7. Si el fichero existe y su tamaño/hash es correcto, **no** se hace ninguna petición de red.

### 3.3 Gestión de Memoria y Concurrencia de Alto Rendimiento

* **Liberación del GIL de Python:** el método `recognize` expuesto a Python debe invocar `py.allow_threads()` antes de procesar los bytes de la imagen. Esto permite paralelismo real multi-hilo en CPU sin el bloqueo del GIL.
* **Seguridad en GPU:** las sesiones de inferencia pesadas (ONNX Runtime, CUDA, DirectML) se encapsulan en punteros atómicos `Arc` para permitir llamadas concurrentes seguras entre hilos nativos sin recargas destructivas de contexto.
* **Ciclo de Vida Limpio (VRAM):** ~~Los motores deben implementar el trait nativo `Drop` para asegurar que al reasignar o destruir una instancia de OCR en Python, los recursos de la GPU se liberen inmediatamente para evitar fugas de VRAM.~~ **Corregido (ADR-005):** `oar-ocr` ya es dueño de las sesiones `ort::Session`, cuyo `Drop` invoca `OrtReleaseSession` mediante RAII. No se implementa `Drop` manual. La VRAM se gobierna con `OrtSessionConfig` (`gpu_memory_budget`, `idle_memory_recovery`).
* **Estabilidad del intérprete (ADR-004):** el perfil release declara `panic = "unwind"`.

| Decisión de concurrencia | Regla |
| :--- | :--- |
| GIL | `py.allow_threads()` envuelve **toda** la inferencia, no solo la decodificación |
| Sesiones | Compartidas vía `Arc`; sin `Drop` manual (ADR-012) |
| Hilos intra-op de ONNX | Por defecto los de ORT. Con `intra_threads = 1` se habilita paralelismo inter-página explícito |
| `rayon` | Solo preprocesamiento de CPU (ADR-008) |

### 3.4 Preprocesamiento: Tiling vs. Scaling

El componente `SmartImageProcessor` debe admitir dos estrategias de segmentación visual en memoria nativa sin duplicar buffers:

1. **`ScaleDown`**: Redimensionamiento manteniendo la relación de aspecto para imágenes sencillas. **Es la estrategia por defecto** y es la que aplica el pipeline general: se delega el escalado geométrico en `oar-ocr` (`preprocess.rs`, `limit_side_len`), que respeta la relación de aspecto que esperan los modelos de layout y tablas de Paddle.
2. **`FullPageTiling`**: Troceado en mosaicos (512x512 píxeles) con un solapamiento (*overlap*) configurable (64px por defecto) para garantizar que las fórmulas matemáticas ubicadas en los márgenes de corte no se dividan ni pierdan consistencia sintáctica. **Corrección (ADR-009):** el mosaico arbitrario **rompe la coherencia geométrica** de los modelos de detección de layout y tablas, por lo que **no** se aplica por defecto al pipeline general. Se conserva como utilidad pura, opt-in y testeable, para quien la invoque explícitamente.

## 4. Registro de Decisiones de Arquitectura (ADR)

### ADR-001: v1 sobre ONNX Runtime; Candle y `oar-ocr-vl` se posponen a v2

* **Contexto.** `DECISIONS.md` §1 propone alternar de forma nativa entre ONNX Runtime y Candle (motor pure-Rust de Hugging Face). `oar-ocr` (ONNX Runtime) y `oar-ocr-vl` (Candle, VLM ~0.9B) son **dos crates distintos**, y este último arrastra `candle-core`, `candle-transformers` y kernels CUDA de `candle-flash-attn`.
* **Decisión.** La v1 usa **solo ONNX Runtime**. Candle / `oar-ocr-vl` queda fuera de v1, como hito posterior bajo una feature opcional `vl`.
* **Consecuencias.** Build reproducible en el host actual (`rustc` 1.95.0) sin CUDA Toolkit completo ni `nvcc`, y sin multiplicar el tiempo de compilación. La cobertura de fórmulas se cubre en v1 con UniMERNet/PP-FormulaNet vía ONNX.
* **Coste (respuesta a `DECISIONS.md` §1).** Se pierde la ruta "CPU estricta y portátil sin binarios nativos de ONNX" hasta v2. Mitigación: `oar-ocr` trae `download-binaries`, así que no hace falta toolchain de ONNX en el host.

### ADR-002: Contrato de carga por presets; se descarta `load_model(&mut self, &str)`

* **Contexto.** El diseño inicial definía `load_model(&mut self, model_path: &str) -> Result<(), String>`. En `0.10.1` ningún pipeline se inicializa con un único `.onnx`: PP-OCRv6 necesita 3 artefactos y PP-StructureV3, 8 (`oar-ocr/src/oarocr/structure.rs:345-360`, cita `A1`); los builders devuelven pipelines inmutables.
* **Decisión.** Se sustituye por presets tipados — `ModelSpec::PpOcrV6(OcrSize)` con `Tiny`/`Small`/`Medium` y `ModelSpec::PpStructureV3` — y el trait del core recibe un `ModelPaths` ya resuelto en lugar de una ruta suelta. La entrada admite ruta (`Path`) y buffer (`&[u8]`).
* **Consecuencias.** La resolución de modelos deja de ser responsabilidad del motor: la hace `storage::config` a partir del preset. `String` como error desaparece en favor de `OcrError`.

### ADR-003: la salida de estructura no se aplana a `OcrResult`

* **Contexto.** El diseño inicial reducía toda inferencia a `recognize(&[u8]) -> OcrResult`, omitiendo `StructureResult` y `to_markdown()`. Eso mutila las tablas HTML, las fórmulas LaTeX y la jerarquía documental de PP-StructureV3.
* **Decisión.** PP-StructureV3 expone `StructureResult` con `to_markdown()` (`oar-ocr-core-0.10.1/src/domain/structure.rs:471`, cita `A1`) y acceso a las regiones.
* **Consecuencias.** La API Python devuelve dos formas de resultado según el preset. Un `OcrResult` plano sigue disponible para PP-OCRv6.

### ADR-004: `panic = "unwind"` obligatorio en `[profile.release]`

* **Contexto.** La referencia `xycutppy` declara `panic = "abort"` (`xycutppy/Cargo.toml:33`, bajo `[profile.release]` en `:28`) para recortar binario en un algoritmo puramente aritmético. Con PyO3, un `panic` de Rust se captura con `catch_unwind` y se traduce a `PyErr`, preservando el intérprete. Con `panic = "abort"` se suprimen las tablas de unwinding: cualquier `unwrap()`, índice fuera de rango o fallo interno de ONNX Runtime llama a `abort()` y **mata el proceso Python entero**, sin traceback ni `try/except`.
* **Decisión.** `pyocrust` **no** declara `abort`; declara `panic = "unwind"` en `[profile.release]`.
* **Consecuencias.** Binario algo mayor que el de `xycutppy`. Un bug en Rust se convierte en excepción capturable, no en caída del backend.

### ADR-005: sin `impl Drop` manual para VRAM

* **Contexto.** El diseño inicial (y `DECISIONS.md` §3) pedía un `Drop` propio que liberase el contexto de CUDA/TensorRT. `OAROCR` y `OARStructure` encapsulan adaptadores que **son dueños** de las sesiones `ort::Session`; `ort::Session` implementa `Drop` e invoca `OrtReleaseSession`, liberando el Execution Provider por RAII determinista.
* **Decisión.** **No** se implementa `Drop` manual ni se llaman APIs de bajo nivel tipo `cudaDeviceReset()`. La VRAM se gobierna con `OrtSessionConfig` (`gpu_memory_budget`, `idle_memory_recovery = true`) y con el ciclo RAII de Rust al desreferenciar la clase en Python.
* **Consecuencias.** Sin riesgo de doble liberación. Riesgos evitados por la decisión: (1) `Use-After-Free` si un hilo conserva una referencia `Arc` mientras otro fuerza la liberación; (2) `cudaDeviceReset()` destruiría el contexto de CUDA de **todo el proceso Python**, rompiendo PyTorch, TensorFlow u otras sesiones ONNX; (3) el *arena allocator* de ONNX Runtime retiene pools por proceso salvo configuración explícita, así que un `Drop` manual sería inútil además de peligroso.
* **Coste (respuesta a `DECISIONS.md` §3).** La liberación "inmediata al reasignar el modelo" deja de estar bajo control del wrapper: depende de que Python suelte el último `Arc`. Mitigación posible sin `Drop` propio: exponer un `close()`/context manager que haga `drop` explícito del handle.

### ADR-006: estructura de módulos simplificada, sin placeholders

* **Contexto.** El árbol inicial proponía `src/core/mod.rs` + `src/engines/mod.rs` con factoría y traits dinámicos para encapsular un solo crate, más `src/engines/scipix_engine.rs` como placeholder y `src/core/image_processor.rs` como etapa obligatoria del pipeline.
* **Decisión.** Se elimina `src/engines/scipix_engine.rs` (YAGNI). Se mantiene un único trait del core (`OcrEngineBackend`) con **dos** implementaciones reales (`oar_text`, `oar_structure`) y una factoría por nombre. El código se organiza en `core/`, `storage/` y `engines/`.
* **Consecuencias.** Cada módulo tiene un motivo verificable. Cualquier tercer motor futuro entra como una implementación más del trait, sin cambiar la API.
* **Desviación registrada.** `A1` propuso además fusionar todo en `src/engine.rs` + `src/types.rs`. El orquestador fijó después la división `core/`/`storage/`/`engines/` en las tarjetas `I2`-`I4`, que son el contrato de implementación vigente. Lo sustantivo del dictamen (fuera el placeholder, fuera la factoría abstracta de un solo producto) se cumple igual.

### ADR-007: política de rutas y descargador HF resiliente; se mantiene `reqwest`

* **Contexto.** El primer dictamen de `A1` pedía eliminar `src/storage/download.rs` y `reqwest` porque `oar-ocr` ya trae `auto-download` con caché `$OAR_HOME`, verificación SHA-256 y escritura atómica (`oar-ocr-core/src/core/download/mod.rs:8-85`, cita `A1`). El dictamen consolidado, contrastado con `DECISIONS.md` §4, mantiene el descargador con otra justificación: `oar-ocr` solo baja de ModelScope, que sufre bloqueos de firewall y latencia alta en entornos corporativos y CI occidentales, y el producto exige Hugging Face.
* **Decisión.** Se **mantiene** `src/storage/download.rs` con `reqwest`, pero **redefinido** y sujeto a contrato (ver §7): streaming a fichero temporal, reanudación por `Range`, verificación obligatoria de tamaño y SHA-256, errores tipados por `DownloadError`, y bypass total de red si el modelo ya está en disco. Se conserva `src/storage/config.rs` como resolución pura de rutas con la prioridad estricta de §3.2 (el primer dictamen lo daba por eliminable; la prioridad de `DECISIONS.md` §4 exige un sitio donde vivir y ese es `config.rs`). Se elimina la descarga ad-hoc previa a la validación.
* **Consecuencias.** La carga de `reqwest` + TLS en el binario es el precio de no depender de ModelScope. Queda prohibido `get(url).unwrap()`.
* **Reversión registrada.** La propuesta inicial de `A1` (borrar el módulo entero) queda apartada, no borrada: ver ADR-007 en este mismo registro.

### ADR-008: `rayon` restringido al preprocesamiento de CPU

* **Contexto.** `DECISIONS.md` §2 pide `rayon` en el core para repartir lotes y tiling entre núcleos. `oar-ocr` ya usa `rayon` internamente para las regiones de texto (`rayon = "1.8"` en su `Cargo.toml`, cita `A1`) y ONNX Runtime tiene su propio pool intra-op con SIMD.
* **Decisión.** En `pyocrust`, `rayon` se usa **solo** para preprocesamiento intensivo de CPU (decodificación de imagen, conversión de espacio de color, transformaciones geométricas). El paralelismo inter-página solo se habilita cuando las sesiones están configuradas con `intra_threads = 1` o coordinadas con `OrtGlobalThreadPoolOptions`.
* **Consecuencias.** Se evita la sobre-suscripción de CPU (*thread thrashing*) y el colapso de cachés L1/L2/L3 que produce lanzar lotes concurrentes contra sesiones ORT multihilo. El cuello real (>90-95% del tiempo) es la inferencia tensorial, no el bucle de lotes.
* **Coste (respuesta a `DECISIONS.md` §2).** Sin `rayon` por defecto sobre lotes, el paralelismo inter-página no existe de fábrica. Se añade cuando una medición lo justifique, no antes.

### ADR-009: preprocesamiento — escalado nativo por defecto, tiling opt-in

* **Contexto.** `DECISIONS.md` §5 exige `FullPageTiling` con mosaicos de 512x512 y solapamiento de 64px para no truncar fórmulas en las líneas de corte. `A1` lo declaró contraproducente para el pipeline general: trocear rompe la relación de aspecto y la coherencia geométrica que esperan los modelos de layout y tablas, que ya escalan con `limit_side_len`.
* **Decisión.** El pipeline general aplica `ScaleDown` (escalado nativo de `oar-ocr`). `FullPageTiling` se conserva como **función pura opt-in** sobre `image::RgbImage`, sin I/O y sin conocer `oar-ocr`, con solapamiento configurable (64px por defecto) y test propio (tarjeta `I2`).
* **Consecuencias.** Nadie pierde la herramienta; se pierde solo el troceado forzado. Una imagen menor que un mosaico produce un único mosaico, y un solapamiento mayor o igual al tamaño del mosaico debe rechazarse con error, no producir un bucle degenerado (criterio que verifica `C1`).
* **Coste (respuesta a `DECISIONS.md` §5).** El usuario que necesite troceado debe invocarlo explícitamente.

### ADR-010: dependencias y features de `Cargo.toml`

* **Contexto.** Alternativas: reimplementar lo que `oar-ocr` ya hace, o apoyarse en sus features.
* **Decisión.** Dependencias: `pyo3` con `extension-module` y `abi3-py310`; `oar-ocr` `0.10.1` con `auto-download` y `simd`, y `cuda`/`directml` como features opcionales; `image`; `rayon` (ADR-008); `reqwest` con `stream` y TLS (ADR-007). `[profile.release]` con `panic = "unwind"` (ADR-004).
* **Consecuencias.** El binario por defecto es CPU; la GPU se activa compilando con `--features cuda` o `--features directml`.

### ADR-011: nomenclatura del paquete

* **Contexto.** `A1` propuso crate `pyocrust_core` y módulo Python `pyocrust._core`. La tarjeta `I1` fijó después `module-name = "pyocrust._pyocrust_core"`, con el paquete Python en `pyocrust/`, compartiendo nombre con el repositorio.
* **Decisión.** Crate Rust: `pyocrust_core`. Módulo nativo: `pyocrust._pyocrust_core`. Paquete Python: `pyocrust/` en la raíz. Licencia única Apache-2.0.
* **Consecuencias.** Que el directorio del repositorio y el paquete importable compartan nombre obliga a que el módulo compilado no se llame igual que el paquete; de ahí el prefijo `_pyocrust_core` en lugar de `_core` (que además chocaría con un futuro paquete `core` de Python). Manda `I1`, por ser la decisión de orquestación más reciente y explícita.

### ADR-012: sesiones compartidas con `Arc`, sin `Drop` manual

* **Contexto.** `DECISIONS.md` §3 exige `Arc` para que varios hilos interroguen el mismo modelo en GPU sin duplicar VRAM. Ese mismo documento pedía `Drop` manual, y ambas cosas juntas son incompatibles.
* **Decisión.** Se mantiene el `Arc` para las sesiones (ORT es thread-safe) y se retira el `Drop` manual (ADR-005). El paralelismo inter-página exige `intra_threads = 1` (ADR-008).
* **Consecuencias.** Compartir sesiones sin `Drop` propio es seguro: la liberación ocurre cuando cae el último `Arc`. Se elimina la condición de carrera que describía `A1`.

## 5. Riesgos Conocidos

| Id | Riesgo | Impacto | Mitigación |
| :--- | :--- | :--- | :--- |
| R1 | La firma exacta de `OARStructureBuilder` en `0.10.1` difiere de la documentada (docstring antiguo con firmas de dos parámetros frente a métodos específicos) | `src/engines/oar_structure.rs` no compila | Contrastar la API real del crate antes de escribir el adaptador; documentar la desviación si aparece (lo exige `I4`) |
| R2 | ModelScope inalcanzable (firewall corporativo, CI) | Sin modelos no hay inferencia | Descargador HF de ADR-007; bypass de red si el modelo ya está en disco |
| R3 | Peso de PP-StructureV3 (8 modelos) y VRAM en GPU de 16 GB | Fallo de carga o OOM | `gpu_memory_budget`; caché en `$OAR_HOME`; presets `Tiny`/`Small` para texto |
| R4 | `maturin` no está instalado en el intérprete activo | No se puede construir el paquete | `pip install maturin` antes de `maturin develop` (criterio de `I1`) |
| R5 | Acoplamiento circular entre `config.rs` (rutas) y `download.rs` (descarga) | Módulos difíciles de testear | `download.rs` recibe rutas ya resueltas; no consulta el entorno |

## 6. Estado Actual

| Elemento | Estado | Evidencia |
| :--- | :--- | :--- |
| `DESIGN.md` | Reescrito en `E1` | Este documento |
| `PLANNING.md` | Reescrito en `E1` | Mapea cada tarea a su tarjeta |
| Dictamen de arquitectura | Emitido y firmado | Tarjeta `A1`, veredicto CAMBIOS OBLIGATORIOS |
| Crate `pyocrust_core` | **No existe** | No hay `Cargo.toml` ni `src/` en la raíz |
| Paquete `pyocrust` | **No existe** | No hay `pyocrust/` ni `tests/` |
| Toolchain | `rustc`/`cargo` 1.95.0 presentes; `maturin` ausente | Verificado en este host |

Lo que este documento **no** sabe: el contenido exacto del árbol de `oar-ocr` `0.10.1` (el crate no está descargado en el host); por eso las citas internas de §3 y §4 van atribuidas a `A1` y se marcan como tales. Tampoco se ha medido el rendimiento real de ningún pipeline, porque no hay código que medir.

## 7. Resolución de Rutas, Almacenamiento y Descargador Hugging Face

### 7.1 `src/storage/config.rs` — resolución de rutas

Orden estricto de §3.2. Devuelve rutas absolutas normalizadas. No abre conexiones de red. Casos que debe resolver sin pánico: directorio inexistente, falta de permisos de lectura y `OAR_HOME` relativa (se resuelve contra el directorio de trabajo actual y se documenta; no se interpreta como error).

### 7.2 `src/storage/models.rs` — preflight

Dado un `ModelSpec`, devuelve la lista de ficheros esperados y cuáles faltan en disco. Es la pieza que permite decir al usuario, antes de cargar nada, qué modelos necesita. No descarga.

### 7.3 `src/storage/download.rs` — descargador resiliente (ADR-007)

Requisitos obligatorios y testeables:

| # | Requisito | Detalle |
| :--- | :--- | :--- |
| 1 | Streaming a temporal | Escritura en `.<filename>.<pid>.part` y renombrado atómico (`std::fs::rename`) solo tras validar |
| 2 | Reanudación | Cabecera `Range: bytes=offset-` ante corte de red |
| 3 | Integridad | Verificación obligatoria de `Content-Length` y de SHA-256 antes de dar la descarga por buena |
| 4 | Errores tipados | `enum DownloadError { Http(reqwest::Error), Io(std::io::Error), ChecksumMismatch { expected, actual }, Incomplete { expected, actual } }`. Prohibido `unwrap()` |
| 5 | Bypass offline | Si el fichero existe en la ruta resuelta y su tamaño/hash es correcto, no se hace ninguna petición de red |

Interfaz prevista: `fn fetch(url: &str, dest: &Path, sha256_hex: &str) -> Result<(), DownloadError>`. Como `reqwest::blocking` no puede ejecutarse dentro de un runtime asíncrono, la llamada se hace fuera de `py.allow_threads` o se usa el cliente asíncrono con un runtime propio; la decisión concreta la fija `I3` y se registra aquí en `D1` si cambia.

## 8. Notas de Evolución

* **v2 — Candle y `oar-ocr-vl`.** Entrarán bajo una feature opcional `vl`, nunca por defecto: requieren CUDA Toolkit completo y kernels de Flash Attention, que multiplican el tiempo de compilación (ADR-001).
* **v2 — paralelismo inter-página.** Solo si una medición lo justifica, y siempre con `intra_threads = 1` para no pelearse con el pool intra-op de ORT (ADR-008).
* **Features de aceleración adicionales.** `tensorrt`, `openvino`, `coreml` y `webgpu` existen en `oar-ocr`; se añaden cuando haya un objetivo de despliegue que los pida, no antes.
* **Gestión explícita de VRAM.** Si la liberación por RAII resulta insuficiente en producción, el camino es un `close()`/context manager que suelte el último `Arc`, **no** un `Drop` manual con llamadas a CUDA (ADR-005).
* **Reconciliación documental.** `D1` vuelve sobre este documento tras `I1`-`I4`, `V1`, `C1` y `S1` para que cada ruta enumerada exista de verdad y cada desviación quede como decisión, no como contradicción silenciosa.
