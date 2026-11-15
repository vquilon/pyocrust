# Benchmark: rectification

| Motor (variante/tamaño) | n | SSIM ↑ | ms/página ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 20 | 0.473 | **9** | Apache-2.0 |
| uvdoc (31.7M) | 20 | <u>0.590</u> | <u>71</u> | Apache-2.0 |
| uvdoc (onnxruntime) | 20 | **0.595** | 74 | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_21-24-42`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
