# Feature report: `table`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --variant vl --limit 8 --device gpu --output-dir results/_gpu --backends glm_ocr,paddleocr_vl,lightonocr,lightonocr3_08b,lightonocr3_4b`
- **dataset**: `omnidocbench_table` · **n** (per engine): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `gpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/_gpu/table/vl/2026-11-15_18-13-46` · **date**: `2026-11-15_18-13-46`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Structural TEDS ↑ | ms/table ↓ |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 8 | 0.919 | **34191** |
| LightOnOCR-2-1B (1B) | 8 | 0.858 | 58834 |
| LightOnOCR-3 (0.8B) | 8 | 0.926 | 162056 |
| LightOnOCR-3 (4B) | 8 | 0.847 | 76940 |
| PaddleOCR-VL (0.9B) | 8 | **0.933** | 35839 |

> Bold values mark the best result for each metric among the **measured** engines in `table`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

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

| Engine (variant) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | 0.919 | 0.919 | 34191 | 34191 | n/a |
| LightOnOCR-2-1B (1B) | 0.858 | 0.858 | 58834 | 58834 | n/a |
| LightOnOCR-3 (0.8B) | 0.926 | 0.926 | 162056 | 162056 | n/a |
| LightOnOCR-3 (4B) | 0.847 | 0.847 | 76940 | 76940 | n/a |
| PaddleOCR-VL (0.9B) | 0.933 | 0.933 | 35839 | 35839 | n/a |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

## Per stratum (`data_source × layout`)

> TEDS table **per engine and stratum** of the page (stratified sample, `page_info.page_attribute`). Engines measured: 5 · strata covered: 6. `—` = this engine has no measurement in that stratum.

> **Strata (pages in the sample)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (2).

### Table TEDS per stratum

| Engine (variant) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | — | 1.000 | 1.000 | 0.757 | 1.000 | 1.000 |
| LightOnOCR-2-1B (1B) | 0.985 | 0.990 | 0.986 | 0.750 | 0.567 | 0.980 |
| LightOnOCR-3 (0.8B) | 1.000 | 1.000 | 1.000 | 0.750 | 0.973 | 0.967 |
| LightOnOCR-3 (4B) | 0.985 | 1.000 | 1.000 | 0.674 | 0.514 | 0.967 |
| PaddleOCR-VL (0.9B) | 1.000 | 0.979 | 1.000 | 0.833 | 0.851 | — |

## Per page type (`digital` / `scanned` / `handwritten`)

> TEDS table **per engine and page type**. The page type is derived from OmniDocBench's `page_info.page_attribute`: `handwritten` = `handwriting` in `special_issue` or `data_source=note`; `scanned` = `fuzzy_scan` in `special_issue` or `data_source=historical_document`; `digital` = everything else. OmniDocBench does **not** annotate an explicit acquisition type: the classification is a declared derivation, not an original label. Engines measured: 5. `N/A` = no measured pages of that page type (never `0.0`); `—` = the engine has no measurement on those pages.

> **Pages per page type in the sample**: `digital` (8), `scanned` (0), `handwritten` (0).

> **No data** for `scanned`, `handwritten` in this feature's sample (`N/A` column): the sampling did not include pages of that page type, so the row is not invented.

| Engine (variant) | digital | scanned | handwritten |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.919 (n=8) | N/A | N/A |
| LightOnOCR-2-1B (1B) | 0.858 (n=8) | N/A | N/A |
| LightOnOCR-3 (0.8B) | 0.926 (n=8) | N/A | N/A |
| LightOnOCR-3 (4B) | 0.847 (n=8) | N/A | N/A |
| PaddleOCR-VL (0.9B) | 0.933 (n=8) | N/A | N/A |

