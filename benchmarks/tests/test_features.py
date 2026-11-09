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


def test_nuevas_alternativas_de_table_registradas():
    """`paddleocr_slanet` y `docling_tableformer` son alternativas medidas de `table`.

    Ambos backends están registrados con su `task_type`/`feature`/`model_name` y
    sus licencias resueltas (Apache-2.0 / MIT), y el banco de `table` los corre
    por defecto junto a `tatr`. La normalización `<th>`->`<td>` del scorer no
    penaliza la cabecera de TableFormer (misma celda en el TEDS-S).
    """
    from common.runner import FEATURE_TYPES, LICENSES, MODEL_NAMES, PROVIDERS, TASK_TYPES
    from features.table.bank import DEFAULT_BACKENDS, _table_html, score_table
    from common.runner import OcrOutput
    from common import Sample
    from PIL import Image

    for backend, model_name, license_name in [
        ("paddleocr_slanet", "SLANet_plus", "Apache-2.0"),
        ("docling_tableformer", "tableformer", "MIT"),
    ]:
        assert backend in PROVIDERS, backend
        assert TASK_TYPES[backend] == FEATURE_TYPES[backend] == "table", backend
        assert MODEL_NAMES[backend][0] == model_name, backend
        assert LICENSES[backend] == license_name, backend
        assert backend in DEFAULT_BACKENDS.split(","), backend

    # `<th>` (cabecera de TableFormer) se normaliza a `<td>`: misma celda.
    sample = Sample("t", Image.new("RGB", (4, 4)), "",
                    gt_html="<table><tr><td>a</td><td>b</td></tr></table>")
    th = OcrOutput("<html><body><table><tr><th>a</th><th>b</th></tr></table></body></html>")
    assert _table_html(th.text).count("<td") == 2
    assert score_table(sample, th) == {"table_teds": 1.0}


def test_default_backends_solo_nombres_que_producen_filas():
    """`text`: el default no anuncia motores sin fabrica (criterio de la tarjeta).

    Los anunciados sin adaptador (`surya`/`paddleocr`/`python-doctr`) quedan fuera del
    default —ahí solo va lo que produce filas— pero siguen siendo un `skipped`
    honesto si se piden de forma explícita.
    """
    from common.runner import PROVIDERS
    from features.text.bank import DEFAULT_BACKENDS, EXTRA_FACTORIES

    defaults = DEFAULT_BACKENDS.split(",")
    assert defaults == ["pyocrust", "rapidocr", "easyocr", "tesseract"]
    for absent in ("surya", "paddleocr", "python-doctr"):
        assert absent not in defaults, absent
        assert absent in EXTRA_FACTORIES, absent  # explícito -> skipped con motivo
    # Todo backend del default tiene fabrica real en `PROVIDERS` o en las EXTRA.
    for name in defaults:
        assert name in PROVIDERS, name


def test_formula_default_sin_motores_fantasma():
    """`formula`: cada nombre de `DEFAULT_BACKENDS` resuelve a una fabrica real.

    Regla de la tarjeta: el default no anuncia lo que nunca produce fila. Los 7
    nombres del default salen de `PROVIDERS` (runner) o de las `EXTRA_FACTORIES`
    del banco, y ninguno es un `unavailable_factory` (eso seria un `skipped`
    anunciado en el default = motor fantasma). Las 5 alternativas declaradas sin
    integrar (`texify`/`nougat`/`pix2text`/`texteller`/`img2latex`) quedan FUERA
    del default, disponibles solo via `--backends` como `skipped` con motivo.
    """
    from common.runner import PROVIDERS
    from features.formula.bank import DEFAULT_BACKENDS, EXTRA_FACTORIES, SPEC

    defaults = [b.strip() for b in DEFAULT_BACKENDS.split(",") if b.strip()]
    real = {**PROVIDERS, **EXTRA_FACTORIES}

    # (1) Todo nombre del default existe y NO es un `unavailable_factory`.
    #     Chequeo ESTRUCTURAL (sin cargar modelos): una `unavailable_factory`
    #     se reconoce por su qualname; llamarla dispararia carga de pesos.
    def _es_unavailable(factory) -> bool:
        return "unavailable_factory" in getattr(factory, "__qualname__", "")

    for name in defaults:
        assert name in real, f"{name}: anunciado en el default sin fabrica"
        assert not _es_unavailable(real[name]), (
            f"{name}: en el default pero es unavailable (motor fantasma)")

    # (2) Las declaradas sin integrar NO viven en el default y sí en las EXTRA
    #     como `unavailable_factory` (skipped honesto si se piden explicitamente).
    declaradas_sin_integrar = {"texify", "nougat", "pix2text", "texteller", "img2latex"}
    for name in declaradas_sin_integrar:
        assert name not in defaults, f"{name}: no debe estar en el default"
        assert name in EXTRA_FACTORIES, name
        assert _es_unavailable(EXTRA_FACTORIES[name]), (
            f"{name}: debia ser unavailable_factory (skipped con motivo)")

    # (3) `unimernet` es la alternativa nueva integrada: en `PROVIDERS`, no en EXTRA.
    assert "unimernet" in defaults
    assert "unimernet" in PROVIDERS
    assert "unimernet" not in EXTRA_FACTORIES

    # (4) `pix2tex` sigue medido (fabrica real) y es una de las declaradas.
    assert "pix2tex" in defaults
    assert SPEC.alternatives["pix2tex (LaTeX-OCR)"][0] == "pix2tex"


