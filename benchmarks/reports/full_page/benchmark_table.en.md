# Benchmark: full_page

| Engine (variant/size) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 6 | **0.204** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **1.119** | 25723 | MIT |
| indra (math) | 6 | 0.029 | N/A | N/A | <u>0.276</u> | N/A | N/A | N/A | N/A | N/A | <u>0.190</u> | N/A | N/A | N/A | N/A | N/A | N/A | <u>3.102</u> | **607** | OpenRAIL-M-Mod |
| pp_structurev3 (default) | 6 | <u>0.083</u> | 0.524 | 0.561 | **0.678** | 0.255 | 0.944 | 1.000 | 0.536 | 0.857 | **0.764** | 0.167 | 0.333 | 0.875 | 1.000 | 0.000 | 0.417 | 5.737 | <u>5865</u> | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-09_14-28-38`, device `cpu`, n ≤ 6); licenses are informational, per `../QUALITY_VS_TIME.md`.
