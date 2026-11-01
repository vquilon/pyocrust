# Benchmarking de `pyocrust`

## Estado vigente — comparativa multi-tarea (2026-11-01)

Run `results/2026-11-01_15-04-00`: FUNSD `train`, **10 imágenes por backend**,
**CPU**, `warmup=1`, `repeats=1`, `device=cpu`, Tiny en `text`. CSV de **22
columnas** con **60 filas** (`pyocrust`, `pyocrust_structure`, `pyocrust_formula`,
`pyocrust_indra`, `rapidocr`, `easyocr`), `task_type`/`model_name`/`model_variant`
rellenos en todas las filas; `tesseract` **skipped** (no instalado). Por primera
vez corren las cuatro casuísticas del wrapper (10/10 cada una): los artefactos
PP-StructureV3 que la nota B9 daba por ausentes ya están en `~/.oar`.

| Backend (variante; tarea) | n | F1 Markdown ↑ | F1 bloques ↑ | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default; text) | 10 | N/A | N/A | 0.344 | 0.745 | 0.527 | 0.819 | _9356_ | _0.11_ |
| **pyocrust** (tiny; text) | 10 | N/A | N/A | **0.694** | **0.392** | 0.470 | **0.685** | _751_ | _1.33_ |
| pyocrust_formula (pp-formulanet-s; formula) | 10 | N/A | N/A | 0.000 | 1.000 | 1.000 | 1.000 | 3133 | 0.32 |
| pyocrust_indra (math; full_page) | 10 | N/A | N/A | 0.444 | 0.658 | 1.560 | 0.824 | **310** | **3.22** |
| pyocrust_structure (default; structure) | 10 | N/A | N/A | 0.471 | 0.622 | 1.131 | 0.823 | 2643 | 0.38 |
| **rapidocr** (default; text) | 10 | N/A | N/A | _0.590_ | _0.502_ | **0.463** | 0.699 | 9472 | 0.11 |

Lectura honesta:

* **`text` (igual a igual, los tres comparables)**: `pyocrust` gana **F1 palabra**
  (0.694 vs 0.590 `rapidocr` vs 0.344 `easyocr`), **WER orden-neutralizado**
  (0.392) y **velocidad** (751 ms/página ≈ **12,6×** más rápido que `rapidocr` y
  ≈ 12,5× que `easyocr`). El **CER crudo** lo gana `rapidocr` por 0.007
  (0.463 vs 0.470), pero esa columna también mide el orden de lectura y no decide
  la marca.
* **`structure`/`formula`/`full_page`**: ejecutan y quedan registradas. **No hay
  GT Markdown/LaTeX/bloques** en FUNSD, así que `markdown_f1`/`block_f1` son
  **N/A** (no se inventan) y las métricas textuales de estas filas comparan contra
  un GT de texto plano, no contra su modalidad real: `pyocrust_formula` emite
  LaTeX (`"\n".join(result.formulas)`), de ahí su `CER=1,0`/`F1=0,0` — demuestra
  que la casuística corre, **no** una calidad matemática medida.
* **Velocidad entre tareas distintas no es un ranking.** `pyocrust_indra` es el
  más rápido (310 ms) porque devuelve Markdown estructurado; comparar su ms/pág.
  con `pyocrust` `text` no es justo. La marca de velocidad solo tiene sentido
  dentro de `text`.
* **`tesseract` skipped** con motivo; `model_variant` es nominal y
  `provider_effective="unverified"` no demuestra el provider ejecutado (B8).

**Defectos B8 que siguen abiertos** (no invalidan los números medidos, sí la
lectura de las columnas de Markdown como titular): `markdown_f1`/`block_f1` solo
son evaluables con GT legítimo de la misma modalidad; `markdown_f1` es LCS de
tokens ordenados, no equivalencia de documento; `block_f1` compara etiquetas
crudas; memoria/CPU-RAM y versiones de datasets/pesos no se registran.

## Estado anterior B9 (2026-10-31; superado por la comparativa multi-tarea de 2026-11-01)

Crítico R2: **APROBADO acotado** al banco. Regresiones comunicadas:
**21 pass, 17 deselected**, no suite global ni reejecución del escriba.
`results/2026-10-31_23-37-34/summary.json` y CSV registran **5/5 Tiny (`text`),
5/5 Indra (`full_page`, `math`) y 5/5 RapidOCR (`text`)**, sin errores.
La herramienta agotó el timeout: artefactos recuperados, exit code del runner
no observado; no se certifica su terminación correcta.
Estructura/fórmula **skipped**: offline con seis artefactos PP-StructureV3 ausentes,
no generan filas. FUNSD sin GT Markdown/bloques: **calidad Markdown N/A / no evaluada**.
CPU solicitado, `provider_effective=unverified`, `warmup=1`, `repeats=1`:
**sin ganador general, claims GPU ni comparación publicable con cinco muestras**.

