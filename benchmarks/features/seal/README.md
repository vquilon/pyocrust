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

| Alternativa | Módulo / `pip install` | Runtime | Licencia | Estado |
| :--- | :--- | :--- | :--- | :--- |
| onnx_seal_det | `onnxruntime` | onnxruntime (Python) | Apache-2.0 | **medido** (real) |
| paddleocr (seal) | `paddleocr paddlepaddle` | Paddle | Apache-2.0 | no integrada (queda `skipped`) |
| doctrl | `doctrl` | — | — | no integrada (queda `skipped`) |

`onnx_seal_det` ejecuta **los mismos pesos** que `pyocrust_seal`
(`pp-ocrv4_mobile_seal_det.onnx`, Apache-2.0) sobre `onnxruntime` en Python —
la alternativa del motor de referencia (Rust `oar-ocr` vs `onnxruntime`),
como `uvdoc`/`lcnet_doc_ori`. En el set sintético (n=20, CPU) da
**recall@IoU 0.5 = 0.750 / IoU medio = 0.607**, frente a **0.750 / 0.686** de
`pyocrust_seal`: misma calidad de detección, ~3× más rápido en Python puro.

## Uso

```
.venv/Scripts/python.exe benchmarks/features/seal/bank.py --limit 8 --backends pyocrust_seal,onnx_seal_det
.venv/Scripts/python.exe benchmarks/features/report.py --feature seal
```

## Estado

**Implementado** y medido sobre el set sintético determinista, con **una
alternativa externa real** (`onnx_seal_det`) además de `pyocrust_seal`.

## Límites del GT sintético (leer antes de extrapolar)

El GT es el **rectángulo del tampón pegado**: sirve para comparar motores entre
sí sobre la misma caja anotada, pero **no** representa sellos reales. Los tampones
del set son **axis-aligned** (sin rotación ni curvatura) y el detector DB los
resuelve sobre todo por el **anillo del borde**; en un anillo hueco perfecto
`findContours` puede devolver dos fronteras (interior y exterior) y, por tanto,
dos cajas donde el GT anota una. Por eso el IoU medio (0.61–0.69) es menor que el
recall (0.75): el motor localiza el sello, pero su caja no coincide al píxel con
el rectángulo GT. Fue el motivo del `skip` de `paddleocr`/`doctrl` (sin adaptador
propio) y es la razón por la que **no** se publica como precisión sobre sellos
reales.

## Provenance

Todo valor publicado aquí es `medido` (comando + dataset + `n` + `warmup` +
`repeats` + device + fecha guardados en el `summary.json` de la run). El dataset es
**sintético**: el `provenance` lo deja explícito. Los valores de `referencia`
(externos) no los produce este banco y solo se citarían con su URL.
