# Benchmark: formula

| Engine (variant/size) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 10 | 0.000 | 0.326 | 0.575 | N/A | **141** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 10 | 0.000 | **0.653** | **0.799** | N/A | 16326 | Apache-2.0 |
| pix2tex (default) | 10 | 0.000 | <u>0.552</u> | <u>0.777</u> | N/A | 5500 | MIT |
| pp-formulanet-s (direct) | 10 | 0.000 | 0.499 | 0.652 | N/A | <u>998</u> | Apache-2.0 |
| pp_structurev3 (default) | 10 | 0.000 | 0.398 | 0.613 | N/A | 2774 | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 10 | 0.000 | 0.497 | 0.708 | N/A | 2474 | Apache-2.0 |
| unimernet (tiny) | 10 | 0.000 | 0.260 | 0.385 | N/A | 17493 | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-09_14-13-57`, device `cpu`, n ≤ 10); licenses are informational, per `../QUALITY_VS_TIME.md`.