**Defectos abiertos (B8):**
1. **CRÍTICO** — `markdown_f1`/`block_f1` vacíos en FUNSD: `gt_markdown`/`gt_blocks`
   son `None` para todas las filas (`run_benchmarks.py:227,525-526,542`); la tabla
   publicada encabeza con `F1 Markdown` pero muestra **N/A** en todas las filas.
2. **MAYOR** — `markdown_f1` mide LCS de tokens ordenados, no equivalencia de
   documento: reordenar secciones baja la puntuación (`run_benchmarks.py:203-218`).
3. **MAYOR** — `block_f1` compara etiquetas crudas sin normalizar; no comparable
   entre motores (`run_benchmarks.py:221-224,314`).
4. **MAYOR** — `model_variant` es nominal; `provider_effective="unverified"` no
   demuestra el provider ejecutado (`run_benchmarks.py:429,445`).
5. **MEDIO** — memoria entre imágenes no medida; CPU/RAM no en meta
   (`run_benchmarks.py:439,471,482,531-556`).
6. **PEQUEÑO** — sin versiones de datasets/HF/pesos; no reproducible exactamente
   entre máquinas (`run_benchmarks.py:531-556`).

> **Nota (`B6`, ver `README.md` §Uso).** El eje `task_type` (columna 18 del CSV)
> se define en el contrato de 22 columnas anterior. La tabla de cobertura de
> `README.md` explica qué `task_type` produce cada predictor y pipeline.

### Contrato vigente (sustituye las definiciones históricas inferiores)

* **22 columnas**, cabecera exacta:
  `run_timestamp,backend,dataset,image_id,cer,wer,cer_ord,wer_ord,word_f1,exact_match,elapsed_ms,n_regions,mean_confidence,n_chars_gt,n_chars_pred,status,error,task_type,model_name,model_variant,markdown_f1,block_f1`.
* **Backends** registrados en `run_benchmarks.py --backends`:
  `pyocrust` (`pp_ocrv6` tiny → `text`), `pyocrust_structure` (`pp_structurev3` →
  `structure`), `pyocrust_formula` (`pp_structurev3` + `pp-formulanet-s` →
  `formula`), `pyocrust_indra` (`indra` con `math(true)` → `full_page`),
  `rapidocr` (`text`), `easyocr` (`text`), `tesseract` (`text`).
  Los no instalados aparecen como `skipped` en `summary.json`, nunca como `ok`.
* `--task-types text,structure,formula,full_page` filtra tareas fijas; no convierte
  salidas. `pyocrust_formula` (`pp_structurev3`, `pp-formulanet-s`) usa
  **`"\n".join(result.formulas)`**, no Markdown de página; Indra devuelve Markdown.
* `--manifest ruta/manifest.json`: array JSON, `image` relativa al manifiesto,
  `id` opcional, `text` GT textual (omitido: cadena vacía), `markdown` GT Markdown/
  LaTeX, `blocks` lista de etiquetas. GT legítimo de la misma entrada/modalidad,
  nunca texto FUNSD convertido artificialmente en Markdown. Esquema ilustrativo,
  no GT real: `[{"image":"pagina.png","text":"Texto anotado","markdown":"# Texto anotado","blocks":["title"]}]`.
* `markdown_f1`: F1 LCS de tokens sensible al orden, case preservado dentro de
  `$...$`/`$$...$$` (usar delimitadores en GT LaTeX). **No es equivalencia de
  documento**: reordenar secciones baja la puntuación (B8). `block_f1`:
  multiconjunto de etiquetas **crudas** (no normalizadas), no geometría
  (B8). Vacías en `text` o sin GT: reportero muestra **N/A**.
* `cer_ord`: Levenshtein sobre **caracteres** de palabras normalizadas, ordenadas
  y unidas con espacios; `wer_ord` sobre listas de palabras. No son idénticos.
  CSV legacy sin `task_type`: antiguo `cer_ord` duplicaba WER, se invalida como
  **None / N/A**, no cero ni CER vigente.
