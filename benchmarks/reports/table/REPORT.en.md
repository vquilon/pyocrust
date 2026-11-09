# Feature report: `table`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --limit 8 --device cpu --output-dir results`
- **dataset**: `omnidocbench_table` · **n** (per engine): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/table/2026-11-09_14-22-58` · **date**: `2026-11-09_14-22-58`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Structural TEDS ↑ | ms/table ↓ |
| :--- | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 8 | 0.889 | **72** |
| pp_structurev3 (default) | 8 | 0.753 | 3530 |
| slanet_plus (default) | 8 | **0.914** | 1103 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | 131 |
| tableformer (docling) | 8 | 0.905 | 28609 |

> Bold values mark the best result for each metric among the **measured** engines in `table`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `SLANet_plus (paddleocr)` — an **independent** model (different project/checkpoint)
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
| SLANet_plus (paddleocr) | 0.889 | N/A | 72 | N/A | n/a (does not run on GPU) |
| pp_structurev3 (default) | 0.753 | 0.753 | 3530 | 3370 | directml |
| slanet_plus (default) | 0.914 | 0.914 | 1103 | 632 | directml |
| table-transformer-structure-recognition (default) | 0.790 | N/A | 131 | N/A | n/a (does not run on GPU) |
| tableformer (docling) | 0.905 | N/A | 28609 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> TEDS table **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 5 · strata covered: 6. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (2).

### Table TEDS per stratum

| Engine (variant) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 1.000 | 1.000 | 1.000 | 0.757 | 0.934 | 0.833 |
| pp_structurev3 (default) | 1.000 | 0.980 | 0.407 | 0.560 | 0.934 | 0.791 |
| slanet_plus (default) | 1.000 | 1.000 | 1.000 | 0.668 | 0.997 | 0.990 |
| table-transformer-structure-recognition (default) | 1.000 | 0.889 | 0.857 | 0.628 | 0.791 | 0.762 |
| tableformer (docling) | 1.000 | 1.000 | 1.000 | 0.669 | 1.000 | 1.000 |

