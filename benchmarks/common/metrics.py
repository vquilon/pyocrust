"""Métricas compartidas por todos los bancos de feature de `benchmarks/`.

Movidas desde el antiguo `benchmarks/run_benchmarks.py` en la reorganización por
feature (cada banco importa de aquí, no de un script de run concreto).

Contenido:

* Texto: `normalize`, `levenshtein`, `cer`, `wer`, `word_f1`, `cer_ord`,
  `wer_ord`, `exact_match`-style helpers, `markdown_f1`, `block_f1`.
* Cajas: `iou`, `box_metrics` (recall@IoU y IoU medio por mejor emparejamiento),
  usadas por el banco de `text` para medir detección, no solo reconocimiento.
* LaTeX: **se reexporta** `benchmarks/latex_metrics.py` (forma canónica
  `normalize_latex`, `latex_exact`, `latex_similarity`, `latex_token_f1`). No se
  duplica: la métrica de fórmulas tiene un único origen de verdad en ese módulo
  (tarjeta de fórmulas `t_fce0921a`).

Autochequeo:
    .venv/Scripts/python.exe benchmarks/common/metrics.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

# Ejecutable también como script (`python benchmarks/common/metrics.py`).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Normalización de fairness: minusculas y espacios colapsados."""
    return " ".join(text.lower().split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,          # borrado
                    current[j - 1] + 1,       # inserción
                    previous[j - 1] + (ca != cb),  # sustitución
                )
            )
        previous = current
    return previous[-1]


def cer(gt: str, pred: str) -> float:
    """Character Error Rate sobre texto normalizado."""
    gt_n, pred_n = normalize(gt), normalize(pred)
    if not gt_n:
        return 0.0 if not pred_n else 1.0
    return levenshtein(gt_n, pred_n) / len(gt_n)


def wer(gt: str, pred: str) -> float:
    """Word Error Rate sobre texto normalizado."""
    gt_w, pred_w = normalize(gt).split(), normalize(pred).split()
    if not gt_w:
        return 0.0 if not pred_w else 1.0
    return levenshtein(gt_w, pred_w) / len(gt_w)