* `--repeats N` (N >= 1): tiempo medio por imagen, calidad de la última salida;
  metadatos guardan tiempos individuales/p95 y `load_ms`, separado de inferencia
  y warmup. `--device cpu|gpu`: **gpu rechazada con `skipped`**, motivo
  `GPU selection not exposed; refusing CPU fallback`, nunca CPU etiquetada GPU.
  `provider_effective=unverified` no demuestra el provider ejecutado.
* Reportero agrupa backend/variante/tarea; marcas solo dentro de la misma tarea,
  calidad textual en `text`, Markdown en las otras. Gráfico de velocidad con
  tareas distintas no permite ranking general. `output_examples/` es mutable.

```bash
# Ejemplos futuros, no ejecutados por B9; siempre --run explícito
.venv/Scripts/python.exe benchmarks/run_benchmarks.py --limit 5 --backends pyocrust,pyocrust_structure,pyocrust_formula,pyocrust_indra,rapidocr --task-types text,structure,formula,full_page --repeats 1 --device cpu
.venv/Scripts/python.exe benchmarks/run_benchmarks.py --manifest ruta/manifest.json --backends pyocrust_indra --task-types full_page --repeats 2 --device cpu
.venv/Scripts/python.exe benchmarks/report_benchmarks.py --run benchmarks/results/2026-10-31_23-37-34
```

## Histórico B3/B4 (2026-10-25; no estado vigente)

Se conserva el registro original siguiente, incluidos comandos/contratos y
rankings superados. No reutilizar como post aprobado ni ganador general;
prevalece la nota B9 y su contrato de 22 columnas.

Banco de pruebas **fuera de `src/`** que mide la **calidad** y la **velocidad** de
`pyocrust` frente a otros OCR sobre un dataset real, y genera la tabla y los
gráficos que se publican (README del repositorio, post de LinkedIn).

Todo se ejecuta con el intérprete del venv local `.venv/Scripts/python.exe`
desde la **raíz del repositorio**.

## Qué mide

Sobre las **mismas imágenes** (FUNSD, formularios escaneados):

* **Calidad** por imagen: `cer`, `wer`, `word_f1` y `exact_match`.
* **Velocidad** por imagen: `elapsed_ms` (y, agregado, ms/página y páginas/s).

Cada backend se calienta con el mismo *warmup* y corre sobre las mismas imágenes.
Los backends que no están instalados (o cuyos modelos faltan) se registran como
`skipped` con el motivo, **nunca** como si hubieran corrido.

| Fichero | Qué es |
| :--- | :--- |
| `run_benchmarks.py` | Runner: carga FUNSD, ejecuta los backends y escribe el CSV + `summary.json` de la run. |
| `report_benchmarks.py` | Agrega los CSV y escribe tablas (`.md`, `.tex`, `.png`, `.svg`) y gráficos en `output_examples/`. |
| `results/<timestamp>/` | Salida por run: `<timestamp>.csv`, `<timestamp>.meta.json`, `<backend>.meta.json` y `summary.json`. |
| `output_examples/` | Artefactos listos para publicar: `benchmark_table.md`, `benchmark_summary.json`, gráficos. |
| `data_cache/` | Caché local de FUNSD (`nielsr/funsd`) descargado con `datasets`. |
| `tests/` | Pruebas funcionales de `pyocrust` sobre FUNSD (`pytest`); las añade la tarjeta `B5` y no forman parte del runner ni del reportero. |

## Cómo ejecutarlo

```bash
# 0) Dependencias del banco (una sola vez). `pyocrust` ya debe estar compilado
#    en el venv con `maturin develop` (ver README.md del repositorio).
.venv/Scripts/python.exe -m pip install datasets pillow matplotlib

# 1) Benchmark: FUNSD train, 30 imágenes, pyocrust vs. rapidocr vs. easyocr
.venv/Scripts/python.exe benchmarks/run_benchmarks.py --limit 30 --backends pyocrust,rapidocr,easyocr

# 2) Tablas y gráficos a partir de la run más reciente (¡ojo, ver «Provenance»!)
.venv/Scripts/python.exe benchmarks/report_benchmarks.py

# 2b) ...o de todas las runs acumuladas
.venv/Scripts/python.exe benchmarks/report_benchmarks.py --all
```

Salidas: `benchmarks/results/<timestamp>/` (CSV + metadatos) y
`benchmarks/output_examples/` (tabla y gráficos).

### Opciones útiles

