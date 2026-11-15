# Benchmark: formula

| Engine (variant/size) | n | Exact LaTeX ↑ | Similarity ↑ | Token F1 ↑ | Outputs with LaTeX ↑ | ms/formula ↓ | license |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 10 | 0.000 | **0.748** | **0.881** | N/A | <u>18719</u> | MIT |
| LightOnOCR-2-1B (1B) | 10 | 0.000 | 0.597 | 0.777 | N/A | 20186 | Apache-2.0 |
| LightOnOCR-3 (0.8B) | 10 | 0.000 | 0.550 | 0.749 | N/A | 24073 | Apache-2.0 |
| LightOnOCR-3 (4B) | 10 | 0.000 | 0.612 | 0.780 | N/A | 30950 | Apache-2.0 |
| PaddleOCR-VL (0.9B) | 10 | 0.000 | <u>0.614</u> | <u>0.843</u> | N/A | **17524** | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_19-06-25`, device `gpu`, n ≤ 10); licenses are informational, per `../QUALITY_VS_TIME.md`.
