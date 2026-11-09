# Feature report: `table`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `omnidocbench_table` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/table/2026-11-09_11-00-34` · **date**: `2026-11-09_11-00-34`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparison (mean by engine)

| Engine (variant) | n | Structural TEDS ↑ | ms/table ↓ |
| :--- | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **87** |
| pp_structurev3 (default) | 20 | 0.608 | 3245 |
| slanet_plus (default) | 20 | 0.780 | 848 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | 198 |
| tableformer (docling) | 20 | 0.807 | 35699 |

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
| SLANet_plus (paddleocr) | 0.828 | N/A | 87 | N/A | n/a (does not run on GPU) |
| pp_structurev3 (default) | 0.608 | 0.608 | 3245 | 5429 | directml |
| slanet_plus (default) | 0.780 | 0.780 | 848 | 1023 | directml |
| table-transformer-structure-recognition (default) | 0.698 | N/A | 198 | N/A | n/a (does not run on GPU) |
| tableformer (docling) | 0.807 | N/A | 35699 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

