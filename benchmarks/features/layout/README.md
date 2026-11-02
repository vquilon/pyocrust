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

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| layoutparser | `layoutparser` |
| docling | `docling` |
| unstructured | `unstructured` |
| paddleocr | `paddleocr paddlepaddle` |
| TATR (transformers) | `transformers` + `table-transformer` |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_layout`) con warmup/repeats sobre
el GT de layout de OmniDocBench y publica mAP/recall por clase. Las alternativas
de la tabla están **documentadas** (se integran como backends cuando se instalen).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
