# Resumen de benchmarks — 9 features (`medido` + `referencia`)

> `medido` = ejecutado en este repo · `referencia` = publicado en un paper (con URL),
> **no comparable 1:1** · `pendiente` = aún sin datos. Una barra rayada es referencia.
> `license` es **informativa** (señala las no permisivas, p. ej. AGPL-3.0); la puerta solo aplica a los modelos de `pyocrust`.

## text — FUNSD — `medido` · **dataset medido**: `funsd`

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust (tiny)** | 0.717 | medido | Apache-2.0 |
| rapidocr | 0.585 | medido | Apache-2.0 |
| easyocr | 0.401 | medido | Apache-2.0 |

## formula — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_formula`

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| paddle_latex_ocr | 0.694 | medido | Apache-2.0 |
| **pyocrust_formulanet (direct)** | 0.497 | medido | Apache-2.0 |
| pix2tex | 0.486 | medido | MIT |
| **pyocrust_formula (pp-formulanet-s)** | 0.196 | medido | Apache-2.0 |
| **pyocrust_indra (math)** | 0.184 | medido | OpenRAIL-M-Mod |
| easyocr | 0.152 | medido | Apache-2.0 |
| rapidocr | 0.104 | medido | Apache-2.0 |

## layout — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_layout`

> ⚠️ **ref: DocLayNet mAP (otro dataset/GT)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| docling_heron_101 | 0.843 | medido | Apache-2.0 |
| **pyocrust_layout (130M)** | 0.827 | medido | Apache-2.0 |

## orientation — sintético — `medido` · **dataset medido**: `synthetic_orientation`

> ⚠️ **ref: PP-LCNet (otro conjunto de eval.)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust_orientation (6.8M)** | 0.950 | medido | Apache-2.0 |
| lcnet_doc_ori (onnxruntime) | 0.950 | medido | Apache-2.0 |

## rectification — sintético — `medido` · **dataset medido**: `synthetic_rectification`

> ⚠️ **ref: UVDoc CER↓ (otra métrica y dataset)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| uvdoc (onnxruntime) | 0.707 | medido | Apache-2.0 |
| **pyocrust_rectify (31.7M)** | 0.707 | medido | Apache-2.0 |

## text_line — sintético — `medido` · **dataset medido**: `synthetic_text_line`

> ⚠️ **ref: PP-LCNet (otro conjunto de eval.)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust_textline (6.8M)** | 1.000 | medido | Apache-2.0 |
| lcnet_textline_ori (onnxruntime) | 1.000 | medido | Apache-2.0 |

## seal — sintético — `medido` · **dataset medido**: `synthetic_seal`

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust_seal (4.8M)** | 0.750 | medido | Apache-2.0 |

## table — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_table`

> ⚠️ **ref: PubTabNet/ICDAR (otro dataset/GT)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust_table** | 0.854 | medido | Apache-2.0 |
| tatr | 0.699 | medido | MIT |

## full_page — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_full_page`

> ⚠️ **ref: OmniDocBench Overall (otra escala 0-100)**

| Motor | Valor | Origen | license |
| :--- | ---: | :--- | :--- |
| **pyocrust_indra (math)** | 0.231 | medido | OpenRAIL-M-Mod |
| **pyocrust_structure** | 0.211 | medido | Apache-2.0 |
