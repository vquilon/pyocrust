# Feature report: `rectification`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/rectification/bank.py --limit 20 --device cpu`
- **dataset**: `synthetic_rectification` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/rectification/2026-11-08_19-53-54` · **date**: `2026-11-08_19-53-54`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | SSIM ↑ | ms/page ↓ |
| :--- | ---: | ---: | ---: |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 20 | 0.491 | **11** |
| uvdoc (31.7M) | 20 | 0.597 | 297 |
| uvdoc (onnxruntime) | 20 | **0.604** | 78 |

> Bold values mark the best result for each metric among the **measured** engines in `rectification`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `perspective-4corner (baseline (OpenCV, sin pesos))` — **classical baseline**, no weights (not a learned model nor a SOTA: a comparison floor)
- `uvdoc (onnxruntime)` — **same weights, a different path** (the SAME PaddleOCR `.onnx` through another runtime — NOT a different model)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | SSIM ↑ (CPU) | SSIM ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | N/A | 11 | N/A | n/a (does not run on GPU) |
| uvdoc (31.7M) | 0.597 | 0.597 | 297 | 298 | directml |
| uvdoc (onnxruntime) | 0.604 | N/A | 78 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

