# Benchmark: full_page

| Engine (variant/size) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | **0.354** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.518** | 33257 | MIT |
| indra (math) | 20 | 0.265 | N/A | N/A | <u>0.361</u> | N/A | N/A | N/A | N/A | N/A | **0.747** | N/A | N/A | N/A | N/A | N/A | N/A | <u>1.231</u> | **2006** | OpenRAIL-M-Mod |
| pp_structurev3 (default) | 20 | <u>0.270</u> | 0.700 | 0.677 | **0.674** | 0.351 | 0.702 | 0.652 | 0.649 | 0.750 | <u>0.661</u> | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.500 | 2.190 | <u>11054</u> | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-09_12-43-20`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
