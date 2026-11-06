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

| Motor | ms/img ↓ | calidad ↑ |
| :--- | ---: | ---: |
| **pyocrust (tiny)** | 786 | 0.734 |
| easyocr (default) | 3915 | 0.384 |
| rapidocr (default) | 6733 | 0.659 |

## formula — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/fórmula ↓ | calidad ↑ |
| :--- | ---: | ---: |
| easyocr (default) | 743 | 0.152 |
| **pyocrust_formulanet** | 1015 | 0.550 |
| pix2tex (default) | 2451 | 0.486 |
| **pyocrust_formula** | 2795 | 0.419 |
| rapidocr (default) | 3026 | 0.104 |

## layout — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/imagen ↓ | calidad ↑ |
| :--- | ---: | ---: |
| yolo26m (21.8M) | 331 | 0.386 |
| yolov10b (20.5M) | 455 | 0.290 |
| yolov10x (31.7M) | 732 | 0.312 |
| docling_heron_101 (default) | 816 | 0.792 |
| **pyocrust_layout (130M)** | 1947 | 0.811 |

## orientation — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| lcnet_doc_ori (onnxruntime) | 4 | 1.000 |
| **pyocrust_orientation (6.8M)** | 702 | 1.000 |

## rectification — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| uvdoc (onnxruntime) | 138 | 0.701 |
| **pyocrust_rectify (31.7M)** | 254 | 0.704 |

## text_line — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/línea ↓ | calidad ↑ |
| :--- | ---: | ---: |
| lcnet_textline_ori (onnxruntime) | 5 | 1.000 |
| **pyocrust_textline (6.8M)** | 33 | 1.000 |

## seal — sintético — device `cpu` · SOLO motores medidos

| Motor | ms/imagen ↓ | calidad ↑ |
| :--- | ---: | ---: |
| **pyocrust_seal (4.8M)** | 591 | 0.750 |

## table — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/tabla ↓ | calidad ↑ |
| :--- | ---: | ---: |
| tatr (default) | 164 | 0.737 |
| **pyocrust_table** | 708 | 0.885 |

## full_page — OmniDocBench — device `cpu` · SOLO motores medidos

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| **pyocrust_indra (math)** | 1954 | 0.176 |
| **pyocrust_structure** | 11253 | 0.158 |
