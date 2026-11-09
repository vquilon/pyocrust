# Comparativa de OCR de fórmulas — `pyocrust` vs otros motores (métrica normalizada)

> **Histórico (pre-estratificado).** Reporte legado de `report_formula.py` para la
> run `2026-11-01_22-14-47` (n=50), cuya carpeta ya no está en `results/`. La run
> de referencia vigente es `reports/formula/REPORT.md` (`2026-11-09_14-13-57`,
> n=10, muestra estratificada). Este fichero no se regenera con la cadena de informes.

Run `benchmarks/results/2026-11-01_22-14-47`. Dataset **`omnidocbench_formula`**: `opendatalab/OmniDocBench` v1.6, **una muestra por fórmula** (bloque `equation_isolated`): el adaptador recibe el **recorte** de la fórmula y el GT es el **LaTeX anotado** de ese bloque (sin los `$` de delimitador). Entrada idéntica (mismo recorte PNG) para todos los motores; un motor a la vez, CPU, `warmup=1`, `repeats=1`.

| Motor (variante; tarea) | n | LaTeX exacto ↑ | LaTeX exacto norm. ↑ | Similitud ↑ | Similitud norm. ↑ | F1 tokens LaTeX ↑ | Levenshtein norm. ↓ | Salidas con LaTeX ↑ | ms/fórmula ↓ | p95 ms ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default; formula) | 50 | 0.000 | 0.000 | 0.216 | 0.222 | 0.454 | 0.784 | 0% | 781 | 2430 |
| pyocrust (tiny; formula) | 50 | 0.000 | 0.000 | 0.194 | 0.226 | 0.466 | 0.806 | 0% | **70** | **188** |
| pyocrust_formula (pp-formulanet-s; formula) | 50 | 0.000 | 0.000 | 0.107 | 0.128 | 0.182 | 0.893 | 28% | 2139 | 3624 |
| pyocrust_formulanet (direct; formula) | 50 | 0.000 | 0.000 | 0.395 | 0.534 | 0.679 | 0.605 | 86% | 754 | 1898 |
| pyocrust_formulanet_l (direct; formula) | 50 | 0.000 | **0.020** | 0.428 | **0.593** | **0.763** | 0.572 | 94% | 5874 | 15994 |
| pyocrust_formulanet_pluss (direct; formula) | 50 | 0.000 | 0.000 | **0.458** | 0.587 | 0.746 | **0.542** | **94%** | 592 | 1583 |
| pyocrust_indra (math; formula) | 50 | 0.000 | 0.000 | 0.240 | 0.275 | 0.514 | 0.760 | 48% | 128 | 305 |
| rapidocr (default; formula) | 50 | 0.000 | 0.000 | 0.119 | 0.135 | 0.307 | 0.881 | 0% | 2320 | 4636 |

> **Dos familias de métrica.** Las columnas *sin* `norm.` puntúan el texto LaTeX tal cual; las `norm.` puntúan la **forma canónica** (`latex_metrics.py`: espaciado, `\left`/`\right`, `array`→`matrix`, `\lbrack`→`[`, alias de comandos). `LaTeX exacto` exige coincidencia carácter a carácter del LaTeX normalizado (0 en todos). `Similitud = 1 - Levenshtein/max(|GT|,|pred|)`. `Salidas con LaTeX` es la fracción de salidas (`<backend>.outputs.json`) que contienen algún comando LaTeX (`\palabra`).

## Lectura honesta

