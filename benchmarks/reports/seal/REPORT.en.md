# Feature report: `seal`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/seal/bank.py --backends pyocrust_seal,onnx_seal_det,paddleocr,doctrl --limit 20`
- **dataset**: `synthetic_seal` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/seal/2026-11-08_15-28-48` · **date**: `2026-11-08_15-28-48`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | recall@IoU 0.5 ↑ | Mean IoU ↑ | ms/image ↓ |
| :--- | ---: | ---: | ---: | ---: |
| pp-ocrv4_mobile_seal_det (4.8M) | 20 | 0.750 | **0.686** | 643 |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 20 | 0.750 | 0.607 | **217** |

> Bold values mark the best result for each metric among the **measured** engines in `seal`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- `doctrl` — pip install doctrl
- `paddleocr` — NotImplementedError: paddleocr adapter pending integration

## Provenance of the alternatives

- `pp-ocrv4_mobile_seal_det (onnxruntime)` — **same weights, a different path** (the SAME PaddleOCR `.onnx` through another runtime — NOT a different model)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | recall@IoU 0.5 ↑ (CPU) | recall@IoU 0.5 ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 0.750 | 643 | 608 | directml |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | N/A | 217 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

