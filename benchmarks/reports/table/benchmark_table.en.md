# Benchmark: table

| Engine (variant/size) | n | Structural TEDS ↑ | ms/table ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **71** | Apache-2.0 |
| slanet_plus (default) | 20 | 0.780 | 796 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | <u>760</u> | MIT |
| tableformer (docling) | 20 | <u>0.807</u> | 32806 | MIT |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-08_18-43-55`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
