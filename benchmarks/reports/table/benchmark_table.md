# Benchmark: table

| Motor (variante/tamaño) | n | TEDS estrut. ↑ | ms/tabla ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 8 | 0.882 | 1900 | Apache-2.0 |
| SLANet_plus (paddleocr) | 8 | 0.889 | <u>247</u> | Apache-2.0 |
| pp_structurev3 (default) | 8 | 0.753 | 1128 | Apache-2.0 |
| slanet_plus (7.8M) | 8 | 0.868 | **52** | Apache-2.0 |
| slanext_wired (367M) | 8 | **0.914** | 577 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | 718 | MIT |
| tableformer (docling) | 8 | <u>0.905</u> | 27457 | MIT |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_20-06-20`, device `cpu`, n ≤ 8); licencias informativas según `../QUALITY_VS_TIME.md`.
