# Quality vs. time by feature — unified CPU/GPU table

> Each point is a **measured** engine (`reports/<feature>/REPORT.md`).
> X = `ms` per unit (left = faster) · Y = quality score (higher = better).
> A panel with one point means **no measured alternatives** are available for that
> feature yet; gaps are shown, never filled in.
>
> **Measured engines only** (same benchmark within each panel): there are **no** external
> references here. This may differ from [`SUMMARY.md`](SUMMARY.md), which includes
> references from a **different dataset/metric** (e.g. YOLO results on DocLayNet in `layout`).

## Same conditions for all engines

- **Same host and interpreter**: repository `.venv` (Python version and other
  runtime details are recorded in each `REPORT.md` provenance). The *device* is
  shown in each panel title.
- **Same benchmark**: all rows in a panel come from the same
  `bank.py`, annotated dataset, and `--limit`/`warmup` settings.
- **One model at a time** (never load two engines in parallel).
- Runtime is **inference + post-processing**: model loading and downloads are excluded.
  `ultralytics` also times its internal preprocessing (see the README note).
- The **engine name includes the model size** (e.g. `yolov10x (DocLayNet) (31.7M)`).

## text — FUNSD — device `cpu` · measured engines

| Engine | Device | ms/img ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp_ocrv6 (tiny)** | cpu | 970 | 0.717 | Apache-2.0 |
| easyocr (default) | cpu | 4600 | 0.401 | Apache-2.0 |
| rapidocr (default) | cpu | 6748 | 0.585 | Apache-2.0 |

## formula — OmniDocBench — device `cpu` · measured engines

| Engine | Device | ms/formula ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 103 | 0.243 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | cpu | 842 | 0.497 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 1512 | 0.196 | Apache-2.0 |
| paddle_latex_ocr (default) | cpu | 4453 | 0.694 | Apache-2.0 |
| pix2tex (default) | cpu | 5971 | 0.460 | MIT |

## layout — OmniDocBench — device `cpu+gpu` · measured engines

| Engine | Device | ms/image ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| hantian/v8-n | cpu | 84 | 0.508 | AGPL-3.0 |
| hantian/y26-s | cpu | 128 | 0.471 | AGPL-3.0 |
| hantian/v11-s | cpu | 145 | 0.429 | AGPL-3.0 |
| hantian/v12-s | cpu | 197 | 0.494 | AGPL-3.0 |
| hantian/v10-m | cpu | 274 | 0.499 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | cpu | 776 | 0.827 | Apache-2.0 |
| hantian/v8-x | cpu | 1147 | 0.497 | AGPL-3.0 |
| docling-layout-heron-101 (default) | cpu | 1575 | 0.843 |  |
| hantian/v8-n | gpu | 29 | 0.508 | AGPL-3.0 |
| hantian/y26-s | gpu | 30 | 0.471 | AGPL-3.0 |
| hantian/v11-s | gpu | 32 | 0.429 | AGPL-3.0 |
| hantian/v12-s | gpu | 39 | 0.494 | AGPL-3.0 |
| hantian/v10-m | gpu | 43 | 0.499 | AGPL-3.0 |
| hantian/v8-x | gpu | 52 | 0.497 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | gpu | 434 | 0.827 | Apache-2.0 |

## orientation — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_doc_ori (onnxruntime)** | cpu | 2 | 0.950 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 1124 | 0.950 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 55 | 0.950 | Apache-2.0 |

## rectification — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **uvdoc (onnxruntime)** | cpu | 74 | 0.707 | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 261 | 0.707 | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 53 | 0.707 | Apache-2.0 |

## text_line — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/line ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_textline_ori (onnxruntime)** | cpu | 5 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 26 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 5 | 1.000 | Apache-2.0 |

## seal — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/image ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 641 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 120 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu` · measured engines

| Engine | Device | ms/table ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| table-transformer-structure-recognition (default) | cpu | 140 | 0.699 |  |
| **slanet_plus (default)** | cpu | 749 | 0.854 | Apache-2.0 |

## full_page — OmniDocBench — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 1547 | 0.231 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | cpu | 10033 | 0.211 | Apache-2.0 |
| **indra (math)** | gpu | 10503 | 0.242 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | gpu | 17198 | 0.210 | Apache-2.0 |
