# Benchmark: formula

| Engine (variant/size) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 20 | <u>0.000</u> | 0.243 | 0.505 | N/A | **103** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.694** | **0.839** | N/A | 4453 | Apache-2.0 |
| pix2tex (default) | 20 | <u>0.000</u> | 0.460 | <u>0.669</u> | N/A | 5971 | MIT |
| pp-formulanet-s (direct) | 20 | <u>0.000</u> | <u>0.497</u> | 0.622 | N/A | <u>842</u> | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 20 | <u>0.000</u> | 0.196 | 0.295 | N/A | 1512 | Apache-2.0 |

> Note: `N/A` = not evaluated, never `0.0`. Values and n match `REPORT.md`; licenses are informational, per `../QUALITY_VS_TIME.md`.
