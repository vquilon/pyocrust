# Feature report: `formula`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/formula/bank.py --variant vl --limit 10 --device gpu --output-dir results/_gpu --backends glm_ocr,paddleocr_vl,lightonocr,lightonocr3_08b,lightonocr3_4b`
- **dataset**: `omnidocbench_formula` · **n** (per engine): `10` · **warmup**: `1` · **repeats**: `1` · **device**: `gpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/_gpu/formula/vl/2026-11-15_19-06-25` · **date**: `2026-11-15_19-06-25`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 10 | 0.000 | **0.748** | **0.881** | N/A | 18719 |
| LightOnOCR-2-1B (1B) | 10 | 0.000 | 0.597 | 0.777 | N/A | 20186 |
| LightOnOCR-3 (0.8B) | 10 | 0.000 | 0.550 | 0.749 | N/A | 24073 |
| LightOnOCR-3 (4B) | 10 | 0.000 | 0.612 | 0.780 | N/A | 30950 |
| PaddleOCR-VL (0.9B) | 10 | 0.000 | 0.614 | 0.843 | N/A | **17524** |

> Bold values mark the best result for each metric among the **measured** engines in `formula`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `GLM-OCR (0.9B)` — an **independent** model (different project/checkpoint)
- `LightOnOCR-2-1B (1B)` — an **independent** model (different project/checkpoint)
- `LightOnOCR-3 (0.8B)` — an **independent** model (different project/checkpoint)
- `LightOnOCR-3 (4B)` — an **independent** model (different project/checkpoint)
- `PaddleOCR-VL (0.9B)` — an **independent** model (different project/checkpoint)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=gpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | 0.748 | 0.748 | 18719 | 18719 | n/a |
| LightOnOCR-2-1B (1B) | 0.597 | 0.597 | 20186 | 20186 | n/a |
| LightOnOCR-3 (0.8B) | 0.550 | 0.550 | 24073 | 24073 | n/a |
| LightOnOCR-3 (4B) | 0.612 | 0.612 | 30950 | 30950 | n/a |
| PaddleOCR-VL (0.9B) | 0.614 | 0.614 | 17524 | 17524 | n/a |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> LaTeX sim **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 5 · strata covered: 5. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×other_layout` (3), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (2), `academic_literature×other_layout` (1).

### LaTeX sim per stratum

| Engine (variant) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.590 | 0.814 | 0.705 | 0.860 | 0.956 |
| LightOnOCR-2-1B (1B) | 0.517 | 0.823 | 0.544 | 0.526 | 0.637 |
| LightOnOCR-3 (0.8B) | 0.456 | 0.516 | 0.508 | 0.625 | 0.835 |
| LightOnOCR-3 (4B) | 0.481 | 0.738 | 0.598 | 0.643 | 0.725 |
| PaddleOCR-VL (0.9B) | 0.518 | 0.620 | 0.681 | 0.626 | 0.736 |

## Per page type (`digital` / `scanned` / `handwritten`)

> LaTeX sim **per engine and page type**. The page type is derived from OmniDocBench's `page_info.page_attribute`: `handwritten` = `handwriting` in `special_issue` or `data_source=note`; `scanned` = `fuzzy_scan` in `special_issue` or `data_source=historical_document`; `digital` = everything else. OmniDocBench does **not** annotate an explicit acquisition type: the classification is a declared derivation, not an original label. Engines measured: 5. `N/A` = no measured pages of that page type (never `0.0`); `—` = the engine has no measurement on those pages.

> **Pages per page type in the sample**: `digital` (10), `scanned` (0), `handwritten` (0).

> **No data** for `scanned`, `handwritten` in this feature's sample (`N/A` column): the sampling did not include pages of that page type, so the row is not invented.

| Engine (variant) | digital | scanned | handwritten |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.748 (n=10) | N/A | N/A |
| LightOnOCR-2-1B (1B) | 0.597 (n=10) | N/A | N/A |
| LightOnOCR-3 (0.8B) | 0.550 (n=10) | N/A | N/A |
| LightOnOCR-3 (4B) | 0.612 (n=10) | N/A | N/A |
| PaddleOCR-VL (0.9B) | 0.614 (n=10) | N/A | N/A |