```bash
# Medir también el pipeline de estructura (necesita los modelos de PP-StructureV3)
.venv/Scripts/python.exe benchmarks/run_benchmarks.py --backends pyocrust,pyocrust_structure

# Cambiar tamaño de muestra, split y warmup
.venv/Scripts/python.exe benchmarks/run_benchmarks.py --limit 50 --split test --warmup 2

# Agregar solo una run concreta
.venv/Scripts/python.exe benchmarks/report_benchmarks.py --run benchmarks/results/2026-10-25_22-07-24
```

Backends disponibles en `run_benchmarks.py --backends`:

* `pyocrust` — preset `pp_ocrv6` (PP-OCRv6, modelo **Tiny**, es el defecto).
* `pyocrust_structure` — preset `pp_structurev3` (PP-StructureV3).
* `rapidocr` — `rapidocr-onnxruntime`.
* `easyocr` — requiere `easyocr` + `torch`.
* `tesseract` — requiere `pytesseract` + el binario de Tesseract.

Los que no estén instalados aparecen como `skipped` en el `summary.json` de la run.

## Contrato del CSV

Una fila por combinación `(backend, imagen)`. Cabecera exacta, **17 columnas**:

```text
run_timestamp,backend,dataset,image_id,cer,wer,cer_ord,wer_ord,word_f1,exact_match,elapsed_ms,n_regions,mean_confidence,n_chars_gt,n_chars_pred,status,error
```

| Columna | Tipo | Significado |
| :--- | :--- | :--- |
| `run_timestamp` | str | Marca de la run (`%Y-%m-%d_%H-%M-%S`). |
| `backend` | str | `pyocrust` / `pyocrust_structure` / `rapidocr` / `easyocr` / `tesseract`. |
| `dataset` | str | `funsd`. |
| `image_id` | str | Identificador de la imagen en FUNSD. |
| `cer` | float | *Character Error Rate* (menor es mejor). **Sensible al orden de lectura.** |
| `wer` | float | *Word Error Rate* (menor es mejor). **Sensible al orden de lectura.** |
| `cer_ord` | float | CER con orden neutralizado: ordena el multiconjunto de palabras antes del Levenshtein. Mide reconocimiento, no disposición. |
| `wer_ord` | float | WER con orden neutralizado (idéntico a `cer_ord` por definición). |
| `word_f1` | float | F1 a nivel de palabra, independiente del orden (mayor es mejor). |
| `exact_match` | float | `1.0` si el texto normalizado coincide exactamente; si no, `0.0`. |
| `elapsed_ms` | float | Milisegundos de la inferencia (sin contar el *warmup*). |
| `n_regions` | int | Nº de regiones/cajas devueltas por el backend. |
| `mean_confidence` | float | Confianza media auto-reportada por el backend. |
| `n_chars_gt` | int | Caracteres del ground truth normalizado. |
| `n_chars_pred` | int | Caracteres de la predicción normalizada. |
| `status` | str | `ok` o `error`. Un backend no disponible **no genera fila** (solo `skipped` en el `summary.json`). |
| `error` | str | Mensaje de error si `status = error`; vacío si `ok`. |

La normalización aplicada antes de comparar es la misma para todos: minúsculas y
espacios colapsados.

## Cómo interpretar cada métrica

* **`cer` ↓** — caracteres erróneos / caracteres del ground truth. `0.0` = texto
  idéntico; `0.45` ≈ el 45 % de los caracteres no coinciden.
* **`wer` ↓** — igual que el CER, pero a nivel de palabra.
* **`word_f1` ↑** — F1 sobre el **multiconjunto** de palabras: no castiga que el
  OCR lineal y el ground truth recorran un formulario multicolumna en distinto
  orden. `1.0` = mismo vocabulario; `0.0` = ninguna palabra en común.
* **`exact_match` ↑** — coincidencia del texto completo normalizado. En OCR real
  suele ser `0.0`: falla un solo carácter y ya es `0`.
* **`ms/pág.` ↓** y **`págs/s` ↑** — velocidad (`mean_ms` y `1000 / mean_ms`).
* **`mean_confidence`** — confianza media que reporta cada motor. **No es
  comparable entre backends**: cada uno usa su propia escala.
* **`cer_std`** — desviación típica del CER entre imágenes; mide la dispersión,
  no la media.

El `report_benchmarks.py` marca en **negrita** el mejor backend por métrica y en
*cursiva* el segundo; solo agrega filas con `status = ok`.

**Qué métrica decide la marca.** Solo rankean `word_f1`, `cer_ord`, `wer_ord`,
`mean_ms` y `pages_per_s`. El `cer`/`wer` **crudos** se publican pero **no llevan
marca**: miden también el orden de lectura, y con un formulario multicolumna esa
penalización es inequitativa entre motores (B4/D1). La regla de orden del
*ground truth* (fila, luego columna) no coincide con el recorrido lineal que
produce un OCR, y castiga más a quien más se desvía de ella.

