# Feature report: `table`

> **Why it wins or loses here:** model vs. engine vs. measurement — see [`ANALISIS_MOTOR_VS_MODELO.md`](../../ANALISIS_MOTOR_VS_MODELO.md).

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --limit 8 --device cpu`
- **dataset**: `omnidocbench_table` · **n** (per engine): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/table/2026-11-15_20-06-20` · **date**: `2026-11-15_20-06-20`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Structural TEDS ↑ | ms/table ↓ |
| :--- | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 8 | 0.882 | 1900 |
| SLANet_plus (paddleocr) | 8 | 0.889 | 247 |
| pp_structurev3 (default) | 8 | 0.753 | 1128 |
| slanet_plus (7.8M) | 8 | 0.868 | **52** |
| slanext_wired (367M) | 8 | **0.914** | 577 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | 718 |
| tableformer (docling) | 8 | 0.905 | 27457 |

> Bold values mark the best result for each metric among the **measured** engines in `table`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `SLANeXt_wired (paddleocr)` — **same weights, a different path** (the SAME PaddleOCR `.onnx` through another runtime — NOT a different model)
- `SLANet_plus (paddleocr)` — **same weights, a different path** (the SAME PaddleOCR `.onnx` through another runtime — NOT a different model)
- `table-transformer-structure-recognition (default)` — an **independent** model (different project/checkpoint)
- `tableformer (docling)` — an **independent** model (different project/checkpoint)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| SLANeXt_wired (paddleocr) | 0.882 | N/A | 1900 | N/A | n/a (does not run on GPU) |
| SLANet_plus (paddleocr) | 0.889 | 0.889 | 247 | 99 | cuda |
| pp_structurev3 (default) | 0.753 | 0.753 | 1128 | 2214 | cuda |
| slanet_plus (7.8M) | 0.868 | 0.868 | 52 | 484 | cuda |
| slanext_wired (367M) | 0.914 | 0.914 | 577 | 202 | cuda |
| table-transformer-structure-recognition (default) | 0.790 | 0.790 | 718 | 47 | cuda |
| tableformer (docling) | 0.905 | 0.905 | 27457 | 19140 | cuda |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> TEDS table **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 7 · strata covered: 6. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (2).

### Table TEDS per stratum

| Engine (variant) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 1.000 | 1.000 | 1.000 | 0.732 | 0.946 | 0.823 |
| SLANet_plus (paddleocr) | 1.000 | 1.000 | 1.000 | 0.757 | 0.934 | 0.833 |
| pp_structurev3 (default) | 1.000 | 0.980 | 0.407 | 0.560 | 0.934 | 0.791 |
| slanet_plus (7.8M) | 1.000 | 0.990 | 0.943 | 0.724 | 0.934 | 0.815 |
| slanext_wired (367M) | 1.000 | 1.000 | 1.000 | 0.668 | 0.997 | 0.990 |
| table-transformer-structure-recognition (default) | 1.000 | 0.889 | 0.857 | 0.628 | 0.791 | 0.762 |
| tableformer (docling) | 1.000 | 1.000 | 1.000 | 0.669 | 1.000 | 1.000 |

## Per page type (`digital` / `scanned` / `handwritten`)

> TEDS table **per engine and page type**. The page type is derived from OmniDocBench's `page_info.page_attribute`: `handwritten` = `handwriting` in `special_issue` or `data_source=note`; `scanned` = `fuzzy_scan` in `special_issue` or `data_source=historical_document`; `digital` = everything else. OmniDocBench does **not** annotate an explicit acquisition type: the classification is a declared derivation, not an original label. Engines measured: 7. `N/A` = no measured pages of that page type (never `0.0`); `—` = the engine has no measurement on those pages.

> **Pages per page type in the sample**: `digital` (8), `scanned` (0), `handwritten` (0).

> **No data** for `scanned`, `handwritten` in this feature's sample (`N/A` column): the sampling did not include pages of that page type, so the row is not invented.

| Engine (variant) | digital | scanned | handwritten |
| :--- | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 0.882 (n=8) | N/A | N/A |
| SLANet_plus (paddleocr) | 0.889 (n=8) | N/A | N/A |
| pp_structurev3 (default) | 0.753 (n=8) | N/A | N/A |
| slanet_plus (7.8M) | 0.868 (n=8) | N/A | N/A |
| slanext_wired (367M) | 0.914 (n=8) | N/A | N/A |
| table-transformer-structure-recognition (default) | 0.790 (n=8) | N/A | N/A |
| tableformer (docling) | 0.905 (n=8) | N/A | N/A |

