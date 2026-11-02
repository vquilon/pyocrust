# CPU vs GPU por feature — misma calidad, distinto tiempo

> Runs **CPU**: `benchmarks/results/<feature>/` · runs **GPU**: `benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT en ambas. La columna GPU solo lista motores que corrieron en un acelerador real (`provider_effective`); el resto queda `N/A` (no corre en GPU / `skipped`). `N/A` = no ejecutado, jamás un `0`. En este host el acelerador real de pyocrust es **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Motor (variante) | Calidad (titular) | ms CPU | ms GPU | provider GPU |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | easyocr (default) | 0.152 | 743 | N/A | n/a (no corre en GPU) |
| `formula` | pix2tex (default) | 0.486 | 2451 | N/A | n/a (no corre en GPU) |
| `formula` | pyocrust_formula (pp-formulanet-s) | 0.419 | 2795 | 4983 | directml |
| `formula` | pyocrust_formulanet (direct) | 0.550 | 1015 | 2600 | directml |
| `formula` | rapidocr (default) | 0.104 | 3026 | N/A | n/a (no corre en GPU) |
| `full_page` | pyocrust_indra (math) | 0.176 | 1954 | 12311 | directml |
| `full_page` | pyocrust_structure (default) | 0.158 | 11253 | 21883 | directml |
| `layout` | docling_heron_101 (default) | 0.658 | 1093 | N/A | n/a (no corre en GPU) |
| `layout` | pyocrust_layout (130M) | 0.764 | 1956 | 1863 | directml |
| `layout` | yolo26m (21.8M) | 0.297 | 402 | N/A | n/a (no corre en GPU) |
| `layout` | yolov10b (20.5M) | 0.145 | 503 | N/A | n/a (no corre en GPU) |
| `layout` | yolov10x (31.7M) | 0.226 | 859 | N/A | n/a (no corre en GPU) |
| `orientation` | lcnet_doc_ori (onnxruntime) | 1.000 | 4 | N/A | n/a (no corre en GPU) |
| `orientation` | pyocrust_orientation (6.8M) | 1.000 | 702 | 720 | directml |
| `rectification` | pyocrust_rectify (31.7M) | 0.704 | 254 | 262 | directml |
| `rectification` | uvdoc (onnxruntime) | 0.701 | 138 | N/A | n/a (no corre en GPU) |
| `seal` | pyocrust_seal (4.8M) | 0.750 | 591 | 585 | directml |
| `table` | pyocrust_table (default) | 0.885 | 708 | 896 | directml |
| `table` | tatr (default) | 0.737 | 164 | N/A | n/a (no corre en GPU) |
| `text` | easyocr (default) | 0.384 | 3915 | N/A | n/a (no corre en GPU) |
| `text` | pyocrust (tiny) | 0.734 | 786 | 1161 | directml |
| `text` | rapidocr (default) | 0.659 | 6733 | N/A | n/a (no corre en GPU) |
| `text_line` | lcnet_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (no corre en GPU) |
| `text_line` | pyocrust_textline (6.8M) | 1.000 | 33 | 33 | directml |
