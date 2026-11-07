# Feature report: `full_page`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_full_page` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/full_page/2026-11-06_23-31-43` · **date**: `2026-11-06_23-31-43`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | Markdown F1 ↑ | Block F1 ↑ | CER ↓ | ms/page ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | **0.231** | 0.000 | **0.996** | **1547** |
| pp_structurev3 (default) | 20 | 0.211 | **0.849** | 3.743 | 10033 |

> Bold values mark the best result for each metric among the **measured** engines in `full_page`. `N/A` = not evaluated (no ground truth for that column), never an invented `0.0`.

## Skipped — not counted as executed

- `pdf_extract_kit` — pip install pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; weights in the HF cache, adapter pending)

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.231 | 0.242 | 1547 | 10503 | directml |
| pp_structurev3 (default) | 0.211 | 0.210 | 10033 | 17198 | directml |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

