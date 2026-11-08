# Benchmark: seal

| Motor (variante/tamaño) | n | recall@IoU 0.5 ↑ | IoU medio ↑ | ms/imagen ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: |
| pp-ocrv4_mobile_seal_det (4.8M) | 20 | 0.750 | **0.686** | <u>643</u> | Apache-2.0 |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 20 | 0.750 | <u>0.607</u> | **217** | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-08_15-28-48`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
