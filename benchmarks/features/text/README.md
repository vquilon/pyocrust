# Feature `text` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ejecutado por nosotros en este repo. El
> `summary.json` de cada run guarda comando, dataset, `n`, `warmup`, `repeats`,
> dispositivo y fecha. No hay referencias externas en este banco.

## Qué mide

Detección + reconocimiento de texto, como el componente `text` de `oar-ocr`: un
motor resuelve las dos cosas. Se miden las **dos caras** del mismo motor:

* **Reconocimiento**: `cer`, `wer`, `word_f1` y `cer_ord`/`wer_ord` (estos dos
  neutralizan el orden de lectura para no castigar la disposición de un formulario
  multicolumna).
* **Detección**: `box_recall` (fracción de cajas GT con una predicción a ≥0.5 de
  IoU) y `box_iou_mean` (IoU medio del mejor candidato por caja GT). Solo cuando
  el dataset anota cajas (FUNSD); si no, la columna queda **vacía** (no evaluada,
  nunca un `0.0`).

## Tarea `pyocrust`

`text_detection` + `text_recognition` (`VeloceOCR` con el preset `pp_ocrv6`,
modelo Tiny por defecto).

## Dataset

* `funsd` (por defecto) — formularios escaneados con GT de texto **y cajas**
  anotadas: permite medir detección.
* `omnidocbench` — páginas documentales reales con GT de texto por orden de
  lectura (no trae cajas por palabra; la columna de cajas queda vacía).

## Alternativas Python reales (a comparar)

| Alternativa | `pip install` | Estado aquí |
| :--- | :--- | :--- |
| rapidocr | `rapidocr-onnxruntime` | integrado |
| easyocr | `easyocr` (requiere torch) | integrado |
| tesseract | `pytesseract` + binario Tesseract | `skipped` (no instalado) |
| surya | `surya-ocr` | `skipped` (adaptador pendiente) |
| paddleocr | `paddleocr paddlepaddle` | `skipped` (adaptador pendiente) |
| doctrl | `doctrl` | `skipped` (adaptador pendiente) |

Las no instaladas quedan **`skipped` con motivo** en el `summary.json`, nunca
como `ok`.

## Cómo correrlo

```bash
# FUNSD (texto + cajas), 5 imágenes, un backend a la vez, CPU
.venv/Scripts/python.exe benchmarks/features/text/bank.py --limit 5 \
  --backends pyocrust,rapidocr,easyocr,tesseract

# Páginas documentales reales (GT de texto por orden de lectura)
.venv/Scripts/python.exe benchmarks/features/text/bank.py --dataset omnidocbench --limit 10 \
  --backends pyocrust,rapidocr,easyocr
```

Salida: `benchmarks/results/text/<timestamp>/` (CSV de 28 columnas + `summary.json`
+ `<backend>.meta.json`). Los artefactos crudos **no se versionan**.

## Provenance

Todos los números de este banco son **`medido`**. Para citarlos: comando exacto +
dataset + `n` + `warmup` + `repeats` + `device` + fecha (todo en el `summary.json`
de la run). Si en el futuro se añade una fila de **`referencia`** (externo), irá
con `[ref: <url> (consultado YYYY-MM-DD)]` y nunca mezclada sin etiquetar.
