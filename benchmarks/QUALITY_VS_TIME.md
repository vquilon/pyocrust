# Calidad vs tiempo por feature — un panel por feature

> Cada punto es un motor **medido** (`features/<feature>/REPORT.md`).
> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).
> Un panel con un solo punto significa: **no hay alternativas medidas** para esa
> feature todavía; el hueco se ve, no se rellena.
>
> **Solo motores medidos** (mismo banco/GT por panel): aquí **no** hay referencias
> externas. Por eso puede contradecir [`SUMMARY.md`](SUMMARY.md), que sí añade
> referencias de **otro dataset/métrica** (p. ej. los YOLO sobre DocLayNet en `layout`).

## Mismas condiciones para todos los motores

- **Mismo host y mismo intérprete**: el `.venv` del repo (la versión de Python y el
  resto del runtime quedan en el `provenance` de cada `REPORT.md`). El *device* se
  anota en el título de cada panel.
- **Mismo banco y mismo GT**: todas las filas de un panel salen del mismo
  `bank.py`, el mismo dataset anotado y el mismo `--limit`/`warmup`.
- Un **modelo a la vez** (nunca dos motores cargados en paralelo).
- El tiempo es **inferencia + post-proceso**: excluye carga de modelo y descarga.
  `ultralytics` cronometra además su preprocesado interno (nota en el README).
- El **nombre del motor lleva el tamaño del modelo** (p. ej. `yolov10x (DocLayNet) (31.7M)`).

## text — FUNSD — device `cpu` · SOLO motores medidos

| Motor | ms/img ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| **pyocrust (tiny)** | 970 | 0.717 | Apache-2.0 |
| easyocr (default) | 4600 | 0.401 | Apache-2.0 |
| rapidocr (default) | 6748 | 0.585 | Apache-2.0 |

## formula — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/fórmula ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| **pyocrust_formulanet** | 979 | 0.497 | Apache-2.0 |
| **pyocrust_formula** | 3464 | 0.196 | Apache-2.0 |
| pix2tex (default) | 7484 | 0.486 | MIT |
| paddle_latex_ocr (default) | 12490 | 0.694 | Apache-2.0 |

## layout — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/imagen ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| yolo26m (21.8M) | 294 | 0.467 | MIT |
| yolov10b (20.5M) | 383 | 0.344 | AGPL-3.0 |
| yolov10x (31.7M) | 658 | 0.381 | AGPL-3.0 |
| docling_heron_101 (default) | 1071 | 0.843 | Apache-2.0 |
| **pyocrust_layout (130M)** | 1987 | 0.827 | Apache-2.0 |

## orientation — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| lcnet_doc_ori (onnxruntime) | 2 | 0.950 | Apache-2.0 |
| **pyocrust_orientation (6.8M)** | 1124 | 0.950 | Apache-2.0 |

## rectification — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| uvdoc (onnxruntime) | 74 | 0.707 | Apache-2.0 |
| **pyocrust_rectify (31.7M)** | 261 | 0.707 | Apache-2.0 |

## text_line — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/línea ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| lcnet_textline_ori (onnxruntime) | 5 | 1.000 | Apache-2.0 |
| **pyocrust_textline (6.8M)** | 26 | 1.000 | Apache-2.0 |

## seal — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/imagen ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| **pyocrust_seal (4.8M)** | 641 | 0.750 | Apache-2.0 |

## table — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/tabla ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| tatr (default) | 140 | 0.699 | MIT |
| **pyocrust_table** | 749 | 0.854 | Apache-2.0 |

## full_page — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ | license |
| :--- | ---: | ---: | :--- |
| **pyocrust_indra (math)** | 1547 | 0.231 | OpenRAIL-M-Mod |
| **pyocrust_structure** | 10033 | 0.211 | Apache-2.0 |
