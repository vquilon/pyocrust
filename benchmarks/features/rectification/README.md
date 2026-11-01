# Feature `rectification` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Rectificación de documentos deformados (páginas curvadas/inclinadas) antes de OCR.

## Tarea `pyocrust`

`document_rectification` (`TaskPredictor`; devuelve un PNG rectificado).

## Métrica

**calidad de enderezado**: rectitud de las líneas de texto y/o similitud con la
referencia enderezada (SSIM/PNSR contra el par de referencia).

## Dataset / ground truth

No hay GT público local de imagen rectificada de referencia. Hace falta un par
(deformada, enderezada); sin él, la calidad queda **no evaluada**.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| docling | `docling` |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras mientras no haya GT local.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
