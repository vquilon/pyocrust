| Backend | n | F1 Markdown ↑ | F1 bloques ↑ | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. | págs/s |
|---|---|---|---|---|---|---|---|---|---|
| pyocrust (tiny; text) | 5 | N/A | N/A | **0.734** | **0.340** | 0.402 | 0.628 | **1290** | **0.78** |
| pyocrust_indra (math; full_page) | 5 | N/A | N/A | 0.457 | 0.648 | 1.552 | 0.815 | 644 | 1.55 |
| rapidocr (default; text) | 5 | N/A | N/A | _0.660_ | _0.431_ | 0.400 | 0.654 | _9355_ | _0.11_ |

> `F1 palabra` y `CER/WER ord.` neutralizan el orden de lectura: miden reconocimiento. `CER`/`WER` crudos miden también la disposición de la página y llevan la marca solo informativa.
