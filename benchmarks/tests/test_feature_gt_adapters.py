"""Tests offline de los adaptadores de GT y las métricas de las features nuevas.

Cubren, **sin descargar datasets ni cargar modelos**:

* que los bancos de layout / tabla / documento / orientación / línea /
  rectificado están implementados y apuntan a un dataset **registrado**;
* que la métrica de cada uno (mAP@IoU, TEDS de estructura, accuracy de
  orientación, SSIM de rectificado) puntúa cuando hay GT y queda **no evaluada**
  (`""`) cuando no lo hay — nunca un `0.0` inventado;
* que el runner deja la calidad textual **no evaluada** (en vez de un `0.0`)
  cuando la muestra no trae GT de texto, y que rellena con el `scorer` las
  columnas de la feature.
"""

from __future__ import annotations

import importlib
import io
import sys

import pytest
from PIL import Image

from common import CSV_FIELDS, DATASETS, OcrOutput, Sample, run_benchmark
from features import _base
from features._base import orientation_accuracy

# Banco implementado -> dataset que declara (debe estar registrado).
NEW_FEATURES = {
    "layout": "omnidocbench_layout",
    "table": "omnidocbench_table",
    "full_page": "omnidocbench_full_page",
    "orientation": "synthetic_orientation",
    "text_line": "synthetic_text_line",
    "rectification": "synthetic_rectification",
}

FEATURE_METRIC_COLUMNS = ("layout_map", "layout_recall", "table_teds", "ori_acc", "rect_sim")


def _bank(feature: str):
    return importlib.import_module(f"features.{feature}.bank")


@pytest.mark.parametrize("feature,dataset", sorted(NEW_FEATURES.items()))
def test_bancos_nuevos_implementados_con_dataset_registrado(feature, dataset):
    bank = _bank(feature)
    assert bank.SPEC.status == "implemented"
    assert feature in _base.IMPLEMENTED_FEATURES
    assert dataset in DATASETS, f"{feature}: dataset no registrado -> {dataset}"


def test_las_columnas_de_las_features_nuevas_estan_en_el_contrato():
    assert set(FEATURE_METRIC_COLUMNS) <= set(CSV_FIELDS)


