# Resumen global — features × modelo × licencia × device × tiempo × calidad

> Una fila por (feature, motor, device) con la **última** corrida medida.
> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.

| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 4600 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 6748 | cpu | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | gpu | 20 | 0.684 | 1954 | directml | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | cpu | 20 | 0.717 | 970 | cpu | funsd |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 20 | 0.196 | 4470 | directml | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 20 | 0.211 | 147 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 20 | 0.243 | 4182 | directml | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | cpu | 20 | 0.399 | 2336 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 20 | 0.497 | 2514 | directml | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 20 | 0.576 | 874 | cpu | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 20 | 0.585 | 11452 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 20 | 0.607 | 2191 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 20 | 0.715 | 7397 | cpu | omnidocbench_formula |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 40 | 0.426 | 1295 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 40 | 0.426 | 81 | cuda | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | cpu | 40 | 0.472 | 442 | cpu | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | gpu | 40 | 0.472 | 64 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 40 | 0.473 | 114 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 40 | 0.473 | 55 | cuda | omnidocbench_layout |
| layout | hantian/v12-n | AGPL-3.0 | layout | cpu | 40 | 0.489 | 114 | cpu | omnidocbench_layout |
| layout | hantian/v12-n | AGPL-3.0 | layout | gpu | 40 | 0.489 | 67 | cuda | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | gpu | 40 | 0.495 | 68 | cuda | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | cpu | 40 | 0.497 | 404 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | cpu | 40 | 0.521 | 94 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | gpu | 40 | 0.521 | 64 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | cpu | 40 | 0.638 | 9890 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 40 | 0.669 | 3988 | cpu | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 40 | 0.747 | 1794 | cpu | omnidocbench_layout |
| orientation | craft_mlt_25k+latin_g2 (easyocr) | Apache-2.0 | orientation | cpu | 20 | 0.350 | 42794 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | gpu | 20 | 0.950 | 55 | directml | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (onnxruntime) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 5 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 1448 | cpu | synthetic_orientation |
| rectification | perspective-4corner (baseline (OpenCV, sin pesos)) | Apache-2.0 | rectification | cpu | 20 | 0.491 | 11 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | cpu | 20 | 0.597 | 297 | cpu | synthetic_rectification |
| rectification | uvdoc (onnxruntime) | Apache-2.0 | rectification | cpu | 20 | 0.604 | 78 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | gpu | 20 | 0.707 | 53 | directml | synthetic_rectification |
| text_line | pp-lcnet_x1_0_textline_ori (onnxruntime) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 5 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 26 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | gpu | 20 | 1.000 | 5 | directml | synthetic_text_line |
| seal | pp-ocrv4_mobile_seal_det (onnxruntime) | Apache-2.0 | seal | cpu | 20 | 0.750 | 217 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | cpu | 20 | 0.750 | 643 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | gpu | 20 | 0.750 | 120 | directml | synthetic_seal |
| table | table-transformer-structure-recognition | MIT | table | cpu | 20 | 0.698 | 760 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | cpu | 20 | 0.780 | 796 | cpu | omnidocbench_table |
| table | tableformer (docling) | MIT | table | cpu | 20 | 0.807 | 32806 | cpu | omnidocbench_table |
| table | SLANet_plus (paddleocr) | Apache-2.0 | table | cpu | 20 | 0.828 | 71 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | gpu | 20 | 0.854 | 668 | directml | omnidocbench_table |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 20 | 0.210 | 17198 | directml | omnidocbench_full_page |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 19 | 0.242 | 10503 | directml | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 20 | 0.270 | 9769 | cpu | omnidocbench_full_page |
| full_page | docling-default (pipeline) | MIT | full_page | cpu | 20 | 0.354 | 29302 | cpu | omnidocbench_full_page |