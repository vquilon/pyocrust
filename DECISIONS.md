# Resumen Técnico de Decisiones de Diseño y Gestión de Recursos

Este documento resume los pilares estratégicos acordados para el desarrollo del paquete unificado en Rust (`ocr_rust_bridge` / `pyocrust`) enfocado en la inferencia de alta velocidad para OCR de fórmulas matemáticas y texto multidisciplinar.

> **Estado:** documento de entrada de diseño. Es la intención de producto que
> `DESIGN.md` debe desarrollar y que `arquitecto` (tarjeta `A1`) debe validar contra
> la realidad del ecosistema.

## 1. Evaluación del Ecosistema de Fórmulas en Rust

- **Librería Base Seleccionada:** `oar-ocr` se elige como la piedra angular por su arquitectura modular. A diferencia de las librerías especializadas en un solo modelo, `oar-ocr` unifica bajo un mismo ecosistema el soporte para arquitecturas críticas del estado del arte: **UniMERNet** (estructuras matemáticas complejas), **PP-FormulaNet** (modelos Paddle estructurados) y **VLMs** de visión-lenguaje.
- **Motores de Inferencia:** Permite alternar de forma nativa entre **ONNX Runtime** (con soporte para aceleración de hardware pesada) y **Candle** (el motor pure-Rust de Hugging Face para entornos portables o CPU estricta).

## 2. Gestión Multihilo y Concurrencia (CPU)

- **Liberación del GIL (Global Interpreter Lock):** En Python, el GIL restringe la ejecución a un solo hilo nativo a la vez. Para lograr un paralelismo real, el wrapper de Rust intercepta la llamada y utiliza el método `py.allow_threads` de PyO3. Esto libera el GIL inmediatamente, permitiendo que Python continúe su flujo o gestione otros hilos mientras Rust procesa la inferencia en hilos nativos del sistema.
- **Paralelismo Interno:** Se integra el crate **`rayon`** en el core de Rust. Si se procesan lotes de imágenes o estrategias de troceado pesado en entornos de solo CPU, Rust distribuirá de forma automática la carga de trabajo entre todos los núcleos físicos disponibles de manera ultraeficiente y sin condiciones de carrera (*data races*).

## 3. Gestión de Contexto en GPU y Eficiencia de VRAM

- **Carga Única y Ciclo de Vida (Lazy/Static Loading):** Cargar un modelo de *deep learning* en la GPU es una operación sumamente costosa que introduce picos de latencia críticos. Los modelos se inicializan una sola vez en el constructor y se mantienen residentes en memoria.
- **Acceso Compartido Seguro:** Para que múltiples hilos nativos interroguen al mismo modelo en la GPU de manera concurrente sin duplicar el consumo de VRAM, las sesiones del motor (como *ONNX Runtime Session*, que es nativamente *Thread-Safe*) se encapsulan en punteros de conteo atómico de referencias (**`Arc`**).
- **Limpieza de VRAM (Evitar fugas de memoria):** Cuando cambies de modelo en tu software de pruebas de calidad, Python destruirá la instancia vieja. Rust interceptará esto implementando el trait nativo **`Drop`**, asegurando que el contexto de CUDA o TensorRT se libere y limpie explícitamente de la tarjeta gráfica antes de inicializar un nuevo modelo.

## 4. Gestión de Almacenamiento e Inicialización Híbrida

El sistema cuenta con un motor de configuración flexible diseñado para tres entornos de despliegue diferentes (*Zero-Config*, *DevOps/Docker* y *Local Puro*):

- **Orden de Prioridad de Paths:**
  1. **Parámetro Directo:** Ruta absoluta al archivo provista en el constructor de Python (`custom_path`).
  2. **Variable de Entorno:** Ruta global definida en `OCR_MODELS_CACHE_DIR`.
  3. **Fallback por Defecto:** Carpeta aislada en el directorio del usuario (`~/.cache/ocr_rust_bridge/`).
- **Mecanismo de Autodescarga (*Auto-download*):** Si al resolver el *path* el modelo físico `.onnx` no existe en el disco, el wrapper activa un pipeline síncrono que crea el árbol de directorios y descarga el peso correspondiente desde repositorios remotos configurados (**Hugging Face**) utilizando **`reqwest::blocking`**, garantizando que el software funcione instantáneamente tras ser instalado por primera vez.

## 5. Preprocesamiento Inteligente de Imágenes en Memoria Nativa

Alimentar un modelo de fórmulas matemáticas con imágenes completas en alta resolución provoca picos drásticos de consumo de RAM/VRAM y pérdida de precisión analítica. El procesador intermedio implementa dos estrategias en memoria nativa:

- **Estrategia `ScaleDown`:** Redimensionamiento bilineal optimizado manteniendo estrictamente la relación de aspecto original para evitar deformar los caracteres y operadores matemáticos.
- **Estrategia `FullPageTiling` (Mosaicos con Solapamiento):** Trocea las páginas de alta densidad en cuadrículas compactas (ej. de 512x512 píxeles). Para solventar el problema de las ecuaciones que quedan ubicadas justo en la línea de división del corte, se introduce un traslape/solapamiento (*overlap*) configurable de **64 píxeles**. Esto actúa como un parche que unifica los fragmentos y garantiza que ninguna fórmula quede truncada a la mitad durante el reconocimiento visual.
