| Backend | n | F1 Markdown ↑ | F1 bloques ↑ | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|---|---|
| easyocr (default; text) | 25 | N/A | N/A | _0.261_ | 1.685 | 1.059 | 1.721 | 10937 | 0.09 |
| pyocrust (tiny; text) | 25 | N/A | N/A | **0.274** | _1.661_ | 1.041 | 1.698 | **1551** | **0.64** |
| pyocrust_formula (pp-formulanet-s; formula) | 25 | N/A | N/A | 0.004 | 2.527 | 1.876 | 2.527 | 8681 | 0.12 |
| pyocrust_indra (math; full_page) | 25 | N/A | N/A | 0.259 | 2.945 | 3.443 | 3.001 | 1045 | 0.96 |
| pyocrust_structure (default; structure) | 25 | N/A | N/A | 0.216 | 3.608 | 7.196 | 3.647 | 8288 | 0.12 |
| rapidocr (default; text) | 25 | N/A | N/A | 0.251 | **1.380** | 0.966 | 1.420 | _8445_ | _0.12_ |

> `F1 palabra` y `CER/WER ord.` neutralizan el orden de lectura: miden reconocimiento. `CER`/`WER` crudos miden también la disposición de la página y llevan la marca solo informativa.
