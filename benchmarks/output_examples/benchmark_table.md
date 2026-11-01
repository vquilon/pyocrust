| Backend | n | F1 Markdown ↑ | F1 bloques ↑ | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|---|---|
| easyocr (default; text) | 10 | N/A | N/A | 0.344 | 0.745 | 0.527 | 0.819 | _9356_ | _0.11_ |
| pyocrust (tiny; text) | 10 | N/A | N/A | **0.694** | **0.392** | 0.470 | 0.685 | **751** | **1.33** |
| pyocrust_formula (pp-formulanet-s; formula) | 10 | N/A | N/A | 0.000 | 1.000 | 1.000 | 1.000 | 3133 | 0.32 |
| pyocrust_indra (math; full_page) | 10 | N/A | N/A | 0.444 | 0.658 | 1.560 | 0.824 | 310 | 3.22 |
| pyocrust_structure (default; structure) | 10 | N/A | N/A | 0.471 | 0.622 | 1.131 | 0.823 | 2643 | 0.38 |
| rapidocr (default; text) | 10 | N/A | N/A | _0.590_ | _0.502_ | 0.463 | 0.699 | 9472 | 0.11 |

> `F1 palabra` y `CER/WER ord.` neutralizan el orden de lectura: miden reconocimiento. `CER`/`WER` crudos miden también la disposición de la página y llevan la marca solo informativa.
