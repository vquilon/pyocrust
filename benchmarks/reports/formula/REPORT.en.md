# Feature report: `formula`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_formula` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/formula/2026-11-09_10-37-15` · **date**: `2026-11-09_10-37-15`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparison (mean by engine)

| Engine (variant) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.211 | 0.437 | N/A | **146** |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.715** | **0.829** | N/A | 3734 |
| pix2tex (default) | 20 | 0.000 | 0.587 | 0.757 | N/A | 5764 |
| pp-formulanet-s (direct) | 20 | 0.000 | 0.576 | 0.701 | N/A | 854 |
| pp_structurev3 (default) | 20 | 0.000 | 0.399 | 0.560 | N/A | 2193 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | 0.607 | 0.746 | N/A | 2247 |
| unimernet (tiny) | 20 | 0.000 | 0.238 | 0.376 | N/A | 18685 |

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
| indra (math) | 0.211 | 0.211 | 146 | 2813 | directml |
| paddle_latex_ocr (default) | 0.715 | 0.715 | 3734 | 1016 | cuda |
| pix2tex (default) | 0.587 | N/A | 5764 | N/A | n/a (does not run on GPU) |
| pp-formulanet-s (direct) | 0.576 | 0.576 | 854 | 1903 | directml |
| pp_structurev3 (default) | 0.399 | 0.400 | 2193 | 2781 | directml |
| pp_structurev3 (pp-formulanet-s) | 0.607 | 0.607 | 2247 | 3485 | directml |
| unimernet (tiny) | 0.238 | N/A | 18685 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> LaTeX sim **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 7 · strata covered: 12. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×other_layout` (2), `PPT2PDF×single_column` (1), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (1), `academic_literature×single_column` (3), `book×other_layout` (3), `book×single_column` (2), `colorful_textbook×double_column` (1), `colorful_textbook×other_layout` (1), `exam_paper×double_column` (2), `exam_paper×other_layout` (1), `note×single_column` (1).

### LaTeX sim per stratum

| Engine (variant) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×single_column | book×other_layout | book×single_column | colorful_textbook×double_column | colorful_textbook×other_layout | exam_paper×double_column | exam_paper×other_layout | note×single_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 0.169 | 0.262 | 0.249 | — | 0.377 | 0.167 | 0.288 | 0.288 | 0.054 | 0.110 | 0.070 | 0.185 |
| paddle_latex_ocr (default) | 0.748 | 0.684 | 0.714 | 0.835 | 0.764 | 0.710 | 0.721 | 0.514 | 0.168 | 0.843 | 1.000 | 0.632 |
| pix2tex (default) | 0.723 | 0.643 | 0.484 | 0.720 | 0.638 | 0.516 | 0.677 | 0.810 | 0.314 | 0.791 | 0.233 | 0.207 |
| pp-formulanet-s (direct) | 0.533 | 0.684 | 0.376 | 0.667 | 0.696 | 0.587 | 0.478 | 0.545 | 0.206 | 0.653 | 0.605 | 0.889 |
| pp_structurev3 (default) | 0.279 | 0.410 | 0.352 | 0.667 | 0.615 | 0.514 | 0.350 | 0.308 | 0.149 | 0.486 | 0.093 | 0.259 |
| pp_structurev3 (pp-formulanet-s) | 0.210 | 0.410 | 0.639 | 0.667 | 0.798 | 0.690 | 0.492 | — | — | 0.870 | — | — |
| unimernet (tiny) | 0.137 | 0.328 | 0.247 | 0.432 | 0.262 | 0.275 | 0.218 | 0.187 | 0.235 | 0.245 | 0.161 | 0.105 |

