# CPU vs. GPU by feature — same quality, different runtime

> **CPU** runs: `benchmarks/results/<feature>/` · **GPU** runs: `benchmarks/results/_gpu/<feature>/` — same benchmark, dataset, and ground truth in both. The GPU column lists only engines that ran on a real accelerator (`provider_effective`); all others are `N/A` (unsupported on GPU / `skipped`). `N/A` means not run, never `0`. On this host, pyocrust's actual accelerator is **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Engine (variant) | Quality (headline metric) | ms CPU | ms GPU | GPU provider |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.243 | 103 | 4182 | directml |
| `formula` | paddle_latex_ocr (default) | 0.694 | 4453 | 1187 | cuda |
| `formula` | pix2tex (default) | 0.460 | 5971 | N/A | n/a (does not run on GPU) |
| `formula` | pp-formulanet-s (direct) | 0.497 | 842 | 2514 | directml |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.196 | 1512 | 4470 | directml |
| `full_page` | indra (math) | 0.231 | 1547 | 10503 | directml |
| `full_page` | pp_structurev3 (default) | 0.211 | 10033 | 17198 | directml |
| `layout` | armaggheddon/y11-m | 0.479 | 433 | 40 | cuda |
| `layout` | armaggheddon/y11-n | 0.426 | 69 | 35 | cuda |
| `layout` | armaggheddon/y11-s | 0.422 | 126 | 33 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.467 | 329 | 38 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.460 | 89 | 31 | cuda |
| `layout` | armaggheddon/y26-s | 0.400 | 139 | 33 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.843 | 1575 | N/A | n/a (does not run on GPU) |
| `layout` | hantian/v10-b | 0.459 | 433 | 40 | cuda |
| `layout` | hantian/v10-l | 0.407 | 604 | 44 | cuda |
| `layout` | hantian/v10-m | 0.499 | 274 | 43 | cuda |
| `layout` | hantian/v10-n | 0.405 | 67 | 38 | cuda |
| `layout` | hantian/v10-s | 0.385 | 154 | 36 | cuda |
| `layout` | hantian/v11-l | 0.420 | 375 | 42 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.427 | 411 | 38 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.402 | 68 | 31 | cuda |
| `layout` | hantian/v11-s | 0.429 | 145 | 32 | cuda |
| `layout` | hantian/v12-l | 0.487 | 600 | 56 | cuda |
| `layout` | hantian/v12-m | 0.458 | 412 | 42 | cuda |
| `layout` | hantian/v12-n | 0.477 | 107 | 36 | cuda |
| `layout` | hantian/v12-s | 0.494 | 197 | 39 | cuda |
| `layout` | hantian/v8-l | 0.414 | 763 | 40 | cuda |
| `layout` | hantian/v8-m | 0.385 | 390 | 35 | cuda |
| `layout` | hantian/v8-n | 0.508 | 84 | 29 | cuda |
| `layout` | hantian/v8-s | 0.415 | 160 | 31 | cuda |
| `layout` | hantian/v8-x | 0.497 | 1147 | 52 | cuda |
| `layout` | hantian/y26-l | 0.410 | 431 | 42 | cuda |
| `layout` | hantian/y26-m | 0.394 | 411 | 35 | cuda |
| `layout` | hantian/y26-n | 0.445 | 81 | 35 | cuda |
| `layout` | hantian/y26-s | 0.471 | 128 | 30 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.344 | 472 | 39 | cuda |
| `layout` | omoured/v10-l | 0.325 | 576 | 38 | cuda |
| `layout` | omoured/v10-m | 0.354 | 285 | 32 | cuda |
| `layout` | omoured/v10-n | 0.437 | 70 | 29 | cuda |
| `layout` | omoured/v10-s | 0.315 | 266 | 37 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.381 | 741 | 50 | cuda |
| `layout` | omoured/v11-l | 0.231 | 477 | 39 | cuda |
| `layout` | omoured/v11-m | 0.288 | 325 | 35 | cuda |
| `layout` | omoured/v11-n | 0.411 | 66 | 30 | cuda |
| `layout` | omoured/v11-s | 0.379 | 179 | 31 | cuda |
| `layout` | omoured/v11-x | 0.252 | 1000 | 56 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.827 | 776 | 434 | directml |
| `layout` | yolo26m (doc-layout) (21.8M) | 0.467 | N/A | 44 | cuda |
| `layout` | yolov10b (DocLayNet) (20.5M) | 0.344 | N/A | 33 | cuda |
| `layout` | yolov10x (DocLayNet) (31.7M) | 0.381 | N/A | 44 | cuda |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 0.950 | 1124 | 55 | directml |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 0.950 | 2 | N/A | n/a (does not run on GPU) |
| `rectification` | uvdoc (31.7M) | 0.707 | 261 | 53 | directml |
| `rectification` | uvdoc (onnxruntime) | 0.707 | 74 | N/A | n/a (does not run on GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 641 | 120 | directml |
| `table` | slanet_plus (default) | 0.854 | 749 | 668 | directml |
| `table` | table-transformer-structure-recognition (default) | 0.699 | 140 | N/A | n/a (does not run on GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1236 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 970 | 1954 | directml |
| `text` | rapidocr (default) | 0.585 | 6748 | 5696 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 26 | 5 | directml |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (does not run on GPU) |
