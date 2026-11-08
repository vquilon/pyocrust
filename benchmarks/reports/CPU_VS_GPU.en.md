# CPU vs. GPU by feature — same quality, different runtime

> **CPU** runs: `benchmarks/results/<feature>/` · **GPU** runs: `benchmarks/results/_gpu/<feature>/` — same benchmark, dataset, and ground truth in both. The GPU column lists only engines that ran on a real accelerator (`provider_effective`); all others are `N/A` (unsupported on GPU / `skipped`). `N/A` means not run, never `0`. On this host, pyocrust's actual accelerator is **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Engine (variant) | Quality (headline metric) | ms CPU | ms GPU | GPU provider |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.211 | 147 | 4182 | directml |
| `formula` | paddle_latex_ocr (default) | 0.715 | 7397 | 1187 | cuda |
| `formula` | pix2tex (default) | 0.585 | 11452 | N/A | n/a (does not run on GPU) |
| `formula` | pp-formulanet-s (direct) | 0.576 | 874 | 2514 | directml |
| `formula` | pp_structurev3 (default) | 0.399 | 2336 | N/A | n/a (does not run on GPU) |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.607 | 2191 | 4470 | directml |
| `full_page` | docling-default (pipeline) | 0.354 | 29302 | N/A | n/a (does not run on GPU) |
| `full_page` | indra (math) | 0.242 | N/A | 10503 | directml |
| `full_page` | pp_structurev3 (default) | 0.270 | 9769 | 17198 | directml |
| `layout` | armaggheddon/y11-m | 0.472 | 442 | 64 | cuda |
| `layout` | armaggheddon/y11-n | 0.461 | 96 | 57 | cuda |
| `layout` | armaggheddon/y11-s | 0.459 | 176 | 60 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.494 | 401 | 65 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.521 | 94 | 64 | cuda |
| `layout` | armaggheddon/y26-s | 0.418 | 191 | 62 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.747 | 1794 | N/A | n/a (does not run on GPU) |
| `layout` | hantian/v10-b | 0.446 | 548 | 66 | cuda |
| `layout` | hantian/v10-l | 0.466 | 789 | 73 | cuda |
| `layout` | hantian/v10-m | 0.497 | 404 | 68 | cuda |
| `layout` | hantian/v10-n | 0.443 | 102 | 60 | cuda |
| `layout` | hantian/v10-s | 0.455 | 181 | 63 | cuda |
| `layout` | hantian/v11-l | 0.468 | 499 | 71 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.442 | 421 | 69 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.457 | 104 | 63 | cuda |
| `layout` | hantian/v11-s | 0.438 | 183 | 63 | cuda |
| `layout` | hantian/v12-l | 0.483 | 683 | 82 | cuda |
| `layout` | hantian/v12-m | 0.459 | 465 | 73 | cuda |
| `layout` | hantian/v12-n | 0.489 | 114 | 67 | cuda |
| `layout` | hantian/v12-s | 0.473 | 219 | 66 | cuda |
| `layout` | hantian/v8-l | 0.449 | 808 | 71 | cuda |
| `layout` | hantian/v8-m | 0.461 | 437 | 60 | cuda |
| `layout` | hantian/v8-n | 0.473 | 114 | 55 | cuda |
| `layout` | hantian/v8-s | 0.451 | 224 | 61 | cuda |
| `layout` | hantian/v8-x | 0.426 | 1295 | 81 | cuda |
| `layout` | hantian/y26-l | 0.443 | 587 | 76 | cuda |
| `layout` | hantian/y26-m | 0.449 | 470 | 69 | cuda |
| `layout` | hantian/y26-n | 0.440 | 174 | 65 | cuda |
| `layout` | hantian/y26-s | 0.431 | 282 | 69 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.353 | 632 | 74 | cuda |
| `layout` | omoured/v10-l | 0.322 | 736 | 79 | cuda |
| `layout` | omoured/v10-m | 0.359 | 389 | 66 | cuda |
| `layout` | omoured/v10-n | 0.410 | 108 | 58 | cuda |
| `layout` | omoured/v10-s | 0.381 | 188 | 59 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.421 | 832 | 72 | cuda |
| `layout` | omoured/v11-l | 0.292 | 513 | 72 | cuda |
| `layout` | omoured/v11-m | 0.318 | 412 | 59 | cuda |
| `layout` | omoured/v11-n | 0.381 | 99 | 55 | cuda |
| `layout` | omoured/v11-s | 0.389 | 188 | 56 | cuda |
| `layout` | omoured/v11-x | 0.287 | 1021 | 70 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.669 | 3988 | N/A | n/a (does not run on GPU) |
| `layout` | pp_structurev3 (default) | 0.638 | 9890 | N/A | n/a (does not run on GPU) |
| `orientation` | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 42794 | N/A | n/a (does not run on GPU) |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 1.000 | 1448 | 55 | directml |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (does not run on GPU) |
| `rectification` | perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 11 | N/A | n/a (does not run on GPU) |
| `rectification` | uvdoc (31.7M) | 0.597 | 297 | 53 | directml |
| `rectification` | uvdoc (onnxruntime) | 0.604 | 78 | N/A | n/a (does not run on GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 643 | 120 | directml |
| `seal` | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A | n/a (does not run on GPU) |
| `table` | SLANet_plus (paddleocr) | 0.828 | 71 | N/A | n/a (does not run on GPU) |
| `table` | slanet_plus (default) | 0.780 | 796 | 668 | directml |
| `table` | table-transformer-structure-recognition (default) | 0.698 | 760 | N/A | n/a (does not run on GPU) |
| `table` | tableformer (docling) | 0.807 | 32806 | N/A | n/a (does not run on GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1236 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 970 | 1954 | directml |
| `text` | rapidocr (default) | 0.585 | 6748 | 5696 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 26 | 5 | directml |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (does not run on GPU) |
