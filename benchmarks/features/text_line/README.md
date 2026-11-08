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

| Alternativa | Módulo / `pip install` | Relación |
| :--- | :--- | :--- |
| rapidocr_mobile_cls | `rapidocr` | **independiente**: red mobile cls de PP-OCRv2 (proyecto RapidAI), NO el PP-LCNet |
| lcnet_textline_ori (`onnxruntime`) | `onnxruntime` | **mismo peso, distinta vía** (el MISMO PP-LCNet de PaddleOCR) |
| paddleocr | `paddleocr paddlepaddle` | envuelve el mismo PP-LCNet |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_textline`) y las alternativas
`lcnet_textline_ori` (mismo peso, otra vía) y `rapidocr_mobile_cls` (independiente)
sobre las líneas giradas y publica la accuracy 0/180. El informe declara la
**procedencia** de cada alternativa (independiente vs mismo peso por otra vía).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
