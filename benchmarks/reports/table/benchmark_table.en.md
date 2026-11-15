# Benchmark: table

| Engine (variant/size) | n | Structural TEDS ↑ | ms/table ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 8 | 0.882 | 1900 | Apache-2.0 |
| SLANet_plus (paddleocr) | 8 | 0.889 | <u>247</u> | Apache-2.0 |
| pp_structurev3 (default) | 8 | 0.753 | 1128 | Apache-2.0 |
| slanet_plus (7.8M) | 8 | 0.868 | **52** | Apache-2.0 |
| slanext_wired (367M) | 8 | **0.914** | 577 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | 718 | MIT |
| tableformer (docling) | 8 | <u>0.905</u> | 27457 | MIT |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_20-06-20`, device `cpu`, n ≤ 8); licenses are informational, per `../QUALITY_VS_TIME.md`.
