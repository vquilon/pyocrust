# CPU vs GPU por feature — misma calidad, distinto tiempo

> Runs **CPU**: `benchmarks/results/<feature>/` · runs **GPU**: `benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT en ambas. La columna GPU solo lista motores que corrieron en un acelerador real (`provider_effective`); el resto queda `N/A` (no corre en GPU / `skipped`). `N/A` = no ejecutado, jamás un `0`. En este host el acelerador real de pyocrust es **DirectML** (`--device gpu` → `device=auto` → `provider_effective=directml`).

| Feature | Motor (variante) | Calidad (titular) | ms CPU | ms GPU | provider GPU |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.243 | 103 | 4182 | directml |
| `formula` | paddle_latex_ocr (default) | 0.694 | 4453 | 1187 | cuda |
| `formula` | pix2tex (default) | 0.460 | 5971 | N/A | n/a (no corre en GPU) |
| `formula` | pp-formulanet-s (direct) | 0.497 | 842 | 2514 | directml |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.196 | 1512 | 4470 | directml |
| `full_page` | indra (math) | 0.231 | 1547 | 10503 | directml |
| `full_page` | pp_structurev3 (default) | 0.211 | 10033 | 17198 | directml |
| `layout` | armaggheddon/y11-m | 0.472 | 380 | 64 | cuda |
| `layout` | armaggheddon/y11-n | 0.461 | 89 | 57 | cuda |
| `layout` | armaggheddon/y11-s | 0.459 | 162 | 60 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.494 | 401 | 65 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.521 | 93 | 64 | cuda |
| `layout` | armaggheddon/y26-s | 0.418 | 169 | 62 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.747 | 985 | N/A | n/a (no corre en GPU) |
| `layout` | hantian/v10-b | 0.446 | 520 | 66 | cuda |
| `layout` | hantian/v10-l | 0.466 | 598 | 73 | cuda |
| `layout` | hantian/v10-m | 0.497 | 342 | 68 | cuda |
| `layout` | hantian/v10-n | 0.443 | 88 | 60 | cuda |
| `layout` | hantian/v10-s | 0.455 | 175 | 63 | cuda |
| `layout` | hantian/v11-l | 0.468 | 509 | 71 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.442 | 410 | 69 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.457 | 98 | 63 | cuda |
| `layout` | hantian/v11-s | 0.438 | 180 | 63 | cuda |
| `layout` | hantian/v12-l | 0.483 | 685 | 82 | cuda |
| `layout` | hantian/v12-m | 0.459 | 541 | 73 | cuda |
| `layout` | hantian/v12-n | 0.489 | 137 | 67 | cuda |
| `layout` | hantian/v12-s | 0.473 | 239 | 66 | cuda |
| `layout` | hantian/v8-l | 0.449 | 864 | 71 | cuda |
| `layout` | hantian/v8-m | 0.461 | 442 | 60 | cuda |
| `layout` | hantian/v8-n | 0.473 | 138 | 55 | cuda |
| `layout` | hantian/v8-s | 0.451 | 213 | 61 | cuda |
| `layout` | hantian/v8-x | 0.426 | 1289 | 81 | cuda |
| `layout` | hantian/y26-l | 0.443 | 693 | 76 | cuda |
| `layout` | hantian/y26-m | 0.449 | 431 | 69 | cuda |
| `layout` | hantian/y26-n | 0.440 | 99 | 65 | cuda |
| `layout` | hantian/y26-s | 0.431 | 183 | 69 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.353 | 561 | 74 | cuda |
| `layout` | omoured/v10-l | 0.322 | 783 | 79 | cuda |
| `layout` | omoured/v10-m | 0.359 | 377 | 66 | cuda |
| `layout` | omoured/v10-n | 0.410 | 95 | 58 | cuda |
| `layout` | omoured/v10-s | 0.381 | 178 | 59 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.421 | 896 | 72 | cuda |
| `layout` | omoured/v11-l | 0.292 | 533 | 72 | cuda |
| `layout` | omoured/v11-m | 0.318 | 492 | 59 | cuda |
| `layout` | omoured/v11-n | 0.381 | 144 | 55 | cuda |
| `layout` | omoured/v11-s | 0.389 | 194 | 56 | cuda |
| `layout` | omoured/v11-x | 0.287 | 984 | 70 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.669 | 528 | 434 | directml |
| `layout` | yolo26m (doc-layout) (21.8M) | 0.467 | N/A | 44 | cuda |
| `layout` | yolov10b (DocLayNet) (20.5M) | 0.344 | N/A | 33 | cuda |
| `layout` | yolov10x (DocLayNet) (31.7M) | 0.381 | N/A | 44 | cuda |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 0.950 | 1124 | 55 | directml |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 0.950 | 2 | N/A | n/a (no corre en GPU) |
| `rectification` | uvdoc (31.7M) | 0.707 | 261 | 53 | directml |
| `rectification` | uvdoc (onnxruntime) | 0.707 | 74 | N/A | n/a (no corre en GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 641 | 120 | directml |
| `table` | slanet_plus (default) | 0.854 | 749 | 668 | directml |
| `table` | table-transformer-structure-recognition (default) | 0.699 | 140 | N/A | n/a (no corre en GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1236 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 970 | 1954 | directml |
| `text` | rapidocr (default) | 0.585 | 6748 | 5696 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 26 | 5 | directml |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (no corre en GPU) |
