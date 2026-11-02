# Feature `rectification` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

Rectificación de documentos deformados (páginas curvadas/inclinadas) antes de OCR.

## Tarea `pyocrust`

`document_rectification` (`TaskPredictor`; UVDoc, devuelve un PNG rectificado).

## Métrica

**SSIM** (similitud estructural, en gris) entre la imagen rectificada por el motor
y la **imagen limpia de referencia**, acotado a `[0, 1]`. La predicción se
reencuadra al tamaño de la referencia (el motor puede devolver otra resolución).

## Dataset / ground truth

`synthetic_rectification`: **GT sintético determinista**. Se toman las páginas de
`OmniDocBench` ya presentes en `benchmarks/data_cache` (sin descargar nada), se
reescalan a un tamaño fijo y se les aplica una **homografía conocida** (cuatro
esquinas fijas); el GT es la imagen limpia original. El par (deformada, limpia) es
reproducible entre ejecuciones.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| paddleocr | `paddleocr paddlepaddle` |
| docling | `docling` |

## Estado

**Implementado**: ejecuta `pyocrust` (`pyocrust_rectify`) sobre las páginas
deformadas y publica el SSIM contra la referencia limpia. Las alternativas están
**documentadas** (se integran como backends cuando se instalen).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