* **Ningún motor reproduce el LaTeX anotado exactamente**: `LaTeX exacto = 0.000` sobre 50 fórmulas en los 8 motores.
* **La normalización sube la similitud pero NO cierra el `exacto`**: en `pyocrust_formulanet` la `Similitud` pasa de 0.395 (cruda) a 0.534 (norm.) y el `F1 tokens` es 0.679, pero `LaTeX exacto norm.` sigue en 0.000. La brecha que queda es real, no solo de espaciado: el modelo emite comandos de **fuente** (`\mathcal`, `\mathbf`), **agrupa** con llaves de más (`{a}_{11}`) y a veces añade **columnas vacías** de más en el `matrix`. La métrica normalizada mide eso, no lo esconde.
* **Solo los motores de fórmulas de `pyocrust` producen LaTeX**: `Salidas con LaTeX` = `pyocrust_formulanet_pluss` 94%, `pyocrust_formulanet_l` 94%, `pyocrust_formulanet` 86%, `pyocrust_indra` 48%, `pyocrust_formula` 28%, frente a `pyocrust` 0%, `rapidocr` 0%, `easyocr` 0% de los OCR de texto, que devuelven los símbolos sueltos y no LaTeX.
* **`pyocrust_indra` matiza**: su 48% de salidas con LaTeX son **símbolos inline** (`$x_{2}$`) dentro de tablas HTML; no emite entornos de bloque (`\begin{}` = 0%), así que no produce LaTeX de fórmula.
* **El cuello de botella es el detector de layout, no el modelo**: `pyocrust_formula` (pp_structurev3 completo sobre el recorte) devuelve **salida vacía en 33/50** recortes (66%); `pyocrust_formulanet` (PP-FormulaNet-S directo, sin layout) no deja ninguna vacía (0/50) y reconoce mejor (F1 tokens 0.679 vs 0.182).
* **Velocidad**: entre los motores que emiten LaTeX de fórmula, `pyocrust_formulanet_pluss` es el más rápido (592 ms/fórmula), ~9.9× que `pyocrust_formulanet_l` (5874 ms). Un modelo a la vez, CPU.

## Comparativa de variantes PP-FormulaNet

Todas comparten `FormulaModelKind::PPFormulaNet` en oar-ocr: el adaptador de `formula_recognition` es el mismo y solo cambia el `.onnx` (registro ModelScope `greatv/oar-ocr`). Aísla el tamaño/entrenamiento del modelo, no el pipeline. Calidad sobre la **forma canónica**:

| Variante (`.onnx`) | n | LaTeX exacto norm. ↑ | Similitud norm. ↑ | F1 tokens LaTeX ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `pyocrust_formulanet` | 50 | 0.000 | 0.534 | 0.679 | 86% | 754 |
| `pyocrust_formulanet_l` | 50 | 0.020 | 0.593 | 0.763 | 94% | 5874 |
| `pyocrust_formulanet_pluss` | 50 | 0.000 | 0.587 | 0.746 | 94% | 592 |

* **Variantes**: mejor `F1 tokens` = `pyocrust_formulanet_l` (0.763); más rápida = `pyocrust_formulanet_pluss` (592 ms/fórmula). Un modelo a la vez, CPU.

## Referencia externa: el benchmark de `oar-ocr` solo mide **tiempos**

El repo original `GreatV/oar-ocr` trae `oar-bench` (crate no publicado `oar-ocr-bench`, doc. en `docs/benchmarking.md`). Mide el pipeline completo por página — `load_ms`, `latency_ms` (media/p50/p95), `pages_per_second`, `output_chars_per_second` (solo VL), `host_peak_bytes` y picos de GPU con NVML — y **compara dos runs** con un umbral de regresión en latencia/throughput.

**No calcula ninguna métrica de calidad.** El propio `docs/benchmarking.md` delega la precisión en herramientas **externas**: `run --save-outputs predictions` y luego el scorer oficial de **OmniDocBench** (`pdf_validation.py`) o de **olmOCR** (`olmocr.bench`). Es decir, `oar-ocr` —y con él el backend de `pyocrust`— **no publica** comparativa de calidad de fórmulas: las columnas `LaTeX exacto norm.`, `Similitud norm.` y `F1 tokens LaTeX` de este reporte son métrica **nuestra**, medida sobre el GT de OmniDocBench.

## Limitaciones

* La unidad es el **recorte** del bloque `equation_isolated` (`poly` anotado, +4 px de margen). No mide el pipeline a nivel de página ni la detección de la fórmula en la página.
* El GT es el **LaTeX anotado** del bloque. Su notación (`array`, `\left\lbrack`) no coincide con la del modelo, así que `LaTeX exacto = 0` no significa «no reconoce».
* La métrica **normalizada NO es equivalencia matemática**: unifica notación (espaciado, `array`/`matrix`, `\left[`/`[`, alias) y compara tokens, pero no evalúa la expresión con un CAS. Las diferencias de **fuente** (`\mathcal`, `\mathbf`) y de **agrupación de llaves** se conservan a propósito (cambian el significado); por eso `LaTeX exacto norm.` queda por debajo de `Similitud norm.`.
* Una sola run, `repeats=1`, **CPU**: los ms no llevan intervalo de confianza y `provider_effective = unverified` (no se instrumenta el provider real).

**Skipped** (modelo/entorno ausente, no un OCR malo):
* `tesseract` — pip install pytesseract + binario Tesseract

