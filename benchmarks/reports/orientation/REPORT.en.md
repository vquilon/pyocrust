# Feature report: `orientation`

> **Source: `measured`** — run by us in this repository. This table contains no external `reference` rows.

## Provenance

- **command**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/orientation/bank.py --limit 20 --device cpu`
- **dataset**: `synthetic_orientation` · **n** (per engine): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: not applicable (deterministic benchmark, no randomness)
- **run**: `benchmarks/results/orientation/2026-11-08_19-54-17` · **date**: `2026-11-08_19-54-17`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparison (mean by engine)

| Engine (variant) | n | accuracy ↑ | ms/page ↓ |
| :--- | ---: | ---: | ---: |
| craft_mlt_25k+latin_g2 (easyocr) | 20 | 35.0% | 42794 |
| pp-lcnet_x1_0_doc_ori (6.8M) | 20 | 100.0% | 1448 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 20 | **100.0%** | **5** |

> Bold values mark the best result for each metric among the **measured** engines in `orientation`. `N/A` = not evaluated (no ground truth for that column **or** the engine does not emit that structure), never an invented `0.0`.

## Skipped — not counted as executed

- (none)

## Provenance of the alternatives

- `craft_mlt_25k+latin_g2 (easyocr)` — an **independent** model (different project/checkpoint)
- `pp-lcnet_x1_0_doc_ori (onnxruntime)` — **same weights, a different path** (the SAME PaddleOCR `.onnx` through another runtime — NOT a different model)

> The reference engine (`pyocrust`) is not listed: it defines the base result. An alternative with **same weights, a different path** measures the same model through another runtime; it does **not** add an independent competitor, and it is stated as such.

## Reporting notes

- Missing engines are never recorded as `ok`: they remain `skipped` with their `pip install` requirement.
- Columns without ground truth are not filled with zeros: they appear as `N/A` (not evaluated).
- Provider integrity: rankings include only rows that actually ran on `device=cpu`. `pyocrust` confirms the actual execution provider in `provider_effective`; without an accelerator, `--device gpu` is `skipped` — a CPU fallback is never counted as GPU.

## CPU vs. GPU (`device_requested` vs. `provider_effective`)

> Same benchmark, dataset, and ground truth in both columns: **quality** should match; only **runtime** changes. The GPU column lists only engines that actually ran on an accelerator (`provider_effective` ∈ cuda/directml/…). A CPU fallback is never counted as GPU. `N/A` means the engine does **not** run on GPU in this benchmark (it is `skipped` with a reason), not a repeated CPU value.

| Engine (variant) | accuracy ↑ (CPU) | accuracy ↑ (GPU) | ms CPU | ms GPU | GPU provider |
| :--- | ---: | ---: | ---: | ---: | :--- |
| craft_mlt_25k+latin_g2 (easyocr) | 0.350 | N/A | 42794 | N/A | n/a (does not run on GPU) |
| pp-lcnet_x1_0_doc_ori (6.8M) | 1.000 | 0.950 | 1448 | 55 | directml |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | N/A | 5 | N/A | n/a (does not run on GPU) |

> The GPU provider comes from the actual `provider_effective` value in the GPU `summary.json` (`n/a` = the engine does not expose GPU execution in this benchmark). No GPU rows are invented: engines that did not run on an accelerator appear as `N/A`.

