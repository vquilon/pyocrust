# Calidad vs tiempo por feature — tabla unificada CPU/GPU

> Cada punto es un motor **medido** (`reports/<feature>/REPORT.md`).
> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).
> Un panel con un solo punto significa: **no hay alternativas medidas** para esa
> feature todavía; el hueco se ve, no se rellena.
>
> **Solo motores medidos** (mismo banco por panel): no hay referencias
> externas, ni aquí ni en [`SUMMARY.md`](SUMMARY.md). Una calidad medida sobre
> otro dataset/GT no es comparable y no se publica en ninguna tabla.

## Mismas condiciones para todos los motores

- **Mismo host y mismo intérprete**: el `.venv` del repo (la versión de Python y el
  resto del runtime quedan en el `provenance` de cada `REPORT.md`). El *device* se
  anota en el título de cada panel.
- **Mismo banco**: todas las filas de un panel salen del mismo
  `bank.py`, el mismo dataset anotado y el mismo `--limit`/`warmup`.
- Un **modelo a la vez** (nunca dos motores cargados en paralelo).
- El tiempo es **inferencia + post-proceso**: excluye carga de modelo y descarga.
  `ultralytics` cronometra además su preprocesado interno (nota en el README).
- El **nombre del motor lleva el tamaño del modelo** (p. ej. `yolov10x (DocLayNet) (31.7M)`).

## text — FUNSD — device `cpu+gpu` · motores medidos

| Motor | Device | ms/img ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp_ocrv6 (tiny)** | cpu | 336 | 0.717 | Apache-2.0 |
| **pp_ocrv6 (small)** | cpu | 866 | 0.784 | Apache-2.0 |
| **pp_ocrv6 (medium)** | cpu | 2223 | 0.800 | Apache-2.0 |
| easyocr (default) | cpu | 3167 | 0.401 | Apache-2.0 |
| rapidocr (default) | cpu | 4286 | 0.585 | Apache-2.0 |
| PP-OCRv6 (medium) | cpu | 19163 | 0.796 | Apache-2.0 |
| **pp_ocrv6 (tiny)** | gpu | 330 | 0.684 | Apache-2.0 |
| easyocr (default) | gpu | 1263 | 0.399 | Apache-2.0 |
| rapidocr (default) | gpu | 5842 | 0.585 | Apache-2.0 |

## formula — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/fórmula ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 141 | 0.326 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | cpu | 998 | 0.499 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 2474 | 0.497 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 2774 | 0.398 | Apache-2.0 |
| pix2tex (default) | cpu | 5500 | 0.552 | MIT |
| paddle_latex_ocr (default) | cpu | 16326 | 0.653 | Apache-2.0 |
| unimernet (tiny) | cpu | 17493 | 0.260 | Apache-2.0 |
| **indra (math)** | gpu | 808 | 0.326 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | gpu | 1603 | 0.499 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | gpu | 2221 | 0.497 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 2553 | 0.398 | Apache-2.0 |
| paddle_latex_ocr (default) | gpu | 4191 | 0.653 | Apache-2.0 |

## layout — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| hantian/v8-n | cpu | 68 | 0.545 | AGPL-3.0 |
| armaggheddon/y26-n (2.6M) | cpu | 69 | 0.572 | MIT |
| armaggheddon/y11-m | cpu | 365 | 0.542 | MIT |
| hantian/v10-l | cpu | 569 | 0.533 | AGPL-3.0 |
| hantian/v12-l | cpu | 711 | 0.550 | AGPL-3.0 |
| docling-layout-heron-101 (default) | cpu | 1005 | 0.818 |  |
| hantian/v8-x | cpu | 1025 | 0.490 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | cpu | 2219 | 0.796 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 7111 | 0.751 | Apache-2.0 |
| hantian/v8-n | gpu | 25 | 0.545 | AGPL-3.0 |
| armaggheddon/y26-n (2.6M) | gpu | 29 | 0.572 | MIT |
| hantian/v10-l | gpu | 36 | 0.533 | AGPL-3.0 |
| armaggheddon/y11-m | gpu | 42 | 0.542 | MIT |
| hantian/v8-x | gpu | 47 | 0.490 | AGPL-3.0 |
| hantian/v12-l | gpu | 53 | 0.550 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | gpu | 488 | 0.796 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 2938 | 0.751 | Apache-2.0 |

## orientation — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 1448 | 1.000 | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | cpu | 42794 | 0.350 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 192 | 1.000 | Apache-2.0 |

## rectification — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| perspective-4corner (baseline (OpenCV, sin pesos)) | cpu | 11 | 0.491 | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 297 | 0.597 | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 33 | 0.590 | Apache-2.0 |

## text_line — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/línea ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 26 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 152 | 1.000 | Apache-2.0 |

## seal — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 643 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 178 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/tabla ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **slanet_plus (7.8M)** | cpu | 49 | 0.868 | Apache-2.0 |
| **slanext_wired (367M)** | cpu | 502 | 0.914 | Apache-2.0 |
| table-transformer-structure-recognition (default) | cpu | 636 | 0.790 | MIT |
| **pp_structurev3 (default)** | cpu | 1289 | 0.753 | Apache-2.0 |
| tableformer (docling) | cpu | 22377 | 0.905 | MIT |
| **slanext_wired (367M)** | gpu | 214 | 0.914 | Apache-2.0 |
| **slanet_plus (7.8M)** | gpu | 850 | 0.868 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 3118 | 0.753 | Apache-2.0 |

## full_page — OmniDocBench (EN) — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
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
