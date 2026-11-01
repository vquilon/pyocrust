# Feature `orientation` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Orientación de la página completa (0/90/180/270°) antes de OCR.

## Tarea `pyocrust`

`document_orientation` (`TaskPredictor`).

## Métrica

**accuracy** de la rotación (4 clases).

## Dataset / ground truth

No hay dataset local con GT de orientación de página. Se puede construir el GT
rotando páginas de OmniDocBench y verificando OCR; queda documentado, no medido.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| docling | `docling` |
| surya | `surya-ocr` (requiere torch) |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras mientras no haya GT local.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
