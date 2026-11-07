# Feature report: `text`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/text/bank.py --limit 20 --device cpu`
- **dataset**: `funsd` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/text/2026-11-06_22-46-46` · **date**: `2026-11-06_22-46-46`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | Word F1 ↑ | Ordered WER ↓ | CER ↓ | WER ↓ | box recall ↑ | Mean IoU ↑ | ms/img ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | 4600 |
| pp_ocrv6 (tiny) | 20 | **0.717** | **0.360** | 0.483 | **0.675** | 0.047 | 0.120 | **970** |
| rapidocr (default) | 20 | 0.585 | 0.512 | **0.476** | 0.701 | 0.037 | 0.108 | 6748 |

> Bold values mark the best result for each metric among the **measured** engines in `text`. `N/A` = not evaluated (no ground truth for that column), never an invented `0.0`.

## Skipped — not counted as executed

- `doctrl` — pip install doctrl
- `paddleocr` — NotImplementedError: paddleocr adapter pending integration
- `surya` — pip install surya-ocr (requiere torch)
- `tesseract` — pip install pytesseract + binario Tesseract

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | Word F1 ↑ (CPU) | Word F1 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| easyocr (default) | 0.401 | 0.399 | 4600 | 1236 | cuda |
| pp_ocrv6 (tiny) | 0.717 | 0.684 | 970 | 1954 | directml |
| rapidocr (default) | 0.585 | 0.585 | 6748 | 5696 | cuda |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

