# Benchmark summary — 9 features (`measured` only)

> `measured` = run in this repository · `pending` = no data yet.
> **No external references are published**: a quality measured on a different
> dataset/ground truth is not comparable, so it never enters any table or figure.
> Una fila per engine sobre **su mismo dataset** (el device solo se publica en los informes con tiempos). El `n` se declara por fila.
> `license` is **informational** (flags non-permissive licenses, e.g. AGPL-3.0); the gate applies only to `pyocrust` models.

## text — FUNSD — `measured` · **measured dataset**: `funsd`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp_ocrv6 (medium)** | 0.800 | 20 | measured | Apache-2.0 |
| PP-OCRv6 (medium) | 0.796 | 20 | measured | Apache-2.0 |
| **pp_ocrv6 (small)** | 0.784 | 20 | measured | Apache-2.0 |
| **pp_ocrv6 (tiny)** | 0.717 | 20 | measured | Apache-2.0 |
| rapidocr | 0.585 | 20 | measured | Apache-2.0 |
| easyocr | 0.401 | 20 | measured | Apache-2.0 |

## formula — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_formula`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| paddle_latex_ocr | 0.653 | 10 | measured | Apache-2.0 |
| pix2tex | 0.552 | 10 | measured | MIT |
| **pp-formulanet-s (direct)** | 0.499 | 10 | measured | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | 0.497 | 10 | measured | Apache-2.0 |
| **pp_structurev3** | 0.398 | 10 | measured | Apache-2.0 |
| **indra (math)** | 0.326 | 10 | measured | OpenRAIL-M-Mod |
| unimernet (tiny) | 0.260 | 10 | measured | Apache-2.0 |

## layout — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_layout`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | 0.818 | 40 | measured |  |
| **pp-doclayoutv3 (130M)** | 0.796 | 40 | measured | Apache-2.0 |
| **pp_structurev3** | 0.751 | 40 | measured | Apache-2.0 |
| armaggheddon/y26-n (2.6M) | 0.572 | 40 | measured | MIT |
| hantian/v12-l | 0.550 | 40 | measured | AGPL-3.0 |
| hantian/v8-n | 0.545 | 40 | measured | AGPL-3.0 |
| armaggheddon/y11-m | 0.542 | 40 | measured | MIT |
| hantian/v10-l | 0.533 | 40 | measured | AGPL-3.0 |
| hantian/v8-x | 0.490 | 40 | measured | AGPL-3.0 |

## orientation — Synthetic — `measured` · **measured dataset**: `synthetic_orientation`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | 1.000 | 20 | measured | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 20 | measured | Apache-2.0 |

## rectification — Synthetic — `measured` · **measured dataset**: `synthetic_rectification`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **uvdoc (31.7M)** | 0.597 | 20 | measured | Apache-2.0 |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 20 | measured | Apache-2.0 |

## text_line — Synthetic — `measured` · **measured dataset**: `synthetic_text_line`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | 1.000 | 20 | measured | Apache-2.0 |

## seal — Synthetic — `measured` · **measured dataset**: `synthetic_seal`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | 0.750 | 20 | measured | Apache-2.0 |

## table — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_table`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| **slanext_wired (367M)** | 0.914 | 8 | measured | Apache-2.0 |
| tableformer (docling) | 0.905 | 8 | measured | MIT |
| **slanet_plus (7.8M)** | 0.868 | 8 | measured | Apache-2.0 |
| table-transformer-structure-recognition | 0.790 | 8 | measured | MIT |

## full_page — OmniDocBench (EN) — `measured` · **measured dataset**: `omnidocbench_full_page_en`

| Engine | Value | n | Source | license |
| :--- | ---: | ---: | :--- | :--- |
| LightOnOCR-3 (0.8B) | 0.625 | 6 | measured | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 0.597 | 6 | measured | Apache-2.0 |
| LightOnOCR-3 (4B) | 0.590 | 6 | measured | Apache-2.0 |
| LightOnOCR-2-1B (1B) | 0.588 | 6 | measured | Apache-2.0 |
| GLM-OCR (0.9B) | 0.559 | 6 | measured | MIT |
| **indra (math)** | 0.556 | 6 | measured | OpenRAIL-M-Mod |
| **pp_structurev3** | 0.530 | 6 | measured | Apache-2.0 |
| docling-default (pipeline) | 0.512 | 6 | measured | MIT |
| PP-StructureV3 (paddleocr) | 0.427 | 6 | measured | Apache-2.0 |
