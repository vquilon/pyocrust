# Calidad vs tiempo por feature — tabla unificada CPU/GPU

> Cada punto es un motor **medido** (`reports/<feature>/REPORT.md`).
> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).
> Un panel con un solo punto significa: **no hay alternativas medidas** para esa
> feature todavía; el hueco se ve, no se rellena.
>
> **Solo motores medidos** (mismo banco por panel): aquí **no** hay referencias
> externas. Por eso puede contradecir [`SUMMARY.md`](SUMMARY.md), que sí añade
> referencias de **otro dataset/métrica** (p. ej. los YOLO sobre DocLayNet en `layout`).

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
| **indra (math)** | cpu | 103 | 0.243 | OpenRAIL-M-Mod |
| **pp-formulanet-s (direct)** | cpu | 842 | 0.497 | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 1512 | 0.196 | Apache-2.0 |
| paddle_latex_ocr (default) | cpu | 4453 | 0.694 | Apache-2.0 |
| pix2tex (default) | cpu | 5971 | 0.460 | MIT |

## layout — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| hantian/v12-n | cpu | 137 | 0.489 | AGPL-3.0 |
| hantian/v8-n | cpu | 138 | 0.473 | AGPL-3.0 |
| hantian/v10-m | cpu | 342 | 0.497 | AGPL-3.0 |
| hantian/y26-m | cpu | 431 | 0.449 | AGPL-3.0 |
| hantian/v11-l | cpu | 509 | 0.468 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | cpu | 528 | 0.669 | Apache-2.0 |
| docling-layout-heron-101 (default) | cpu | 985 | 0.747 |  |
| hantian/v8-x | cpu | 1289 | 0.426 | AGPL-3.0 |
| hantian/v8-n | gpu | 55 | 0.473 | AGPL-3.0 |
| hantian/v12-n | gpu | 67 | 0.489 | AGPL-3.0 |
| hantian/v10-m | gpu | 68 | 0.495 | AGPL-3.0 |
| hantian/y26-m | gpu | 69 | 0.449 | AGPL-3.0 |
| hantian/v11-l | gpu | 71 | 0.468 | AGPL-3.0 |
| hantian/v8-x | gpu | 81 | 0.426 | AGPL-3.0 |
| **pp-doclayoutv3 (130M)** | gpu | 434 | 0.827 | Apache-2.0 |

## orientation — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_doc_ori (onnxruntime)** | cpu | 2 | 0.950 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 1124 | 0.950 | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 55 | 0.950 | Apache-2.0 |

## rectification — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **uvdoc (onnxruntime)** | cpu | 74 | 0.707 | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 261 | 0.707 | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 53 | 0.707 | Apache-2.0 |

## text_line — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/línea ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-lcnet_x1_0_textline_ori (onnxruntime)** | cpu | 5 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 26 | 1.000 | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 5 | 1.000 | Apache-2.0 |

## seal — sintético — device `cpu+gpu` · motores medidos

| Motor | Device | ms/imagen ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 641 | 0.750 | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 120 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu` · motores medidos

| Motor | Device | ms/tabla ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| table-transformer-structure-recognition (default) | cpu | 140 | 0.699 |  |
| **slanet_plus (default)** | cpu | 749 | 0.854 | Apache-2.0 |

## full_page — OmniDocBench — device `cpu+gpu` · motores medidos

| Motor | Device | ms/página ↓ | calidad ↑ | license |
| :--- | :--- | ---: | ---: | :--- |
| **indra (math)** | cpu | 1547 | 0.231 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | cpu | 10033 | 0.211 | Apache-2.0 |
| **indra (math)** | gpu | 10503 | 0.242 | OpenRAIL-M-Mod |
| **pp_structurev3 (default)** | gpu | 17198 | 0.210 | Apache-2.0 |
