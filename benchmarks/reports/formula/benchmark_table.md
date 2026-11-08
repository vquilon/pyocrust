# Benchmark: formula

| Motor (variante/tamaño) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.211 | 0.437 | N/A | **147** | OpenRAIL-M-Mod |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.715** | **0.829** | N/A | 7397 | Apache-2.0 |
| pix2tex (default) | 20 | 0.000 | 0.585 | <u>0.759</u> | N/A | 11452 | MIT |
| pp-formulanet-s (direct) | 20 | <u>0.000</u> | 0.576 | 0.701 | N/A | <u>874</u> | Apache-2.0 |
| pp_structurev3 (default) | 20 | 0.000 | 0.399 | 0.560 | N/A | 2336 | Apache-2.0 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | <u>0.607</u> | 0.746 | N/A | 2191 | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-08_16-01-52`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
