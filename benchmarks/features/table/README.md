# Feature `table` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

Tablas: clasificación (hay/no hay), estructura (filas/columnas) y detección de
celdas.

## Tarea `pyocrust`

`table_structure_recognition` (`TaskPredictor`; SLANet/SLANeXt).

## Métrica

**TEDS de estructura** = `1 - editDist(etiquetas HTML) / max(longitudes)`: la
secuencia de etiquetas (`<tr>`, `<td>`, `</tr>`...) sin el texto de las celdas y
sin envoltorios (`<table>`/`<body>`). Es la variante *TEDS-S* de la literatura.

El modelo de estructura **no emite el texto de celda**, así que el TEDS de árbol
completo (que lo exige) no se puede medir aquí: comparar etiquetas mide filas,
columnas y fusiones, que es lo que el modelo predice; el contenido de cada celda
lo resuelve el OCR y no entra en esta métrica.

## Dataset / ground truth

`omnidocbench_table`: cada bloque `table` anotado de `OmniDocBench` se recorta por
su `poly` y su **`html` anotado** es el GT (no se inventa nada). `PubTabNet` sería
el dataset alternativo estándar de TEDS; no está en caché local.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| table-transformer (TATR) | `transformers` + `table-transformer` |
| docling | `docling` |
| paddleocr PP-Structure | `paddleocr paddlepaddle` |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_table`) **y la alternativa real
TATR** (`tatr`: `transformers` + `microsoft/table-transformer-structure-recognition`)
sobre los recortes de tabla anotados y publica el TEDS de estructura. `tatr` es
**CPU-only**: `--device gpu` lo deja `skipped` con motivo (nunca un fallback CPU
etiquetado GPU). El resto de alternativas sigue **documentado** (se integran como
backends cuando se instalen).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
