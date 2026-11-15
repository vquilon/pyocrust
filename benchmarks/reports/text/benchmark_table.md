# Benchmark: text

| Motor (variante/tamaño) | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | box recall ↑ | IoU medio ↑ | ms/img ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-OCRv6 (medium) | 20 | <u>0.796</u> | <u>0.266</u> | 0.473 | <u>0.644</u> | 0.039 | 0.115 | 19163 | Apache-2.0 |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | 3167 | Apache-2.0 |
| pp_ocrv6 (medium) | 20 | **0.800** | **0.260** | **0.472** | **0.643** | 0.042 | 0.116 | 2223 | Apache-2.0 |
| pp_ocrv6 (small) | 20 | 0.784 | 0.280 | <u>0.472</u> | 0.650 | 0.042 | 0.117 | <u>866</u> | Apache-2.0 |
| pp_ocrv6 (tiny) | 20 | 0.717 | 0.360 | 0.483 | 0.675 | <u>0.047</u> | <u>0.120</u> | **336** | Apache-2.0 |
| rapidocr (default) | 20 | 0.585 | 0.512 | 0.476 | 0.701 | 0.037 | 0.108 | 4286 | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_12-06-10`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
