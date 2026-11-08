# Benchmark: seal

| Engine (variant/size) | n | recall@IoU 0.5 ↑ | Mean IoU ↑ | ms/image ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: |
| pp-ocrv4_mobile_seal_det (4.8M) | 20 | 0.750 | **0.686** | <u>643</u> | Apache-2.0 |
| pp-ocrv4_mobile_seal_det (onnxruntime) | 20 | 0.750 | <u>0.607</u> | **217** | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-08_15-28-48`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
