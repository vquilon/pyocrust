# Resumen global — features × modelo × licencia × device × tiempo × calidad

> Una fila por (feature, motor, device) con la **última** corrida medida.
> `license` es **informativa** (señala las no permisivas); la puerta solo aplica a los modelos de `pyocrust`.

| Feature | Motor | Licencia | Task | Device | n | Calidad | ms | Proveedor | Dataset |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| text | easyocr | Apache-2.0 | text | gpu | 20 | 0.399 | 1236 | cuda | funsd |
| text | easyocr | Apache-2.0 | text | cpu | 20 | 0.401 | 4600 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | cpu | 20 | 0.585 | 6748 | cpu | funsd |
| text | rapidocr | Apache-2.0 | text | gpu | 20 | 0.585 | 5696 | cuda | funsd |
| text | pyocrust | Apache-2.0 | text | cpu | 20 | 0.717 | 970 | cpu | funsd |

| formula | rapidocr | Apache-2.0 | formula | cpu | 5 | 0.104 | 3026 | cpu | omnidocbench_formula |
| formula | easyocr | Apache-2.0 | formula | cpu | 5 | 0.152 | 743 | cpu | omnidocbench_formula |
| formula | pyocrust_indra | OpenRAIL-M-Mod | formula | cpu | 5 | 0.184 | 196 | cpu | omnidocbench_formula |
| formula | pyocrust_formula | Apache-2.0 | formula | cpu | 20 | 0.196 | 3464 | cpu | omnidocbench_formula |
| formula | pix2tex | MIT | formula | cpu | 20 | 0.486 | 7484 | cpu | omnidocbench_formula |
| formula | pyocrust_formulanet | Apache-2.0 | formula | cpu | 20 | 0.497 | 979 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | cpu | 20 | 0.694 | 12490 | cpu | omnidocbench_formula |
| formula | paddle_latex_ocr | Apache-2.0 | formula | gpu | 20 | 0.694 | 1187 | cuda | omnidocbench_formula |

| layout | pyocrust_layout | Apache-2.0 | layout | cpu | 20 | 0.827 | 1987 | cpu | omnidocbench_layout |
| layout | docling_heron_101 | Apache-2.0 | layout | cpu | 20 | 0.843 | 1071 | cpu | omnidocbench_layout |

| orientation | lcnet_doc_ori |  | orientation | cpu | 20 | 0.950 | 2 | cpu | synthetic_orientation |
| orientation | pyocrust_orientation | Apache-2.0 | orientation | cpu | 20 | 0.950 | 1124 | cpu | synthetic_orientation |

| rectification | pyocrust_rectify | Apache-2.0 | rectification | cpu | 20 | 0.707 | 261 | cpu | synthetic_rectification |
| rectification | uvdoc |  | rectification | cpu | 20 | 0.707 | 74 | cpu | synthetic_rectification |

| text_line | lcnet_textline_ori |  | text_line | cpu | 20 | 1.000 | 5 | cpu | synthetic_text_line |
| text_line | pyocrust_textline | Apache-2.0 | text_line | cpu | 20 | 1.000 | 26 | cpu | synthetic_text_line |

| seal | pyocrust_seal | Apache-2.0 | seal | cpu | 20 | 0.750 | 641 | cpu | synthetic_seal |

| table | tatr | MIT | table | cpu | 20 | 0.699 | 140 | cpu | omnidocbench_table |
| table | pyocrust_table | Apache-2.0 | table | cpu | 20 | 0.854 | 749 | cpu | omnidocbench_table |

| full_page | pyocrust_structure | Apache-2.0 | structure | cpu | 20 | 0.211 | 10033 | cpu | omnidocbench_full_page |
| full_page | pyocrust_indra | OpenRAIL-M-Mod | full_page | cpu | 20 | 0.231 | 1547 | cpu | omnidocbench_full_page |
