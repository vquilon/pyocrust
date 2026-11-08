# Benchmark: rectification

| Engine (variant/size) | n | SSIM ↑ | ms/page ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 20 | 0.491 | **11** | Apache-2.0 |
| uvdoc (31.7M) | 20 | <u>0.597</u> | 297 | Apache-2.0 |
| uvdoc (onnxruntime) | 20 | **0.604** | <u>78</u> | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-08_19-53-54`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
