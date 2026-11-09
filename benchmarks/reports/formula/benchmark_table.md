# Benchmark: formula

| Motor (variante/tamaño) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 10 | 0.000 | 0.326 | 0.575 | N/A | **141** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 10 | 0.000 | **0.653** | **0.799** | N/A | 16326 | Apache-2.0 |
| pix2tex (default) | 10 | 0.000 | <u>0.552</u> | <u>0.777</u> | N/A | 5500 | MIT |
| pp-formulanet-s (direct) | 10 | 0.000 | 0.499 | 0.652 | N/A | <u>998</u> | Apache-2.0 |
| pp_structurev3 (default) | 10 | 0.000 | 0.398 | 0.613 | N/A | 2774 | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 10 | 0.000 | 0.497 | 0.708 | N/A | 2474 | Apache-2.0 |
| unimernet (tiny) | 10 | 0.000 | 0.260 | 0.385 | N/A | 17493 | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-09_14-13-57`, device `cpu`, n ≤ 10); licencias informativas según `../QUALITY_VS_TIME.md`.
