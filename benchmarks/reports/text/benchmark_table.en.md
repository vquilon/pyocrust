# Benchmark: text

| Engine (variant/size) | n | Word F1 ↑ | Ordered WER ↓ | CER ↓ | WER ↓ | box recall ↑ | Mean IoU ↑ | ms/img ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-OCRv6 (medium) | 20 | <u>0.796</u> | <u>0.266</u> | 0.473 | <u>0.644</u> | 0.039 | 0.115 | 19811 | Apache-2.0 |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | 3662 | Apache-2.0 |
| pp_ocrv6 (medium) | 20 | **0.800** | **0.260** | **0.472** | **0.643** | 0.042 | 0.116 | 2138 | Apache-2.0 |
| pp_ocrv6 (small) | 20 | 0.784 | 0.280 | <u>0.472</u> | 0.650 | 0.042 | 0.117 | <u>823</u> | Apache-2.0 |
| pp_ocrv6 (tiny) | 20 | 0.717 | 0.360 | 0.483 | 0.675 | <u>0.047</u> | <u>0.120</u> | **318** | Apache-2.0 |
| rapidocr (default) | 20 | 0.585 | 0.512 | 0.476 | 0.701 | 0.037 | 0.108 | 4807 | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_20-11-47`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
