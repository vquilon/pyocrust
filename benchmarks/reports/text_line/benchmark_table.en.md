# Benchmark: text_line

| Engine (variant/size) | n | accuracy ↑ | ms/line ↓ | license |
| :--- | ---: | ---: | ---: | ---: |
| ch_ppocr_mobile_v2.0_cls (rapidocr) | 20 | 90.0% | 3 | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (6.8M) | 20 | **100.0%** | <u>3</u> | Apache-2.0 |
| pp-lcnet_x1_0_textline_ori (onnxruntime) | 20 | <u>100.0%</u> | **2** | Apache-2.0 |

> Note: `N/A` = **not evaluated** — no ground truth for that column, or the engine does not emit that structure (e.g. `docling`, which emits Markdown only); `0.000` = **evaluated** and the engine got it wrong, never an unmeasured `0.0`. Values and n match `REPORT.md` (run `2026-11-15_20-30-55`, device `cpu`, n ≤ 20); licenses are informational, per `../QUALITY_VS_TIME.md`.
