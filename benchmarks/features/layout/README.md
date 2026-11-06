# Feature `layout` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

Detección de layout de página: cada bloque (título, párrafo, tabla, figura,
fórmula, encabezado...) con su clase y su caja.

## Tarea `pyocrust`

`layout_detection` (`TaskPredictor`, `pp_doclayoutv3`).

## Métrica

**mAP@IoU 0.5 y recall@IoU 0.5 macro por clase**: emparejado voraz 1-a-1 de las
cajas GT con las detectadas (AP acumulado a un único umbral, VOC2007).

## Dataset / ground truth

`omnidocbench_layout`: `OmniDocBench` anota `category_type` + `poly` por bloque,
así que **hay GT de layout real** (no se inventa nada).

Solo se puntúan las clases con equivalencia declarada entre el vocabulario del
modelo (25 clases de PP-DocLayoutV3) y las categorías anotadas
(`common.datasets.LAYOUT_MODEL_TO_GT`):

| Clase del modelo | Categoría anotada |
| :--- | :--- |
| `text` | `text_block` |
| `doc_title`, `paragraph_title` | `title` |
| `display_formula` | `equation_isolated` |
| `table` | `table` |
| `image` | `figure` |
| `figure_title` | `figure_caption` |
| `header` / `footer` | `header` / `footer` |
| `number` | `page_number` |
| `footnote` | `page_footnote` |
| `reference`, `reference_content` | `reference` |

Las etiquetas del modelo sin contrapartida anotada (`inline_formula`,
`formula_number`, `seal`, `chart`, ...) se ignoran: no se cuentan como acierto
ni como fallo, porque el dataset no las anota de forma separable.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` | Medida |
| :--- | :--- | :--- |
| docling-layout-heron-101 (RT-DETR) | `transformers` | sí (`docling_heron_101`) |
| yolo26m (doc-layout) | `ultralytics` | sí (`yolo26m`, 21.8M) |
| yolov10b (DocLayNet) | `ultralytics` | sí (`yolov10b`, 20.5M) |
| yolov10x (DocLayNet) | `ultralytics` | sí (`yolov10x`, 31.7M) |
| deformable-detr-DocLayNet | `transformers` | `skipped` (sin `preprocessor_config.json` en caché) |
| layoutparser | `layoutparser` | no integrada |
| docling | `docling` | no integrada |
| unstructured | `unstructured` | no integrada |
| paddleocr | `paddleocr paddlepaddle` | no integrada |

Los tres YOLO documentales comparten el vocabulario DocLayNet (11 clases) — verificado cargando los pesos .pt con ultralytics.YOLO y leyendo model.names; todos son fine-tuneados sobre DocLayNet, no modelos base. Criterio del banco: solo modelos documentales (DocLayNet-fine-tuned); los YOLO base quedan excluidos. pyocrust_layout usa pp-doclayoutv3. Pesos .pt en D:/Environments/cache/models/layout/, todo en CPU.

> **Nota de equidad del tiempo.** Los adaptadores de `transformers` cronometran
> solo forward + post-proceso (preprocesado fuera, igual que `pyocrust`).
> `ultralytics` cronometra su `model.predict(...)` entero, que **incluye** su
> preprocesado interno; su columna `ms/imagen` es por tanto algo conservadora y no
> mide exactamente el mismo tramo. Separarlo exigiría reimplementar el letterbox.

> **Nota de equidad del AP.** El mAP se calcula sobre la curva precision-recall
> completa, así que los adaptadores emiten las detecciones crudas (suelo
> `LAYOUT_AP_SCORE_FLOOR = 0.05` en `common/runner.py`) y el barrido lo hace
> `_class_ap`. Emitir solo `score>=0.5` medía un único punto de operación y hundía
> el número: en este host 0.236→0.303 (yolo26m) y 0.658→0.821 (heron-101) al
> bajarlo. `pyocrust_layout` recibe el mismo suelo vía `score_threshold`.

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_layout`) con warmup/repeats sobre
el GT de layout de OmniDocBench y publica mAP/recall por clase, más las
alternativas reales ya integradas (RT-DETR heron-101 y tres YOLO documentales).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
