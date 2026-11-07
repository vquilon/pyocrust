# Feature report: `formula`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/formula/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_formula` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/formula/2026-11-07_14-47-19` · **date**: `2026-11-07_14-47-19`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparison (mean by engine)

| Engine (variant) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.243 | 0.505 | N/A | **103** |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.694** | **0.839** | N/A | 4453 |
| pix2tex (default) | 20 | 0.000 | 0.460 | 0.669 | N/A | 5971 |
| pp-formulanet-s (direct) | 20 | 0.000 | 0.497 | 0.622 | N/A | 842 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | 0.196 | 0.295 | N/A | 1512 |

> Bold values mark the best result for each metric among the **measured** engines in `formula`. `N/A` = not evaluated (no ground truth for that column), never an invented `0.0`.

## Skipped — not counted as executed

- `img2latex` — pip install img2latex
- `nougat` — pip install nougat-ocr
- `pix2text` — pip install pix2text (not forced: degrades transformers/huggingface_hub and changes opencv-python-headless→opencv-python)
- `texify` — pip install texify
- `texteller` — pip install texteller
- `unimernet` — pip install unimernet (github.com/opendatalab/UniMERNet)

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.243 | 0.243 | 103 | 4182 | directml |
| paddle_latex_ocr (default) | 0.694 | 0.694 | 4453 | 1187 | cuda |
| pix2tex (default) | 0.460 | N/A | 5971 | N/A | n/a (does not run on GPU) |
| pp-formulanet-s (direct) | 0.497 | 0.497 | 842 | 2514 | directml |
| pp_structurev3 (pp-formulanet-s) | 0.196 | 0.196 | 1512 | 4470 | directml |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