## Estado de la última ejecución registrada

Los artefactos de `output_examples/` que documentan esta página se generaron con
`report_benchmarks.py --run benchmarks/results/2026-10-25_22-26-51` — dataset FUNSD
`train`, `--limit 30`, `warmup = 1`, **30 imágenes medidas por backend** — en
**CPU**, sin GPU. Es la run posterior a la revisión metodológica de `B4`.

| Backend | Estado | Motivo |
| :--- | :--- | :--- |
| `pyocrust` | ok (30/30) | — |
| `rapidocr` | ok (30/30) | — |
| `easyocr` | ok (30/30) | — |
| `pyocrust_structure` | no incluido | faltan 6 artefactos del preset `pp_structurev3` |
| `tesseract` | no incluido | `pytesseract` + binario de Tesseract no instalados |

Tabla resultante (`output_examples/benchmark_table.md`, generada por el reportero):

| Backend | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|
| easyocr | 30 | 0.426 | 0.670 | 0.526 | 0.794 | 3247 | 0.31 |
| pyocrust | 30 | **0.745** | **0.325** | 0.487 | 0.670 | **643** | **1.56** |
| rapidocr | 30 | _0.607_ | _0.487_ | 0.482 | 0.699 | 4534 | 0.22 |

Lectura honesta: `pyocrust` gana en **F1 de palabra** (0.745), en **WER con orden
neutralizado** (0.325) y en **velocidad** (643 ms/página, 1.56 págs/s: ~7× más
rápido que `rapidocr` y ~5× que `easyocr`). El **CER crudo** lo sigue ganando
`rapidocr` (0.482 vs 0.487), pero esa columna mide también el orden de lectura
y **no decide la marca**; con el orden neutralizado `pyocrust` gana por 0.162.
Todo con el modelo **Tiny** (preset por defecto), en CPU y con n=30: indicios
sólidos, no un veredicto de paper.

Los valores agregados completos (incluidos `median_ms`, `p95_ms`, `cer_std` y
`mean_confidence`) están en `output_examples/benchmark_summary.json`.

> **Provenance.** `report_benchmarks.py` se puede re-ejecutar en cualquier
> momento, así que estos números son los que había en `output_examples/` cuando se
> escribió esta documentación (run `2026-10-25_22-07-24`). Una run posterior los
> sustituye.

## Limitaciones conocidas

* **Modelo Tiny.** `pyocrust` corre con el preset `pp_ocrv6` (PP-OCRv6), un
  modelo **Tiny**; no es la variante grande. Compararlo con el modelo por defecto
  de `rapidocr` **no es igual a igual** en capacidad.
* **Solo CPU.** La ejecución registrada no usa GPU (features `cuda`/`directml`
  sin activar); los milisegundos valen para CPU, no para un despliegue con GPU.
* **Muestra pequeña.** Se midieron **29 imágenes** (el defecto del runner es 20);
  hay `cer_std`, pero no intervalos de confianza ni test de significancia.
* **FUNSD solo en inglés.** Son formularios escaneados en inglés: el banco no
  mide español, manuscrito ni documentos largos.
* **Ground truth lineal.** FUNSD se linealiza ordenando las palabras por caja
  (fila y luego columna); el orden real de un OCR lineal no tiene por qué
  coincidir. Por eso la métrica que debería encabezar la calidad es `word_f1`
  (independiente del orden), no el CER.
* **Entrada distinta por backend.** `pyocrust` recibe los **bytes PNG
  re-codificados** de la imagen (`_image_bytes`); `rapidocr` recibe un array RGB
  de NumPy. No es la misma ruta de preprocesado y puede afectar al tiempo medido.
* **Cobertura parcial.** Corrieron tres backends (`pyocrust`, `rapidocr`,
  `easyocr`); siguen pendientes `pyocrust_structure` (faltan artefactos del preset
  `pp_structurev3`) y `tesseract` (no instalado).
* **Versiones no fijadas.** La run registra Python, plataforma y versión de
  `pyocrust` (`summary.json` → `runtime`), pero **no** fija la versión exacta de
  los modelos ONNX ni la de los baselines.
* **El reportero usa por defecto solo la run más reciente.** `report_benchmarks.py`
  sin `--run` lee únicamente la última carpeta de `results/` (comparaciones
  limpias); con `--all` agrega todas las runs y mezcla sus filas en una media.
