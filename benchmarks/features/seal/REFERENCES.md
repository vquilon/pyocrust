# Referencias externas — feature `seal`

Esta referencia separa resultados publicados de nuestras mediciones. Las puntuaciones de los modelos externos no se ejecutaron en este proyecto y no son comparables directamente con `synthetic_seal`.

## Datasets

| Dataset | Tamaño | `seal` / rectificación / orientación | URL | Licencia declarada | Descargable | GT | Métrica publicada |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DKDS** (Degraded Kuzushiji Documents with Seals) | 50 páginas (40 train, 10 test), 128 instancias de sello (100 train / 28 test) | Sí: detección de sellos en páginas degradadas; no rectificación ni orientación | [GitHub](https://github.com/RuiyangJu/DKDS)[4][5] | CC BY-SA 4.0 (dataset; atribuir también CODH/Kuzushiji original) | Sí; enlace de descarga OneDrive en README | Sí; cajas/instancias de sello y carácter | Precision, recall, F1 y AP50; el paper reporta AP50 de detección de sellos |
| **LEI-Detection / LEI-Benchmark / LEI-Stamps** | Detection: 6.759 cajas de sello dentro de 27.732 instancias (3 clases); benchmark end-to-end: 1.369 fichas; reconocimiento: 170.400 recortes, 3.817 clases | Detección/reconocimiento de sellos sí; no GT de rectificación ni orientación | [Repo](https://github.com/umr-ds/textual-stamp-recognition) · [Zenodo](https://zenodo.org/records/22788319)[20] | CC BY-NC 4.0 | Sí; descargas en Zenodo | Sí: cajas de stamp/etymon/content en detection; imágenes con GT end-to-end en benchmark, sin cajas; etiquetas de clase para recortes | Paper: mAP detección 98,80%; accuracy reconocimiento 97,02%; accuracy end-to-end 98,61% (protocolo benchmark) [22] |
| **CSD** (Chinese-Seal Dataset) | 1.486 imágenes, 16.688 sellos y 33.364 anotaciones | Detección/segmentación/reconocimiento de sellos chinos; no evidencia de GT de rectificación/orientación | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5079459) · [Google Drive](https://drive.google.com/file/d/1B_QUJymMC7_hvIu1EvE4tvaMR4QN2ME-/view?pli=1)[21] | SSRN indica “All rights reserved. No reuse allowed without permission”; dataset con permiso/licencia abierta no confirmado | Sí, enlace de Drive publicado; acceso efectivo no comprobado | Paper afirma anotaciones para benchmark; esquema/cobertura detallada no queda confirmada en el abstract | El abstract dice que publica benchmark, pero no aporta cifra/métrica concreta; no usar como cifra de modelo sin consultar el paper completo |
| **Clean Core Stamp Detection Dataset** | 7.854 imágenes; 12.659 cajas; 6.608 positivas y 1.246 negativas | Sí: detección de sellos documentales; no rectificación ni orientación | [Hugging Face](https://huggingface.co/datasets/123yohei/stamps)[6] | CC BY 4.0 | Sí; archivos zip de train/val/test, 970 MB en la ficha | Sí; YOLO bbox (train 10.046, val 1.298, test 1.315) | El dataset no publica una puntuación de modelo en su ficha; usar mAP/precision/recall/F1 con protocolo fijado |
| **Loay & Maha Stamps** | 1.557 recortes de sellos; 49 MB | Sólo imágenes recortadas de sellos (clasificación/lectura); no detección sobre página, rectificación ni orientación | [Mendeley Data](https://data.mendeley.net/datasets/ktr99fc826/3)[7] | CC0 1.0 | Sí | No hay cajas sobre página completa; las imágenes ya son recortes de sello | No declara métrica de benchmark de detección |

DKDS es el referente de detección más próximo a sellos impresos sobre documentos degradados. LEI aporta anotaciones/casos de uso de sellos textuales en fichas italianas y resultados publicados; CSD amplía cobertura a sellos chinos, pero no se recomienda reutilizarlo hasta obtener permiso/licencia explícitos. Clean Core ofrece volumen y cajas de una clase; Loay & Maha sólo sirve para recortes positivos, no detección sobre página completa. [4][5][6][7][20][21][22]

## Modelos y resultados publicados

DKDS evalúa YOLO en tres conjuntos de prueba (E, D y R). Sus resultados varían materialmente entre splits: [4]

| Modelo | Conjunto / protocolo | P sello | R sello | F1 sello | AP50 / AP50:95 sello |
| :--- | :--- | ---: | ---: | ---: | :--- |
| YOLOv8m | Tabla del paper (test DKDS) | — | — | — | AP50 99,1%; AP50:95 86,2% [5] |
| YOLOv9m | Testing-E (README) | 99,8% | 96,4% | 98,1% | No reportado en README [4] |
| YOLOv8m | Testing-D (README) | 92,9% | 81,4% | 86,8% | No reportado en README [4] |
| YOLOv8m | Testing-R (README) | 75,8% | 85,7% | 80,4% | No reportado en README [4] |

Los splits E/D/R del README y la tabla agregada del paper publican métricas distintas; no atribuir el AP50 del paper a Testing-E ni elegir el mejor split como cifra general. La caída de F1 de YOLOv8m de 86,8% en D a 80,4% en R ilustra sensibilidad a condiciones de prueba. [4][5]

Los resultados publicados de LEI son del workflow propuesto por Korfhage et al.: detección mAP 98,80%, reconocimiento de sellos accuracy 97,02% y evaluación end-to-end accuracy 98,61%. Son tareas/protocolos diferentes y no deben colapsarse en una única cifra; el paper también informa 91,60% y 89,47% para dos baselines OCR LLM y hasta 84,58% para MM-LLM en su benchmark. [22]

## Recomendación para este benchmark

- Añadir DKDS como evaluación externa opcional de detección, si se valida compatibilidad de las cajas/clases y el uso de datos CC BY-SA 4.0.
- Priorizar LEI para evaluación de detección/reconocimiento de sellos textuales en fichas; su licencia es CC BY-NC 4.0, por tanto no asumir uso comercial. [20][22]
- Clean Core es una segunda fuente de detección apropiada; antes de integrarlo, verificar calidad/procedencia de sus fuentes y comparar contra el test split sin mezclarlo con entrenamiento.
- CSD es una opción de investigación con acceso público enlazado, pero no incorporarlo hasta aclarar permiso/licencia de reutilización. [21]
- No usar Loay & Maha para medir localización en página completa; puede servir para reconocimiento/clasificación de recortes.
- OmniDocBench y ParseBench no son benchmarks de sellos: sus etiquetas de watermark/layout o sus reglas de parsing no equivalen a boxes GT de sellos. Ver referencias de esos datasets en las features correspondientes.

## Sources

[4] https://github.com/RuiyangJu/DKDS
[5] https://ar5iv.labs.arxiv.org/html/2511.09117
[6] https://huggingface.co/datasets/123yohei/stamps/raw/main/README.md
[7] https://data.mendeley.com/datasets/ktr99fc826/3
[20] https://github.com/umr-ds/textual-stamp-recognition
[21] https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5079459
[22] https://academic.oup.com/ijl/article-abstract/doi/10.1093/ijl/ecag001/8507197?redirectedFrom=fulltext