def test_layout_map_puntua_y_queda_vacia_sin_gt():
    bank = _bank("layout")
    sample = Sample("p", Image.new("RGB", (10, 10)), "",
                    gt_layout={"text_block": ((0.0, 0.0, 10.0, 5.0),)})
    hit = OcrOutput("", extra={"elements": [
        {"element_type": "text", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    ]})
    assert bank.score_layout(sample, hit) == {"layout_map": 1.0, "layout_recall": 1.0}
    miss = OcrOutput("", extra={"elements": [
        {"element_type": "text", "score": 0.9, "bbox": [[50, 50], [60, 50], [60, 60], [50, 60]]},
    ]})
    assert bank.score_layout(sample, miss) == {"layout_map": 0.0, "layout_recall": 0.0}
    # Sin cajas GT: métrica no evaluada, nunca un 0.0 espurio.
    assert bank.score_layout(Sample("q", Image.new("RGB", (2, 2)), ""), hit) == {
        "layout_map": "", "layout_recall": ""}


def test_table_teds_ignora_el_texto_de_celda_y_queda_vacia_sin_gt():
    bank = _bank("table")
    sample = Sample("t", Image.new("RGB", (4, 4)), "",
                    gt_html="<table><tr><td>a</td><td>b</td></tr></table>")
    assert bank.score_table(sample, OcrOutput("<tr><td></td><td></td></tr>")) == {"table_teds": 1.0}
    assert bank.score_table(sample, OcrOutput("<tr><td></td></tr>"))["table_teds"] < 1.0
    assert bank.score_table(Sample("u", Image.new("RGB", (4, 4)), ""), OcrOutput("")) == {
        "table_teds": ""}


def test_full_page_desgrana_contenido_y_estructura_en_la_misma_pasada():
    """`full_page` mide layout/tabla/fórmula además de markdown_f1/block_f1.

    Regla del banco: sin GT de la modalidad, la métrica queda **no evaluada**
    (`""`); una tabla con texto correcto pero estructura mal **baja el TEDS**
    aunque `markdown_f1` no lo vea.
    """
    from common.metrics import markdown_f1

    bank = _bank("full_page")
    image = Image.new("RGB", (10, 10))
    sample = Sample(
        "p", image, "", gt_markdown="hola", gt_blocks=("text",),
        gt_layout={"text_block": ((0.0, 0.0, 10.0, 5.0),), "table": ((0.0, 5.0, 10.0, 9.0),)},
        gt_html="<table><tr><td>x</td></tr></table>",
        gt_by_task={"formula": "$$x$$"},
    )
    hit = OcrOutput(
        "hola\n<table border=\"1\"><tr><td>x</td></tr></table>\n$$x$$",
        extra={
            "elements": [
                {"element_type": "text", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
                {"element_type": "table", "score": 0.9, "bbox": [[0, 5], [10, 5], [10, 9], [0, 9]]},
            ],
            "formulas": ["$$x$$"],
        },
    )
    scored = bank.score_full_page(sample, hit)
    assert scored["layout_map"] == 1.0 and scored["layout_recall"] == 1.0
    assert scored["table_teds"] == 1.0
    assert scored["latex_sim"] == 1.0 and scored["latex_token_f1"] == 1.0

    # Mismo texto de celda, estructura MAL (una fila en vez de dos).
    bad = OcrOutput("<table><tr><td>a</td><td>b</td></tr></table>",
                    extra={"elements": hit.extra["elements"], "formulas": ["$$x$$"]})
    bad_sample = Sample("t", image, "", gt_markdown="a b", gt_blocks=("table",),
                        gt_html="<table><tr><td>a</td></tr><tr><td>b</td></tr></table>")
    assert markdown_f1(bad_sample.gt_markdown, "a b") == 1.0        # contenido intacto
    assert bank.score_full_page(bad_sample, bad)["table_teds"] < 1.0  # estructura penalizada

    # Sin GT de cada modalidad: no evaluada (""), nunca un 0.0 inventado.
    bare = Sample("q", image, "", gt_markdown="hola", gt_blocks=("text",))
    bare_scored = bank.score_full_page(bare, hit)
    for key in ("layout_map", "layout_recall", "table_teds", "latex_sim", "latex_token_f1"):
        assert bare_scored[key] == "", key


def test_figuras_y_caption_asociado_como_metrica_propia():
    """`full_page` mide figuras (detección) y la **asociación figura↔caption**.

    Criterio: una página con las figuras detectadas pero **sin** sus captions no
    puede puntuar igual que una completa. Las métricas quedan `""` (no
    evaluadas) en páginas sin GT de figuras, y las máscaras (`*_mask`) no entran.
    """
    bank = _bank("full_page")
    image = Image.new("RGB", (10, 10))
    # GT en vocabulario del pipeline: figura = `image`, caption = `figure_title`.
    gt_blocks = (
        ((0.0, 0.0, 10.0, 6.0), "image", ""),
        ((0.0, 6.0, 10.0, 8.0), "figure_title", "Fig 1: diagrama"),
    )
    sample = Sample("f", image, "", gt_markdown="x", gt_blocks=("figure",),
                    gt_ordered_blocks=gt_blocks)
    full = OcrOutput("", extra={"elements": [
        {"element_type": "image", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 6], [0, 6]]},
        {"element_type": "figure_title", "score": 0.9, "text": "Fig 1: diagrama",
         "bbox": [[0, 6], [10, 6], [10, 8], [0, 8]]},
    ]})
    ok = bank.score_full_page(sample, full)
    assert ok["figure_recall"] == 1.0 and ok["figure_precision"] == 1.0
    assert ok["figure_caption_recall"] == 1.0
    assert ok["figure_caption_pair_f1"] == 1.0
    assert ok["figure_caption_text_f1"] == 1.0

    # Figuras detectadas, caption ausente: la asociación cae -> NO puntúa igual.
    no_caption = OcrOutput("", extra={"elements": [
        {"element_type": "image", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 6], [0, 6]]},
    ]})
    partial = bank.score_full_page(sample, no_caption)
    assert partial["figure_recall"] == 1.0                 # la figura sí se ve
    assert partial["figure_caption_pair_f1"] == 0.0        # la asociación no
    assert partial["figure_caption_pair_f1"] < ok["figure_caption_pair_f1"]
    # Las máscaras no son emitibles: aunque el motor no las emita, no puntúan.
    masked = Sample("m", image, "", gt_markdown="x", gt_blocks=("figure",),
                    gt_ordered_blocks=gt_blocks + (
                        ((0.0, 8.0, 10.0, 9.0), "unknown_mask", ""),))
    assert bank.score_full_page(masked, no_caption)["figure_recall"] == 1.0

    # Página sin GT de figuras: no evaluada (""), nunca 0.0.
    no_fig = Sample("g", image, "", gt_markdown="x", gt_blocks=("text",),
                    gt_ordered_blocks=(((0.0, 3.0, 10.0, 8.0), "text", "cuerpo"),))
    nf = bank.score_full_page(no_fig, full)
    for key in ("figure_recall", "figure_precision", "figure_caption_recall",
                "figure_caption_precision", "figure_caption_pair_f1",
                "figure_caption_text_f1"):
        assert nf[key] == "", key


