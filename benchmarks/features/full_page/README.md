# Feature `full_page` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

El pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas
juntos).

## Tarea `pyocrust`

`pp_structurev3` (`VeloceOCR`) e Indra (pipeline completo de página).

## Métrica

**markdown_f1 / block_f1**: equivalencia de documento (tokens LCS sensibles al
orden y conservando el LaTeX) y multiconjunto de tipos de bloque, además del
CER/WER de texto que ya mide el runner.

## Dataset / ground truth

`omnidocbench_full_page`: la release de `OmniDocBench` **no** publica un Markdown
de página renderizado, pero **sí** anota el contenido de cada bloque
(`text`/`latex`/`html`) y su `order` de lectura. El Markdown de referencia se
**reconstruye** concatenando esos contenidos en ese orden (las máscaras `*_mask` y
los bloques `ignore`/`abandon` no son contenido), y los tipos de bloque se
traducen al vocabulario que emite el pipeline (`kind`, vía
`common.datasets.ODB_CATEGORY_TO_KIND`) para que `block_f1` compare la misma
taxonomía en ambos lados. No se inventa contenido: solo se serializa lo anotado.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| docling | `docling` |
| unstructured | `unstructured` |
| paddleocr PP-StructureV3 | `paddleocr paddlepaddle` |
| marker-pdf | `marker-pdf` |

## Estado

**Implementado**: ejecuta `pyocrust_structure` (PP-StructureV3) y `pyocrust_indra`
sobre las páginas anotadas y publica `markdown_f1`/`block_f1`. Si Indra no tiene
sus 9 artefactos en disco, queda **`skipped` con su motivo** (no se mide a medias).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
