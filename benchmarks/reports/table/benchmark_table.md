# Benchmark: table

| Motor (variante/tamaño) | n | TEDS estrut. ↑ | ms/tabla ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **71** | Apache-2.0 |
| slanet_plus (default) | 20 | 0.780 | 796 | Apache-2.0 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | <u>760</u> | MIT |
| tableformer (docling) | 20 | <u>0.807</u> | 32806 | MIT |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-08_18-43-55`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
