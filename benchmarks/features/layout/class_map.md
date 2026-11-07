# Mapa de equivalencia de clases — feature `layout`

> **Qué es.** El mapa de equivalencias entre las **taxonomías de clases** de los
> motores de layout que medimos (DocLayNet ↔ PP-DocLayoutV3 ↔ OmniDocBench) y la
> regla con la que se puntúan. Cada par lleva su fuente (`[ref: …]`) o la marca
> **`decisión propia`** si es criterio nuestro. Lo que no se puede sostener con
> evidencia se deja **pendiente** en vez de inventarse.
>
> **Código que lo usa:** `common/datasets.py`
> (`LAYOUT_MODEL_TO_GT`, `LAYOUT_DOCLAYNET_LABEL_TO_GT`, `layout_gt_classes`) y
> `features/layout/bank.py::score_layout`. Los adaptadores que emiten el
> vocabulario de cada motor están en `common/runner.py`.
>
> **Sin arreglo a mano.** Todas las cifras de la sección *Antes/después* salen de
> ejecutar el banco con el mapa implementado; ninguna se ha retocado.

## 1. El problema

En `layout`, las alternativas YOLO son SOTA en su paper y **rinden muy mal en
nuestro banco**:

| Motor | mAP@IoU 0.5 medido (nuestro GT) | mAP@0.5 publicado (DocLayNet) |
| :--- | ---: | ---: |
| pyocrust_layout | **0.764** | — |
| docling_heron_101 | 0.508 | 0.780 |
| yolov10x | 0.169 | **0.924** |
| yolov10b | 0.109 | 0.922 |
| yolo26m | 0.222 | — |

La causa **no** es (solo) que el modelo sea malo: es que se comparaban etiquetas
de vocabularios incompatibles y, además, categorías anotadas que el motor **no
puede emitir** se contaban como fallo (`AP = 0`), inflando el castigo.

## 2. Taxonomías fuente

