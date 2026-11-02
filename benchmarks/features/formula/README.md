# Feature `formula` — banco de benchmark (implementado)

> Origen de los números. Todo valor numérico producido por este banco es
> **`medido`** (ejecutado por nosotros; ver el `summary.json` de la run). Las
> **`referencia`** de este README son **URLs de software**, no cifras de terceros:
> no se copia ninguna métrica externa, por eso no necesita tabla comparativa ajena.

## Qué mide

Fórmula (imagen) → **LaTeX**. La crítica del usuario es explícita: **easyocr y
rapidocr no tienen modelo de fórmulas→LaTeX**, así que este banco **no** se
compara contra OCR de texto como si fueran alternativas del ranking. La unidad es
**cada fórmula anotada**: el bloque `equation_isolated` de OmniDocBench
(recorte por su `poly` + 4 px de margen) y el GT es su **LaTeX anotado** (sin los
`$` de delimitador). Misma entrada PNG para todos los motores.

## Tarea `pyocrust`

`formula_recognition` (`TaskPredictor`, PP-FormulaNet) **directo** sobre el
recorte, y el pipeline completo (`pp_structurev3` + PP-FormulaNet) e **Indra**
(`math`), que resuelven la fórmula dentro de la página.

## Métrica (sobre la forma canónica LaTeX)

`latex_metrics.py` normaliza espaciado, `\left`/`\right`, `array`↔`matrix`,
`\lbrack`↔`[` y alias de comandos antes de medir; así la métrica no castiga
diferencias que **no** son errores de reconocimiento:

* `latex_exact` — 1.0 si la forma canónica coincide.
* `latex_sim` — `1 − Levenshtein(canónico)/max(|canónico|)`.
* `latex_token_f1` — F1 sobre el multiconjunto de comandos/símbolos (insensible
  al orden): mide qué reproduce el motor.
* `ms/fórmula` y **cobertura LaTeX** (`\palabra` / `\begin{}`): separa quien
  **emite LaTeX** de quien solo repite símbolos como texto.

## Dataset

`omnidocbench_formula` — `opendatalab/OmniDocBench` v1.6, una muestra por
bloque `equation_isolated`.

## Alternativas Python reales (motores que SÍ producen LaTeX)

| Alternativa | `pip install` | URL (software, no cifras) | Estado aquí |
| :--- | :--- | :--- | :--- |
| pix2tex (LaTeX-OCR) | `pix2tex` | https://github.com/lukas-blecher/LaTeX-OCR | **`medido`** (CPU: `LatexOCR` con `no_cuda=True`) |
| texify (surya_latex_ocr) | `texify` | https://github.com/VikParuchuri/texify | `skipped` (adaptador pendiente) |
| nougat | `nougat-ocr` | https://github.com/facebookresearch/nougat | `skipped` (adaptador pendiente) |
| UniMERNet | repo | https://github.com/opendatalab/UniMERNet | `skipped` (adaptador pendiente) |
| Pix2Text | `pix2text` | https://github.com/breezedeus/Pix2Text | `skipped` (instalación **no forzada**: degrada `transformers`/`huggingface_hub` y cambia `opencv-python-headless`→`opencv-python`) |
| TexTeller | `texteller` | https://github.com/OleehyO/TexTeller | `skipped` (adaptador pendiente) |
| img2latex | `img2latex` | PyPI `img2latex` | `skipped` (adaptador pendiente) |

**Controles** (no son alternativas del ranking, se incluyen etiquetados): el OCR
de texto `easyocr`/`rapidocr`/`tesseract`, que no emiten LaTeX (0% de cobertura)
y sirven para demostrarlo, no para comparar calidad de fórmula.

## Cómo correrlo

```bash
# Recortes de fórmula de OmniDocBench; un motor a la vez, CPU
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 10 \
  --backends pyocrust_formulanet,pyocrust_formula,pyocrust_indra,pix2tex,easyocr,rapidocr
```

Salida: `benchmarks/results/formula/<timestamp>/` (CSV de 28 columnas con
`latex_*` + `summary.json` + `<backend>.outputs.json` con la salida cruda para
medir la cobertura LaTeX). Los artefactos crudos **no se versionan**.

## Provenance

Todas las cifras son **`medido`** (comando + dataset + `n` + `warmup` + `repeats` +
`device` + fecha en el `summary.json`). Referencias externas: solo las URLs de
software de la tabla (no se copian métricas ajenas). Ningún motor ausente se cita
como si hubiera corrido: queda `skipped` con su `pip install`.
