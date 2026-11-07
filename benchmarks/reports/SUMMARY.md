# Resumen de benchmarks — 9 features (`medido` + `referencia`)

> `medido` = ejecutado en este repo · `referencia` = publicado en un paper (con URL),
> **no comparable 1:1** · `pendiente` = aún sin datos. Una barra rayada es referencia.
> Las filas medidas se separan por device y muestran `n`; si difiere entre motores, queda declarado por fila.
> `license` es **informativa** (señala las no permisivas, p. ej. AGPL-3.0); la puerta solo aplica a los modelos de `pyocrust`.

## text — FUNSD — `medido` · **dataset medido**: `funsd`

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp_ocrv6 (tiny)** | cpu | 0.717 | 20 | medido | Apache-2.0 |
| **pp_ocrv6 (tiny)** | gpu | 0.684 | 20 | medido | Apache-2.0 |
| rapidocr | gpu | 0.585 | 20 | medido | Apache-2.0 |
| rapidocr | cpu | 0.585 | 20 | medido | Apache-2.0 |
| easyocr | cpu | 0.401 | 20 | medido | Apache-2.0 |
| easyocr | gpu | 0.399 | 20 | medido | Apache-2.0 |

## formula — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_formula`

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| paddle_latex_ocr | cpu | 0.694 | 20 | medido | Apache-2.0 |
| paddle_latex_ocr | gpu | 0.694 | 20 | medido | Apache-2.0 |
| **pp-formulanet-s (direct)** | cpu | 0.497 | 20 | medido | Apache-2.0 |
| **pp-formulanet-s (direct)** | gpu | 0.497 | 20 | medido | Apache-2.0 |
| pix2tex | cpu | 0.460 | 20 | medido | MIT |
| **indra (math)** | cpu | 0.243 | 20 | medido | OpenRAIL-M-Mod |
| **indra (math)** | gpu | 0.243 | 20 | medido | OpenRAIL-M-Mod |
| **pp_structurev3 (pp-formulanet-s)** | cpu | 0.196 | 20 | medido | Apache-2.0 |
| **pp_structurev3 (pp-formulanet-s)** | gpu | 0.196 | 20 | medido | Apache-2.0 |

## layout — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_layout`

> ⚠️ **ref: DocLayNet mAP (otro dataset/GT)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| docling-layout-heron-101 | cpu | 0.843 | 20 | medido |  |
| **pp-doclayoutv3 (130M)** | cpu | 0.827 | 20 | medido | Apache-2.0 |
| **pp-doclayoutv3 (130M)** | gpu | 0.827 | 20 | medido | Apache-2.0 |
| hantian/v8-n | gpu | 0.508 | 20 | medido | AGPL-3.0 |
| hantian/v8-n | cpu | 0.508 | 20 | medido | AGPL-3.0 |
| hantian/v10-m | cpu | 0.499 | 20 | medido | AGPL-3.0 |
| hantian/v10-m | gpu | 0.499 | 20 | medido | AGPL-3.0 |
| hantian/v8-x | gpu | 0.497 | 20 | medido | AGPL-3.0 |
| hantian/v8-x | cpu | 0.497 | 20 | medido | AGPL-3.0 |
| hantian/v12-s | cpu | 0.494 | 20 | medido | AGPL-3.0 |
| hantian/v12-s | gpu | 0.494 | 20 | medido | AGPL-3.0 |
| hantian/y26-s | gpu | 0.471 | 20 | medido | AGPL-3.0 |
| hantian/y26-s | cpu | 0.471 | 20 | medido | AGPL-3.0 |
| hantian/v11-s | cpu | 0.429 | 20 | medido | AGPL-3.0 |
| hantian/v11-s | gpu | 0.429 | 20 | medido | AGPL-3.0 |

## orientation — sintético — `medido` · **dataset medido**: `synthetic_orientation`

> ⚠️ **ref: PP-LCNet (otro conjunto de eval.)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | cpu | 0.950 | 20 | medido | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | cpu | 0.950 | 20 | medido | Apache-2.0 |
| **pp-lcnet_x1_0_doc_ori (6.8M)** | gpu | 0.950 | 20 | medido | Apache-2.0 |

## rectification — sintético — `medido` · **dataset medido**: `synthetic_rectification`

> ⚠️ **ref: UVDoc CER↓ (otra métrica y dataset)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| uvdoc (onnxruntime) | cpu | 0.707 | 20 | medido | Apache-2.0 |
| **uvdoc (31.7M)** | cpu | 0.707 | 20 | medido | Apache-2.0 |
| **uvdoc (31.7M)** | gpu | 0.707 | 20 | medido | Apache-2.0 |

## text_line — sintético — `medido` · **dataset medido**: `synthetic_text_line`

> ⚠️ **ref: PP-LCNet (otro conjunto de eval.)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | cpu | 1.000 | 20 | medido | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | cpu | 1.000 | 20 | medido | Apache-2.0 |
| **pp-lcnet_x1_0_textline_ori (6.8M)** | gpu | 1.000 | 20 | medido | Apache-2.0 |

## seal — sintético — `medido` · **dataset medido**: `synthetic_seal`

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **pp-ocrv4_mobile_seal_det (4.8M)** | cpu | 0.750 | 20 | medido | Apache-2.0 |
| **pp-ocrv4_mobile_seal_det (4.8M)** | gpu | 0.750 | 20 | medido | Apache-2.0 |

## table — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_table`

> ⚠️ **ref: PubTabNet/ICDAR (otro dataset/GT)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **slanet_plus** | cpu | 0.854 | 20 | medido | Apache-2.0 |
| **slanet_plus** | gpu | 0.854 | 20 | medido | Apache-2.0 |
| table-transformer-structure-recognition | cpu | 0.699 | 20 | medido |  |

## full_page — OmniDocBench — `medido` · **dataset medido**: `omnidocbench_full_page`

> ⚠️ **ref: OmniDocBench Overall (otra escala 0-100)**

| Motor | Device | Valor | n | Origen | license |
| :--- | :--- | ---: | ---: | :--- | :--- |
| **indra (math)** | gpu | 0.242 | 19 | medido | OpenRAIL-M-Mod |
| **indra (math)** | cpu | 0.231 | 20 | medido | OpenRAIL-M-Mod |
| **pp_structurev3** | cpu | 0.211 | 20 | medido | Apache-2.0 |
| **pp_structurev3** | gpu | 0.210 | 20 | medido | Apache-2.0 |
