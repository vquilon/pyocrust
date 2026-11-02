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
