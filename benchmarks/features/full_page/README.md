# Feature `full_page` — banco de benchmark (esqueleto)

> Origen de los números: **sin valores numéricos (esqueleto)**.

## Qué mide

El pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas
juntos).

## Tarea `pyocrust`

`pp_structurev3` / `Indra` (`VeloceOCR`, pipeline completo).

## Métrica

**markdown_f1 / block_f1**: equivalencia de documento (tokens LCS y
multiconjunto de etiquetas de bloque), no solo OCR de texto.

## Dataset / ground truth

`OmniDocBench` da texto + LaTeX por bloque, pero su release **no** publica un
Markdown de página renderizado: sin GT de esa modalidad, `markdown_f1`/`block_f1`
quedan **no evaluadas** (nunca un `0.0`). Ya se mide el pipeline
(`task_type=full_page`) contra el GT textual.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| docling | `docling` |
| unstructured | `unstructured` |
| paddleocr PP-StructureV3 | `paddleocr paddlepaddle` |
| marker-pdf | `marker-pdf` |

## Estado

Esqueleto **documentado** para la parte Markdown/bloques; el pipeline ya corre
vía `common.runner` (`task_type=full_page`). `markdown_f1`/`block_f1` no se
evalúan sin GT propio.

## Provenance

Sin valores numéricos publicados. Cuando este banco se implemente, cada cifra irá
etiquetada `medido` (comando + dataset + n + warmup + repeats + device + fecha) o
`[ref: <url> (consultado YYYY-MM-DD)]`; nunca mezcladas sin etiquetar.
