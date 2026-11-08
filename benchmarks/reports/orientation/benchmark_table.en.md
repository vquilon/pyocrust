# Benchmark: orientation

| Engine (variant/size) | n | accuracy ↑ | ms/page ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| craft_mlt_25k+latin_g2 (easyocr) | 20 | 35.0% | 42794 | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (6.8M) | 20 | **100.0%** | <u>1448</u> | Apache-2.0 |
| pp-lcnet_x1_0_doc_ori (onnxruntime) | 20 | <u>100.0%</u> | **5** | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-08_19-54-17`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
