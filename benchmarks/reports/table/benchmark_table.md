# Benchmark: table

| Motor (variante/tamaño) | n | TEDS estrut. ↑ | ms/tabla ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **87** | Apache-2.0 |
| pp_structurev3 (default) | 20 | 0.608 | 3245 | Apache-2.0 |
| slanet_plus (default) | 20 | 0.780 | 848 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | <u>198</u> | MIT |
| tableformer (docling) | 20 | <u>0.807</u> | 35699 | MIT |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-09_11-00-34`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