| Vocabulario | Nº clases | Fuente |
| :--- | ---: | :--- |
| **DocLayNet** | 11 | [ref: https://huggingface.co/datasets/ds4sd/DocLayNet] · paper [ref: https://doi.org/10.1145/3534678.3539043] |
| **docling-layout-heron-101** | 17 | [ref: https://huggingface.co/docling-project/docling-layout-heron-101] · 11 de DocLayNet + `Code`, `Checkbox-Selected`, `Checkbox-Unselected`, `Document Index`, `Form`, `Key-Value Region` (verificado localmente sobre `config.id2label`) |
| **PP-DocLayoutV3** | 25 | [ref: https://paddlepaddle.github.io/PaddleX/latest/en/module_usage/tutorials/ocr_modules/layout_detection.html] · verificado en el código que ejecutamos (`oar-ocr-core` 0.10.1, `layout_detection_adapter.rs::pp_doclayoutv3`) |
| **OmniDocBench** (nuestro GT) | 19 categorías de layout | [ref: https://arxiv.org/abs/2412.07626] · [ref: https://huggingface.co/datasets/opendatalab/OmniDocBench] |

Clases de DocLayNet tal y como las emiten los pesos que usamos (minúsculas):
`caption, footnote, formula, list-item, page-footer, page-header, picture,
section-header, table, text, title`.

Las 25 de PP-DocLayoutV3: `abstract, algorithm, aside_text, chart, content,
display_formula, doc_title, figure_title, footer, footer_image, footnote,
formula_number, header, header_image, image, inline_formula, number,
paragraph_title, reference, reference_content, seal, table, text, vertical_text,
vision_footnote`.

## 3. Equivalencias

### 3.1 DocLayNet → OmniDocBench (alternativas RT-DETR / Deformable-DETR / YOLO)

Es el mapa `LAYOUT_DOCLAYNET_LABEL_TO_GT`; coincide con la composición
`runner.LAYOUT_DOCLAYNET_LABEL_TO_MODEL` ∘ `LAYOUT_MODEL_TO_GT` (ambos caminos dan
el mismo resultado — aserto en el autochequeo de `common/datasets.py`).

| DocLayNet | OmniDocBench | Fuente |
| :--- | :--- | :--- |
| `text` | `text_block` | [ref: DocLayNet 11 clases] — única clase de prosa |
| `title` | `title` | [ref: DocLayNet 11 clases] |
| `section-header` | `title` | **decisión propia** — OmniDocBench agrupa *todo* encabezado en `title`; DocLayNet separa `Title` de `Section-header` |
| `formula` | `equation_isolated` | [ref: DocLayNet 11 clases] — `Formula` = fórmula mostrada |
| `table` | `table` | [ref: DocLayNet 11 clases] |
| `picture` | `figure` | [ref: DocLayNet 11 clases] |
| `caption` | `figure_caption` | **decisión propia** — DocLayNet tiene **un solo** `Caption` (figura y tabla); OmniDocBench distingue `figure_caption` / `table_caption` / `equation_caption` |
| `page-header` | `header` | [ref: DocLayNet 11 clases] |
| `page-footer` | `footer` | [ref: DocLayNet 11 clases] |
| `footnote` | `page_footnote` | [ref: DocLayNet 11 clases] |
| `list-item` | — **pendiente** | DocLayNet `List-item` no tiene equivalencia 1:1 con ninguna categoría de layout de OmniDocBench de forma sostenible con evidencia. Se **ignora** (no se cuenta ni a favor ni en contra). |
| *(no existe)* | `page_number` | **sin equivalencia** — DocLayNet no tiene clase de número de página ⇒ se **ignora** al puntuar motores DocLayNet |
| *(no existe)* | `reference` | **sin equivalencia** — DocLayNet no tiene clase de referencia bibliográfica ⇒ se **ignora** |

`code`, `checkbox-selected`, `checkbox-unselected`, `document index`, `form`,
`key-value region` (solo heron-101): sin categoría de layout equivalente en
OmniDocBench ⇒ **ignoradas**.

### 3.2 PP-DocLayoutV3 → OmniDocBench (motor propio `pyocrust_layout`)

Es el mapa `LAYOUT_MODEL_TO_GT` (13 de las 25 clases tienen destino).

| PP-DocLayoutV3 | OmniDocBench | Fuente |
| :--- | :--- | :--- |
| `text` | `text_block` | [ref: PP-DocLayoutV3] / [ref: OmniDocBench] |
| `doc_title`, `paragraph_title` | `title` | [ref: PP-DocLayoutV3] — OmniDocBench solo tiene `title` |
| `display_formula` | `equation_isolated` | [ref: PP-DocLayoutV3] |
| `table` | `table` | [ref: PP-DocLayoutV3] |
| `image` | `figure` | [ref: PP-DocLayoutV3] |
| `figure_title` | `figure_caption` | **decisión propia** — es el rótulo de figura/tabla |
| `header` / `footer` | `header` / `footer` | [ref: PP-DocLayoutV3] |
| `number` | `page_number` | [ref: PP-DocLayoutV3] |
| `footnote` | `page_footnote` | [ref: PP-DocLayoutV3] |
| `reference`, `reference_content` | `reference` | **decisión propia** — ambas son la sección de bibliografía |

Sin destino (ignoradas): `abstract`, `algorithm`, `aside_text`, `chart`,
`content`, `footer_image`, `formula_number`, `header_image`, `inline_formula`,
`seal`, `vertical_text`, `vision_footnote`, y las que solo tienen cabida parcial
(`abstract`/`content` podrían ser `text_block`, pero no hay equivalencia sostenible
con evidencia ⇒ **pendiente**).

## 4. Regla de evaluación

La métrica es **mAP/recall@IoU 0.5 macro**, pero solo promedia sobre la
intersección de la GT con las categorías que el motor **puede emitir**:

```
GT evaluable = { categoría anotada  :  categoría ∈ vocabulario_del_motor }
```

- Una clase del modelo sin equivalencia ⇒ **no entra** en la predicción.
- Una categoría anotada que el motor no puede emitir ⇒ **se ignora** (fuera de la
  media), nunca un `0.0` espurio.
- Si el GT evaluable queda vacío ⇒ la métrica es **no evaluada** (`""`), no `0.0`.

En concreto: para los motores DocLayNet, `page_number` (presente en 7 de las 8
páginas del banco) y `reference` dejan de contar como fallo. `pyocrust_layout`
**no cambia** porque su vocabulario cubre todas las categorías de
`LAYOUT_MODEL_TO_GT`.

## 5. Código que aplica el mapa

- `common/datasets.py::layout_gt_classes(engine)` — devuelve el conjunto de
  categorías emitibles por familia de motor; un `engine` desconocido recibe el
  conjunto **completo** (el más amplio: `pp_doclayoutv3`), para no perder
  categorías por defecto.
- `features/layout/bank.py::score_layout` — acota el GT con esa función antes de
  `detection_map`.
- Autochequeos: `python benchmarks/common/datasets.py` y
  `python benchmarks/features/layout/bank.py --self-check`.

## 6. Antes / después (medido, n=8, CPU)

Sobre las **mismas predicciones**, cambiando solo la regla de evaluación
(`python benchmarks/features/layout/bank.py --limit 8` y sonda de doble
puntuación):

| Motor | mAP@0.5 antes | mAP@0.5 después | recall antes | recall después | categorías ignoradas |
| :--- | ---: | ---: | ---: | ---: | :--- |
| pyocrust_layout | 0.7641 | 0.7641 | 0.7945 | 0.7945 | — |
| docling_heron_101 | 0.5082 | **0.6577** | 0.5844 | 0.7507 | `page_number` |
| yolo26m | 0.2221 | **0.2974** | 0.2337 | 0.3127 | `page_number` |
| yolov10x | 0.1695 | **0.2260** | 0.1869 | 0.2493 | `page_number` |
| yolov10b | 0.1089 | **0.1452** | 0.1096 | 0.1461 | `page_number` |

`REPORT.md` de la feature refleja ya el **después** (run
`benchmarks/results/layout/2026-11-02_17-21-23`).

## 7. Qué **no** explica el mapeo (honestidad con datos)

El mapeo sube a los motores DocLayNet un 24–33 % relativo, pero **no** cierra la
brecha hasta el ~0.92 publicado. Con datos, la brecha restante es por:

1. **Distribución del banco.** Las 8 páginas que puntuamos son las *ricas en
   fórmula/tabla* que selecciona `common.datasets._odb_rich_first` (pensado para
   los bancos de estructura y fórmula): de las 8, todas tienen `equation_isolated`
   y suman **55 fórmulas** anotadas frente a 73 `text_block`. DocLayNet evalúa
   sobre 1 025² px de *seis* categorías documentales; aquí medimos páginas
   académicas densas en matemáticas.
2. **Umbral de confianza.** A `conf=0.5` los YOLO emiten muy pocas cajas. Medido
   sobre una página densa (`page-14cd673f`, GT=19 bloques): `yolov10x` emite
   **1** caja a `conf=0.5`, 5 a `conf=0.25` y 10 a `conf=0.10`. El `0.0` de esa
   página no es clasificación errónea: es infra-detección.
3. **Granularidad dentro de una clase mapeada.** DocLayNet tiene dos clases de
   encabezado (`Title`, `Section-header`) que OmniDocBench funde en `title`
   (§3.1, *decisión propia*): una caja puede ser acierto de caja y "clase
   distinta" a la vez. No se ha corregido porque no hay una equivalencia
   defendible con evidencia ⇒ queda documentado, no "arreglado".

## 8. Coherencia `SUMMARY` vs `QUALITY_VS_TIME`

Existe una incoherencia de **etiqueta de dataset**, no de números:

- `benchmarks/reports/SUMMARY.md` titula el bloque `layout — OmniDocBench` y avisa que la
  `referencia` es DocLayNet.
- `benchmarks/reports/QUALITY_VS_TIME.md` titula el mismo bloque `layout — DocLayNet`.

Ambas tablas miden **nuestras** alternativas sobre `omnidocbench_layout` (el
`dataset` del `summary.json` de la run es `omnidocbench_layout`); la única
columna DocLayNet son las filas de `referencia` (números publicados, no
comparables 1:1). El título de `QUALITY_VS_TIME.md` hereda la etiqueta del
panel `summary.py` y está **desalineado** con el de `SUMMARY.md`.

Datos que lo fijan:

- `summary.json` (run 17-21-23): `"dataset": "omnidocbench_layout"`.
- `REPORT.md` de la feature: `dataset: omnidocbench_layout`.
- La GT son categorías `category_type` de OmniDocBench (`text_block`,
  `equation_isolated`, …), no las 11 clases de DocLayNet.

El arreglo vive en `features/summary.py` / `features/quality_vs_time.py` (que
etiquetan el panel). Esos ficheros los está tocando la tarjeta en curso
`t_b469fff0` [VENV], así que **este card no los modifica**: se deja constancia
aquí y se señala el desalineo para que la tarjeta que regenera `SUMMARY.md` /
`QUALITY_VS_TIME.md` lo aplique. Ambos generadores **derivan** las cifras de
`reports/<feature>/REPORT.md` (sección `## Comparativa`), que ya lleva el
*después*: al regenerarlos, las filas de `layout` de los dos documentos salen ya
corregidas y con la misma etiqueta de dataset.

## 9. Estado del repo y reproducibilidad

Los adaptadores de las alternativas **YOLO** (`_yolo_layout_backend` y las
entradas `yolov10x/yolov10b/yolo26m` de `PROVIDERS`, en `common/runner.py`) están
**sin commitear** en el árbol: los está integrando la tarjeta en curso
`t_b469fff0` [VENV] (que instala `ultralytics`). Este card **no los toca ni los
commitea** (punto caliente compartido): `score_layout` y el mapa son ortogonales a
esos adaptadores. Por eso el `REPORT.md` aquí commiteado mide 5 motores, pero un
`git checkout` de este commit solo puede reproducir las filas de
`pyocrust_layout` y `docling_heron_101` (el `deformable_detr` sale `skipped`); las
tres filas YOLO quedan reproducibles cuando la tarjeta [VENV] / [COMMIT] aterrice
su adaptador.

## 10. Otras features: ¿coincide la granularidad del GT?

- **`table`.** GT = el `html` anotado del bloque `table` de OmniDocBench; la
  alternativa (TATR) emite una **rejilla** que se serializa a la misma gramática
  `<tr>/<td>` (`runner._tatr_grid_html`) y se compara con `table_teds`, que
  **ignora atributos y texto de celda**. Ambas partes quedan reducidas a la misma
  granularidad ⇒ **no se necesita mapa de clases**. (Deuda conocida: TATR
  `row_labels={table row, table column header}`,
  `col_labels={table column, table projected row header}`; `rowspan`/`colspan`
  no cambian TEDS-S.)
- **`full_page`.** GT = Markdown reconstruido de los bloques anotados; métrica
  `markdown_f1` (LCS de tokens). No hay taxonomía de clases en juego ⇒ **no
  procede mapa**.
- **`formula`.** GT = LaTeX por bloque `equation_isolated`; métricas sobre la
  forma canónica de LaTeX. No hay clase de layout en juego ⇒ **no procede mapa**.

## 11. Pendientes (no inventados)

- `list-item` (DocLayNet) ↔ `list_group` (OmniDocBench): sin equivalencia
  sostenible con evidencia.
- `abstract` / `content` (PP-DocLayoutV3) → `text_block`: plausible, sin
  evidencia ⇒ **pendiente**.
- Mapeo de `Code` (heron-101) → `code_txt` (OmniDocBench): existen ambas clases,
  pero `code_txt` no está en el conjunto evaluado de la métrica macro; queda
  fuera por ahora.
