"""Tests de la organización por feature de `benchmarks/` y de su contrato.

Verifican, sin descargar datasets ni cargar modelos:

* que cada feature (`text`, `formula` + los esqueletos) tiene `bank.py` con un
  `SPEC` completo y su `README.md`;
* que el estado declarado (`implemented` vs `skeleton`) coincide con la realidad;
* que el contrato del CSV mantiene las 22 columnas históricas **en orden** y solo
  **añade** columnas nuevas;
* que una alternativa no instalada queda `skipped` con motivo (nunca `ok`);
* que la métrica de cajas (`box_recall`/`box_iou_mean`) mide cuando hay GT de
  cajas y queda **vacía** (no evaluada) cuando no lo hay.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from PIL import Image

from common import CSV_FIELDS, OcrOutput, Sample, box_metrics, run_benchmark
from features import _base

# Las 22 columnas históricas, en su orden exacto (contrato que NO se rompe).
LEGACY_CSV_FIELDS = [
    "run_timestamp", "backend", "dataset", "image_id", "cer", "wer", "cer_ord",
    "wer_ord", "word_f1", "exact_match", "elapsed_ms", "n_regions",
    "mean_confidence", "n_chars_gt", "n_chars_pred", "status", "error",
    "task_type", "model_name", "model_variant", "markdown_f1", "block_f1",
]

ALL_FEATURES = _base.all_feature_dirs()


def _bank(feature: str):
    return importlib.import_module(f"features.{feature}.bank")


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_cada_feature_tiene_spec_documentado(feature):
    spec = _bank(feature).SPEC
    assert spec.feature == feature
    assert spec.summary.strip(), f"{feature}: falta el resumen"
    assert spec.pyocrust_task, f"{feature}: falta la tarea de pyocrust"
    assert spec.metric.strip(), f"{feature}: falta la métrica"
    assert spec.dataset.strip(), f"{feature}: falta el dataset"
    assert spec.alternatives, f"{feature}: sin alternativas Python reales"
    for name, value in spec.alternatives.items():
        assert isinstance(value, tuple) and len(value) == 2, f"{feature}/{name}"
        assert all(str(part).strip() for part in value), f"{feature}/{name}"
    assert spec.status in {"implemented", "skeleton"}
    # Declarar el origen de cada número es obligatorio (regla de provenance).
    assert spec.provenance.strip(), f"{feature}: falta la nota de provenance"


@pytest.mark.parametrize("feature", _base.IMPLEMENTED_FEATURES)
def test_features_implementadas_lo_declaran(feature):
    assert _bank(feature).SPEC.status == "implemented"


@pytest.mark.parametrize("feature", _base.SKELETON_FEATURES)
def test_esqueletos_no_publican_cifras(feature):
    spec = _bank(feature).SPEC
    assert spec.status == "skeleton"
    assert "sin valores numéricos" in spec.provenance


def test_informes_y_graficas_viven_en_carpetas_por_feature():
    benchmarks = Path(__file__).resolve().parents[1]
    for feature in ALL_FEATURES:
        report_dir = benchmarks / "reports" / feature
        figure_dir = benchmarks / "figures" / feature
        assert (report_dir / "REPORT.md").is_file(), feature
        assert (figure_dir / "REPORT.png").is_file(), feature
        assert (figure_dir / "REPORT.svg").is_file(), feature


def test_el_csv_conserva_las_22_columnas_y_solo_anade():
    assert CSV_FIELDS[: len(LEGACY_CSV_FIELDS)] == LEGACY_CSV_FIELDS
    added = set(CSV_FIELDS[len(LEGACY_CSV_FIELDS):])
    assert added, "la reorganización debe añadir columnas aditivas"
    # El contrato exige que las columnas aditivas INCLUYAN estas; no se fija la
    # lista exacta porque cada banco por feature añade las suyas (layout, tabla,
    # orientación, rectificado...) además de las de proveedor.
    required = {"latex_exact", "latex_sim", "latex_token_f1", "feature",
                "box_recall", "box_iou_mean",
                "device_requested", "provider_effective"}
    assert required <= added, f"faltan columnas aditivas del contrato: {required - added}"


def test_alternativa_no_instalada_es_skipped_no_ok():
    sample = Sample("local", Image.new("RGB", (3, 2)), "hola")
    rows, meta = run_benchmark(
        [sample], "surya", "local", warmup=0,
        backend_factory=_base.unavailable_factory("surya", "surya-ocr (requiere torch)"),
    )
    assert rows == []
    assert meta["status"] == "skipped"
    assert "surya" in meta["reason"]
    assert meta["feature"] == "text"


def test_box_metrics_mide_con_gt_y_queda_vacio_sin_gt():
    # Con cajas GT: el adaptador devuelve la misma caja -> recall 1.0, IoU 1.0.
    with_boxes = Sample("b", Image.new("RGB", (4, 4)), "hola",
                        gt_boxes=((0.0, 0.0, 2.0, 2.0),))
    rows, meta = run_benchmark(
        [with_boxes], "pyocrust", "local", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput(
            "hola", extra={"boxes": [[0.0, 0.0, 2.0, 2.0]]}),
    )
    assert meta["status"] == "ok" and meta["n_ok"] == 1
    assert rows[0]["box_recall"] == 1.0 and rows[0]["box_iou_mean"] == 1.0
    # Sin cajas GT: la columna queda vacía (no evaluada), nunca un 0.0 espurio.
    without_boxes = Sample("c", Image.new("RGB", (4, 4)), "hola")
    rows, _ = run_benchmark(
        [without_boxes], "pyocrust", "local", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput("hola", extra={"boxes": []}),
    )
    assert rows[0]["box_recall"] == "" and rows[0]["box_iou_mean"] == ""


def test_box_metrics_sin_gt_no_se_inventa_un_cero():
    with pytest.raises(ValueError):
        box_metrics([], [(0, 0, 1, 1)])
    recall, mean_best = box_metrics([(0, 0, 2, 2), (10, 10, 12, 12)], [(0, 0, 2, 2)])
    assert recall == 0.5 and mean_best == 0.5


def test_tatr_registrado_como_alternativa_de_table_sin_tocar_el_csv():
    """TATR es la alternativa medida de `table` y no altera el contrato del CSV."""
    from common.runner import FEATURE_TYPES, MODEL_NAMES, PROVIDERS, TASK_TYPES, _tatr_grid_html
    from common.metrics import html_tags, table_teds

    assert "tatr" in PROVIDERS
    assert TASK_TYPES["tatr"] == FEATURE_TYPES["tatr"] == "table"
    assert MODEL_NAMES["tatr"][0] == "table-transformer-structure-recognition"
    assert "table_teds" in CSV_FIELDS
    # La rejilla de TATR produce la gramática que puntúa `table_teds`: 2 filas x 3
    # columnas -> 2*(<tr> + 3*(<td></td>) + </tr>) y TEDS 1.0 contra el mismo GT.
    grid = _tatr_grid_html(2, 3)
    assert html_tags(grid) == ["<tr>", "<td>", "</td>", "<td>", "</td>", "<td>", "</td>", "</tr>"] * 2
    assert table_teds(grid, "<table><tr><td>a</td><td>b</td><td>c</td></tr>"
                            "<tr><td>d</td><td>e</td><td>f</td></tr></table>") == 1.0
    assert table_teds(_tatr_grid_html(0, 0), grid) == 0.0


def test_seal_registrado_y_medido_sobre_gt_sintetico():
    """`seal` es una feature medida: backend registrado y dataset sintético con GT.

    El GT es sintético determinista (sello pegado en posición conocida); la métrica
    es la de cajas compartida, así que no se añade un scorer propio.
    """
    from common.datasets import DATASETS, load_synthetic_seal
    from common.runner import FEATURE_TYPES, MODEL_NAMES, PROVIDERS, TASK_TYPES
    from features import _base

    assert "seal" in _base.IMPLEMENTED_FEATURES and "seal" not in _base.SKELETON_FEATURES
    assert "pyocrust_seal" in PROVIDERS
    assert TASK_TYPES["pyocrust_seal"] == FEATURE_TYPES["pyocrust_seal"] == "seal"
    assert MODEL_NAMES["pyocrust_seal"][0] == "pp-ocrv4_mobile_seal_det"
    assert "synthetic_seal" in DATASETS
    # GT determinista: la primera caja es el rectángulo del sello pegado.
    sample = load_synthetic_seal(limit=1)[0]
    assert sample.gt_boxes == ((120.0, 140.0, 540.0, 300.0),)


def test_alternativas_onnx_de_orientation_textline_rectification():
    """`lcnet_doc_ori`/`lcnet_textline_ori`/`uvdoc` están registradas y preprocesan bien.

    Sin cargar ningún `.onnx`: comprueba el registro (backend -> tarea/banco/peso) y
    la forma + normalización ImageNet del tensor que consume el clasificador PP-LCNet.
    """
    import numpy as np

    from common.runner import (FEATURE_TYPES, MODEL_NAMES, ONNX_MODEL_FILES,
                               PROVIDERS, TASK_TYPES, _lcnet_tensor)

    esperado = {"lcnet_doc_ori": "orientation", "lcnet_textline_ori": "text_line",
                "uvdoc": "rectification"}
    for backend, feature in esperado.items():
        assert backend in PROVIDERS
        assert backend in ONNX_MODEL_FILES
        assert TASK_TYPES[backend] == FEATURE_TYPES[backend] == feature
    assert MODEL_NAMES["lcnet_doc_ori"] == ("pp-lcnet_x1_0_doc_ori", "onnxruntime")
    assert MODEL_NAMES["lcnet_textline_ori"] == ("pp-lcnet_x1_0_textline_ori", "onnxruntime")

    # Tensor CHW (1,3,H,W) con normalización ImageNet RGB del color de entrada.
    solid = Image.new("RGB", (400, 300), (128, 128, 128))
    doc = _lcnet_tensor(solid, (224, 224), 256)          # resize_short=256 + center crop
    line = _lcnet_tensor(solid, (80, 160), None)         # resize directo a 80x160
    assert doc.shape == (1, 3, 224, 224) and line.shape == (1, 3, 80, 160)
    expected = (128 / 255.0 - 0.485) / 0.229
    assert abs(float(doc[0, 0, 0, 0]) - expected) < 1e-4
    assert np.isfinite(doc).all() and np.isfinite(line).all()


def test_registro_de_39_yolo_doclaynet_y_resumen_canonico(monkeypatch):
    import common.runner as runner
    from features.summary import _license_for, _motor_label

    names = set(runner.YOLO_LAYOUT_MODELS)
    assert len(names) == 39
    assert names == set(runner.LICENSES) == {
        backend for backend in runner.MODEL_NAMES if backend in runner.YOLO_LAYOUT_MODELS
    }
    assert {runner.LICENSES[name] for name in names if name.startswith(("hantian_", "omoured_"))} == {"AGPL-3.0"}
    assert {runner.LICENSES[name] for name in names if name.startswith("armaggheddon_")} == {"MIT"}
    assert names <= set(runner.PROVIDERS) == set(runner.BACKENDS)
    assert names <= runner.GPU_CAPABLE_BACKENDS
    assert names <= set(runner.TASK_TYPES) and names <= set(runner.FEATURE_TYPES)
    assert all(runner.YOLO_LAYOUT_MODELS[name].endswith(".pt") for name in names)
    assert not {"yolov10x", "yolov10b", "yolo26m"} & names
    assert len(runner.DOCLAYNET_CLASSES) == 11

    assert runner.MODEL_NAMES["omoured_v10x"] == ("omoured/v10-x", "31.7M")
    assert runner.MODEL_NAMES["hantian_v11n"] == ("hantian/v11-n", "2.6M")
    assert runner.MODEL_NAMES["hantian_v11m"] == ("hantian/v11-m", "21.8M")
    assert runner.MODEL_NAMES["armaggheddon_y26n"] == ("armaggheddon/y26-n", "2.6M")
    for backend in names:
        model_name, params = runner.MODEL_NAMES[backend]
        label = _motor_label(backend, params or "", model_name)
        assert "/" in label
        assert _license_for(label) == runner.LICENSES[backend]

    import features.summary as summary
    monkeypatch.setattr(summary, "collect_rows", lambda: {
        ("layout", "cpu", "hantian_v11n"): [{
            "layout_map": "0.5", "model_name": "hantian/v11-n", "model_variant": "2.6M",
        }],
    })
    assert summary.measured_from_rows("layout") == {
        ("hantian/v11-n (2.6M)", "cpu"): (0.5, 1, "hantian_v11n"),
    }

    # Resuelve las 39 factorías sin cargar los pesos; el smoke con modelo real se
    # limita a un único YOLO pequeño, como exige la envolvente del banco.
    calls = []

    def fake_backend(name, device="cpu"):
        calls.append((name, device))
        return lambda image: None

    monkeypatch.setattr(runner, "_yolo_layout_backend", fake_backend)
    for backend in names:
        assert callable(runner.BACKENDS[backend](device="gpu"))
    assert set(calls) == {(name, "gpu") for name in names}
