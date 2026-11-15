# Benchmark: text

| Engine (variant/size) | n | Word F1 ↑ | Ordered WER ↓ | CER ↓ | WER ↓ | box recall ↑ | Mean IoU ↑ | ms/img ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-OCRv6 (medium) | 20 | **0.796** | **0.266** | **0.473** | **0.644** | 0.039 | 0.115 | 19361 | Apache-2.0 |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | <u>3701</u> | Apache-2.0 |
| pp_ocrv6 (tiny) | 20 | <u>0.717</u> | <u>0.360</u> | 0.483 | <u>0.675</u> | <u>0.047</u> | <u>0.120</u> | **332** | Apache-2.0 |
| rapidocr (default) | 20 | 0.585 | 0.512 | <u>0.476</u> | 0.701 | 0.037 | 0.108 | 4710 | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_11-52-57`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
