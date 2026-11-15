# CPU vs. GPU by feature — same quality, different runtime

> **CPU** runs: `benchmarks/results/<feature>/` · **GPU** runs: `benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT en ambas. La columna GPU solo lista motores que corrieron en un real accelerator (`provider_effective`); el resto queda `N/A` (does not run on GPU / `skipped`). `N/A` = no ejecutado, jamás un `0`. El real accelerator de cada fila lo confirma `provider_effective` (columna *GPU provider*), no una suposición del host.

| Feature | Engine (variant) | Quality (headline metric) | ms CPU | ms GPU | GPU provider |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.326 | 82 | 708 | cuda |
| `formula` | paddle_latex_ocr (default) | 0.653 | 11331 | 3322 | cuda |
| `formula` | pix2tex (default) | 0.555 | 4659 | 1182 | cuda |
| `formula` | pp-formulanet-s (direct) | 0.499 | 696 | 1385 | cuda |
| `formula` | pp_structurev3 (default) | 0.398 | 1028 | 2095 | cuda |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.497 | 1052 | 2031 | cuda |
| `formula` | unimernet (tiny) | 0.260 | 14927 | N/A | n/a (does not run on GPU) |
| `full_page` | GLM-OCR (0.9B) | 0.559 | N/A | 30716 | cuda |
| `full_page` | LightOnOCR-2-1B (1B) | 0.588 | N/A | 44737 | cuda |
| `full_page` | LightOnOCR-3 (0.8B) | 0.625 | N/A | 320707 | cuda |
| `full_page` | LightOnOCR-3 (4B) | 0.590 | N/A | 72249 | cuda |
| `full_page` | PP-StructureV3 (paddleocr) | 0.427 | 180058 | 68269 | cuda |
| `full_page` | PaddleOCR-VL (0.9B) | 0.597 | N/A | 60907 | cuda |
| `full_page` | docling-default (pipeline) | 0.512 | 26739 | 22740 | cuda |
| `full_page` | indra (math) | 0.556 | 1251 | 1793 | cuda |
| `full_page` | pp_structurev3 (default) | 0.530 | 3652 | 4350 | cuda |
| `layout` | armaggheddon/y11-m | 0.542 | 367 | 45 | cuda |
| `layout` | armaggheddon/y11-n | 0.522 | 64 | 36 | cuda |
| `layout` | armaggheddon/y11-s | 0.516 | 142 | 36 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.568 | 365 | 44 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.572 | 62 | 33 | cuda |
| `layout` | armaggheddon/y26-s | 0.476 | 136 | 36 | cuda |
| `layout` | docling-layout-egret-xlarge (default) | 0.818 | 688 | 77 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.818 | 999 | 71 | cuda |
| `layout` | hantian/v10-b | 0.484 | 464 | 43 | cuda |
| `layout` | hantian/v10-l | 0.533 | 585 | 47 | cuda |
| `layout` | hantian/v10-m | 0.526 | 311 | 45 | cuda |
| `layout` | hantian/v10-n | 0.461 | 68 | 29 | cuda |
| `layout` | hantian/v10-s | 0.495 | 136 | 34 | cuda |
| `layout` | hantian/v11-l | 0.502 | 444 | 52 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.520 | 351 | 43 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.520 | 61 | 32 | cuda |
| `layout` | hantian/v11-s | 0.473 | 123 | 31 | cuda |
| `layout` | hantian/v12-l | 0.550 | 623 | 71 | cuda |
| `layout` | hantian/v12-m | 0.523 | 444 | 49 | cuda |
| `layout` | hantian/v12-n | 0.547 | 86 | 40 | cuda |
| `layout` | hantian/v12-s | 0.542 | 175 | 40 | cuda |
| `layout` | hantian/v8-l | 0.486 | 730 | 45 | cuda |
| `layout` | hantian/v8-m | 0.494 | 379 | 36 | cuda |
| `layout` | hantian/v8-n | 0.545 | 68 | 29 | cuda |
| `layout` | hantian/v8-s | 0.495 | 156 | 30 | cuda |
| `layout` | hantian/v8-x | 0.490 | 1128 | 55 | cuda |
| `layout` | hantian/y26-l | 0.508 | 436 | 55 | cuda |
| `layout` | hantian/y26-m | 0.492 | 353 | 43 | cuda |
| `layout` | hantian/y26-n | 0.499 | 65 | 31 | cuda |
| `layout` | hantian/y26-s | 0.492 | 140 | 36 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.382 | 467 | 43 | cuda |
| `layout` | omoured/v10-l | 0.366 | 593 | 48 | cuda |
| `layout` | omoured/v10-m | 0.381 | 311 | 41 | cuda |
| `layout` | omoured/v10-n | 0.485 | 65 | 31 | cuda |
| `layout` | omoured/v10-s | 0.427 | 129 | 33 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.451 | 784 | 54 | cuda |
| `layout` | omoured/v11-l | 0.350 | 461 | 52 | cuda |
| `layout` | omoured/v11-m | 0.392 | 351 | 44 | cuda |
| `layout` | omoured/v11-n | 0.448 | 66 | 31 | cuda |
| `layout` | omoured/v11-s | 0.406 | 139 | 31 | cuda |
| `layout` | omoured/v11-x | 0.331 | 940 | 65 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.796 | 505 | 883 | cuda |
| `layout` | pp_structurev3 (default) | 0.751 | 2926 | 3201 | cuda |
| `orientation` | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 43311 | N/A | n/a (does not run on GPU) |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 1.000 | 60 | 298 | cuda |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 4 | N/A | n/a (does not run on GPU) |
| `rectification` | perspective-4corner (baseline (OpenCV, sin pesos)) | 0.473 | 9 | N/A | n/a (does not run on GPU) |
| `rectification` | uvdoc (31.7M) | 0.590 | 71 | 34 | cuda |
| `rectification` | uvdoc (onnxruntime) | 0.595 | 74 | N/A | n/a (does not run on GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 643 | 287 | cuda |
| `seal` | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A | n/a (does not run on GPU) |
| `table` | SLANeXt_wired (paddleocr) | 0.882 | 1900 | N/A | n/a (does not run on GPU) |
| `table` | SLANet_plus (paddleocr) | 0.889 | 247 | 99 | cuda |
| `table` | pp_structurev3 (default) | 0.753 | 1128 | 2214 | cuda |
| `table` | slanet_plus (7.8M) | 0.868 | 52 | 484 | cuda |
| `table` | slanext_wired (367M) | 0.914 | 577 | 202 | cuda |
| `table` | table-transformer-structure-recognition (default) | 0.790 | 718 | 47 | cuda |
| `table` | tableformer (docling) | 0.905 | 27457 | 19140 | cuda |
| `text` | PP-OCRv6 (medium) | 0.796 | 19811 | 487 | cuda |
| `text` | easyocr (default) | 0.401 | 3662 | 1660 | cuda |
| `text` | pp_ocrv6 (medium) | 0.800 | 2138 | 2258 | cuda |
| `text` | pp_ocrv6 (small) | 0.784 | 823 | 1012 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 318 | 419 | cuda |
| `text` | rapidocr (default) | 0.585 | 4807 | 4498 | cuda |
| `text_line` | ch_ppocr_mobile_v2.0_cls (rapidocr) | 0.900 | 3 | N/A | n/a (does not run on GPU) |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 3 | 205 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 2 | N/A | n/a (does not run on GPU) |