def test_el_backend_estructura_expone_los_elementos_que_antes_se_tiraban(monkeypatch):
    """`pp_structurev3` ya trae `elements` (kind + caja); el adaptador los expone.

    Sin esto, `full_page` no puede puntuar layout: el dato viajaba en el
    `StructureResult` y se descartaba al construir el `OcrOutput`.
    """
    import types

    from PIL import Image as PILImage

    from common.runner import _bbox_quad, _pyocrust_backend

    class _Box:
        x1, y1, x2, y2 = 0.0, 0.0, 10.0, 5.0

    class _Element:
        kind, text, confidence, box = "table", "", 0.8, _Box()

    class _Result:
        markdown = "<table><tr><td>x</td></tr></table>"
        elements = [_Element()]
        regions = []
        formulas = ["$$x$$"]

        def to_markdown(self):
            return self.markdown

    class _Engine:
        def __init__(self, **_kwargs):
            self.provider_effective = "cpu"

        def recognize(self, _data):
            return _Result()

    monkeypatch.setitem(sys.modules, "pyocrust", types.SimpleNamespace(VeloceOCR=_Engine))
    run = _pyocrust_backend("pp_structurev3", device="cpu")
    output = run(PILImage.new("RGB", (10, 10)))
    assert output.extra["elements"] == [{
        "element_type": "table", "score": 0.8,
        "bbox": [[0.0, 0.0], [10.0, 0.0], [10.0, 5.0], [0.0, 5.0]], "text": "",
    }]
    assert output.extra["formulas"] == ["$$x$$"]
    assert _bbox_quad(None) == []


def test_orientation_accuracy_solo_cuando_hay_etiqueta_gt():
    labelled = Sample("o", Image.new("RGB", (4, 4)), "", gt_label="270")
    assert orientation_accuracy(labelled, OcrOutput("270", extra={"label": "270"})) == {"ori_acc": 1.0}
    assert orientation_accuracy(labelled, OcrOutput("0", extra={"label": "0"})) == {"ori_acc": 0.0}
    unlabelled = Sample("o", Image.new("RGB", (4, 4)), "")
    assert orientation_accuracy(unlabelled, OcrOutput("0", extra={"label": "0"})) == {"ori_acc": ""}


