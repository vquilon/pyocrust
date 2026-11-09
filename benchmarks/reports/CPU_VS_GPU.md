# CPU vs GPU por feature — misma calidad, distinto tiempo

> Runs **CPU**: `benchmarks/results/<feature>/` · runs **GPU**: `benchmarks/results/_gpu/<feature>/` — mismo banco, mismo dataset y mismo GT en ambas. La columna GPU solo lista motores que corrieron en un acelerador real (`provider_effective`); el resto queda `N/A` (no corre en GPU / `skipped`). `N/A` = no ejecutado, jamás un `0`. El acelerador real de cada fila lo confirma `provider_effective` (columna *provider GPU*), no una suposición del host.

| Feature | Motor (variante) | Calidad (titular) | ms CPU | ms GPU | provider GPU |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `formula` | indra (math) | 0.326 | 141 | 460 | cuda |
| `formula` | paddle_latex_ocr (default) | 0.653 | 16326 | 2763 | cuda |
| `formula` | pix2tex (default) | 0.552 | 5500 | N/A | n/a (no corre en GPU) |
| `formula` | pp-formulanet-s (direct) | 0.499 | 998 | 1910 | cuda |
| `formula` | pp_structurev3 (default) | 0.398 | 2774 | 2236 | cuda |
| `formula` | pp_structurev3 (pp-formulanet-s) | 0.497 | 2474 | 2254 | cuda |
| `formula` | unimernet (tiny) | 0.260 | 17493 | N/A | n/a (no corre en GPU) |
| `full_page` | PP-StructureV3 (paddleocr) | 0.086 | 124261 | N/A | n/a (no corre en GPU) |
| `full_page` | docling-default (pipeline) | 0.204 | 27542 | N/A | n/a (no corre en GPU) |
| `full_page` | indra (math) | 0.029 | 200 | 1118 | cuda |
| `full_page` | pp_structurev3 (default) | 0.083 | 2181 | 1805 | cuda |
| `layout` | armaggheddon/y11-m | 0.542 | 365 | 42 | cuda |
| `layout` | armaggheddon/y11-n | 0.522 | 65 | 30 | cuda |
| `layout` | armaggheddon/y11-s | 0.516 | 167 | 29 | cuda |
| `layout` | armaggheddon/y26-m (21.8M) | 0.568 | 333 | 31 | cuda |
| `layout` | armaggheddon/y26-n (2.6M) | 0.572 | 69 | 29 | cuda |
| `layout` | armaggheddon/y26-s | 0.476 | 157 | 30 | cuda |
| `layout` | docling-layout-heron-101 (default) | 0.818 | 1005 | N/A | n/a (no corre en GPU) |
| `layout` | hantian/v10-b | 0.484 | 456 | 33 | cuda |
| `layout` | hantian/v10-l | 0.533 | 569 | 36 | cuda |
| `layout` | hantian/v10-m | 0.526 | 332 | 41 | cuda |
| `layout` | hantian/v10-n | 0.461 | 66 | 30 | cuda |
| `layout` | hantian/v10-s | 0.495 | 131 | 30 | cuda |
| `layout` | hantian/v11-l | 0.502 | 422 | 48 | cuda |
| `layout` | hantian/v11-m (21.8M) | 0.520 | 342 | 40 | cuda |
| `layout` | hantian/v11-n (2.6M) | 0.520 | 67 | 33 | cuda |
| `layout` | hantian/v11-s | 0.473 | 163 | 35 | cuda |
| `layout` | hantian/v12-l | 0.550 | 711 | 53 | cuda |
| `layout` | hantian/v12-m | 0.523 | 447 | 42 | cuda |
| `layout` | hantian/v12-n | 0.547 | 88 | 34 | cuda |
| `layout` | hantian/v12-s | 0.542 | 180 | 31 | cuda |
| `layout` | hantian/v8-l | 0.486 | 699 | 37 | cuda |
| `layout` | hantian/v8-m | 0.494 | 364 | 33 | cuda |
| `layout` | hantian/v8-n | 0.545 | 68 | 25 | cuda |
| `layout` | hantian/v8-s | 0.495 | 207 | 27 | cuda |
| `layout` | hantian/v8-x | 0.490 | 1025 | 47 | cuda |
| `layout` | hantian/y26-l | 0.508 | 433 | 37 | cuda |
| `layout` | hantian/y26-m | 0.492 | 353 | 32 | cuda |
| `layout` | hantian/y26-n | 0.499 | 69 | 29 | cuda |
| `layout` | hantian/y26-s | 0.492 | 150 | 32 | cuda |
| `layout` | omoured/v10-b (20.5M) | 0.382 | 415 | 33 | cuda |
| `layout` | omoured/v10-l | 0.366 | 550 | 36 | cuda |
| `layout` | omoured/v10-m | 0.381 | 292 | 33 | cuda |
| `layout` | omoured/v10-n | 0.485 | 70 | 28 | cuda |
| `layout` | omoured/v10-s | 0.427 | 140 | 28 | cuda |
| `layout` | omoured/v10-x (31.7M) | 0.451 | 748 | 54 | cuda |
| `layout` | omoured/v11-l | 0.350 | 481 | 45 | cuda |
| `layout` | omoured/v11-m | 0.392 | 354 | 38 | cuda |
| `layout` | omoured/v11-n | 0.448 | 137 | 36 | cuda |
| `layout` | omoured/v11-s | 0.406 | 144 | 43 | cuda |
| `layout` | omoured/v11-x | 0.331 | 849 | 55 | cuda |
| `layout` | pp-doclayoutv3 (130M) | 0.796 | 2219 | 488 | cuda |
| `layout` | pp_structurev3 (default) | 0.751 | 7111 | 2938 | cuda |
| `orientation` | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 42794 | N/A | n/a (no corre en GPU) |
| `orientation` | pp-lcnet_x1_0_doc_ori (6.8M) | 1.000 | 1448 | 192 | cuda |
| `orientation` | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (no corre en GPU) |
| `rectification` | perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | 11 | N/A | n/a (no corre en GPU) |
| `rectification` | uvdoc (31.7M) | 0.597 | 297 | 33 | cuda |
| `rectification` | uvdoc (onnxruntime) | 0.604 | 78 | N/A | n/a (no corre en GPU) |
| `seal` | pp-ocrv4_mobile_seal_det (4.8M) | 0.750 | 643 | 178 | cuda |
| `seal` | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A | n/a (no corre en GPU) |
| `table` | SLANet_plus (paddleocr) | 0.889 | 72 | N/A | n/a (no corre en GPU) |
| `table` | pp_structurev3 (default) | 0.753 | 3530 | 1479 | cuda |
| `table` | slanet_plus (default) | 0.914 | 1103 | 172 | cuda |
| `table` | table-transformer-structure-recognition (default) | 0.790 | 131 | N/A | n/a (no corre en GPU) |
| `table` | tableformer (docling) | 0.905 | 28609 | N/A | n/a (no corre en GPU) |
| `text` | easyocr (default) | 0.401 | 4600 | 1263 | cuda |
| `text` | pp_ocrv6 (tiny) | 0.717 | 970 | 330 | cuda |
| `text` | rapidocr (default) | 0.585 | 6748 | 5842 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (6.8M) | 1.000 | 26 | 152 | cuda |
| `text_line` | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 5 | N/A | n/a (no corre en GPU) |
