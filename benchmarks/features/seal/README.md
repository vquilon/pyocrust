# Feature `seal` — banco de benchmark

> Origen de los números: **`medido`** por este banco (ejecutado en este repo).

## Qué mide

Detección de **regiones de sello** (tampones) superpuestas al documento.

## Tarea `pyocrust`

`seal_text_detection` (`TaskPredictor`; PP-OCRv4 mobile seal det).

## Métrica

**Cajas**: `box_recall` = recall@IoU 0.5 de las cajas de sello, `box_iou_mean` =
IoU medio del mejor candidato por caja GT. Son las métricas de cajas compartidas
(`common/metrics.py::box_metrics`), que el runner ya calcula cuando la muestra
anota `gt_boxes`; el banco no duplica un scorer de IoU.

## Dataset / ground truth

**`synthetic_seal` — GT SINTÉTICO determinista.** No hay set público local con
sellos anotados: OmniDocBench v1.6 **no** anota `category_type=seal` (verificado
sobre la anotación cacheada en `benchmarks/data_cache`). El banco **genera**
documentos blancos con un tampón (doble borde rojo + texto) pegado en una posición
conocida; la caja GT es el rectángulo del sello pegado. El set se declara
**sintético** aquí y en el `provenance` del banco: **no** es anotación humana de
sellos reales.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` | Estado |
| :--- | :--- | :--- |
| paddleocr (seal) | `paddleocr paddlepaddle` | no integrada (queda `skipped`) |
| doctrl | `doctrl` | no integrada (queda `skipped`) |

## Uso

```
.venv/Scripts/python.exe benchmarks/features/seal/bank.py --limit 8 --backends pyocrust_seal
.venv/Scripts/python.exe benchmarks/features/report.py --feature seal
```

## Estado

**Implementado** y medido sobre el set sintético determinista.

## Provenance

Todo valor publicado aquí es `medido` (comando + dataset + `n` + `warmup` +
`repeats` + device + fecha guardados en el `summary.json` de la run). El dataset es
**sintético**: el `provenance` lo deja explícito. Los valores de `referencia`
(externos) no los produce este banco y solo se citarían con su URL.
