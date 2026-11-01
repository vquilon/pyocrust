# Feature `seal` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Detección de texto dentro de sellos (tampones) superpuestos al documento.

## Tarea `pyocrust`

`seal_text_detection` (`TaskPredictor`).

## Métrica

**IoU / detección**: precision@IoU de las cajas de sello.

## Dataset / ground truth

No hay dataset local con GT de sellos. Requiere un set con sellos anotados; no se
inventa GT.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr (seal) | `paddleocr paddlepaddle` |
| doctrl | `doctrl` |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras mientras no haya GT local.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
