# Benchmark: table

| Motor (variante/tamaño) | n | TEDS estrut. ↑ | ms/tabla ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 8 | 0.919 | **34191** | MIT |
| LightOnOCR-2-1B (1B) | 8 | 0.858 | 58834 | Apache-2.0 |
| LightOnOCR-3 (0.8B) | 8 | <u>0.926</u> | 162056 | Apache-2.0 |
| LightOnOCR-3 (4B) | 8 | 0.847 | 76940 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 8 | **0.933** | <u>35839</u> | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_18-13-46`, device `gpu`, n ≤ 8); licencias informativas según `../QUALITY_VS_TIME.md`.
