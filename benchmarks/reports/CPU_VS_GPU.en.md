# CPU vs. GPU by feature — same quality, different runtime

> **CPU** runs: `benchmarks/results/<feature>/` · **GPU** runs: `benchmarks/results/_gpu/<feature>/` — same benchmark, dataset, and ground truth in both. The GPU column lists only engines that ran on a real accelerator (`provider_effective`); all others are `N/A` (unsupported on GPU / `skipped`). `N/A` means not run, never `0`. On this host, pyocrust's actual accelerator is **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Engine (variant) | Quality (headline metric) | ms CPU | ms GPU | GPU provider |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.211 | 146 | 2813 | directml |
| `formula` | paddle_latex_ocr (default) | 0.715 | 3734 | 1016 | cuda |
| `formula` | pix2tex (default) | 0.587 | 5764 | N/A | n/a (does not run on GPU) |
| `formula` | pp-formulanet-s (direct) | 0.576 | 854 | 1903 | directml |
| `formula` | pp_structurev3 (default) | 0.399 | 2193 | 2781 | directml |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.607 | 2247 | 3485 | directml |
| `formula` | unimernet (tiny) | 0.238 | 18685 | N/A | n/a (does not run on GPU) |
| `full_page` | docling-default (pipeline) | 0.354 | 33257 | N/A | n/a (does not run on GPU) |
| `full_page` | indra (math) | 0.265 | 2006 | 8901 | directml |
| `full_page` | pp_structurev3 (default) | 0.270 | 11054 | 14053 | directml |
| `layout` | armaggheddon/y11-m | 0.472 | 442 | 53 | cuda |
| `layout` | armaggheddon/y11-n | 0.461 | 96 | 51 | cuda |
| `layout` | armaggheddon/y11-s | 0.459 | 176 | 55 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.494 | 401 | 56 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.521 | 94 | 55 | cuda |
| `layout` | armaggheddon/y26-s | 0.418 | 191 | 55 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.747 | 1794 | N/A | n/a (does not run on GPU) |
| `layout` | hantian/v10-b | 0.446 | 548 | 56 | cuda |
| `layout` | hantian/v10-l | 0.466 | 789 | 59 | cuda |
| `layout` | hantian/v10-m | 0.497 | 404 | 62 | cuda |
| `layout` | hantian/v10-n | 0.443 | 102 | 50 | cuda |
| `layout` | hantian/v10-s | 0.455 | 181 | 51 | cuda |
| `layout` | hantian/v11-l | 0.468 | 499 | 61 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.442 | 421 | 58 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.457 | 104 | 54 | cuda |
| `layout` | hantian/v11-s | 0.438 | 183 | 53 | cuda |
| `layout` | hantian/v12-l | 0.483 | 683 | 70 | cuda |
| `layout` | hantian/v12-m | 0.459 | 465 | 65 | cuda |
| `layout` | hantian/v12-n | 0.489 | 114 | 61 | cuda |
| `layout` | hantian/v12-s | 0.473 | 219 | 57 | cuda |
| `layout` | hantian/v8-l | 0.449 | 808 | 61 | cuda |
| `layout` | hantian/v8-m | 0.461 | 437 | 55 | cuda |
| `layout` | hantian/v8-n | 0.473 | 114 | 50 | cuda |
| `layout` | hantian/v8-s | 0.451 | 224 | 47 | cuda |
| `layout` | hantian/v8-x | 0.426 | 1295 | 71 | cuda |
| `layout` | hantian/y26-l | 0.443 | 587 | 62 | cuda |
| `layout` | hantian/y26-m | 0.449 | 470 | 53 | cuda |
| `layout` | hantian/y26-n | 0.440 | 174 | 48 | cuda |
| `layout` | hantian/y26-s | 0.431 | 282 | 47 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.353 | 632 | 52 | cuda |
| `layout` | omoured/v10-l | 0.322 | 736 | 57 | cuda |
| `layout` | omoured/v10-m | 0.359 | 389 | 47 | cuda |
| `layout` | omoured/v10-n | 0.410 | 108 | 44 | cuda |
| `layout` | omoured/v10-s | 0.381 | 188 | 42 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.421 | 832 | 60 | cuda |
| `layout` | omoured/v11-l | 0.292 | 513 | 55 | cuda |
| `layout` | omoured/v11-m | 0.318 | 412 | 51 | cuda |
| `layout` | omoured/v11-n | 0.381 | 99 | 46 | cuda |
| `layout` | omoured/v11-s | 0.389 | 188 | 46 | cuda |
| `layout` | omoured/v11-x | 0.287 | 1021 | 70 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.669 | 3988 | 3288 | directml |
| `layout` | pp_structurev3 (default) | 0.638 | 9890 | 14190 | directml |
| `orientation` | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 42794 | N/A | n/a (does not run on GPU) |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 1.000 | 1448 | 1608 | directml |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (does not run on GPU) |
| `rectification` | perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 11 | N/A | n/a (does not run on GPU) |
| `rectification` | uvdoc (31.7M) | 0.597 | 297 | 298 | directml |
| `rectification` | uvdoc (onnxruntime) | 0.604 | 78 | N/A | n/a (does not run on GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 643 | 608 | directml |
| `seal` | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A | n/a (does not run on GPU) |
| `table` | SLANet_plus (paddleocr) | 0.828 | 87 | N/A | n/a (does not run on GPU) |
| `table` | pp_structurev3 (default) | 0.608 | 3245 | 5429 | directml |
| `table` | slanet_plus (default) | 0.780 | 848 | 1023 | directml |
| `table` | table-transformer-structure-recognition (default) | 0.698 | 198 | N/A | n/a (does not run on GPU) |
| `table` | tableformer (docling) | 0.807 | 35699 | N/A | n/a (does not run on GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1098 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 970 | 1182 | directml |
| `text` | rapidocr (default) | 0.585 | 6748 | 5530 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 26 | 25 | directml |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (does not run on GPU) |
