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

**Desgranado estructura/posición** (misma pasada): `layout mAP@0.5`, `TEDS tabla`
y similitud `LaTeX`; detección + texto + secuencia de **títulos** y **orden de
lectura** (Kendall τ); y, como métrica **propia**, **figuras e imágenes**:
`figure_recall`/`figure_precision` (detección de las cajas `figure`, IoU@0.5 como
`layout`), `figure_caption_recall`/`figure_caption_precision` (detección de las
captions) y **`figure_caption_pair_f1`** (asociación figura↔caption: exige que,
detectada la figura, se localice su caption compañera; una página con las figuras
detectadas pero **sin** sus captions puntúa bajo aquí aunque su `figure_recall`
sea `1.0`). Sin GT de figuras, quedan `N/A` (nunca `0.0`). Las **máscaras**
(`*_mask`), no emitibles por el pipeline, se **ignoran** al puntuar.

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

**Medidas hoy**: `docling` (MIT). PaddleOCR `pp_structurev3_api` (Apache-2.0) queda
`skipped`: su pipeline en proceso **cuelga o segfaultea** (exit 139) en páginas reales
de la muestra (medido 2026-11-09, imagen grande 11112x7925, tras cargar 16 submodelos),
así que se retiró del `DEFAULT_BACKENDS` y se registra como `unavailable_factory`
(pedido explícito → `skipped` con motivo, nunca cuelga el banco). Falta envolverlo en
subproceso con timeout. `unstructured`, `marker-pdf` y `pdf_extract_kit` siguen
`skipped` (adaptador pendiente / solo publican un detector de layout, no un pipeline
de documento).

### docling — versión y entorno (reproducible)

`docling` **no** se instala en el venv del banco: su `[standard]` arrastra
torch/torchvision y degradaría los backends de `layout`/`table`. Vive en un venv
aislado `benchmarks/.venv_docling` y se invoca por **subproceso**, un modelo a la
vez (ver `common/runner.py::_docling_backend`).

| Paquete | Versión medida |
| :--- | :--- |
| `docling` | **2.149.0** |
| `transformers` | 5.22.2 |
| `huggingface_hub` | 2.4.0 (requiere `>=2` por `ResolvedRevision` que importa transformers 5.x) |
| `tokenizers` | 0.23.3 (`transformers` 5.22 exige `>=0.23.1,<0.24`) |
| `torch` | 2.15.0 (CPU) |

Creación del venv (si no existe) y pins que hubo que corregir:

```bash
uv venv benchmarks/.venv_docling
uv pip install --python benchmarks/.venv_docling/Scripts/python.exe docling
# pins obligatorios: sin ellos docling no arranca con transformers 5.x
uv pip install --python benchmarks/.venv_docling/Scripts/python.exe \
    "huggingface_hub>=2" "tokenizers>=0.23.1,<0.24.0"
```

## Estado

**Implementado**: ejecuta `pyocrust_structure` (PP-StructureV3) y `pyocrust_indra`
sobre las páginas anotadas y publica `markdown_f1`/`block_f1`. Si Indra no tiene
sus 9 artefactos en disco, queda **`skipped` con su motivo** (no se mide a medias).

**Alternativa externa medida**: `docling` (MIT) n=6 CPU → `markdown_f1` **0.204**
frente a **0.083** de `pp_structurev3`, con CER 1.119 vs 5.737. Run
`results/full_page/2026-11-09_14-28-38` (6/6 `ok`). Ahora `full_page` **ya no
tiene 0 externos medidos**.

> **Límite honesto de docling en este banco**: el adaptador devuelve **solo el
> Markdown** (`export_to_markdown`), sin cajas ni tipos de bloque. Por eso sus
> columnas de estructura (`block_f1`, `layout mAP`, `title_recall`,
> `figure_recall`) salen **`N/A`** —el motor no emite esa modalidad y el informe
> no la evalúa—, nunca un `0.000`. La comparación justa con `pyocrust_structure`
> es la columna `markdown_f1`/`CER`; desgranar layout/tabla/fórmula de docling
> exigiría un adaptador sobre `export_to_dict` (fuera del alcance de esta tarjeta).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
