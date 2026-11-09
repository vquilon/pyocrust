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

## text — FUNSD — device `cpu` · motores medidos

| Motor | Device | ms/img ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp_ocrv6 (tiny)** | cpu | 970 | 0.717 | Apache-2.0 |
| easyocr (default) | cpu | 4600 | 0.401 | Apache-2.0 |
| rapidocr (default) | cpu | 6748 | 0.585 | Apache-2.0 |

## formula — OmniDocBench — device `cpu` · motores medidos

| Motor | Device | ms/fórmula ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 146 | 0.211 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | cpu | 854 | 0.576 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 2193 | 0.399 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 2247 | 0.607 | Apache-2.0 |
| paddle_latex_ocr (default) | cpu | 3734 | 0.715 | Apache-2.0 |
| pix2tex (default) | cpu | 5764 | 0.587 | MIT |
| unimernet (tiny) | cpu | 18685 | 0.238 | Apache-2.0 |

## layout — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| armaggheddon/y26-n (2.6M) | cpu | 94 | 0.521 | MIT |
| hantian/v12-n | cpu | 114 | 0.489 | AGPL-3.0 |
| hantian/v8-n | cpu | 114 | 0.473 | AGPL-3.0 |
| hantian/v10-m | cpu | 404 | 0.497 | AGPL-3.0 |
| armaggheddon/y11-m | cpu | 442 | 0.472 | MIT |
| hantian/v8-x | cpu | 1295 | 0.426 | AGPL-3.0 |
| docling-layout-heron-101 (default) | cpu | 1794 | 0.747 |  |
| **pp-doclayoutv3 (130M)** | cpu | 3988 | 0.669 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 9890 | 0.638 | Apache-2.0 |
| hantian/v8-n | gpu | 50 | 0.473 | AGPL-3.0 |
| armaggheddon/y11-m | gpu | 53 | 0.472 | MIT |
| armaggheddon/y26-n (2.6M) | gpu | 55 | 0.521 | MIT |
| hantian/v12-n | gpu | 61 | 0.489 | AGPL-3.0 |
| hantian/v10-m | gpu | 62 | 0.495 | AGPL-3.0 |
| hantian/v8-x | gpu | 71 | 0.426 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | gpu | 3288 | 0.669 | Apache-2.0 |
| **pp_structurev3 (default)** | gpu | 14190 | 0.639 | Apache-2.0 |

## orientation — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_doc_ori (onnxruntime)** | cpu | 5 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 1448 | 1.000 | Apache-2.0 |
| craft_mlt_25k+latin_g2 (easyocr) | cpu | 42794 | 0.350 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 1608 | 1.000 | Apache-2.0 |

## rectification — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| perspective-4corner (baseline (OpenCV, sin pesos)) | cpu | 11 | 0.491 | Apache-2.0 |
| **uvdoc (onnxruntime)** | cpu | 78 | 0.604 | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 297 | 0.597 | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 298 | 0.597 | Apache-2.0 |

## text_line — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/línea ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_textline_ori (onnxruntime)** | cpu | 5 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 26 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 25 | 1.000 | Apache-2.0 |

## seal — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-ocrv4_mobile_seal_det (onnxruntime)** | cpu | 217 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 643 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 608 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu` · motores medidos

| Motor | Device | ms/tabla ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| SLANet_plus (paddleocr) | cpu | 87 | 0.828 | Apache-2.0 |
| table-transformer-structure-recognition (default) | cpu | 198 | 0.698 | MIT |
| **slanet_plus (default)** | cpu | 848 | 0.780 | Apache-2.0 |
| **pp_structurev3 (default)** | cpu | 3245 | 0.608 | Apache-2.0 |
| tableformer (docling) | cpu | 35699 | 0.807 | MIT |

## full_page — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 2006 | 0.265 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | cpu | 11054 | 0.270 | Apache-2.0 |
| docling-default (pipeline) | cpu | 33257 | 0.354 | MIT |
| **indra (math)** | gpu | 8901 | 0.265 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | gpu | 14053 | 0.267 | Apache-2.0 |
