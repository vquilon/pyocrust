# Feature report: `full_page`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --dataset omnidocbench_full_page_en --limit 6 --warmup 1 --device cpu --variant vl --backends pyocrust_vl --output-dir benchmarks/results`
- **dataset**: `omnidocbench_full_page_en` · **n** (per engine): `6` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/full_page/vl/2026-11-15_17-04-26` · **date**: `2026-11-15_17-04-26`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Markdown F1 ↑ | Block F1 ↑ | layout mAP ↑ | TEDS table ↑ | LaTeX sim ↑ | titles recall ↑ | titles prec. ↑ | titles text F1 ↑ | titles sequence τ ↑ | reading order τ ↑ | figures recall ↑ | figures prec. ↑ | captions recall ↑ | captions prec. ↑ | fig↔caption assoc. ↑ | captions text F1 ↑ | CER ↓ | ms/page ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pyocrust (vl) | 6 | 0.534 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2.590 | 141693 |

> Bold values mark the best result for each metric among the **measured** engines in `full_page`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | N/A | 0.559 | N/A | 30716 | cuda |
| LightOnOCR-2-1B (1B) | N/A | 0.588 | N/A | 44737 | cuda |
| LightOnOCR-3 (0.8B) | N/A | 0.625 | N/A | 320707 | cuda |
| LightOnOCR-3 (4B) | N/A | 0.590 | N/A | 72249 | cuda |
| PaddleOCR-VL (0.9B) | N/A | 0.597 | N/A | 60907 | cuda |
| pyocrust (vl) | 0.534 | N/A | 141693 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `Block F1` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la table esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS table` = estructura HTML de table (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de formula. Una table **mal estructurada con el texto correcto** baja `TEDS table` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`Block F1` sólo ven el **texto** y el **tipo** de la figura, never su posición ni si la caption quedó ligada: una page con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la page/el engine no aporta GT o no emite esa modalidad (p. ej. un engine sin fórmulas separadas), never un `0.0`.

## Per stratum (`data_source × layout`)

> Markdown F1 **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 1 · strata covered: 4. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×other_layout` (2), `PPT2PDF×single_column` (1), `academic_literature×1andmore_column` (2).

### Markdown F1 per stratum

| Engine (variant) | PPT2PDF×1andmore_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column |
| :--- | ---: | ---: | ---: | ---: |
| pyocrust (vl) | 0.721 | 0.674 | 0.077 | 0.528 |

## Per page type (`digital` / `scanned` / `handwritten`)

> Markdown F1 **per engine and page type**. The page type is derived from OmniDocBench's `page_info.page_attribute`: `handwritten` = `handwriting` in `special_issue` or `data_source=note`; `scanned` = `fuzzy_scan` in `special_issue` or `data_source=historical_document`; `digital` = everything else. OmniDocBench does **not** annotate an explicit acquisition type: the classification is a declared derivation, not an original label. Engines measured: 1. `N/A` = no measured pages of that page type (never `0.0`); `—` = the engine has no measurement on those pages.

> **Pages per page type in the sample**: `digital` (6), `scanned` (0), `handwritten` (0).

> **No data** for `scanned`, `handwritten` in this feature's sample (`N/A` column): the sampling did not include pages of that page type, so the row is not invented.

| Engine (variant) | digital | scanned | handwritten |
| :--- | ---: | ---: | ---: |
| pyocrust (vl) | 0.534 (n=6) | N/A | N/A |