def test_orientation_y_rectification_con_alternativa_no_paddleocr():
    """`orientation` y `rectification` ≥2 entradas, ≥1 NO pesos PaddleOCR.

    `orientation`: `easyocr_rotation` (reconocimiento en 4 rotaciones, proyecto
    EasyOCR). `rectification`: `opencv_perspective` (línea base geométrica clásica
    sin pesos). Ninguno carga un `.onnx` de PaddleOCR.
    """
    from common.runner import (ALTERNATIVE_PROVENANCE, FEATURE_TYPES, MODEL_NAMES,
                               PROVIDERS, TASK_TYPES, alternative_provenance)
    from features.orientation.bank import DEFAULT_BACKENDS as ORI
    from features.rectification.bank import DEFAULT_BACKENDS as RECT

    assert "easyocr_rotation" in ORI.split(",")
    assert "opencv_perspective" in RECT.split(",")
    for backend, task in (("easyocr_rotation", "orientation"),
                          ("opencv_perspective", "rectification")):
        assert backend in PROVIDERS, backend
        assert TASK_TYPES[backend] == FEATURE_TYPES[backend] == task, backend
        assert alternative_provenance(backend) != "mismo_peso_otra_via", backend
    # `onxx`/PaddleOCR de esas tareas SÍ se declaran "mismo peso, distinta vía".
    for backend in ("lcnet_doc_ori", "uvdoc"):
        assert alternative_provenance(backend) == "mismo_peso_otra_via", backend
    assert MODEL_NAMES["easyocr_rotation"][0] == "craft_mlt_25k+latin_g2"
    assert MODEL_NAMES["opencv_perspective"][0] == "perspective-4corner"
    assert "baseline_clasico" in set(ALTERNATIVE_PROVENANCE.values())


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
    # Alternativa externa real: mismos pesos, otro runtime (`onnxruntime`).
    from common.runner import ONNX_MODEL_FILES
    assert "onnx_seal_det" in PROVIDERS
    assert TASK_TYPES["onnx_seal_det"] == FEATURE_TYPES["onnx_seal_det"] == "seal"
    assert MODEL_NAMES["onnx_seal_det"] == ("pp-ocrv4_mobile_seal_det", "onnxruntime")
    assert ONNX_MODEL_FILES["seal_det"] == "pp-ocrv4_mobile_seal_det.onnx"
    # GT determinista: la primera caja es el rectángulo del sello pegado.
    sample = load_synthetic_seal(limit=1)[0]
    assert sample.gt_boxes == ((120.0, 140.0, 540.0, 300.0),)


def test_seal_det_postproceso_db_extrae_una_caja():
    """El postproceso DB (`_paddle_det_boxes`) saca la caja del anillo del sello.

    Mapa de probabilidad sintético: un anillo (marco) blanco sobre negro, como el
    borde de un tampón. `findContours` devuelve ambas fronteras del anillo (exterior
    e interior), así que se comprueba que la caja **exterior** —la del sello— está
    entre las extraídas y alineada con el marco (`unclip=1.0`: sin expansión).
    """
    import numpy as np

    from common.runner import (_SEAL_DET_BOX_THRESH, _SEAL_DET_MIN_AREA, _SEAL_DET_THRESH,
                               _SEAL_DET_UNCLIP, _paddle_det_boxes)

    prob = np.zeros((200, 300), np.float32)
    prob[40:160, 30:270] = 0.9           # relleno del sello
    prob[60:140, 50:250] = 0.0           # hueco central (solo queda el anillo)
    boxes = _paddle_det_boxes(prob, 1.0, _SEAL_DET_THRESH, _SEAL_DET_BOX_THRESH,
                              _SEAL_DET_UNCLIP, _SEAL_DET_MIN_AREA)
    assert boxes, "el anillo del sello debe producir al menos una caja"
    # La caja exterior del sello: la de mayor área.
    x1, y1, x2, y2 = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    assert abs(x1 - 30) <= 3 and abs(y1 - 40) <= 3 and abs(x2 - 270) <= 6 and abs(y2 - 160) <= 6, (x1, y1, x2, y2)


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
    # Los 39 YOLO son un subconjunto **propio** de `LICENSES`: los pipelines
    # documentales `full_page` (`pp_structurev3_api`, `docling`) también se
    # licencian ahí, pero no son YOLO. La igualdad se acota a los YOLO.
    assert names == {b for b in runner.MODEL_NAMES if b in runner.YOLO_LAYOUT_MODELS}
    assert names <= set(runner.LICENSES)
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
