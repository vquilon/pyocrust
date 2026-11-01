#!/usr/bin/env python
"""Métrica LaTeX **normalizada** para el benchmark de fórmulas→LaTeX.

La similitud de caracteres cruda (CER / Levenshtein sobre el texto tal cual)
castiga diferencias que **no** son errores de reconocimiento: espaciado, comandos
de tamaño (`\\left`/`\\right`), el entorno `array` frente a `matrix`, delimitadores
equivalentes (`\\lbrack` vs `[`) y alias de comandos (`\\le` vs `\\leq`).
`normalize_latex` lleva ambos lados a una **forma canónica** y las métricas de aquí
miden corrección sobre esa forma:

* `latex_exact` (↑): 1.0 si la forma canónica coincide; antes daba 0.000 en 50/50.
* `latex_similarity` (↑): `1 - Levenshtein(canónico)/max(|canónico|)`, igual que la
  `Similitud` del reporte pero sobre la forma canónica.
* `latex_token_f1` (↑): F1 sobre el **multiconjunto de tokens** (comandos y símbolos),
  insensible al orden: mide qué símbolos reproduce el motor, no su disposición.

No es equivalencia matemática (no evalúa la expresión con un CAS): es normalización
canónica + comparación superficial endurecida. Se documenta como tal, no se vende
como más de lo que es.

Uso:
    from latex_metrics import normalize_latex, latex_exact, latex_similarity, latex_token_f1

Autochequeo (sin dependencias del resto del harness salvo `levenshtein`):
    .venv/Scripts/python.exe benchmarks/latex_metrics.py
"""

from __future__ import annotations

import re
from collections import Counter

# Alias de comandos: mismo significado matemático, distinto nombre.
_COMMAND_ALIASES = {
    r"\le": r"\leq",
    r"\ge": r"\geq",
    r"\ne": r"\neq",
    r"\dfrac": r"\frac",
    r"\tfrac": r"\frac",
    r"\to": r"\rightarrow",
    r"\ast": r"*",
    r"\ldots": r"\dots",
    r"\cdotp": r"\cdot",
    r"\varepsilon": r"\epsilon",
}

# Alias de delimitadores: se unifican a su símbolo desnudo.
_DELIM_ALIASES = {
    r"\lbrack": "[",
    r"\rbrack": "]",
    r"\lbrace": r"\{",
    r"\rbrace": r"\}",
    r"\lvert": "|",
    r"\rvert": "|",
    r"\vert": "|",
    r"\lVert": r"\|",
    r"\rVert": r"\|",
    r"\Vert": r"\|",
}

# Comandos de tamaño/estilo/espacio: no cambian el contenido, se eliminan.
_DROP_COMMANDS = (
    "left", "right", "big", "Big", "bigg", "Bigg",
    "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "displaystyle", "textstyle", "scriptstyle", "scriptscriptstyle",
    "limits", "nolimits", "quad", "qquad", "thinspace", "medspace",
    "thickspace", "enspace", "negthinspace",
)

_DISPLAY_DELIMS = re.compile(r"\\[()\[\]]")
_ARRAY_BEGIN = re.compile(r"\\begin\{array\}(?:\{(?:[^{}]|\{[^{}]*\})*\})?")
_CTRL_WORD_SPACE = re.compile(r"(\\[A-Za-z]+)[ \t\n\r]+")
_TOKEN = re.compile(r"\\[A-Za-z]+|\\[^A-Za-z]|[^\s]")


