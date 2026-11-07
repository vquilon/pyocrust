# Resumen global — features × modelo × licencia × device × tiempo × calidad

> Una fila por (feature, motor, device) con la **última** corrida medida.
> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.

| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | gpu | 20 | 0.399 | 1236 | cuda | funsd |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 4600 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 6748 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | gpu | 20 | 0.585 | 5696 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | gpu | 20 | 0.684 | 1954 | directml | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | cpu | 20 | 0.717 | 970 | cpu | funsd |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 20 | 0.196 | 1512 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 20 | 0.196 | 4470 | directml | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 20 | 0.243 | 103 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 20 | 0.243 | 4182 | directml | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 20 | 0.460 | 5971 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 20 | 0.497 | 842 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 20 | 0.497 | 2514 | directml | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 20 | 0.694 | 4453 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 20 | 0.694 | 1187 | cuda | omnidocbench_formula |
| layout | hantian/v11-s | AGPL-3.0 | layout | cpu | 20 | 0.429 | 145 | cpu | omnidocbench_layout |
| layout | hantian/v11-s | AGPL-3.0 | layout | gpu | 20 | 0.429 | 32 | cuda | omnidocbench_layout |
| layout | hantian/y26-s | AGPL-3.0 | layout | cpu | 20 | 0.471 | 128 | cpu | omnidocbench_layout |
| layout | hantian/y26-s | AGPL-3.0 | layout | gpu | 20 | 0.471 | 30 | cuda | omnidocbench_layout |
| layout | hantian/v12-s | AGPL-3.0 | layout | cpu | 20 | 0.494 | 197 | cpu | omnidocbench_layout |
| layout | hantian/v12-s | AGPL-3.0 | layout | gpu | 20 | 0.494 | 39 | cuda | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 20 | 0.497 | 1147 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 20 | 0.497 | 52 | cuda | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | cpu | 20 | 0.499 | 274 | cpu | omnidocbench_layout |
| layout | hantian/v10-m | AGPL-3.0 | layout | gpu | 20 | 0.499 | 43 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 20 | 0.508 | 84 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 20 | 0.508 | 29 | cuda | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 20 | 0.827 | 776 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | gpu | 20 | 0.827 | 434 | directml | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 20 | 0.843 | 1575 | cpu | omnidocbench_layout |
| orientation | pp-lcnet_x1_0_doc_ori (onnxruntime) | Apache-2.0 | orientation | cpu | 20 | 0.950 | 2 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | cpu | 20 | 0.950 | 1124 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | gpu | 20 | 0.950 | 55 | directml | synthetic_orientation |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | cpu | 20 | 0.707 | 261 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | gpu | 20 | 0.707 | 53 | directml | synthetic_rectification |
| rectification | uvdoc (onnxruntime) | Apache-2.0 | rectification | cpu | 20 | 0.707 | 74 | cpu | synthetic_rectification |
| text_line | pp-lcnet_x1_0_textline_ori (onnxruntime) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 5 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 26 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | gpu | 20 | 1.000 | 5 | directml | synthetic_text_line |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | cpu | 20 | 0.750 | 641 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | gpu | 20 | 0.750 | 120 | directml | synthetic_seal |
| table | table-transformer-structure-recognition |  | table | cpu | 20 | 0.699 | 140 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | cpu | 20 | 0.854 | 749 | cpu | omnidocbench_table |
| table | slanet_plus | Apache-2.0 | table | gpu | 20 | 0.854 | 668 | directml | omnidocbench_table |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 20 | 0.210 | 17198 | directml | omnidocbench_full_page |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 20 | 0.211 | 10033 | cpu | omnidocbench_full_page |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | cpu | 20 | 0.231 | 1547 | cpu | omnidocbench_full_page |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 19 | 0.242 | 10503 | directml | omnidocbench_full_page |