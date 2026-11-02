# Resumen de benchmarks — 9 features (`medido` + `referencia`)

> `medido` = ejecutado en este repo · `referencia` = publicado en un paper (con URL),
> **no comparable 1:1** · `pendiente` = aún sin datos. Una barra rayada es referencia.

## text — FUNSD — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust (tiny)** | 0.734 | medido |
| rapidocr (default) | 0.660 | medido |
| easyocr (default) | 0.384 | medido |

## formula — OmniDocBench — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_formulanet (direct)** | 0.550 | medido |
| pix2tex (default) | 0.489 | medido |
| **pyocrust_formula (pp-formulanet-s)** | 0.419 | medido |
| easyocr (default) | 0.152 | medido |
| rapidocr (default) | 0.104 | medido |

## layout — DocLayNet — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_layout (default)** | 0.764 | medido |
| docling_heron_101 (default) | 0.508 | medido |
| YOLOv10-x (DocLayNet fine-tune) | 0.924 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-b (DocLayNet fine-tune) | 0.922 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-l (DocLayNet fine-tune) | 0.921 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-m (DocLayNet fine-tune) | 0.917 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-s (DocLayNet fine-tune) | 0.905 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-n (DocLayNet fine-tune) | 0.892 | referencia [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| DocLayout-YOLO | 0.797 | referencia [ref: https://arxiv.org/abs/2410.12628] |
| Docling heron-101 | 0.780 | referencia [ref: https://arxiv.org/abs/2509.11720] |
| RT-DETR (Docling) | 0.758 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| Docling heron | 0.699 | referencia [ref: https://arxiv.org/abs/2509.11720] |
| YOLO-doclaynet (MinerU) | 0.675 | referencia [ref: https://arxiv.org/abs/2502.14949] |
| Surya | 0.404 | referencia [ref: https://arxiv.org/abs/2502.14949] |

## orientation — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| lcnet_doc_ori (onnxruntime) | 1.000 | medido |
| **pyocrust_orientation (default)** | 1.000 | medido |
| PP-LCNet_x1_0_doc_ori (4 clases: 0/90/180/270°) | 0.991 | referencia [ref: https://paddlepaddle.github.io/PaddleX/latest/en/pipeline_usage/tutorials/ocr_pipelines/PP-StructureV3.html] |

## rectification — `medido`

> ⚠️ **ref = CER↓ (otra métrica; no comparable con SSIM↑)**

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_rectify (default)** | 0.704 | medido |
| uvdoc (onnxruntime) | 0.701 | medido |
| UVDoc | 0.179 | referencia [ref: https://paddlepaddle.github.io/PaddleX/latest/en/pipeline_usage/tutorials/ocr_pipelines/PP-StructureV3.html] |

## text_line — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| lcnet_textline_ori (onnxruntime) | 1.000 | medido |
| **pyocrust_textline (default)** | 1.000 | medido |
| PP-LCNet_x1_0_textline_ori | 0.994 | referencia [ref: https://paddlepaddle.github.io/PaddleX/latest/en/pipeline_usage/tutorials/ocr_pipelines/OCR.html] |
| PP-LCNet_x0_25_textline_ori | 0.989 | referencia [ref: https://paddlepaddle.github.io/PaddleX/latest/en/pipeline_usage/tutorials/ocr_pipelines/OCR.html] |

## seal — sintético — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_seal (default)** | 0.750 | medido |

## table — PubTabNet — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_table (default)** | 0.885 | medido |
| tatr (default) | 0.737 | medido |
| TATR (PubTables-1M+FinTabNet.c) | 0.965 | referencia [ref: https://ar5iv.labs.arxiv.org/html/2303.00716] |
| TATR-v1.1-Pub | 0.961 | referencia [ref: https://arxiv.org/html/2512.10888v1] |
| TableFormer | 0.950 | referencia [ref: https://docling.ai/papers/] |

## full_page — OmniDocBench — `medido`

| Motor | Valor | Origen |
| :--- | ---: | :--- |
| **pyocrust_indra (math)** | 0.176 | medido |
| **pyocrust_structure (default)** | 0.158 | medido |
| MinerU2.5-Pro | 95.750 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| MinerU-2.5 | 93.040 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| MinerU-Pipeline | 86.470 | referencia [ref: https://github.com/OpenDataLab/OmniDocBench] |
| PaddleOCR (OCR-based) | 73.600 | referencia [ref: https://arxiv.org/html/2412.07626v2] |
