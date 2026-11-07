# Benchmark summary — 9 features (`measured` + `reference`)

> `measured` = run in this repository · `reference` = published in a paper (with URL),
> **not directly comparable** · `pending` = no data yet. A hatched bar indicates a reference.
> Measured rows are separated by device and show `n`; per-engine differences are stated in each row.
> `license` is **informational** (flags non-permissive licenses, e.g. AGPL-3.0); the gate applies only to `pyocrust` models.

## text — FUNSD — `measured` · **measured dataset**: `funsd`

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp_ocrv6 (tiny)** | cpu | 0.717 | 20 | measured | Apache-2.0 |
| **pp_ocrv6 (tiny)** | gpu | 0.684 | 20 | measured | Apache-2.0 |
| rapidocr | gpu | 0.585 | 20 | measured | Apache-2.0 |
| rapidocr | cpu | 0.585 | 20 | measured | Apache-2.0 |
| easyocr | cpu | 0.401 | 20 | measured | Apache-2.0 |
| easyocr | gpu | 0.399 | 20 | measured | Apache-2.0 |

## formula — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_formula`

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| paddle_latex_ocr | cpu | 0.694 | 20 | measured | Apache-2.0 |
| paddle_latex_ocr | gpu | 0.694 | 20 | measured | Apache-2.0 |
| **pp-formulanet-s (direct)** | cpu | 0.497 | 20 | measured | Apache-2.0 |
| **pp-formulanet-s (direct)** | gpu | 0.497 | 20 | measured | Apache-2.0 |
| pix2tex | cpu | 0.460 | 20 | measured | MIT |
| **indra (math)** | cpu | 0.243 | 20 | measured | OpenRAIL-M-Mod |
| **indra (math)** | gpu | 0.243 | 20 | measured | OpenRAIL-M-Mod |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 0.196 | 20 | measured | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | gpu | 0.196 | 20 | measured | Apache-2.0 |

## layout — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_layout`

> ⚠️ **reference: DocLayNet mAP (different dataset/ground truth)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | cpu | 0.843 | 20 | measured |  |
| **pp-doclayoutv3 (130M)** | cpu | 0.827 | 20 | measured | Apache-2.0 |
| **pp-doclayoutv3 (130M)** | gpu | 0.827 | 20 | measured | Apache-2.0 |
| hantian/v8-n | gpu | 0.508 | 20 | measured | AGPL-3.0 |
| hantian/v8-n | cpu | 0.508 | 20 | measured | AGPL-3.0 |
| hantian/v10-m | cpu | 0.499 | 20 | measured | AGPL-3.0 |
| hantian/v10-m | gpu | 0.499 | 20 | measured | AGPL-3.0 |
| hantian/v8-x | gpu | 0.497 | 20 | measured | AGPL-3.0 |
| hantian/v8-x | cpu | 0.497 | 20 | measured | AGPL-3.0 |
| hantian/v12-s | cpu | 0.494 | 20 | measured | AGPL-3.0 |
| hantian/v12-s | gpu | 0.494 | 20 | measured | AGPL-3.0 |
| hantian/y26-s | gpu | 0.471 | 20 | measured | AGPL-3.0 |
| hantian/y26-s | cpu | 0.471 | 20 | measured | AGPL-3.0 |
| hantian/v11-s | cpu | 0.429 | 20 | measured | AGPL-3.0 |
| hantian/v11-s | gpu | 0.429 | 20 | measured | AGPL-3.0 |

## orientation — Synthetic — `measured` · **measured dataset**: `synthetic_orientation`

> ⚠️ **reference: PP-LCNet (different evaluation set)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 0.950 | 20 | measured | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | cpu | 0.950 | 20 | measured | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 0.950 | 20 | measured | Apache-2.0 |

## rectification — Synthetic — `measured` · **measured dataset**: `synthetic_rectification`

> ⚠️ **reference: UVDoc CER↓ (different metric and dataset)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| uvdoc (onnxruntime) | cpu | 0.707 | 20 | measured | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 0.707 | 20 | measured | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 0.707 | 20 | measured | Apache-2.0 |

## text_line — Synthetic — `measured` · **measured dataset**: `synthetic_text_line`

> ⚠️ **reference: PP-LCNet (different evaluation set)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 1.000 | 20 | measured | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | cpu | 1.000 | 20 | measured | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 1.000 | 20 | measured | Apache-2.0 |

## seal — Synthetic — `measured` · **measured dataset**: `synthetic_seal`

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 0.750 | 20 | measured | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 0.750 | 20 | measured | Apache-2.0 |

## table — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_table`

> ⚠️ **reference: PubTabNet/ICDAR (different dataset/ground truth)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **slanet_plus** | cpu | 0.854 | 20 | measured | Apache-2.0 |
| **slanet_plus** | gpu | 0.854 | 20 | measured | Apache-2.0 |
| table-transformer-structure-recognition | cpu | 0.699 | 20 | measured |  |

## full_page — OmniDocBench — `measured` · **measured dataset**: `omnidocbench_full_page`

> ⚠️ **reference: OmniDocBench Overall (different 0–100 scale)**

| Engine | Device | Value | n | Source | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **indra (math)** | gpu | 0.242 | 19 | measured | OpenRAIL-M-Mod |
| **indra (math)** | cpu | 0.231 | 20 | measured | OpenRAIL-M-Mod |
| **pp_structurev3** | cpu | 0.211 | 20 | measured | Apache-2.0 |
| **pp_structurev3** | gpu | 0.210 | 20 | measured | Apache-2.0 |
