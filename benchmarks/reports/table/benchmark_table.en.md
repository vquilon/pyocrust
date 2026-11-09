# Benchmark: table

| Engine (variant/size) | n | Structural TEDS ↑ | ms/table ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **87** | Apache-2.0 |
| pp_structurev3 (default) | 20 | 0.608 | 3245 | Apache-2.0 |
| slanet_plus (default) | 20 | 0.780 | 848 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | <u>198</u> | MIT |
| tableformer (docling) | 20 | <u>0.807</u> | 35699 | MIT |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-09_11-00-34`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
