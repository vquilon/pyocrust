# Comparativa de OCR de fórmulas — `pyocrust` (pp-formulanet-s) vs otros motores

Run `benchmarks/results/2026-11-01_16-08-20`. Dataset **`omnidocbench_formula`**: `opendatalab/OmniDocBench` v1.6, **una muestra por fórmula** (bloque `equation_isolated`): el adaptador recibe el **recorte** de la fórmula y el GT es el **LaTeX anotado** de ese bloque (sin los `$` de delimitador). Entrada idéntica (mismo recorte PNG) para todos los motores; un motor a la vez, CPU, `warmup=1`, `repeats=1`.

| Motor (variante; tarea) | n | LaTeX exacto ↑ | Similitud ↑ | Levenshtein norm. ↓ | Salidas con LaTeX ↑ | ms/fórmula ↓ | p95 ms ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default; formula) | 50 | 0.000 | 0.216 | 0.784 | 0% | 1379 | 3910 |
| pyocrust (tiny; formula) | 50 | 0.000 | 0.194 | 0.806 | 0% | **80** | **224** |
| pyocrust_formula (pp-formulanet-s; formula) | 50 | 0.000 | 0.107 | 0.893 | 28% | 2189 | 3856 |
| pyocrust_formulanet (direct; formula) | 50 | 0.000 | **0.395** | **0.605** | **86%** | 749 | 1844 |
| pyocrust_indra (math; formula) | 50 | 0.000 | 0.240 | 0.760 | 48% | 131 | 340 |
| rapidocr (default; formula) | 50 | 0.000 | 0.119 | 0.881 | 0% | 2562 | 5037 |

> `LaTeX exacto` exige coincidencia carácter a carácter del LaTeX normalizado (0 en todos: la notación del dataset —`\begin{array}`, `\left\lbrack`— no coincide con la del modelo). `Similitud = 1 - Levenshtein/max(|GT|,|pred|)`. `Salidas con LaTeX` es la fracción de salidas (medida sobre `<backend>.outputs.json`) que contienen algún comando LaTeX (`\palabra`): separa un motor que **emite LaTeX** de uno que solo repite los símbolos como texto.

## Lectura honesta

* **Ningún motor reproduce el LaTeX anotado exactamente**: `LaTeX exacto = 0.000` sobre 50 fórmulas en los 6 motores.
* **Solo los motores de fórmulas de `pyocrust` producen LaTeX**: `Salidas con LaTeX` = `pyocrust_formulanet` 86%, `pyocrust_indra` 48%, `pyocrust_formula` 28%, frente a `pyocrust` 0%, `rapidocr` 0%, `easyocr` 0% de los OCR de texto, que devuelven los símbolos sueltos y no LaTeX.
* **`pyocrust_indra` matiza**: su 48% de salidas con LaTeX son **símbolos inline** (`$x_{2}$`) dentro de tablas HTML; no emite entornos de bloque (`\begin{}` = 0%), así que no produce LaTeX de fórmula.
* **El cuello de botella es el detector de layout, no el modelo**: `pyocrust_formula` (pp_structurev3 completo sobre el recorte) devuelve **salida vacía en 33/50** recortes (66%); `pyocrust_formulanet` (PP-FormulaNet-S directo, sin layout) no deja ninguna vacía (0/50) y reconoce mejor (Similitud 0.395 vs 0.107).
* **Velocidad**: entre los motores que emiten LaTeX de fórmula, `pyocrust_formulanet` es el más rápido (749 ms/fórmula), ~2.9× que `pyocrust_formula` (2189 ms, el pipeline completo). Un modelo a la vez, CPU.
* **La `Similitud` de caracteres no mide corrección matemática**: el motor de fórmulas emite LaTeX verboso (`\begin{matrix}` frente a `\begin{array}`, llaves de agrupación) y comparte con el GT la estructura, no los comandos exactos. Se reporta como se pidió; `Salidas con LaTeX` es la columna que sí separa quién produce LaTeX de quién no.

## Limitaciones

* La unidad es el **recorte** del bloque `equation_isolated` (`poly` anotado, +4 px de margen). No mide el pipeline a nivel de página ni la detección de la fórmula en la página.
* El GT es el **LaTeX anotado** del bloque. Su notación (`array`, `\left\lbrack`) no coincide con la del modelo, así que `LaTeX exacto = 0` no significa «no reconoce».
* Una sola run, `repeats=1`, **CPU**: los ms no llevan intervalo de confianza y `provider_effective = unverified` (no se instrumenta el provider real).
* No hay métrica **semántica** (equivalencia matemática), solo superficial sobre el texto; un LaTeX distinto pero equivalente puntúa como error.

**Skipped** (modelo/entorno ausente, no un OCR malo):
* `tesseract` — pip install pytesseract + binario Tesseract

