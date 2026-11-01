# Feature `text_line` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Orientación de cada línea de texto (0/180°) antes de reconocerla.

## Tarea `pyocrust`

`text_line_orientation` (`TaskPredictor`).

## Métrica

**accuracy** 0/180 por línea.

## Dataset / ground truth

No hay dataset local con GT de orientación de línea. El GT es barato de generar
(voltear líneas recortadas) pero no está incluido aún.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| surya | `surya-ocr` (requiere torch) |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras mientras no haya GT local.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
