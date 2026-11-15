# Quality vs. time by feature — unified CPU/GPU table

> Each point is a **measured** engine (`reports/<feature>/REPORT.md`).
> X = `ms` per unit (left = faster) · Y = quality score (higher = better).
> A panel with one point means **no measured alternatives** are available for that
> feature yet; gaps are shown, never filled in.
>
> **Measured engines only** (same benchmark within each panel): there are no
> external references, here or in [`SUMMARY.md`](SUMMARY.md). A quality measured on
> a different dataset/ground truth is not comparable and is never published in any table.

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

## text — FUNSD — device `cpu+gpu` · measured engines

| Engine | Device | ms/img ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp_ocrv6 (tiny)** | cpu | 318 | 0.717 | Apache-2.0 |
| **pp_ocrv6 (small)** | cpu | 823 | 0.784 | Apache-2.0 |
| **pp_ocrv6 (medium)** | cpu | 2138 | 0.800 | Apache-2.0 |
| easyocr (default) | cpu | 3662 | 0.401 | Apache-2.0 |
| rapidocr (default) | cpu | 4807 | 0.585 | Apache-2.0 |
| PP-OCRv6 (medium) | cpu | 19811 | 0.796 | Apache-2.0 |
| **pp_ocrv6 (tiny)** | gpu | 419 | 0.684 | Apache-2.0 |
| PP-OCRv6 (medium) | gpu | 487 | 0.796 | Apache-2.0 |
| **pp_ocrv6 (small)** | gpu | 1012 | 0.767 | Apache-2.0 |
| easyocr (default) | gpu | 1660 | 0.399 | Apache-2.0 |
| **pp_ocrv6 (medium)** | gpu | 2258 | 0.779 | Apache-2.0 |
| rapidocr (default) | gpu | 4498 | 0.585 | Apache-2.0 |

## formula — OmniDocBench — device `cpu+gpu` · measured engines

| Engine | Device | ms/formula ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 82 | 0.326 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | cpu | 696 | 0.499 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 1028 | 0.398 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 1052 | 0.497 | Apache-2.0 |
| pix2tex (default) | cpu | 4659 | 0.555 | MIT |
| paddle_latex_ocr (default) | cpu | 11331 | 0.653 | Apache-2.0 |
| unimernet (tiny) | cpu | 14927 | 0.260 | Apache-2.0 |
| **indra (math)** | gpu | 708 | 0.326 | OpenRAIL-M-Mod |
| pix2tex (default) | gpu | 1182 | 0.566 | MIT |
| **pp-formulanet-s (direct)** | gpu | 1385 | 0.499 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | gpu | 2031 | 0.497 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 2095 | 0.398 | Apache-2.0 |
| paddle_latex_ocr (default) | gpu | 3322 | 0.653 | Apache-2.0 |

## layout — OmniDocBench — device `cpu+gpu` · measured engines

| Engine | Device | ms/image ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| armaggheddon/y26-n (2.6M) | cpu | 62 | 0.572 | MIT |
| hantian/v8-n | cpu | 68 | 0.545 | AGPL-3.0 |
| armaggheddon/y11-m | cpu | 367 | 0.542 | MIT |
| **pp-doclayoutv3 (130M)** | cpu | 505 | 0.796 | Apache-2.0 |
| hantian/v10-l | cpu | 585 | 0.533 | AGPL-3.0 |
| hantian/v12-l | cpu | 623 | 0.550 | AGPL-3.0 |
| docling-layout-egret-xlarge (default) | cpu | 688 | 0.818 | MIT |
| docling-layout-heron-101 (default) | cpu | 999 | 0.818 |  |
| hantian/v8-x | cpu | 1128 | 0.490 | AGPL-3.0 |
| **pp_structurev3 (default)** | cpu | 2926 | 0.751 | Apache-2.0 |
| hantian/v8-n | gpu | 29 | 0.545 | AGPL-3.0 |
| armaggheddon/y26-n (2.6M) | gpu | 33 | 0.572 | MIT |
| armaggheddon/y11-m | gpu | 45 | 0.542 | MIT |
| hantian/v10-l | gpu | 47 | 0.533 | AGPL-3.0 |
| hantian/v8-x | gpu | 55 | 0.490 | AGPL-3.0 |
| docling-layout-heron-101 (default) | gpu | 71 | 0.818 |  |
| hantian/v12-l | gpu | 71 | 0.550 | AGPL-3.0 |
| docling-layout-egret-xlarge (default) | gpu | 77 | 0.817 | MIT |
| **pp-doclayoutv3 (130M)** | gpu | 883 | 0.796 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 3201 | 0.751 | Apache-2.0 |

## orientation — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 60 | 1.000 | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | cpu | 43311 | 0.350 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 298 | 1.000 | Apache-2.0 |

## rectification — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| perspective-4corner (baseline (OpenCV, sin pesos)) | cpu | 9 | 0.473 | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 71 | 0.590 | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 34 | 0.590 | Apache-2.0 |

## text_line — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/line ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| ch_ppocr_mobile_v2.0_cls (rapidocr) | cpu | 3 | 0.900 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 3 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 205 | 1.000 | Apache-2.0 |

## seal — Synthetic — device `cpu+gpu` · measured engines

| Engine | Device | ms/image ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 643 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 287 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu+gpu` · measured engines

| Engine | Device | ms/table ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **slanet_plus (7.8M)** | cpu | 52 | 0.868 | Apache-2.0 |
| **slanext_wired (367M)** | cpu | 577 | 0.914 | Apache-2.0 |
| table-transformer-structure-recognition (default) | cpu | 718 | 0.790 | MIT |
| **pp_structurev3 (default)** | cpu | 1128 | 0.753 | Apache-2.0 |
| tableformer (docling) | cpu | 27457 | 0.905 | MIT |
| table-transformer-structure-recognition (default) | gpu | 47 | 0.790 | MIT |
| **slanext_wired (367M)** | gpu | 202 | 0.914 | Apache-2.0 |
| **slanet_plus (7.8M)** | gpu | 484 | 0.868 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 2214 | 0.753 | Apache-2.0 |
| tableformer (docling) | gpu | 19140 | 0.905 | MIT |

## full_page — OmniDocBench (EN) — device `cpu+gpu` · measured engines

| Engine | Device | ms/page ↓ | Quality ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 1251 | 0.556 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | cpu | 3652 | 0.530 | Apache-2.0 |
| docling-default (pipeline) | cpu | 26739 | 0.512 | MIT |
| PP-StructureV3 (paddleocr) | cpu | 180058 | 0.427 | Apache-2.0 |
| **indra (math)** | gpu | 1793 | 0.556 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | gpu | 4350 | 0.528 | Apache-2.0 |
| docling-default (pipeline) | gpu | 22740 | 0.512 | MIT |
| GLM-OCR (0.9B) | gpu | 30716 | 0.559 | MIT |
| LightOnOCR-2-1B (1B) | gpu | 44737 | 0.588 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | gpu | 60907 | 0.597 | Apache-2.0 |
| PP-StructureV3 (paddleocr) | gpu | 68269 | 0.496 | Apache-2.0 |
| LightOnOCR-3 (4B) | gpu | 72249 | 0.590 | Apache-2.0 |
| LightOnOCR-3 (0.8B) | gpu | 320707 | 0.625 | Apache-2.0 |
