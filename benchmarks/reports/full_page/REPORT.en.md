# Feature report: `full_page`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/full_page/bank.py --limit 6 --device cpu --output-dir results`
- **dataset**: `omnidocbench_full_page` · **n** (per engine): `6` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/full_page/2026-11-09_14-28-38` · **date**: `2026-11-09_14-28-38`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 6 | **0.204** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **1.119** | 25723 |
| indra (math) | 6 | 0.029 | N/A | N/A | 0.276 | N/A | N/A | N/A | N/A | N/A | 0.190 | N/A | N/A | N/A | N/A | N/A | N/A | 3.102 | **607** |
| pp_structurev3 (default) | 6 | 0.083 | 0.524 | 0.561 | **0.678** | 0.255 | 0.944 | 1.000 | 0.536 | 0.857 | **0.764** | 0.167 | 0.333 | 0.875 | 1.000 | 0.000 | 0.417 | 5.737 | 5865 |

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
| docling-default (pipeline) | 0.204 | N/A | 25723 | N/A | n/a (does not run on GPU) |
| indra (math) | 0.029 | 0.029 | 607 | 4802 | directml |
| pp_structurev3 (default) | 0.083 | 0.085 | 5865 | 4754 | directml |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `Block F1` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la table esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS table` = estructura HTML de table (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de formula. Una table **mal estructurada con el texto correcto** baja `TEDS table` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`Block F1` sólo ven el **texto** y el **tipo** de la figura, never su posición ni si la caption quedó ligada: una page con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la page/el engine no aporta GT o no emite esa modalidad (p. ej. un engine sin fórmulas separadas), never un `0.0`.

## Per stratum (`data_source × layout`)

> Markdown F1 **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 3 · strata covered: 3. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (2), `PPT2PDF×other_layout` (3).

### Markdown F1 per stratum

| Engine (variant) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 0.438 | 0.188 | 0.138 |
| indra (math) | 0.025 | 0.028 | 0.031 |
| pp_structurev3 (default) | 0.115 | 0.000 | 0.127 |

## Title coverage and hierarchy (not measurable)

> The **titles/index** metric is only evaluated on pages the annotation marks with `category_type=title`; elsewhere it is `N/A` and does **not** enter the mean (it is not diluted into a global average). The `OmniDocBench` dataset (v1.6, 1651 pages) annotates `title` on **1179** pages (**71.4 %**); the rest have no title ground truth.

> **Title hierarchy (h1/h2/h3) is NOT measurable with this annotation**: the `attribute` field is **always empty** in OmniDocBench, there is no annotated hierarchy level. This metric therefore measures **presence, position, text and sequence**, and does **not** emit a `0.0` for depth nor fake a nested index: where the dataset does not annotate, the report says so.

| Engine (variant) | pages measured | pages with title GT | title coverage |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 6 | 4 | 67% |
| indra (math) | 6 | 4 | 67% |
| pp_structurev3 (default) | 6 | 4 | 67% |

## Figure coverage and the non-emittable (masks)

> The **figures/captions** metric is only evaluated on pages the annotation marks with `category_type=figure`; elsewhere it is `N/A` and does **not** enter the mean (it is not diluted into a global average). The `OmniDocBench` dataset (v1.6, 1651 pages) annotates `figure` on **613** pages (**37.1 %**; 1385 `figure` instances in total); the rest have no figure ground truth.

> **Las máscaras (`*_mask`) NO son emitibles por el pipeline** y por eso **no se puntúan**: `chart_mask`, `table_mask`, `algorithm_mask`, `organic_chemical_formula_mask`, `text_mask`, `need_mask`, `abandon`, `unknown_mask` se **ignoran** al puntuar (quedan fuera del GT de bloques, ver `_odb_content_blocks`); **never** cuentan como `0.0` por no emitirlas, igual que `page_number`/`reference` en `layout`. Un engine que no las emite no se penaliza.

> La **asociación figura↔caption** (`asoc. fig↔caption`) exige que, además de detectar la figura, se localice su caption compañera: una page con las figuras detectadas pero **sin** sus captions baja esa columna aunque su `figuras recall` sea `1.0`, así que no puede puntuar igual que una completa.

| Engine (variant) | pages measured | pages with figure GT | figure coverage |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 6 | 3 | 50% |
| indra (math) | 6 | 3 | 50% |
| pp_structurev3 (default) | 6 | 3 | 50% |

