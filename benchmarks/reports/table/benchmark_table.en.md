# Benchmark: table

| Engine (variant/size) | n | Structural TEDS ↑ | ms/table ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 8 | 0.889 | **72** | Apache-2.0 |
| pp_structurev3 (default) | 8 | 0.753 | 3530 | Apache-2.0 |
| slanet_plus (default) | 8 | **0.914** | 1103 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | <u>131</u> | MIT |
| tableformer (docling) | 8 | <u>0.905</u> | 28609 | MIT |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-09_14-22-58`, device `cpu`, n ≤ 8); licenses are informational, per `../QUALITY_VS_TIME.md`.
