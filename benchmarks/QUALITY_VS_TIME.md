# Calidad vs tiempo por feature — un panel por feature

> Cada punto es un motor **medido** (`features/<feature>/REPORT.md`).
> X = `ms` por unidad (izquierda = mejor) · Y = índice de calidad (arriba = mejor).
> Un panel con un solo punto significa: **no hay alternativas medidas** para esa
> feature todavía; el hueco se ve, no se rellena.

## text — FUNSD — device `cpu`

| Motor | ms/img ↓ | calidad ↑ |
| :--- | ---: | ---: |
| **pyocrust (tiny)** | 787 | 0.734 |
| easyocr (default) | 4387 | 0.384 |
| rapidocr (default) | 7372 | 0.660 |

## formula — OmniDocBench — device `cpu`

| Motor | ms/fórmula ↓ | calidad ↑ |
| :--- | ---: | ---: |
| easyocr (default) | 908 | 0.152 |
| **pyocrust_formulanet** | 1049 | 0.550 |
| rapidocr (default) | 2813 | 0.104 |
| pix2tex (default) | 2841 | 0.489 |
| **pyocrust_formula** | 2938 | 0.419 |

## layout — DocLayNet — device `cpu`

| Motor | ms/imagen ↓ | calidad ↑ |
| :--- | ---: | ---: |
| docling_heron_101 (default) | 966 | 0.508 |
| **pyocrust_layout** | 1899 | 0.764 |

## orientation — device `cpu`

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| lcnet_doc_ori (onnxruntime) | 4 | 1.000 |
| **pyocrust_orientation** | 694 | 1.000 |

## rectification — device `cpu`

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| uvdoc (onnxruntime) | 97 | 0.701 |
| **pyocrust_rectify** | 259 | 0.704 |

## text_line — device `cpu`

| Motor | ms/línea ↓ | calidad ↑ |
| :--- | ---: | ---: |
| lcnet_textline_ori (onnxruntime) | 2 | 1.000 |
| **pyocrust_textline** | 31 | 1.000 |

## seal — device `?`

_Sin tiempo medido todavía._

## table — PubTabNet — device `cpu`

| Motor | ms/tabla ↓ | calidad ↑ |
| :--- | ---: | ---: |
| tatr (default) | 219 | 0.737 |
| **pyocrust_table** | 1001 | 0.885 |

## full_page — OmniDocBench — device `cpu`

| Motor | ms/página ↓ | calidad ↑ |
| :--- | ---: | ---: |
| **pyocrust_indra (math)** | 2411 | 0.176 |
| **pyocrust_structure** | 12384 | 0.158 |
