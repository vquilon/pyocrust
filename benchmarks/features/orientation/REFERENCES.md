# Referencias externas — feature `orientation`

Resultados **publicados**; no ejecutados aquí. La accuracy de un dataset externo no se compara 1:1 con nuestro GT sintético: cambian idiomas, ángulos, distribución y protocolo.

## Datasets

| Dataset | Tamaño | `seal` / rectificación / orientación | URL | Licencia declarada | Descargable | GT | Métrica |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ORB / OCR-Rotation-Bench** | 1.863 imágenes reportadas: ORB-En 897, ORB-Indic 966 (11 lenguas); HF publica cinco Parquet (10,6 + 322 + 320 + 226 + 509 MB ≈ 1,388 MB decimales / 1,39 GB) con variantes de 4/8/12 clases | Orientación/rotación: sí; seal y rectificación geométrica: no | [Paper](https://arxiv.org/html/2511.04161v2) · [HF dataset](https://huggingface.co/datasets/krutrim-ai-labs/ocr_rotation_bench/tree/main)[8][9] | Krutrim Community License Agreement v1.0 (`other` en HF) | Sí; los cinco Parquet se muestran como descargables en la ficha HF (metadatos comprobados, sin descargar datos) | Sí; etiquetas/clase de rotación y GT OCR disponible en subconjuntos | Accuracy por número de clases; downstream CER/WER/ANLS |
| **OmniDocBench** | 1.651 páginas PDF (release actual descrito en la ficha) | `orientation`: no GT de rotación global; atributos `text_rotate` y `table_vertical` sólo etiquetan texto/tablas rotados. `rectification`: no. `seal`: no; `watermark` no es clase de sello | [Hugging Face](https://huggingface.co/datasets/opendatalab/OmniDocBench) · [GitHub](https://github.com/opendatalab/OmniDocBench)[1] | Research only / no comercial, según copyright statement de la ficha | Sí | GT rico para parsing/layout/OCR, pero no GT de orientación global, rectificación o sello | Layout, OCR/text, tablas y fórmulas; no accuracy de orientación |
| **ParseBench** | 2.078 páginas únicas; 169.011 reglas en cinco dimensiones | No cubre orientación, rectificación ni detección de sellos | [HF](https://huggingface.co/datasets/llamaindex/ParseBench) · [GitHub](https://github.com/run-llama/ParseBench)[2][3] | Apache-2.0, según ficha/repo; los documentos vienen de fuentes públicas | Sí | GT basado en reglas para tablas, charts, contenido, formato y layout; no ángulos de rotación | GTRM, ChartDataPointMatch, Content Faithfulness, Semantic Formatting y Element Pass Rate |

ORB es el candidato directamente evaluable para orientación: las variantes publicadas cubren 4, 8 y 12 clases. La ficha HF consultada contiene cinco Parquet visibles como descargables; sólo se consultaron metadatos, no se bajaron los datos ni los pesos incluidos en `weights.zip`. [8][9]

OmniDocBench sirve para parsing general, no para medir orientación de página: `text_rotate` y `table_vertical` describen atributos de bloques, no la orientación global ni una transformación GT para enderezar la página. ParseBench mide fidelidad estructural/semántica y tampoco anota rotación. [1][2][3]

## Modelos y resultados publicados

| Modelo | Benchmark y protocolo | Resultado | Fuente |
| :--- | :--- | :--- | :--- |
| Clasificador propuesto basado en encoder Phi-3.5-Vision + dynamic cropping (~304M parámetros reportados) | ORB, 12 clases (30°) | Accuracy: 98,00% ORB-En; 96,71% ORB-Indic | [Paper, tabla 4](https://arxiv.org/html/2511.04161v2)[8] |
| Mismo clasificador | ORB, 4 clases (90°) | Accuracy: 96,81% ORB-En; 92,68% ORB-Indic | [Paper, tabla 7](https://arxiv.org/html/2511.04161v2)[8] |
| PP-LCNet_x1_0_doc_ori | Dataset propio PaddleX de 1.000 imágenes multi-escenario (incluye documentos e IDs), 4 orientaciones | Top-1 accuracy: 99,06%; modelo 7 MB | [PaddleOCR docs](https://www.paddleocr.ai/latest/en/version3.x/module_usage/doc_img_orientation_classification.html)[10] |

No comparar directamente el 99,06% de Paddle (su conjunto interno de 1.000 imágenes) con ORB; la composición y el protocolo no son los mismos. El artículo ORB reporta además mejoras OCR al corregir rotación, pero las métricas OCR downstream no sustituyen accuracy de clasificación. [8][10]

## Sources

[1] https://huggingface.co/datasets/opendatalab/OmniDocBench/raw/main/README.md
[2] https://github.com/run-llama/ParseBench/blob/main/README.md
[3] https://huggingface.co/datasets/llamaindex/ParseBench
[8] https://arxiv.org/html/2511.04161v2
[9] https://huggingface.co/datasets/krutrim-ai-labs/ocr_rotation_bench
[10] https://www.paddleocr.ai/latest/en/version3.x/module_usage/doc_img_orientation_classification.html
