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
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 20 | 0.211 | 146 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 20 | 0.211 | 2813 | directml | omnidocbench_formula |
| formula | unimernet (tiny) | Apache-2.0 | formula | cpu | 20 | 0.238 | 18685 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | cpu | 20 | 0.399 | 2193 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | gpu | 20 | 0.400 | 2781 | directml | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 20 | 0.576 | 854 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 20 | 0.576 | 1903 | directml | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 20 | 0.587 | 5764 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 20 | 0.607 | 2247 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 20 | 0.607 | 3485 | directml | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 20 | 0.715 | 3734 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 20 | 0.715 | 1016 | cuda | omnidocbench_formula |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 40 | 0.426 | 1295 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 40 | 0.426 | 71 | cuda | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | cpu | 40 | 0.472 | 442 | cpu | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | gpu | 40 | 0.472 | 53 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 40 | 0.473 | 114 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 40 | 0.473 | 50 | cuda | omnidocbench_layout |
| layout | hantian/v12-n | AGPL-3.0 | layout | cpu | 40 | 0.489 | 114 | cpu | omnidocbench_layout |
| layout | hantian/v12-n | AGPL-3.0 | layout | gpu | 40 | 0.489 | 61 | cuda | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | gpu | 40 | 0.495 | 62 | cuda | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | cpu | 40 | 0.497 | 404 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | cpu | 40 | 0.521 | 94 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | gpu | 40 | 0.521 | 55 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | cpu | 40 | 0.638 | 9890 | cpu | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | gpu | 40 | 0.639 | 14190 | directml | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 40 | 0.669 | 3988 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | gpu | 40 | 0.669 | 3288 | directml | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 40 | 0.747 | 1794 | cpu | omnidocbench_layout |
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
| table | pp_structurev3 | Apache-2.0 | table | cpu | 20 | 0.608 | 3245 | cpu | omnidocbench_table |
| table | pp_structurev3 | Apache-2.0 | table | gpu | 20 | 0.608 | 5429 | directml | omnidocbench_table |
| table | table-transformer-structure-recognition | MIT | table | cpu | 20 | 0.698 | 198 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | cpu | 20 | 0.780 | 848 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | gpu | 20 | 0.780 | 1023 | directml | omnidocbench_table |
| table | tableformer (docling) | MIT | table | cpu | 20 | 0.807 | 35699 | cpu | omnidocbench_table |
| table | SLANet_plus (paddleocr) | Apache-2.0 | table | cpu | 20 | 0.828 | 87 | cpu | omnidocbench_table |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | cpu | 20 | 0.265 | 2006 | cpu | omnidocbench_full_page |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 20 | 0.265 | 8901 | directml | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 20 | 0.267 | 14053 | directml | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 20 | 0.270 | 11054 | cpu | omnidocbench_full_page |
| full_page | docling-default (pipeline) | MIT | full_page | cpu | 20 | 0.354 | 33257 | cpu | omnidocbench_full_page |