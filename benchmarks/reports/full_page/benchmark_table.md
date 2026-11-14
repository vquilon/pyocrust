# Benchmark: full_page

| Motor (variante/tamaño) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 6 | 0.559 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.850 | 151850 | MIT |
| LightOnOCR-2-1B (1B) | 6 | <u>0.590</u> | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1.241 | 151454 | Apache-2.0 |
| PP-StructureV3 (paddleocr) | 6 | 0.427 | N/A | N/A | **1.000** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1.443 | 176264 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 4 | **0.669** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | <u>0.514</u> | 430548 | Apache-2.0 |
| docling-default (pipeline) | 6 | 0.512 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.509** | 26023 | MIT |
| indra (math) | 6 | 0.556 | N/A | N/A | <u>0.840</u> | N/A | N/A | N/A | N/A | N/A | **0.628** | N/A | N/A | N/A | N/A | N/A | N/A | 0.784 | **1253** | OpenRAIL-M-Mod |
| pp_structurev3 (default) | 6 | 0.530 | 0.725 | 0.762 | 0.735 | 0.401 | 0.875 | 0.875 | 0.942 | N/A | <u>0.512</u> | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.827 | 1.344 | <u>3527</u> | Apache-2.0 |

> Nota: `N/A` = **no evaluada** — sin GT de esa columna, o el motor no emite esa estructura (p. ej. `docling`, que solo emite Markdown); `0.000` = **evaluada** y el motor no acertó, nunca un `0.0` sin medir. Cifras y n reproducen `REPORT.md` (run `2026-11-14_18-38-10`, device `cpu`, n ≤ 6); licencias informativas según `../QUALITY_VS_TIME.md`.
