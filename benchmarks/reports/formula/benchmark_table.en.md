# Benchmark: formula

| Engine (variant/size) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 10 | 0.000 | 0.326 | 0.575 | N/A | **82** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 10 | 0.000 | **0.653** | **0.799** | N/A | 11331 | Apache-2.0 |
| pix2tex (default) | 10 | 0.000 | <u>0.555</u> | <u>0.793</u> | N/A | 4659 | MIT |
| pp-formulanet-s (direct) | 10 | 0.000 | 0.499 | 0.652 | N/A | <u>696</u> | Apache-2.0 |
| pp_structurev3 (default) | 10 | 0.000 | 0.398 | 0.613 | N/A | 1028 | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 10 | 0.000 | 0.497 | 0.708 | N/A | 1052 | Apache-2.0 |
| unimernet (tiny) | 10 | 0.000 | 0.260 | 0.385 | N/A | 14927 | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_20-24-00`, device `cpu`, n ≤ 10); licenses are informational, per `../QUALITY_VS_TIME.md`.
