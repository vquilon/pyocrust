# Resumen de benchmarks — 9 features (`medido` + `referencia`)

> `medido` = ejecutado en este repo · `referencia` = publicado en un paper (con URL),
> **no comparable 1:1** · `pendiente` = aún sin datos. Una barra rayada es referencia.

## text — FUNSD — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust (tiny)** | 0.734 | medido |
| rapidocr (default) | 0.660 | medido |
| easyocr (default) | 0.384 | medido |
| RapidOCR | 56.980 | referencia [ref: https://arxiv.org/abs/2502.06445] |
| EasyOCR | 49.300 | referencia [ref: https://arxiv.org/abs/2502.06445] |

## formula — OmniDocBench — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_formulanet (direct)** | 0.550 | medido |
| pix2tex (default) | 0.533 | medido |
| **pyocrust_formula (pp-formulanet-s)** | 0.419 | medido |
| **pyocrust_indra (math)** | 0.184 | medido |
| easyocr (default) | 0.152 | medido |
| rapidocr (default) | 0.104 | medido |
| texify | 0.842 | referencia [ref: https://github.com/VikParuchuri/texify] |
| nougat | 0.698 | referencia [ref: https://github.com/VikParuchuri/texify] |
| pix2tex | 0.383 | referencia [ref: https://github.com/VikParuchuri/texify] |

## layout — DocLayNet — `referencia`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| Docling heron-101 | 0.780 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| RT-DETR (Docling) | 0.758 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| Docling heron | 0.699 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| YOLO-doclaynet (MinerU) | 0.675 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| Surya | 0.404 | referencia [ref: https://arxiv.org/abs/2502.14949] |

## orientation — `pendiente`

_Sin datos ni referencia todavía._

## rectification — `pendiente`

_Sin datos ni referencia todavía._

## text_line — `pendiente`

_Sin datos ni referencia todavía._

## seal — `pendiente`

_Sin datos ni referencia todavía._

## table — PubTabNet — `referencia`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| TATR (PubTables-1M+FinTabNet.c) | 0.965 | referencia [ref: https://docling.ai/papers/] |
| TATR-v1.1-Pub | 0.961 | referencia [ref: https://docling.ai/papers/] |
| TableFormer | 0.950 | referencia [ref: https://docling.ai/papers/] |

## full_page — OmniDocBench — `referencia`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| MinerU2.5-Pro | 95.750 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| MinerU-2.5 | 93.040 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| MinerU-Pipeline | 86.470 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| PaddleOCR (OCR-based) | 73.600 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
