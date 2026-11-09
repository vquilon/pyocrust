# Benchmark: full_page

| Motor (variante/tamaño) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 6 | **0.204** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **1.119** | 25723 | MIT |
| indra (math) | 6 | 0.029 | N/A | N/A | <u>0.276</u> | N/A | N/A | N/A | N/A | N/A | <u>0.190</u> | N/A | N/A | N/A | N/A | N/A | N/A | <u>3.102</u> | **607** | OpenRAIL-M-Mod |
| pp_structurev3 (default) | 6 | <u>0.083</u> | 0.524 | 0.561 | **0.678** | 0.255 | 0.944 | 1.000 | 0.536 | 0.857 | **0.764** | 0.167 | 0.333 | 0.875 | 1.000 | 0.000 | 0.417 | 5.737 | <u>5865</u> | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-09_14-28-38`, device `cpu`, n ≤ 6); licencias informativas según `../QUALITY_VS_TIME.md`.
