# Benchmark: formula

| Engine (variant/size) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.211 | 0.437 | N/A | **147** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.715** | **0.829** | N/A | 7397 | Apache-2.0 |
| pix2tex (default) | 20 | 0.000 | 0.585 | <u>0.759</u> | N/A | 11452 | MIT |
| pp-formulanet-s (direct) | 20 | <u>0.000</u> | 0.576 | 0.701 | N/A | <u>874</u> | Apache-2.0 |
| pp_structurev3 (default) | 20 | 0.000 | 0.399 | 0.560 | N/A | 2336 | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | <u>0.607</u> | 0.746 | N/A | 2191 | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-08_16-01-52`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
