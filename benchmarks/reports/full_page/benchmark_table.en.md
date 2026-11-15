# Benchmark: full_page

| Engine (variant/size) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 6 | 0.427 | N/A | N/A | **1.000** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1.443 | 180058 | Apache-2.0 |
| docling-default (pipeline) | 6 | 0.512 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.509** | 26739 | MIT |
| indra (math) | 6 | **0.556** | N/A | N/A | <u>0.840</u> | N/A | N/A | N/A | N/A | N/A | **0.628** | N/A | N/A | N/A | N/A | N/A | N/A | <u>0.784</u> | **1251** | OpenRAIL-M-Mod |
| pp_structurev3 (default) | 6 | <u>0.530</u> | 0.725 | 0.762 | 0.735 | 0.401 | 0.875 | 0.875 | 0.942 | N/A | <u>0.512</u> | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.827 | 1.344 | <u>3652</u> | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_12-50-54`, device `cpu`, n ≤ 6); licenses are informational, per `../QUALITY_VS_TIME.md`.
