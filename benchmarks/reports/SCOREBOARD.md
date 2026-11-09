# Resumen global — features × modelo × licencia × device × tiempo × calidad

> Una fila por (feature, motor, device) con la **última** corrida medida.
> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.

| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | gpu | 20 | 0.399 | 1098 | cuda | funsd |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 4600 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 6748 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | gpu | 20 | 0.585 | 5530 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | gpu | 20 | 0.684 | 1182 | directml | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | cpu | 20 | 0.717 | 970 | cpu | funsd |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 9 | 0.243 | 1989 | directml | omnidocbench_formula |
| formula | unimernet (tiny) | Apache-2.0 | formula | cpu | 10 | 0.260 | 17493 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 10 | 0.326 | 141 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | cpu | 10 | 0.398 | 2774 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | gpu | 10 | 0.398 | 2110 | directml | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 10 | 0.497 | 2474 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 10 | 0.497 | 2800 | directml | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 10 | 0.499 | 998 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 10 | 0.499 | 2487 | directml | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 10 | 0.552 | 5500 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 10 | 0.653 | 16326 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 10 | 0.653 | 2276 | cuda | omnidocbench_formula |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 40 | 0.490 | 1025 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 40 | 0.490 | 43 | cuda | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | cpu | 40 | 0.533 | 569 | cpu | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | gpu | 40 | 0.533 | 39 | cuda | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | cpu | 40 | 0.542 | 365 | cpu | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | gpu | 40 | 0.542 | 37 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 40 | 0.545 | 68 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 40 | 0.545 | 29 | cuda | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | cpu | 40 | 0.550 | 711 | cpu | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | gpu | 40 | 0.550 | 48 | cuda | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | cpu | 40 | 0.572 | 69 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | gpu | 40 | 0.572 | 32 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | gpu | 40 | 0.751 | 6853 | directml | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | cpu | 40 | 0.751 | 7111 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 40 | 0.796 | 2219 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | gpu | 40 | 0.796 | 437 | directml | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 40 | 0.818 | 1005 | cpu | omnidocbench_layout |
| orientation | craft_mlt_25k+latin_g2 (easyocr) | Apache-2.0 | orientation | cpu | 20 | 0.350 | 42794 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (onnxruntime) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 5 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 1448 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | gpu | 20 | 1.000 | 1608 | directml | synthetic_orientation |
| rectification | perspective-4corner (baseline (OpenCV, sin pesos)) | Apache-2.0 | rectification | cpu | 20 | 0.491 | 11 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | cpu | 20 | 0.597 | 297 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | gpu | 20 | 0.597 | 298 | directml | synthetic_rectification |
| rectification | uvdoc (onnxruntime) | Apache-2.0 | rectification | cpu | 20 | 0.604 | 78 | cpu | synthetic_rectification |
| text_line | pp-lcnet_x1_0_textline_ori (onnxruntime) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 5 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 26 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | gpu | 20 | 1.000 | 25 | directml | synthetic_text_line |
| seal | pp-ocrv4_mobile_seal_det (onnxruntime) | Apache-2.0 | seal | cpu | 20 | 0.750 | 217 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | cpu | 20 | 0.750 | 643 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | gpu | 20 | 0.750 | 608 | directml | synthetic_seal |
| table | pp_structurev3 | Apache-2.0 | table | cpu | 8 | 0.753 | 3530 | cpu | omnidocbench_table |
| table | pp_structurev3 | Apache-2.0 | table | gpu | 8 | 0.753 | 3370 | directml | omnidocbench_table |
| table | table-transformer-structure-recognition | MIT | table | cpu | 8 | 0.790 | 131 | cpu | omnidocbench_table |
| table | SLANet_plus (paddleocr) | Apache-2.0 | table | cpu | 8 | 0.889 | 72 | cpu | omnidocbench_table |
| table | tableformer (docling) | MIT | table | cpu | 8 | 0.905 | 28609 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | cpu | 8 | 0.914 | 1103 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | gpu | 8 | 0.914 | 632 | directml | omnidocbench_table |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | cpu | 6 | 0.029 | 607 | cpu | omnidocbench_full_page |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 6 | 0.029 | 4802 | directml | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 6 | 0.083 | 5865 | cpu | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 6 | 0.085 | 4754 | directml | omnidocbench_full_page |
| full_page | docling-default (pipeline) | MIT | full_page | cpu | 6 | 0.204 | 25723 | cpu | omnidocbench_full_page |