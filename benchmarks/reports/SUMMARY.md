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
| paddle_latex_ocr | 0.715 | 20 | medido | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | 0.607 | 20 | medido | Apache-2.0 |
| pix2tex | 0.587 | 20 | medido | MIT |
| **pp-formulanet-s (direct)** | 0.576 | 20 | medido | Apache-2.0 |
| **pp_structurev3** | 0.399 | 20 | medido | Apache-2.0 |
| unimernet (tiny) | 0.238 | 20 | medido | Apache-2.0 |
| **indra (math)** | 0.211 | 20 | medido | OpenRAIL-M-Mod |

## layout — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_layout`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | 0.747 | 40 | medido |  |
| **pp-doclayoutv3 (130M)** | 0.669 | 40 | medido | Apache-2.0 |
| **pp_structurev3** | 0.638 | 40 | medido | Apache-2.0 |
| armaggheddon/y26-n (2.6M) | 0.521 | 40 | medido | MIT |
| hantian/v10-m | 0.497 | 40 | medido | AGPL-3.0 |
| hantian/v12-n | 0.489 | 40 | medido | AGPL-3.0 |
| hantian/v8-n | 0.473 | 40 | medido | AGPL-3.0 |
| armaggheddon/y11-m | 0.472 | 40 | medido | MIT |
| hantian/v8-x | 0.426 | 40 | medido | AGPL-3.0 |

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
| SLANet_plus (paddleocr) | 0.828 | 20 | medido | Apache-2.0 |
| tableformer (docling) | 0.807 | 20 | medido | MIT |
| **slanet_plus** | 0.780 | 20 | medido | Apache-2.0 |
| table-transformer-structure-recognition | 0.698 | 20 | medido | MIT |
| **pp_structurev3** | 0.608 | 20 | medido | Apache-2.0 |

## full_page — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_full_page`

| Motor | Valor | n | Origen | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-default (pipeline) | 0.354 | 20 | medido | MIT |
| **pp_structurev3** | 0.270 | 20 | medido | Apache-2.0 |
| **indra (math)** | 0.265 | 20 | medido | OpenRAIL-M-Mod |
