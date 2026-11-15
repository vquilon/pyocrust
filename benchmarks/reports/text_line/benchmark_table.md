# Benchmark: text_line

| Motor (variante/tamaño) | n | accuracy ↑ | ms/línea ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| ch_ppocr_mobile_v2.0_cls (rapidocr) | 20 | 90.0% | 3 | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (6.8M) | 20 | **100.0%** | <u>3</u> | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | 20 | <u>100.0%</u> | **2** | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-15_20-30-55`, device `cpu`, n ≤ 20); licencias informativas según `../QUALITY_VS_TIME.md`.
