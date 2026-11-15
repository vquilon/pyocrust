# Feature report: `text`

> **Why it wins or loses here:** model vs. engine vs. measurement — see [`ANALISIS_MOTOR_VS_MODELO.md`](../../ANALISIS_MOTOR_VS_MODELO.md).

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/text/bank.py --limit 20 --device cpu`
- **dataset**: `funsd` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/text/2026-11-15_20-11-47` · **date**: `2026-11-15_20-11-47`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparison (mean by engine)

| Engine (variant) | n | Word F1 ↑ | Ordered WER ↓ | CER ↓ | WER ↓ | box recall ↑ | Mean IoU ↑ | ms/img ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-OCRv6 (medium) | 20 | 0.796 | 0.266 | 0.473 | 0.644 | 0.039 | 0.115 | 19811 |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | 3662 |
| pp_ocrv6 (medium) | 20 | **0.800** | **0.260** | **0.472** | **0.643** | 0.042 | 0.116 | 2138 |
| pp_ocrv6 (small) | 20 | 0.784 | 0.280 | 0.472 | 0.650 | 0.042 | 0.117 | 823 |
| pp_ocrv6 (tiny) | 20 | 0.717 | 0.360 | 0.483 | 0.675 | 0.047 | 0.120 | **318** |
| rapidocr (default) | 20 | 0.585 | 0.512 | 0.476 | 0.701 | 0.037 | 0.108 | 4807 |

> Bold values mark the best result for each metric among the **measured** engines in `text`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- `tesseract` — pip install pytesseract + binario Tesseract

## Provenance of the alternatives

- `PP-OCRv6 (medium)` — an **independent** model (different project/checkpoint)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Word F1 ↑ (CPU) | Word F1 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| PP-OCRv6 (medium) | 0.796 | 0.796 | 19811 | 487 | cuda |
| easyocr (default) | 0.401 | 0.399 | 3662 | 1660 | cuda |
| pp_ocrv6 (medium) | 0.800 | 0.779 | 2138 | 2258 | cuda |
| pp_ocrv6 (small) | 0.784 | 0.767 | 823 | 1012 | cuda |
| pp_ocrv6 (tiny) | 0.717 | 0.684 | 318 | 419 | cuda |
| rapidocr (default) | 0.585 | 0.585 | 4807 | 4498 | cuda |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

