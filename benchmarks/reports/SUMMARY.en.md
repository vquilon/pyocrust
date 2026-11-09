# Benchmark summary — 9 features (`measured` only)

> `measured` = run in this repository · `pending` = no data yet.
> **No external references are published**: a quality measured on a different
> dataset/ground truth is not comparable, so it never enters any table or figure.
> Una fila per engine sobre **su mismo dataset** (el device solo se publica en los informes con tiempos). El `n` se declara por fila.
> `license` is **informational** (flags non-permissive licenses, e.g. AGPL-3.0); the gate applies only to `pyocrust` models.

## text — FUNSD — `measured` · **measured dataset**: `funsd`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp_ocrv6 (tiny)** | 0.717 | 20 | measured | Apache-2.0 |
| rapidocr | 0.585 | 20 | measured | Apache-2.0 |
| easyocr | 0.401 | 20 | measured | Apache-2.0 |

## formula — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_formula`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| paddle_latex_ocr | 0.715 | 20 | measured | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | 0.607 | 20 | measured | Apache-2.0 |
| pix2tex | 0.587 | 20 | measured | MIT |
| **pp-formulanet-s (direct)** | 0.576 | 20 | measured | Apache-2.0 |
| **pp_structurev3** | 0.399 | 20 | measured | Apache-2.0 |
| unimernet (tiny) | 0.238 | 20 | measured | Apache-2.0 |
| **indra (math)** | 0.211 | 20 | measured | OpenRAIL-M-Mod |

## layout — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_layout`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | 0.747 | 40 | measured |  |
| **pp-doclayoutv3 (130M)** | 0.669 | 40 | measured | Apache-2.0 |
| **pp_structurev3** | 0.638 | 40 | measured | Apache-2.0 |
| armaggheddon/y26-n (2.6M) | 0.521 | 40 | measured | MIT |
| hantian/v10-m | 0.497 | 40 | measured | AGPL-3.0 |
| hantian/v12-n | 0.489 | 40 | measured | AGPL-3.0 |
| hantian/v8-n | 0.473 | 40 | measured | AGPL-3.0 |
| armaggheddon/y11-m | 0.472 | 40 | measured | MIT |
| hantian/v8-x | 0.426 | 40 | measured | AGPL-3.0 |

## orientation — Synthetic — `measured` · **measured dataset**: `synthetic_orientation`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | 1.000 | 20 | measured | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 20 | measured | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 20 | measured | Apache-2.0 |

## rectification — Synthetic — `measured` · **measured dataset**: `synthetic_rectification`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| uvdoc (onnxruntime) | 0.604 | 20 | measured | Apache-2.0 |
| **uvdoc (31.7M)** | 0.597 | 20 | measured | Apache-2.0 |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 20 | measured | Apache-2.0 |

## text_line — Synthetic — `measured` · **measured dataset**: `synthetic_text_line`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | 1.000 | 20 | measured | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 20 | measured | Apache-2.0 |

## seal — Synthetic — `measured` · **measured dataset**: `synthetic_seal`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | 0.750 | 20 | measured | Apache-2.0 |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 20 | measured | Apache-2.0 |

## table — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_table`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| SLANet_plus (paddleocr) | 0.828 | 20 | measured | Apache-2.0 |
| tableformer (docling) | 0.807 | 20 | measured | MIT |
| **slanet_plus** | 0.780 | 20 | measured | Apache-2.0 |
| table-transformer-structure-recognition | 0.698 | 20 | measured | MIT |
| **pp_structurev3** | 0.608 | 20 | measured | Apache-2.0 |

## full_page — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_full_page`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-default (pipeline) | 0.354 | 20 | measured | MIT |
| **pp_structurev3** | 0.270 | 20 | measured | Apache-2.0 |
| **indra (math)** | 0.265 | 20 | measured | OpenRAIL-M-Mod |
