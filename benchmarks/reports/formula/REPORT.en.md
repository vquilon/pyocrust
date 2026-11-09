# Feature report: `formula`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/formula/bank.py --limit 10 --device cpu --output-dir results`
- **dataset**: `omnidocbench_formula` · **n** (per engine): `10` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/formula/2026-11-09_14-13-57` · **date**: `2026-11-09_14-13-57`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 10 | 0.000 | 0.326 | 0.575 | N/A | **141** |
| paddle_latex_ocr (default) | 10 | 0.000 | **0.653** | **0.799** | N/A | 16326 |
| pix2tex (default) | 10 | 0.000 | 0.552 | 0.777 | N/A | 5500 |
| pp-formulanet-s (direct) | 10 | 0.000 | 0.499 | 0.652 | N/A | 998 |
| pp_structurev3 (default) | 10 | 0.000 | 0.398 | 0.613 | N/A | 2774 |
| pp_structurev3 (pp-formulanet-s) | 10 | 0.000 | 0.497 | 0.708 | N/A | 2474 |
| unimernet (tiny) | 10 | 0.000 | 0.260 | 0.385 | N/A | 17493 |

> Bold values mark the best result for each metric among the **measured** engines in `formula`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `unimernet (tiny)` — an **independent** model (different project/checkpoint)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.326 | 0.326 | 141 | 808 | cuda |
| paddle_latex_ocr (default) | 0.653 | 0.653 | 16326 | 4191 | cuda |
| pix2tex (default) | 0.552 | N/A | 5500 | N/A | n/a (does not run on GPU) |
| pp-formulanet-s (direct) | 0.499 | 0.499 | 998 | 1603 | cuda |
| pp_structurev3 (default) | 0.398 | 0.398 | 2774 | 2553 | cuda |
| pp_structurev3 (pp-formulanet-s) | 0.497 | 0.497 | 2474 | 2221 | cuda |
| unimernet (tiny) | 0.260 | N/A | 17493 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> LaTeX sim **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 7 · strata covered: 5. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×other_layout` (3), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (2), `academic_literature×other_layout` (1).

### LaTeX sim per stratum

| Engine (variant) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 0.197 | 0.243 | 0.249 | 0.366 | 0.989 |
| paddle_latex_ocr (default) | 0.401 | 0.700 | 0.714 | 0.838 | 0.824 |
| pix2tex (default) | 0.449 | 0.397 | 0.525 | 0.779 | 0.777 |
| pp-formulanet-s (direct) | 0.382 | 0.447 | 0.376 | 0.764 | 0.670 |
| pp_structurev3 (default) | 0.300 | 0.354 | 0.352 | 0.764 | 0.143 |
| pp_structurev3 (pp-formulanet-s) | 0.300 | 0.410 | 0.639 | 0.764 | — |
| unimernet (tiny) | 0.218 | 0.233 | 0.247 | 0.338 | 0.305 |

