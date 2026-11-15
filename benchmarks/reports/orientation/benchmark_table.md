# Benchmark: orientation

| Motor (variante/tamaño) | n | accuracy ↑ | ms/página ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| craft_mlt_25k+latin_g2 (easyocr) | 20 | 35.0% | 43311 | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (6.8M) | 20 | **100.0%** | <u>60</u> | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 20 | <u>100.0%</u> | **4** | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_21-08-32`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