def test_rectification_ssim_contra_la_referencia_limpia():
    bank = _bank("rectification")
    clean = Image.new("RGB", (24, 16), "white")
    buffer = io.BytesIO()
    clean.save(buffer, format="PNG")
    sample = Sample("r", clean, "", gt_image=clean)
    assert bank.score_rectification(
        sample, OcrOutput("", extra={"image": buffer.getvalue()})
    )["rect_sim"] == 1.0
    # Sin salida rectificada o sin imagen de referencia: no evaluada.
    assert bank.score_rectification(sample, OcrOutput("", extra={"image": b""})) == {"rect_sim": ""}
    assert bank.score_rectification(
        Sample("r", clean, ""), OcrOutput("", extra={"image": buffer.getvalue()})
    ) == {"rect_sim": ""}


def test_el_runner_no_inventa_calidad_textual_cuando_la_feature_no_tiene_gt_de_texto():
    sample = Sample("s", Image.new("RGB", (4, 4)), "", gt_label="0")
    rows, meta = run_benchmark(
        [sample], "pyocrust_orientation", "synthetic_orientation", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput("180", extra={"label": "180"}),
        scorer=orientation_accuracy,
    )
    assert meta["status"] == "ok" and meta["n_ok"] == 1
    row = rows[0]
    for key in ("cer", "wer", "cer_ord", "wer_ord", "word_f1", "exact_match", "n_chars_gt"):
        assert row[key] == "", f"{key} debía quedar no evaluada"
    assert row["ori_acc"] == 0.0            # la métrica propia SÍ se mide
    assert row["n_chars_pred"] == len("180")
    assert meta["mean_cer"] is None          # ni una media textual inventada
    # Las columnas de las features que este banco no produce quedan vacías.
    assert row["layout_map"] == "" and row["table_teds"] == "" and row["rect_sim"] == ""


def test_los_adaptadores_de_gt_de_omnidocbench_serializan_lo_anotado():
    from common.datasets import _odb_page_blocks, _odb_page_layout, _odb_page_markdown

    page = {
        "layout_dets": [
            {"category_type": "text_block", "ignore": False, "order": 1,
             "poly": [0, 0, 10, 0, 10, 5, 0, 5], "text": "hola"},
            {"category_type": "table", "ignore": False, "order": 2,
             "poly": [0, 5, 10, 5, 10, 9, 0, 9], "html": "<table><tr><td>x</td></tr></table>"},
            {"category_type": "equation_isolated", "ignore": False, "order": 3,
             "poly": [0, 9, 10, 9, 10, 12, 0, 12], "latex": "$$x$$"},
            {"category_type": "abandon", "ignore": True, "order": 0, "text": "no"},
        ],
        "page_info": {"image_path": "p.png"},
    }
    assert _odb_page_markdown(page) == "hola\n\n<table><tr><td>x</td></tr></table>\n\n$$x$$"
    assert _odb_page_blocks(page) == ("text", "table", "formula")
    assert _odb_page_layout(page) == {
        "text_block": ((0.0, 0.0, 10.0, 5.0),),
        "table": ((0.0, 5.0, 10.0, 9.0),),
        "equation_isolated": ((0.0, 9.0, 10.0, 12.0),),
    }


def test_las_features_sinteticas_funcionan_sin_cache(tmp_path):
    """Sin `data_cache` (checkout limpio o sin red) las sintéticas generan su página.

    Regresión: antes dependían de las páginas cacheadas de OmniDocBench y lanzaban
    `DatasetUnavailable`; ahora caen a páginas sintéticas deterministas.
    """
    from common.datasets import (
        load_synthetic_orientation,
        load_synthetic_rectification,
        load_synthetic_text_line,
    )

    vacio = tmp_path / "sin_cache"
    vacio.mkdir()
    for loader in (load_synthetic_orientation, load_synthetic_text_line,
                   load_synthetic_rectification):
        first = loader(limit=4, cache_dir=vacio)
        assert len(first) == 4, loader.__name__
        second = loader(limit=4, cache_dir=vacio)
        assert first[0].image.tobytes() == second[0].image.tobytes(), loader.__name__


