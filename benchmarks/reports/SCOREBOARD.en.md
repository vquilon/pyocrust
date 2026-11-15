# Global scoreboard — features × model × license × device × time × quality

> One row per (feature, engine, device), using the **latest** measured run.
> `license` is **informational** (flags non-permissive licenses); the gate applies only to `pyocrust` models.

| Feature | Engine | License | Task | Device | n | Quality | ms | Provider | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | gpu | 20 | 0.399 | 1263 | cuda | funsd |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 3167 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 4286 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | gpu | 20 | 0.585 | 5842 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | gpu | 20 | 0.684 | 330 | cuda | funsd |
| text | pp_ocrv6 (tiny) | Apache-2.0 | text | cpu | 20 | 0.717 | 336 | cpu | funsd |
| text | pp_ocrv6 (small) | Apache-2.0 | text | cpu | 20 | 0.784 | 866 | cpu | funsd |
| text | PP-OCRv6 (medium) | Apache-2.0 | text | cpu | 20 | 0.796 | 19163 | cpu | funsd |
| text | pp_ocrv6 (medium) | Apache-2.0 | text | cpu | 20 | 0.800 | 2223 | cpu | funsd |
| formula | unimernet (tiny) | Apache-2.0 | formula | cpu | 10 | 0.260 | 17493 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | cpu | 10 | 0.326 | 141 | cpu | omnidocbench_formula |
| formula | indra (math) | OpenRAIL-M-Mod | formula | gpu | 10 | 0.326 | 808 | cuda | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | cpu | 10 | 0.398 | 2774 | cpu | omnidocbench_formula |
| formula | pp_structurev3 | Apache-2.0 | formula | gpu | 10 | 0.398 | 2553 | cuda | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | cpu | 10 | 0.497 | 2474 | cpu | omnidocbench_formula |
| formula | pp_structurev3 (pp-formulanet-s) | Apache-2.0 | formula | gpu | 10 | 0.497 | 2221 | cuda | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | cpu | 10 | 0.499 | 998 | cpu | omnidocbench_formula |
| formula | pp-formulanet-s (direct) | Apache-2.0 | formula | gpu | 10 | 0.499 | 1603 | cuda | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 10 | 0.552 | 5500 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 10 | 0.653 | 16326 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 10 | 0.653 | 4191 | cuda | omnidocbench_formula |
| layout | hantian/v8-x | AGPL-3.0 | layout | cpu | 40 | 0.490 | 1025 | cpu | omnidocbench_layout |
| layout | hantian/v8-x | AGPL-3.0 | layout | gpu | 40 | 0.490 | 47 | cuda | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | cpu | 40 | 0.533 | 569 | cpu | omnidocbench_layout |
| layout | hantian/v10-l | AGPL-3.0 | layout | gpu | 40 | 0.533 | 36 | cuda | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | cpu | 40 | 0.542 | 365 | cpu | omnidocbench_layout |
| layout | armaggheddon/y11-m | MIT | layout | gpu | 40 | 0.542 | 42 | cuda | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | cpu | 40 | 0.545 | 68 | cpu | omnidocbench_layout |
| layout | hantian/v8-n | AGPL-3.0 | layout | gpu | 40 | 0.545 | 25 | cuda | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | cpu | 40 | 0.550 | 711 | cpu | omnidocbench_layout |
| layout | hantian/v12-l | AGPL-3.0 | layout | gpu | 40 | 0.550 | 53 | cuda | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | cpu | 40 | 0.572 | 69 | cpu | omnidocbench_layout |
| layout | armaggheddon/y26-n (2.6M) | MIT | layout | gpu | 40 | 0.572 | 29 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | gpu | 40 | 0.751 | 2938 | cuda | omnidocbench_layout |
| layout | pp_structurev3 | Apache-2.0 | structure | cpu | 40 | 0.751 | 7111 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | cpu | 40 | 0.796 | 2219 | cpu | omnidocbench_layout |
| layout | pp-doclayoutv3 (130M) | Apache-2.0 | layout | gpu | 40 | 0.796 | 488 | cuda | omnidocbench_layout |
| layout | docling-layout-heron-101 |  | layout | cpu | 40 | 0.818 | 1005 | cpu | omnidocbench_layout |
| orientation | craft_mlt_25k+latin_g2 (easyocr) | Apache-2.0 | orientation | cpu | 20 | 0.350 | 42794 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | cpu | 20 | 1.000 | 1448 | cpu | synthetic_orientation |
| orientation | pp-lcnet_x1_0_doc_ori (6.8M) | Apache-2.0 | orientation | gpu | 20 | 1.000 | 192 | cuda | synthetic_orientation |
| rectification | perspective-4corner (baseline (OpenCV, sin pesos)) | Apache-2.0 | rectification | cpu | 20 | 0.491 | 11 | cpu | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | gpu | 20 | 0.590 | 33 | cuda | synthetic_rectification |
| rectification | uvdoc (31.7M) | Apache-2.0 | rectification | cpu | 20 | 0.597 | 297 | cpu | synthetic_rectification |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | cpu | 20 | 1.000 | 26 | cpu | synthetic_text_line |
| text_line | pp-lcnet_x1_0_textline_ori (6.8M) | Apache-2.0 | text_line | gpu | 20 | 1.000 | 152 | cuda | synthetic_text_line |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | cpu | 20 | 0.750 | 643 | cpu | synthetic_seal |
| seal | pp-ocrv4_mobile_seal_det (4.8M) | Apache-2.0 | seal | gpu | 20 | 0.750 | 178 | cuda | synthetic_seal |
| table | table-transformer-structure-recognition | MIT | table | cpu | 8 | 0.790 | 703 | cpu | omnidocbench_table |
| table | slanet_plus (7.8M) | Apache-2.0 | table | cpu | 8 | 0.868 | 47 | cpu | omnidocbench_table |
| table | slanet_plus (7.8M) | Apache-2.0 | table | gpu | 8 | 0.868 | 474 | cuda | omnidocbench_table |
| table | tableformer (docling) | MIT | table | cpu | 8 | 0.905 | 20362 | cpu | omnidocbench_table |
| table | slanext_wired (367M) | Apache-2.0 | table | cpu | 8 | 0.914 | 500 | cpu | omnidocbench_table |
| table | slanext_wired (367M) | Apache-2.0 | table | gpu | 8 | 0.914 | 190 | cuda | omnidocbench_table |
| full_page | PP-StructureV3 (paddleocr) | Apache-2.0 | full_page | cpu | 6 | 0.427 | 180058 | cpu | omnidocbench_full_page_en |
| full_page | PP-StructureV3 (paddleocr) | Apache-2.0 | full_page | gpu | 6 | 0.496 | 68269 | cuda | omnidocbench_full_page_en |
| full_page | docling-default (pipeline) | MIT | full_page | cpu | 6 | 0.512 | 26739 | cpu | omnidocbench_full_page_en |
| full_page | docling-default (pipeline) | MIT | full_page | gpu | 6 | 0.512 | 22740 | cuda | omnidocbench_full_page_en |
| full_page | pp_structurev3 | Apache-2.0 | structure | gpu | 6 | 0.528 | 4350 | cuda | omnidocbench_full_page_en |
| full_page | pp_structurev3 | Apache-2.0 | structure | cpu | 6 | 0.530 | 3652 | cpu | omnidocbench_full_page_en |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | cpu | 6 | 0.556 | 1251 | cpu | omnidocbench_full_page_en |
| full_page | indra (math) | OpenRAIL-M-Mod | full_page | gpu | 6 | 0.556 | 1793 | cuda | omnidocbench_full_page_en |
| full_page | GLM-OCR (0.9B) | MIT | full_page | gpu | 6 | 0.559 | 30716 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-2-1B (1B) | Apache-2.0 | full_page | gpu | 6 | 0.588 | 44737 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-3 (4B) | Apache-2.0 | full_page | gpu | 6 | 0.590 | 72249 | cuda | omnidocbench_full_page_en |
| full_page | PaddleOCR-VL (0.9B) | Apache-2.0 | full_page | gpu | 6 | 0.597 | 60907 | cuda | omnidocbench_full_page_en |
| full_page | LightOnOCR-3 (0.8B) | Apache-2.0 | full_page | gpu | 6 | 0.625 | 320707 | cuda | omnidocbench_full_page_en |