# Feature `layout` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Detección de layout de página: cada bloque (título, párrafo, tabla, figura,
fórmula, encabezado...) con su clase y su caja.

## Tarea `pyocrust`

`layout_detection` (`TaskPredictor`, `pp_doclayoutv3`).

## Métrica

**mAP / IoU por clase** frente al GT (precisión@IoU y recall por clase de bloque).

## Dataset / ground truth

`OmniDocBench` anota `category_type` + `poly` por bloque, así que **hay GT de
layout**. Falta el adaptador que empareja las cajas predichas con los bloques GT.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| layoutparser | `layoutparser` |
| docling | `docling` |
| unstructured | `unstructured` |
| paddleocr | `paddleocr paddlepaddle` |
| TATR (transformers) | `transformers` + `table-transformer` |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras. El dataset documental ya trae GT de layout;
falta el emparejador caja↔bloque y la métrica por clase.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
