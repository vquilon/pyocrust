# Resumen global — features × modelo × licencia × device × tiempo × calidad

> Una fila por (feature, motor, device) con la **última** corrida medida.
> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.

| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | gpu | 20 | 0.399 | 1660 | cuda | funsd |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 3662 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 4807 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | gpu | 20 | 0.585 | 4498 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | gpu | 20 | 0.684 | 419 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | cpu | 20 | 0.717 | 318 | cpu | funsd |
| text | pp_ocrv6 (small) | Apache-2.0 | text | gpu | 20 | 0.767 | 1012 | cuda | funsd |
| text | pp_ocrv6 (medium) | Apache-2.0 | text | gpu | 20 | 0.779 | 2258 | cuda | funsd |
| text | pp_ocrv6 (small) | Apache-2.0 | text | cpu | 20 | 0.784 | 823 | cpu | funsd |
| text | PP-OCRv6 (medium) | Apache-2.0 | text | cpu | 20 | 0.796 | 19811 | cpu | funsd |
| text | PP-OCRv6 (medium) | Apache-2.0 | text | gpu | 20 | 0.796 | 487 | cuda | funsd |
| text | pp_ocrv6 (medium) | Apache-2.0 | text | cpu | 20 | 0.800 | 2138 | cpu | funsd |
| formula | unimernet (tiny) | Apache-2.0 | formula | cpu | 10 | 0.260 | 14927 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 10 | 0.326 | 82 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 10 | 0.326 | 708 | cuda | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | cpu | 10 | 0.398 | 1028 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | gpu | 10 | 0.398 | 2095 | cuda | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 10 | 0.497 | 1052 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 10 | 0.497 | 2031 | cuda | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 10 | 0.499 | 696 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 10 | 0.499 | 1385 | cuda | omnidocbench_formula |
| formula | LightOnOCR-3 (0.8B) | Apache-2.0 | formula | gpu | 10 | 0.550 | 24073 | cuda | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 10 | 0.555 | 4659 | cpu | omnidocbench_formula |
| formula | pix2tex | MIT | formula | gpu | 10 | 0.566 | 1182 | cuda | omnidocbench_formula |
| formula | LightOnOCR-2-1B (1B) | Apache-2.0 | formula | gpu | 10 | 0.597 | 20186 | cuda | omnidocbench_formula |
| formula | LightOnOCR-3 (4B) | Apache-2.0 | formula | gpu | 10 | 0.612 | 30950 | cuda | omnidocbench_formula |
| formula | PaddleOCR-VL (0.9B) | Apache-2.0 | formula | gpu | 10 | 0.614 | 17524 | cuda | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 10 | 0.653 | 11331 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 10 | 0.653 | 3322 | cuda | omnidocbench_formula |
| formula | GLM-OCR (0.9B) | MIT | formula | gpu | 10 | 0.748 | 18719 | cuda | omnidocbench_formula |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 40 | 0.490 | 1128 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 40 | 0.490 | 55 | cuda | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | cpu | 40 | 0.533 | 585 | cpu | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | gpu | 40 | 0.533 | 47 | cuda | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | cpu | 40 | 0.542 | 367 | cpu | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | gpu | 40 | 0.542 | 45 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 40 | 0.545 | 68 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 40 | 0.545 | 29 | cuda | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | cpu | 40 | 0.550 | 623 | cpu | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | gpu | 40 | 0.550 | 71 | cuda | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | cpu | 40 | 0.572 | 62 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | gpu | 40 | 0.572 | 33 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | gpu | 40 | 0.751 | 3201 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | cpu | 40 | 0.751 | 2926 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 40 | 0.796 | 505 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | gpu | 40 | 0.796 | 883 | cuda | omnidocbench_layout |
| layout | docling-layout-egret-xlarge | MIT | layout | gpu | 40 | 0.817 | 77 | cuda | omnidocbench_layout |
| layout | docling-layout-egret-xlarge | MIT | layout | cpu | 40 | 0.818 | 688 | cpu | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 40 | 0.818 | 999 | cpu | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | gpu | 40 | 0.818 | 71 | cuda | omnidocbench_layout |
| orientation | craft_mlt_25k+latin_g2 (easyocr) | Apache-2.0 | orientation | cpu | 20 | 0.350 | 43311 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 60 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | gpu | 20 | 1.000 | 298 | cuda | synthetic_orientation |
| rectification | perspective-4corner (baseline (OpenCV, sin pesos)) | Apache-2.0 | rectification | cpu | 20 | 0.473 | 9 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | gpu | 20 | 0.590 | 34 | cuda | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | cpu | 20 | 0.590 | 71 | cpu | synthetic_rectification |
| text_line | ch_ppocr_mobile_v2.0_cls (rapidocr) | Apache-2.0 | text_line | cpu | 20 | 0.900 | 3 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 3 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | gpu | 20 | 1.000 | 205 | cuda | synthetic_text_line |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | cpu | 20 | 0.750 | 643 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | gpu | 20 | 0.750 | 287 | cuda | synthetic_seal |
| table | pp_structurev3 | Apache-2.0 | table | cpu | 8 | 0.753 | 1128 | cpu | omnidocbench_table |
| table | pp_structurev3 | Apache-2.0 | table | gpu | 8 | 0.753 | 2214 | cuda | omnidocbench_table |
| table | table-transformer-structure-recognition | MIT | table | cpu | 8 | 0.790 | 718 | cpu | omnidocbench_table |
| table | table-transformer-structure-recognition | MIT | table | gpu | 8 | 0.790 | 47 | cuda | omnidocbench_table |
| table | LightOnOCR-3 (4B) | Apache-2.0 | table | gpu | 8 | 0.847 | 76940 | cuda | omnidocbench_table |
| table | LightOnOCR-2-1B (1B) | Apache-2.0 | table | gpu | 8 | 0.858 | 58834 | cuda | omnidocbench_table |
| table | slanet_plus (7.8M) | Apache-2.0 | table | cpu | 8 | 0.868 | 52 | cpu | omnidocbench_table |
| table | slanet_plus (7.8M) | Apache-2.0 | table | gpu | 8 | 0.868 | 484 | cuda | omnidocbench_table |
| table | tableformer (docling) | MIT | table | cpu | 8 | 0.905 | 27457 | cpu | omnidocbench_table |
| table | tableformer (docling) | MIT | table | gpu | 8 | 0.905 | 19140 | cuda | omnidocbench_table |
| table | slanext_wired (367M) | Apache-2.0 | table | cpu | 8 | 0.914 | 577 | cpu | omnidocbench_table |
| table | slanext_wired (367M) | Apache-2.0 | table | gpu | 8 | 0.914 | 202 | cuda | omnidocbench_table |
| table | GLM-OCR (0.9B) | MIT | table | gpu | 8 | 0.919 | 34191 | cuda | omnidocbench_table |
| table | LightOnOCR-3 (0.8B) | Apache-2.0 | table | gpu | 8 | 0.926 | 162056 | cuda | omnidocbench_table |
| table | PaddleOCR-VL (0.9B) | Apache-2.0 | table | gpu | 8 | 0.933 | 35839 | cuda | omnidocbench_table |
| full_page | PP-StructureV3 (paddleocr) | Apache-2.0 | full_page | cpu | 6 | 0.427 | 180058 | cpu | omnidocbench_full_page_en |
| full_page | PP-StructureV3 (paddleocr) | Apache-2.0 | full_page | gpu | 6 | 0.496 | 68269 | cuda | omnidocbench_full_page_en |
| full_page | docling-default (pipeline) | MIT | full_page | cpu | 6 | 0.512 | 26739 | cpu | omnidocbench_full_page_en |
| full_page | docling-default (pipeline) | MIT | full_page | gpu | 6 | 0.512 | 22740 | cuda | omnidocbench_full_page_en |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 6 | 0.528 | 4350 | cuda | omnidocbench_full_page_en |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 6 | 0.530 | 3652 | cpu | omnidocbench_full_page_en |
| full_page | pyocrust (vl) | Apache-2.0 | full_page | cpu | 6 | 0.534 | 141693 | cpu | omnidocbench_full_page_en |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | cpu | 6 | 0.556 | 1251 | cpu | omnidocbench_full_page_en |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 6 | 0.556 | 1793 | cuda | omnidocbench_full_page_en |
| full_page | GLM-OCR (0.9B) | MIT | full_page | gpu | 6 | 0.559 | 30716 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-2-1B (1B) | Apache-2.0 | full_page | gpu | 6 | 0.588 | 44737 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-3 (4B) | Apache-2.0 | full_page | gpu | 6 | 0.590 | 72249 | cuda | omnidocbench_full_page_en |
| full_page | PaddleOCR-VL (0.9B) | Apache-2.0 | full_page | gpu | 6 | 0.597 | 60907 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-3 (0.8B) | Apache-2.0 | full_page | gpu | 6 | 0.625 | 320707 | cuda | omnidocbench_full_page_en |