# ---------------------------------------------------------------------------
# Comparación cruzada: el **pipeline completo** (`pyocrust_structure`) medido en
# la tarea de cada feature, contra el especialista, con el MISMO GT (t_8b618f13).
# ---------------------------------------------------------------------------

def test_el_pipeline_completo_es_backend_por_defecto_de_layout_table_formula():
    for feature in ("layout", "table", "formula"):
        assert "pyocrust_structure" in _bank(feature).DEFAULT_BACKENDS.split(","), feature
    from common.runner import FEATURE_TYPES, MODEL_NAMES, PROVIDERS, TASK_TYPES

    assert "pyocrust_structure" in PROVIDERS
    assert MODEL_NAMES["pyocrust_structure"] == ("pp_structurev3", "default")
    assert TASK_TYPES["pyocrust_structure"] == "structure"
    assert FEATURE_TYPES["pyocrust_structure"] == "full_page"


def test_layout_puntua_las_cajas_del_pipeline_con_su_vocabulario():
    """El pipeline dice `formula` (no `display_formula`): con la unión de
    vocabularios del banco, sus cajas SÍ puntúan contra `equation_isolated`."""
    bank = _bank("layout")
    sample = Sample("e", Image.new("RGB", (10, 10)), "",
                    gt_layout={"equation_isolated": ((0.0, 0.0, 10.0, 5.0),)})
    struct = OcrOutput("", extra={"elements": [
        {"element_type": "formula", "score": 0.9, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    ]})
    assert bank.score_layout(sample, struct) == {"layout_map": 1.0, "layout_recall": 1.0}


def test_table_puntua_la_tabla_embebida_del_pipeline_y_queda_vacia_sin_tabla():
    """El pipeline inyecta `<table>…</table>` en su Markdown: se extrae y puntúa.

    Sin tabla alguna, la métrica queda **no evaluada** (`""`), nunca un `0.0`.
    """
    bank = _bank("table")
    sample = Sample("t", Image.new("RGB", (4, 4)), "",
                    gt_html="<table><tr><td>a</td><td>b</td></tr></table>")
    embedded = OcrOutput("hola\n<div><table border=\"1\"><tr><td>a</td><td>b</td></tr></table></div>\nfin")
    assert bank.score_table(sample, embedded) == {"table_teds": 1.0}
    assert bank.score_table(sample, OcrOutput("sin tabla")) == {"table_teds": ""}
    # Gramática suelta del especialista (sin envoltorio `<table>`) sigue puntuando.
    assert bank.score_table(sample, OcrOutput("<tr><td></td><td></td></tr>")) == {"table_teds": 1.0}


def test_formula_puntua_el_latex_aislado_del_pipeline_no_el_markdown_de_pagina():
    """El banco de fórmula puntúa el LaTeX **aislado**: `extra["formulas"]` del
    pipeline, no su Markdown de página. Sin LaTeX -> no evaluada (`"\"`), no 0.0."""
    bank = _bank("formula")
    sample = Sample("f", Image.new("RGB", (4, 4)), "", gt_by_task={"formula": r"x^2"})
    pipeline = OcrOutput("## titulo\n<div>algo</div>", extra={"formulas": [r"x^2"]})
    assert bank.score_formula(sample, pipeline) == {
        "latex_exact": 1.0, "latex_sim": 1.0, "latex_token_f1": 1.0}
    # Markdown de página sin fórmulas aisladas: no evaluada, nunca un 0.0.
    assert bank.score_formula(sample, OcrOutput("## titulo\n<div>algo</div>")) == {
        "latex_exact": "", "latex_sim": "", "latex_token_f1": ""}
    # Un motor LaTeX puro (pix2tex) sigue puntuando desde `text`.
    assert bank.score_formula(sample, OcrOutput(r"x^2"))["latex_sim"] == 1.0


# ---------------------------------------------------------------------------
# Celdas `0.0` falsas: un motor que no emite estructura publica `N/A`, no `0.0`.
# ---------------------------------------------------------------------------

_TEXT_ONLY_SAMPLE = Sample(
    "s", Image.new("RGB", (10, 10)), "hola", gt_markdown="hola", gt_blocks=("text",),
    gt_layout={"text_block": ((0.0, 0.0, 10.0, 5.0),)},
    gt_html="<table><tr><td>x</td></tr></table>",
    gt_by_task={"formula": "$$x$$"},
    gt_ordered_blocks=(((0.0, 0.0, 10.0, 5.0), "paragraph_title", "T"),),
)


def test_un_motor_sin_declaracion_emits_se_puntua_como_completo():
    """Compatibilidad: sin la señal `emits` el scorer mide como siempre (0.0 real)."""
    bank = _bank("full_page")
    # Elementos del vocabulario del banco pero cajas fuera: 0.0 evaluado, no N/A.
    out = OcrOutput("", extra={"elements": [
        {"element_type": "text", "score": 0.9, "bbox": [[50, 50], [60, 50], [60, 60], [50, 60]]}]})
    scored = bank.score_full_page(_TEXT_ONLY_SAMPLE, out)
    assert scored["layout_map"] == 0.0        # medido (y fallado), no N/A
    assert scored["title_recall"] == 0.0


def test_un_motor_solo_texto_declara_canales_y_las_columnas_de_estructura_son_na():
    """La señal viene del ADAPTADOR (`extra["emits"]`), no de adivinar por el resultado.

    docling solo emite Markdown (`emits=frozenset()`): aunque el GT de estructura
    exista, esas columnas quedan **no evaluadas** (`""`), nunca `0.0`.
    """
    bank = _bank("full_page")
    out = OcrOutput("hola", extra={"emits": frozenset()})
    scored = bank.score_full_page(_TEXT_ONLY_SAMPLE, out)
    for key in ("layout_map", "layout_recall", "table_teds", "latex_sim",
                "latex_token_f1", "title_recall", "title_precision",
                "title_text_f1", "title_seq_tau", "read_order_tau",
                "figure_recall", "figure_precision", "figure_caption_recall",
                "figure_caption_precision", "figure_caption_pair_f1",
                "figure_caption_text_f1"):
        assert scored[key] == "", f"{key} debia quedar no evaluada (docling)"


def test_el_runner_no_inventa_block_f1_de_un_motor_solo_texto():
    """`block_f1` de un motor que no emite bloques del banco queda `""`, no `0.0`."""
    rows, meta = run_benchmark(
        [_TEXT_ONLY_SAMPLE], "docling", "omnidocbench_full_page", warmup=0,
        backend_factory=lambda: _text_only_runner,
        scorer=_bank("full_page").score_full_page,
    )
    assert meta["status"] == "ok" and meta["n_ok"] == 1
    row = rows[0]
    assert row["block_f1"] == "" and row["layout_map"] == "" and row["table_teds"] == ""
    # El contenido textual SÍ se mide: es lo que el motor emite.
    assert row["markdown_f1"] == 1.0 and row["cer"] == 0.0


def _text_only_runner(image):
    return OcrOutput("hola", extra={"emits": frozenset()})


def test_not_evaluable_metrics_por_motor():
    """El mapa motor->columnas no medibles: docling ninguna estructura, pyocrust todas."""
    from common import not_evaluable_metrics
    assert "layout_map" in not_evaluable_metrics("docling")
    assert "block_f1" in not_evaluable_metrics("docling")
    assert "table_teds" in not_evaluable_metrics("docling")
    assert not_evaluable_metrics("pyocrust_structure") == frozenset()
    # Indra emite cajas (orden de lectura) y tablas HTML, pero no layout ni fórmulas.
    indra = not_evaluable_metrics("pyocrust_indra")
    assert "layout_map" in indra and "table_teds" not in indra and "read_order_tau" not in indra
