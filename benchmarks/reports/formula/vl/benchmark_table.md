# Benchmark: formula

| Motor (variante/tamaño) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 10 | 0.000 | **0.748** | **0.881** | N/A | <u>18719</u> | MIT |
| LightOnOCR-2-1B (1B) | 10 | 0.000 | 0.597 | 0.777 | N/A | 20186 | Apache-2.0 |
| LightOnOCR-3 (0.8B) | 10 | 0.000 | 0.550 | 0.749 | N/A | 24073 | Apache-2.0 |
| LightOnOCR-3 (4B) | 10 | 0.000 | 0.612 | 0.780 | N/A | 30950 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 10 | 0.000 | <u>0.614</u> | <u>0.843</u> | N/A | **17524** | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_19-06-25`, device `gpu`, n ≤ 10); licencias informativas según `../QUALITY_VS_TIME.md`.
