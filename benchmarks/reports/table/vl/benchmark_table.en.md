# Benchmark: table

| Engine (variant/size) | n | Structural TEDS ↑ | ms/table ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 8 | 0.919 | **34191** | MIT |
| LightOnOCR-2-1B (1B) | 8 | 0.858 | 58834 | Apache-2.0 |
| LightOnOCR-3 (0.8B) | 8 | <u>0.926</u> | 162056 | Apache-2.0 |
| LightOnOCR-3 (4B) | 8 | 0.847 | 76940 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 8 | **0.933** | <u>35839</u> | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_18-13-46`, device `gpu`, n ≤ 8); licenses are informational, per `../QUALITY_VS_TIME.md`.
