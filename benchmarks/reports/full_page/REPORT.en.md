# Feature report: `full_page`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/full_page/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `omnidocbench_full_page` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/full_page/2026-11-09_12-43-20` · **date**: `2026-11-09_12-43-20`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparison (mean by engine)

| Engine (variant) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | **0.354** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.518** | 33257 |
| indra (math) | 20 | 0.265 | N/A | N/A | 0.361 | N/A | N/A | N/A | N/A | N/A | **0.747** | N/A | N/A | N/A | N/A | N/A | N/A | 1.231 | **2006** |
| pp_structurev3 (default) | 20 | 0.270 | 0.700 | 0.677 | **0.674** | 0.351 | 0.702 | 0.652 | 0.649 | 0.750 | 0.661 | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.500 | 2.190 | 11054 |

> Bold values mark the best result for each metric among the **measured** engines in `full_page`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- `pdf_extract_kit` — pip install pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; weights in the HF cache, adapter pending)

## Provenance of the alternatives

- `docling-default (pipeline)` — an **independent** model (different project/checkpoint)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| docling-default (pipeline) | 0.354 | N/A | 33257 | N/A | n/a (does not run on GPU) |
| indra (math) | 0.265 | 0.265 | 2006 | 8901 | directml |
| pp_structurev3 (default) | 0.270 | 0.267 | 11054 | 14053 | directml |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `Block F1` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la table esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS table` = estructura HTML de table (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de formula. Una table **mal estructurada con el texto correcto** baja `TEDS table` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`Block F1` sólo ven el **texto** y el **tipo** de la figura, never su posición ni si la caption quedó ligada: una page con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la page/el engine no aporta GT o no emite esa modalidad (p. ej. un engine sin fórmulas separadas), never un `0.0`.

## Title coverage and hierarchy (not measurable)

> The **titles/index** metric is only evaluated on pages the annotation marks with `category_type=title`; elsewhere it is `N/A` and does **not** enter the mean (it is not diluted into a global average). The `OmniDocBench` dataset (v1.6, 1651 pages) annotates `title` on **1179** pages (**71.4 %**); the rest have no title ground truth.

> **Title hierarchy (h1/h2/h3) is NOT measurable with this annotation**: the `attribute` field is **always empty** in OmniDocBench, there is no annotated hierarchy level. This metric therefore measures **presence, position, text and sequence**, and does **not** emit a `0.0` for depth nor fake a nested index: where the dataset does not annotate, the report says so.

| Engine (variant) | pages measured | pages with title GT | title coverage |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | 14 | 70% |
| indra (math) | 20 | 14 | 70% |
| pp_structurev3 (default) | 20 | 14 | 70% |

## Figure coverage and the non-emittable (masks)

> The **figures/captions** metric is only evaluated on pages the annotation marks with `category_type=figure`; elsewhere it is `N/A` and does **not** enter the mean (it is not diluted into a global average). The `OmniDocBench` dataset (v1.6, 1651 pages) annotates `figure` on **613** pages (**37.1 %**; 1385 `figure` instances in total); the rest have no figure ground truth.

> **Las máscaras (`*_mask`) NO son emitibles por el pipeline** y por eso **no se puntúan**: `chart_mask`, `table_mask`, `algorithm_mask`, `organic_chemical_formula_mask`, `text_mask`, `need_mask`, `abandon`, `unknown_mask` se **ignoran** al puntuar (quedan fuera del GT de bloques, ver `_odb_content_blocks`); **never** cuentan como `0.0` por no emitirlas, igual que `page_number`/`reference` en `layout`. Un engine que no las emite no se penaliza.

> La **asociación figura↔caption** (`asoc. fig↔caption`) exige que, además de detectar la figura, se localice su caption compañera: una page con las figuras detectadas pero **sin** sus captions baja esa columna aunque su `figuras recall` sea `1.0`, así que no puede puntuar igual que una completa.

| Engine (variant) | pages measured | pages with figure GT | figure coverage |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | 4 | 20% |
| indra (math) | 20 | 4 | 20% |
| pp_structurev3 (default) | 20 | 4 | 20% |

