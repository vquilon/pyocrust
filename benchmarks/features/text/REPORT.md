# Reporte por feature: `text`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/text/bank.py --limit 5 --warmup 1 --backends pyocrust,rapidocr,easyocr,tesseract,surya,paddleocr,doctrl`
- **dataset**: `funsd` · **n** (por motor): `5` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/text/2026-11-01_22-56-05` · **fecha**: `2026-11-01_22-56-05`
- **runtime**: {'python': '3.14.9', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0'}

## Comparativa (media por motor)

| Motor (variante) | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | box recall ↑ | IoU medio ↑ | ms/img ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 5 | 0.384 | 0.707 | 0.467 | 0.789 | **0.056** | **0.155** | 6282 |
| pyocrust (tiny) | 5 | **0.734** | **0.340** | 0.402 | **0.628** | 0.042 | 0.116 | **1123** |
| rapidocr (default) | 5 | 0.660 | 0.431 | **0.400** | 0.654 | 0.040 | 0.107 | 8321 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `text`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `doctrl` — pip install doctrl
- `paddleocr` — pip install paddleocr paddlepaddle
- `surya` — pip install surya-ocr (requiere torch)
- `tesseract` — pip install pytesseract + binario Tesseract

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).

