# Feature report: `table`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/table/bank.py --limit 20 --device cpu --backends pyocrust_table,tatr`
- **dataset**: `omnidocbench_table` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/table/2026-11-06_23-57-06` · **date**: `2026-11-06_23-57-06`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | Structural TEDS ↑ | ms/table ↓ |
| :--- | ---: | ---: | ---: |
| slanet_plus (default) | 20 | **0.854** | 749 |
| table-transformer-structure-recognition (default) | 20 | 0.699 | **140** |

> Bold values mark the best result for each metric among the **measured** engines in `table`. `N/A` = not evaluated (no ground truth for that column), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| slanet_plus (default) | 0.854 | 0.854 | 749 | 668 | directml |
| table-transformer-structure-recognition (default) | 0.699 | N/A | 140 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