def normalize_latex(text: str) -> str:
    """Forma canónica de una fórmula LaTeX (ver las reglas del módulo)."""
    s = (text or "").strip()
    if not s:
        return ""
    s = s.replace("$$", "").replace("$", "")
    s = _DISPLAY_DELIMS.sub("", s)
    # Entornos: `array` (con su spec de columnas `{l|c|r}`) -> `matrix`.
    s = _ARRAY_BEGIN.sub(r"\\begin{matrix}", s)
    s = s.replace(r"\end{array}", r"\end{matrix}")
    s = re.sub(r"\\(" + "|".join(_DROP_COMMANDS) + r")\b", "", s)
    s = re.sub(r"\\[,;:!]", "", s)      # espacios finos/negativos
    s = s.replace("\\ ", "").replace("~", "")
    for old, new in _DELIM_ALIASES.items():
        s = s.replace(old, new)
    for old, new in _COMMAND_ALIASES.items():
        # Frontera de palabra: `\le` no debe tocar `\leq` ni `\left`.
        s = re.sub(re.escape(old) + r"(?![A-Za-z])", lambda _m, n=new: n, s)
    # Un espacio tras una palabra de control (`\alpha b`) sí separa significado:
    # se marca con un centinela que sobrevive al borrado de espacios.
    s = _CTRL_WORD_SPACE.sub("\\1\x00", s)
    s = re.sub(r"\s+", "", s)
    return s.replace("\x00", " ")


def latex_tokens(text: str) -> list[str]:
    """Tokens de la forma canónica: comandos completos o símbolos sueltos."""
    return _TOKEN.findall(text)


def _levenshtein(a: str, b: str) -> int:
    # Import diferido: `run_benchmarks` importa este módulo, así que traer la
    # distancia en tiempo de import sería circular. Al llamar ya está cargado.
    from run_benchmarks import levenshtein  # noqa: PLC0415

    return levenshtein(a, b)


def latex_exact(gt: str, pred: str) -> float:
    """1.0 si las dos fórmulas comparten la misma forma canónica."""
    return 1.0 if normalize_latex(gt) == normalize_latex(pred) else 0.0


def latex_similarity(gt: str, pred: str) -> float:
    """Similitud de caracteres sobre la forma canónica (1 idéntico, 0 distinto)."""
    a, b = normalize_latex(gt), normalize_latex(pred)
    if not a and not b:
        return 1.0
    denom = max(len(a), len(b))
    if not denom:
        return 1.0
    return 1.0 - _levenshtein(a, b) / denom


def latex_token_f1(gt: str, pred: str) -> float:
    """F1 sobre el multiconjunto de tokens de LaTeX (independiente del orden)."""
    gt_t = Counter(latex_tokens(normalize_latex(gt)))
    pred_t = Counter(latex_tokens(normalize_latex(pred)))
    if not gt_t and not pred_t:
        return 1.0
    if not gt_t or not pred_t:
        return 0.0
    overlap = sum((gt_t & pred_t).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(pred_t.values())
    recall = overlap / sum(gt_t.values())
    return 2 * precision * recall / (precision + recall)


def _self_check() -> None:
    # Espaciado / delimitadores de display
    assert normalize_latex("$$  E = mc^2  $$") == "E=mc^2"
    assert latex_exact(r"\le", r"\leq") == 1.0
    assert latex_exact(r"\dfrac{1}{2}", r"\frac{1}{2}") == 1.0
    # `array` (con spec de columnas) equivale a `matrix`
    assert normalize_latex(r"\begin{array}{cc}a&b\\c&d\end{array}") == \
        normalize_latex(r"\begin{matrix}a&b\\c&d\end{matrix}")
    # `\left[`/`\lbrack` equivalen a `[`
    assert latex_exact(r"\left[ x \right]", "[x]") == 1.0
    assert latex_exact(r"\left\lbrack x \right\rbrack", "[x]") == 1.0
    assert latex_exact(r"a \, b", "ab") == 1.0
    # Un espacio tras palabra de control NO se pierde (cambia el significado)
    assert normalize_latex(r"\alpha b") != normalize_latex(r"\alphab")
    # Distinto de verdad: no se fuerza la igualdad
    assert latex_exact(r"\frac{1}{2}", r"\frac{1}{3}") == 0.0
    assert latex_similarity(r"x^2", r"\frac{a}{b}") < 0.5
    assert latex_token_f1("abc", "abc") == 1.0
    assert latex_token_f1("abc", "cab") == 1.0       # insensible al orden
    assert latex_token_f1("abc", "abd") < 1.0        # símbolos distintos
    print("latex_metrics self-check OK")


if __name__ == "__main__":
    _self_check()
