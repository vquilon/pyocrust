# Feature `text_line` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

Orientación de cada línea de texto (0/180°) antes de reconocerla.

## Tarea `pyocrust`

`text_line_orientation` (`TaskPredictor`; PP-LCNet).

## Métrica

**accuracy** 0/180 por línea.

## Dataset / ground truth

`synthetic_text_line`: **GT sintético determinista**. Se recortan los bloques de
texto anotados de las páginas de `OmniDocBench` ya presentes en
`benchmarks/data_cache` (sin descargar nada) y se giran 0/180; el GT es la
etiqueta de orientación aplicada. La entrada es un **recorte de línea** (la tarea
espera una línea, no una página completa).

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| surya | `surya-ocr` (requiere torch) |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_textline`) sobre las líneas giradas
y publica la accuracy 0/180. Las alternativas están **documentadas** (se integran
como backends cuando se instalen).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
