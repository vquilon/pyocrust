| Backend | n | F1 Markdown ↑ | F1 bloques ↑ | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|---|---|
| easyocr (default; formula) | 100 | N/A | N/A | 0.111 | 0.994 | 0.784 | 0.991 | 1080 | 0.93 |
| easyocr (default; text) | 35 | N/A | N/A | 0.284 | 1.417 | 0.907 | 1.463 | 10485 | 0.10 |
| easyocr (legacy; text) | 59 | N/A | N/A | 0.427 | 0.670 | 0.525 | 0.793 | 5732 | 0.17 |
| pyocrust (legacy; text) | 115 | N/A | N/A | **0.730** | **0.325** | 0.477 | 0.670 | **691** | **1.45** |
| pyocrust (tiny; formula) | 100 | N/A | N/A | 0.060 | 1.035 | 0.806 | 1.043 | **75** | **13.35** |
| pyocrust (tiny; text) | 75 | N/A | N/A | 0.569 | 0.796 | 0.646 | 1.008 | _1232_ | _0.81_ |
| pyocrust_formula (pp-formulanet-s; formula) | 146 | N/A | N/A | 0.003 | 2.341 | 1.319 | 2.341 | 3659 | 0.27 |
| pyocrust_formulanet (direct; formula) | 100 | N/A | N/A | 0.018 | 2.103 | 1.246 | 2.103 | 752 | 1.33 |
| pyocrust_formulanet_l (direct; formula) | 50 | N/A | N/A | 0.009 | 0.993 | 2.862 | 0.993 | 5874 | 0.17 |
| pyocrust_formulanet_pluss (direct; formula) | 50 | N/A | N/A | 0.010 | 2.505 | 1.002 | 2.506 | 592 | 1.69 |
| pyocrust_indra (math; formula) | 100 | N/A | N/A | 0.070 | 1.631 | 0.834 | 1.632 | _130_ | _7.72_ |
| pyocrust_indra (math; full_page) | 51 | N/A | N/A | 0.364 | 1.768 | 2.462 | 1.888 | 898 | 1.11 |
| pyocrust_structure (default; structure) | 46 | N/A | N/A | 0.341 | 2.235 | 4.402 | 2.355 | 6634 | 0.15 |
| rapidocr (default; formula) | 100 | N/A | N/A | 0.027 | 1.021 | 0.881 | 1.022 | 2441 | 0.41 |
| rapidocr (default; text) | 52 | N/A | N/A | 0.452 | 0.898 | 0.688 | 1.032 | 10064 | 0.10 |
| rapidocr (legacy; text) | 115 | N/A | N/A | _0.598_ | _0.487_ | 0.471 | 0.695 | 5914 | 0.17 |

> `F1 palabra` y `CER/WER ord.` neutralizan el orden de lectura: miden reconocimiento. `CER`/`WER` crudos miden también la disposición de la página y llevan la marca solo informativa.
