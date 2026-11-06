# CPU vs GPU por feature — misma calidad, distinto tiempo

> Runs **CPU**: `benchmarks/results/<feature>/` · runs **GPU**: `benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT en ambas. La columna GPU solo lista motores que corrieron en un acelerador real (`provider_effective`); el resto queda `N/A` (no corre en GPU / `skipped`). `N/A` = no ejecutado, jamás un `0`. En este host el acelerador real de pyocrust es **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Motor (variante) | Calidad (titular) | ms CPU | ms GPU | provider GPU |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | paddle_latex_ocr (default) | 0.694 | 12490 | 1187 | cuda |
| `formula` | pix2tex (default) | 0.486 | 7484 | N/A | n/a (no corre en GPU) |
| `formula` | pyocrust_formula (pp-formulanet-s) | 0.196 | 3464 | N/A | n/a (no corre en GPU) |
| `formula` | pyocrust_formulanet (direct) | 0.497 | 979 | N/A | n/a (no corre en GPU) |
| `full_page` | pyocrust_indra (math) | 0.231 | 1547 | N/A | n/a (no corre en GPU) |
| `full_page` | pyocrust_structure (default) | 0.211 | 10033 | N/A | n/a (no corre en GPU) |
| `layout` | docling_heron_101 (default) | 0.843 | 1071 | N/A | n/a (no corre en GPU) |
| `layout` | pyocrust_layout (130M) | 0.827 | 1987 | N/A | n/a (no corre en GPU) |
| `layout` | yolo26m (21.8M) | 0.467 | 294 | 44 | cuda |
| `layout` | yolov10b (20.5M) | 0.344 | 383 | 33 | cuda |
| `layout` | yolov10x (31.7M) | 0.381 | 658 | 44 | cuda |
| `orientation` | lcnet_doc_ori (onnxruntime) | 0.950 | 2 | N/A | n/a (no corre en GPU) |
| `orientation` | pyocrust_orientation (6.8M) | 0.950 | 1124 | N/A | n/a (no corre en GPU) |
| `rectification` | pyocrust_rectify (31.7M) | 0.707 | 261 | N/A | n/a (no corre en GPU) |
| `rectification` | uvdoc (onnxruntime) | 0.707 | 74 | N/A | n/a (no corre en GPU) |
| `seal` | pyocrust_seal (4.8M) | 0.750 | 641 | N/A | n/a (no corre en GPU) |
| `table` | pyocrust_table (default) | 0.854 | 749 | N/A | n/a (no corre en GPU) |
| `table` | tatr (default) | 0.699 | 140 | N/A | n/a (no corre en GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1236 | cuda |
| `text` | pyocrust (tiny) | 0.717 | 970 | N/A | n/a (no corre en GPU) |
| `text` | rapidocr (default) | 0.585 | 6748 | 5696 | cuda |
| `text_line` | lcnet_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (no corre en GPU) |
| `text_line` | pyocrust_textline (6.8M) | 1.000 | 26 | N/A | n/a (no corre en GPU) |
