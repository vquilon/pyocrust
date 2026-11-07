# Benchmark: text

| Motor (variante/tamaño) | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | box recall ↑ | IoU medio ↑ | ms/img ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | <u>4600</u> | Apache-2.0 |
| pp_ocrv6 (tiny) | 20 | **0.717** | **0.360** | <u>0.483</u> | **0.675** | <u>0.047</u> | <u>0.120</u> | **970** | Apache-2.0 |
| rapidocr (default) | 20 | <u>0.585</u> | <u>0.512</u> | **0.476** | <u>0.701</u> | 0.037 | 0.108 | 6748 | Apache-2.0 |

> Nota: `N/A` = no evaluada, nunca `0.0`. Cifras y n reproducen `REPORT.md`; licencias informativas según `../QUALITY_VS_TIME.md`.
