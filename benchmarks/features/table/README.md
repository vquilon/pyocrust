# Feature `table` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

Tablas: clasificación (hay/no hay), estructura (filas/columnas) y detección de
celdas.

## Tarea `pyocrust`

`table_classification` / `table_structure_recognition` / `table_cell_detection`
(`TaskPredictor`).

## Métrica

**TEDS / estructura**: edit distance del árbol de estructura reconstruido (TEDS)
e IoU de celdas detectadas.

## Dataset / ground truth

`OmniDocBench` anota tablas (`html`/`latex`); el estándar de TEDS es PubTabNet.
TEDS necesita el HTML de la tabla GT; falta el adaptador que lo extrae por bloque.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| table-transformer (TATR) | `transformers` + `table-transformer` |
| docling | `docling` |
| paddleocr PP-Structure | `paddleocr paddlepaddle` |

## Estado

Esqueleto **documentado**: declara tarea, métrica y alternativas, pero **no**
ejecuta motores ni publica cifras mientras no haya GT adaptado.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
