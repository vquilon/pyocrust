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
| PaddleOCR SLANet | `paddleocr paddlepaddle` |
| docling TableFormer | `docling` (venv aislado `benchmarks/.venv_docling`) |
| paddleocr PP-Structure | `paddleocr paddlepaddle` |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_table`) **y tres alternativas
externas reales** sobre los recortes de tabla anotados y publica el TEDS de
estructura:

- **`tatr`** — `transformers` + `microsoft/table-transformer-structure-recognition`
  (**MIT**), CPU-only.
- **`paddleocr_slanet`** — SLANet_plus de PaddleOCR por su API oficial
  `TableStructureRecognition` (**Apache-2.0**), CPU-only. Mismo motor SLANeXt que
  `pyocrust` pero implementación de PaddleOCR: la comparación es 1:1 sobre el
  mismo GT.
- **`docling_tableformer`** — TableFormer de docling (**MIT**) en el venv aislado
  `benchmarks/.venv_docling` (por subproceso, como el `docling` de `full_page`),
  CPU-only. Emite HTML **con** texto de celda, pero se puntúa con el **mismo
  TEDS-S** (secuencia de etiquetas): la cabecera `<th>` se normaliza a `<td>` para
  no penalizar la etiqueta (para filas/columnas/fusiones son la misma celda).

Los backends CPU-only (`tatr`, `paddleocr_slanet`, `docling_tableformer`):
`--device gpu` los deja `skipped` con motivo (nunca un fallback CPU etiquetado GPU).

**Límite honesto de `docling_tableformer`**: `DocumentConverter` solo emite tabla
si la detecta en el recorte; en algunos recortes (p. ej. tablas muy simples o con
líneas tenues) no devuelve tabla y la métrica queda **no evaluada** (`N/A`, nunca
un 0.0). El TEDS medio se calcula sobre las muestras evaluadas, no sobre las 20.

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
