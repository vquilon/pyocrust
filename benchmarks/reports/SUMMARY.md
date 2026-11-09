# Resumen de benchmarks — 9 features (solo `medido`)

> `medido` = ejecutado en este repo · `pendiente` = aún sin datos.
> **No se publican referencias externas**: una calidad medida sobre otro
> dataset/GT no es comparable, así que no entra en ninguna tabla ni gráfica.
> Una fila por motor sobre **su mismo dataset** (el device solo se publica en los informes con tiempos). El `n` se declara por fila.
> `license` es **informativa** (señala las no permisivas, p. ej. AGPL-3.0); la puerta solo aplica a los modelos de `pyocrust`.

## text — FUNSD — `medido` · **dataset medido**: `funsd`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp_ocrv6 (tiny)** | 0.717 | 20 | medido | Apache-2.0 |
| rapidocr | 0.585 | 20 | medido | Apache-2.0 |
| easyocr | 0.401 | 20 | medido | Apache-2.0 |

## formula — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_formula`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| paddle_latex_ocr | 0.653 | 10 | medido | Apache-2.0 |
| pix2tex | 0.552 | 10 | medido | MIT |
| **pp-formulanet-s (direct)** | 0.499 | 10 | medido | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | 0.497 | 10 | medido | Apache-2.0 |
| **pp_structurev3** | 0.398 | 10 | medido | Apache-2.0 |
| **indra (math)** | 0.326 | 10 | medido | OpenRAIL-M-Mod |
| unimernet (tiny) | 0.260 | 10 | medido | Apache-2.0 |

## layout — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_layout`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | 0.818 | 40 | medido |  |
| **pp-doclayoutv3 (130M)** | 0.796 | 40 | medido | Apache-2.0 |
| **pp_structurev3** | 0.751 | 40 | medido | Apache-2.0 |
| armaggheddon/y26-n (2.6M) | 0.572 | 40 | medido | MIT |
| hantian/v12-l | 0.550 | 40 | medido | AGPL-3.0 |
| hantian/v8-n | 0.545 | 40 | medido | AGPL-3.0 |
| armaggheddon/y11-m | 0.542 | 40 | medido | MIT |
| hantian/v10-l | 0.533 | 40 | medido | AGPL-3.0 |
| hantian/v8-x | 0.490 | 40 | medido | AGPL-3.0 |

## orientation — sintético — `medido` · **dataset medido**: `synthetic_orientation`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | 1.000 | 20 | medido | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 20 | medido | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 20 | medido | Apache-2.0 |

## rectification — sintético — `medido` · **dataset medido**: `synthetic_rectification`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| uvdoc (onnxruntime) | 0.604 | 20 | medido | Apache-2.0 |
| **uvdoc (31.7M)** | 0.597 | 20 | medido | Apache-2.0 |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 20 | medido | Apache-2.0 |

## text_line — sintético — `medido` · **dataset medido**: `synthetic_text_line`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | 1.000 | 20 | medido | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 20 | medido | Apache-2.0 |

## seal — sintético — `medido` · **dataset medido**: `synthetic_seal`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | 0.750 | 20 | medido | Apache-2.0 |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 20 | medido | Apache-2.0 |

## table — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_table`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| **slanet_plus** | 0.914 | 8 | medido | Apache-2.0 |
| tableformer (docling) | 0.905 | 8 | medido | MIT |
| SLANet_plus (paddleocr) | 0.889 | 8 | medido | Apache-2.0 |
| table-transformer-structure-recognition | 0.790 | 8 | medido | MIT |
| **pp_structurev3** | 0.753 | 8 | medido | Apache-2.0 |

## full_page — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_full_page`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-default (pipeline) | 0.204 | 6 | medido | MIT |
| PP-StructureV3 (paddleocr) | 0.086 | 6 | medido | Apache-2.0 |
| **pp_structurev3** | 0.083 | 6 | medido | Apache-2.0 |
| **indra (math)** | 0.029 | 6 | medido | OpenRAIL-M-Mod |
