# Benchmark: full_page

| Motor (variante/tamaño) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | **0.354** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.518** | <u>29302</u> | MIT |
| pp_structurev3 (default) | 20 | <u>0.270</u> | 0.700 | 0.677 | 0.674 | 0.351 | 0.702 | 0.652 | 0.649 | 0.750 | 0.661 | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.500 | <u>2.190</u> | **9769** | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-08_17-40-47`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
