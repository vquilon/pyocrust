# Feature `orientation` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

Orientación de la página completa (0/90/180/270°) antes de OCR.

## Tarea `pyocrust`

`document_orientation` (`TaskPredictor`; PP-LCNet).

## Métrica

**accuracy** de la rotación (4 clases).

## Dataset / ground truth

`synthetic_orientation`: **GT sintético determinista**. Se toman las páginas de
`OmniDocBench` ya presentes en `benchmarks/data_cache` (sin descargar nada) y se
rotan 0/90/180/270; el GT es la etiqueta de corrección que el clasificador debe
emitir para esa rotación, `(360 - a) mod 360` — convención **comprobada sobre las
cuatro clases en una página real** antes de escribir el banco.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| docling | `docling` |
| surya | `surya-ocr` (requiere torch) |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_orientation`) sobre las páginas
rotadas y publica la accuracy de las 4 clases. Las alternativas están
**documentadas** (se integran como backends cuando se instalen).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
