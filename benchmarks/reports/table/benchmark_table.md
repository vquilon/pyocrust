# Benchmark: table

| Motor (variante/tamaño) | n | TEDS estrut. ↑ | ms/tabla ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 8 | 0.889 | **72** | Apache-2.0 |
| pp_structurev3 (default) | 8 | 0.753 | 3530 | Apache-2.0 |
| slanet_plus (default) | 8 | **0.914** | 1103 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | <u>131</u> | MIT |
| tableformer (docling) | 8 | <u>0.905</u> | 28609 | MIT |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-09_14-22-58`, device `cpu`, n ≤ 8); licencias informativas según `../QUALITY_VS_TIME.md`.