def word_f1(gt: str, pred: str) -> float:
    """F1 a nivel de palabra, independiente del orden de lectura (multi-columna).

    Un formulario con varias columnas hace que el orden lineal del OCR y el del
    ground truth difieran sin que ninguno de los dos esté mal; este F1 compara
    el multiconjunto de palabras y no castiga ese desorden.
    """
    gt_w = Counter(normalize(gt).split())
    pred_w = Counter(normalize(pred).split())
    if not gt_w and not pred_w:
        return 1.0
    if not gt_w or not pred_w:
        return 0.0
    overlap = sum((gt_w & pred_w).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(pred_w.values())
    recall = overlap / sum(gt_w.values())
    return 2 * precision * recall / (precision + recall)


def _ordered(text: str) -> list[str]:
    """Palabras del texto ordenadas: neutraliza el orden de lectura."""
    return sorted(normalize(text).split())


def cer_ord(gt: str, pred: str) -> float:
    """CER con orden de lectura neutralizado (B4/D1).

    El CER crudo castiga la diferencia de recorrido entre el OCR lineal y el
    ground truth ordenado por caja; este CER compara el **multiconjunto** de
    palabras y mide reconocimiento, no disposición.
    """
    gt_o, pred_o = " ".join(_ordered(gt)), " ".join(_ordered(pred))
    if not gt_o:
        return 0.0 if not pred_o else 1.0
    return levenshtein(gt_o, pred_o) / len(gt_o)


def wer_ord(gt: str, pred: str) -> float:
    """WER con orden de lectura neutralizado (B4/D1)."""
    gt_o, pred_o = _ordered(gt), _ordered(pred)
    if not gt_o:
        return 0.0 if not pred_o else 1.0
    return levenshtein(gt_o, pred_o) / len(gt_o)


def markdown_f1(gt: str, pred: str) -> float:
    """Order-sensitive token LCS F1; preserve LaTeX case."""
    def tokens(text):
        parts = re.split(r"(\$\$.*?\$\$|\$[^$]*\$)", text, flags=re.DOTALL)
        return [token for part in parts for token in (part if part.startswith("$") else part.lower()).split()]
    a, b = tokens(gt), tokens(pred)
    if not a and not b:
        return 1.0
    previous = [0] * (len(b) + 1)
    for token in a:
        current = [0]
        for j, other in enumerate(b, 1):
            current.append(previous[j - 1] + 1 if token == other else max(previous[j], current[-1]))
        previous = current
    return 2 * previous[-1] / (len(a) + len(b))


def block_f1(gt: Sequence[str], pred: Sequence[str]) -> float:
    a, b = Counter(gt), Counter(pred)
    return 2 * sum((a & b).values()) / (sum(a.values()) + sum(b.values())) if a or b else 1.0


# ---------------------------------------------------------------------------
# Cajas (detección): el banco de `text` mide también la geometría.
# ---------------------------------------------------------------------------


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    """IoU de dos cajas `(x1, y1, x2, y2)`; 0.0 si no se solapan o son degeneradas."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def box_metrics(
    gt_boxes: Iterable[Sequence[float]],
    pred_boxes: Iterable[Sequence[float]],
    thr: float = 0.5,
) -> tuple[float, float]:
    """`(recall, mean_best_iou)` emparejando cada caja GT con la predicción de más IoU.

    `recall` = fracción de cajas GT con alguna predicción a >= `thr` de IoU
    (detección encontrada). `mean_best_iou` = IoU medio del mejor candidato por
    caja GT (0.0 si no hay predicción). Sin cajas GT **no se evalúa**: el
    llamante debe saltarse la métrica, no inventar un 0.0.
    """
    gt_list = [tuple(map(float, b)) for b in gt_boxes]
    pred_list = [tuple(map(float, b)) for b in pred_boxes]
    if not gt_list:
        raise ValueError("box_metrics requires at least one ground-truth box")
    matched, bests = 0, []
    for gt_box in gt_list:
        best = max((iou(gt_box, p) for p in pred_list), default=0.0)
        bests.append(best)
        matched += best >= thr
    return matched / len(gt_list), sum(bests) / len(bests)


# ---------------------------------------------------------------------------
# Layout (detección): mAP@IoU por clase + recall macro
# ---------------------------------------------------------------------------


def _class_ap(
    gt_boxes: Sequence[Sequence[float]],
    preds: Sequence[tuple[float, Sequence[float]]],
    thr: float,
) -> tuple[float, float] | None:
    """`(AP@thr, recall@thr)` de **una** clase; `None` si esa clase no tiene GT.

    Emparejamiento voraz 1-a-1: se recorren las predicciones por `score`
    descendente y cada una se lleva la caja GT libre de mayor IoU; el AP es el
    área bajo la curva precisión-recall a un único umbral (VOC2007), con
    `tp/(tp+fp)` acumulado en cada acierto.
    """
    if not gt_boxes:
        return None
    matched = [False] * len(gt_boxes)
    tp = fp = 0
    ap = 0.0
    for _score, box in sorted(preds, key=lambda p: -float(p[0])):
        best_i, best_iou = -1, 0.0
        for i, gt_box in enumerate(gt_boxes):
            if matched[i]:
                continue
            value = iou(gt_box, box)
            if value > best_iou:
                best_i, best_iou = i, value
        if best_i >= 0 and best_iou >= thr:
            matched[best_i] = True
            tp += 1
            ap += tp / (tp + fp)
        else:
            fp += 1
    return ap / len(gt_boxes), sum(matched) / len(gt_boxes)


def detection_map(
    gt_by_class: dict[str, Sequence[Sequence[float]]],
    pred_by_class: dict[str, Sequence[tuple[float, Sequence[float]]]],
    thr: float = 0.5,
) -> tuple[float | None, float | None]:
    """`(mAP@thr, recall@thr)` macro sobre las clases **presentes en el GT**.

    `gt_by_class` mapea clase -> cajas GT; `pred_by_class` mapea clase -> lista
    `(score, caja)`. Solo se evalúan las clases con GT (sin positivos el recall
    es indefinido, no cero). Si el GT no trae ninguna caja devuelve
    `(None, None)`: la métrica queda **no evaluada**, nunca un `0.0` espurio.
    """
    aps, recalls = [], []
    for cls, gt_boxes in gt_by_class.items():
        result = _class_ap(list(gt_boxes), list(pred_by_class.get(cls, ())), thr)
        if result is not None:
            aps.append(result[0])
            recalls.append(result[1])
    if not aps:
        return None, None
    return sum(aps) / len(aps), sum(recalls) / len(recalls)


# ---------------------------------------------------------------------------
# Tablas: TEDS de estructura (secuencia de etiquetas, sin texto de celda)
# ---------------------------------------------------------------------------

# Envoltorios que no aportan estructura de tabla: el modelo emite la gramática
# `<tr>/<td>` sin ellos, así que se ignoran en ambos lados.
_HTML_WRAPPER_TAGS = frozenset({"html", "body", "table", "tbody", "thead", "tfoot"})


def html_tags(html: str) -> list[str]:
    """Secuencia de etiquetas HTML (sin texto y sin envoltorios de tabla)."""
    from html.parser import HTMLParser

    tags: list[str] = []

    class _Collector(HTMLParser):
        def handle_starttag(self, tag: str, attrs: object) -> None:
            if tag.lower() not in _HTML_WRAPPER_TAGS:
                tags.append(f"<{tag.lower()}>")

        def handle_startendtag(self, tag: str, attrs: object) -> None:
            self.handle_starttag(tag, attrs)
            tags.append(f"</{tag.lower()}>")

        def handle_endtag(self, tag: str) -> None:
            if tag.lower() not in _HTML_WRAPPER_TAGS:
                tags.append(f"</{tag.lower()}>")

    _Collector(convert_charrefs=True).feed(html or "")
    return tags


def table_teds(gt_html: str, pred_html: str) -> float:
    """**TEDS de estructura**: `1 - editDist(etiquetas) / max(longitudes)`.

    El modelo de estructura de tabla emite solo la gramática
    (`<tr>`, `<td>`, `</tr>`...) y **no** el texto de las celdas, así que la
    comparación honesta es sobre la secuencia de etiquetas (filas, columnas y
    fusiones) sin el contenido: la variante *TEDS-S* de la literatura. El TEDS de
    árbol completo exigiría el texto de celda, que aquí no se predice.
    """
    a, b = html_tags(gt_html), html_tags(pred_html)
    if not a and not b:
        return 1.0
    return 1.0 - levenshtein(a, b) / max(len(a), len(b))


# ---------------------------------------------------------------------------
# Rectificación: similitud estructural (SSIM) con la imagen limpia de referencia
# ---------------------------------------------------------------------------


def image_ssim(reference, prediction) -> float | None:
    """SSIM en gris entre la imagen rectificada y su referencia limpia.

    Reencuadra la predicción al tamaño de la referencia (el motor puede devolver
    otra resolución) y recorta a `[0, 1]`. Devuelve `None` — métrica **no
    evaluada**, nunca un `0.0` — si falta `scikit-image`.
    """
    try:  # pragma: no cover - dependencia opcional
        import numpy as np
        from skimage.metrics import structural_similarity
    except ImportError:  # pragma: no cover - entorno sin scikit-image
        return None
    reference_gray = reference.convert("L")
    grayscale = prediction.convert("L").resize(reference_gray.size)
    value = structural_similarity(
        np.asarray(reference_gray), np.asarray(grayscale), data_range=255
    )
    return max(0.0, float(value))


# ---------------------------------------------------------------------------
# LaTeX: reexport del módulo canónico (no se duplica la implementación).
# ---------------------------------------------------------------------------

from latex_metrics import (  # noqa: E402  (import al final: único origen de la métrica)
    latex_exact,
    latex_similarity,
    latex_token_f1,
    normalize_latex,
)

__all__ = [
    "normalize", "levenshtein", "cer", "wer", "word_f1", "cer_ord", "wer_ord",
    "markdown_f1", "block_f1", "iou", "box_metrics",
    "detection_map", "html_tags", "table_teds", "image_ssim",
    "normalize_latex", "latex_exact", "latex_similarity", "latex_token_f1",
]


def _self_check() -> None:
    # texto
    assert normalize("  Hola\tMUNDO  ") == "hola mundo"
    assert levenshtein("abc", "abd") == 1
    assert cer("hola mundo", "hola mund") == 1 / 10
    assert wer("hola mundo", "hola") == 0.5
    assert word_f1("a b c", "c b a") == 1.0
    assert cer_ord("hola mundo", "MUNDO hola") == 0
    assert markdown_f1("Texto $X$", "TEXTO $X$") == 1.0
    assert block_f1(["title"], ["title"]) == 1.0
    # cajas
    assert iou((0, 0, 2, 2), (0, 0, 2, 2)) == 1.0
    assert iou((0, 0, 2, 2), (5, 5, 6, 6)) == 0.0
    recall, mean_best = box_metrics([(0, 0, 2, 2), (10, 10, 12, 12)], [(0, 0, 2, 2)])
    assert recall == 0.5 and mean_best == 0.5
    # latex (reexportado)
    assert latex_exact(r"\dfrac{1}{2}", r"\frac{1}{2}") == 1.0
    assert latex_token_f1("abc", "cab") == 1.0
    # layout: mAP@0.5 y recall macro por clase (solo clases con GT)
    #   texto: 2 GT, pred 1 acierto + 1 falso positivo -> AP = (1/2)/2 = 0.5, recall 0.5
    #   tabla: 1 GT sin predicción -> AP = 0.0, recall 0.0
    ap, recall = detection_map(
        {"text": [(0, 0, 10, 10), (20, 20, 30, 30)], "table": [(0, 0, 5, 5)]},
        {"text": [(0.9, (0, 0, 10, 10)), (0.5, (100, 100, 110, 110))], "table": []},
    )
    assert (ap, recall) == (0.25, 0.25)
    # sin cajas GT no hay métrica (nunca un 0.0 inventado)
    assert detection_map({}, {}) == (None, None)
    # tablas: TEDS de estructura ignora el texto de celda y los envoltorios
    html = "<table><tr><td>a</td><td>b</td></tr></table>"
    assert table_teds(html, "<tr><td></td><td></td></tr>") == 1.0
    assert table_teds("<tr><td></td></tr>", "<tr><td></td><td></td></tr>") < 1.0
    assert html_tags("<table><tr><td>x</td></tr></table>") == ["<tr>", "<td>", "</td>", "</tr>"]
    print("common.metrics self-check OK")


if __name__ == "__main__":
    _self_check()
