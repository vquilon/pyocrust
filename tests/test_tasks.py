"""End-to-end schemas for task-specific ``oar-ocr`` predictors.

Run with: ``python -m pytest tests/test_tasks.py -q``. If an artifact is
missing, run ``python -c \"import pyocrust; pyocrust.TaskPredictor('<task>')\"``
to fetch it through the ModelScope registry.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import pyocrust

IMAGE = Path(__file__).parent / "data" / "sample_text.png"
TASKS = {
    "document_orientation": (("pp-lcnet_x1_0_doc_ori.onnx",), "orientations"),
    "document_rectification": (("uvdoc.onnx",), "image"),
    "text_line_orientation": (("pp-lcnet_x1_0_textline_ori.onnx",), "orientations"),
    "seal_text_detection": (("pp-ocrv4_mobile_seal_det.onnx",), "detections"),
    "formula_recognition": (("pp-formulanet-s.onnx", "pp-formulanet-tokenizer.json"), "formula"),
}


@pytest.mark.parametrize(("task", "artifacts", "key"), [(k, *v) for k, v in TASKS.items()])
def test_task_predictor_result_schema(task: str, artifacts: tuple[str, ...], key: str, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    models_dir = Path(os.environ.get("OAR_HOME", Path.home() / ".oar"))
    missing = [name for name in artifacts if not (models_dir / name).is_file()]
    if missing:
        pytest.skip(
            f"faltan {', '.join(missing)}; ejecutar: python -c \"import pyocrust; "
            f"pyocrust.TaskPredictor('{task}')\""
        )
    options = (
        {"input_shape": (80, 160), "topk": 1, "score_threshold": 0.0}
        if task == "text_line_orientation" else {}
    )
    predictor = pyocrust.TaskPredictor(task, **options)
    result = predictor.predict(IMAGE)
    if task == "text_line_orientation":
        assert len(result["orientations"]) == 1
    assert isinstance(result, dict)
    assert key in result
    if key == "orientations":
        assert isinstance(result[key], list)
        if result[key]:
            assert {"class_id", "label", "score"} <= set(result[key][0])
            assert isinstance(result[key][0]["class_id"], int)
            assert isinstance(result[key][0]["label"], str)
            assert isinstance(result[key][0]["score"], float)
    elif key == "image":
        from io import BytesIO

        from PIL import Image

        results = [result, predictor.predict(IMAGE.read_bytes()), predictor.predict(str(IMAGE))]
        batch = predictor.predict_batch([IMAGE, IMAGE.read_bytes()])
        assert isinstance(batch, list) and len(batch) == 2
        for rectified in results + batch:
            assert isinstance(rectified, dict)
            assert isinstance(rectified["image"], bytes)
            assert isinstance(rectified["width"], int) and isinstance(rectified["height"], int)
            with Image.open(BytesIO(rectified["image"])) as decoded:
                assert decoded.format == "PNG"
                decoded.load()
                assert decoded.size == (rectified["width"], rectified["height"])
    elif key == "detections":
        assert isinstance(result[key], list)
        if result[key]:
            assert {"bbox", "score"} <= set(result[key][0])
            assert isinstance(result[key][0]["bbox"], list)
            assert isinstance(result[key][0]["score"], float)
    else:
        assert isinstance(result[key], str)
        assert result["score"] is None or isinstance(result["score"], float)


@pytest.mark.parametrize(("task", "option"), [
    (task, option)
    for task, supported in {
        "document_orientation": {"score_threshold", "topk"},
        "text_line_orientation": {"score_threshold", "topk", "input_shape"},
        "seal_text_detection": {"score_threshold"},
        "document_rectification": set(),
        "formula_recognition": set(),
    }.items()
    for option in ("unknown_option", "score_threshold", "topk", "input_shape")
    if option not in supported
])
def test_unsupported_options_precede_model_loading(task, option, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrValueError, match=f"unsupported option '{option}'"):
        pyocrust.TaskPredictor(task, models="nonexistent-task-model.onnx", **{option: 1})


NEW_TASKS = {
    "text_detection": (("pp-ocrv6_tiny_det.onnx",), "detections"),
    "text_recognition": (("pp-ocrv6_tiny_rec.onnx", "ppocrv6_tiny_dict.txt"), "text"),
    "layout_detection": (("pp-doclayoutv3.onnx",), "elements"),
    "table_classification": (("pp-lcnet_x1_0_table_cls.onnx",), "classifications"),
    "table_structure_recognition": (("slanext_wired.onnx", "table_structure_dict_ch.txt"), "structures"),
    "table_cell_detection": (("rt-detr-l_wired_table_cell_det.onnx",), "cells"),
}


@pytest.mark.parametrize(("task", "artifacts", "key"), [(k, *v) for k, v in NEW_TASKS.items()])
def test_new_task_defaults_and_batch_two(task, artifacts, key, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    models_dir = Path(os.environ.get("OAR_HOME", Path.home() / ".oar"))
    missing = [name for name in artifacts if not (models_dir / name).is_file()]
    if missing:
        pytest.skip(
            f"faltan {', '.join(missing)}; ejecutar fuera de offline: python -c \"import pyocrust; "
            f"pyocrust.TaskPredictor('{task}')\""
        )
    predictor = pyocrust.TaskPredictor(task)
    single = predictor.predict(IMAGE)
    batch = predictor.predict_batch([IMAGE, IMAGE.read_bytes()])
    assert isinstance(batch, list) and len(batch) == 2
    for result in [single, *batch]:
        assert isinstance(result, dict) and key in result
        if key == "text":
            assert isinstance(result[key], str) and result[key]
            assert isinstance(result["score"], float)
            continue
        assert isinstance(result[key], list)
        if key == "classifications":
            assert result[key], "classification must not pass vacuously"
            for item in result[key]:
                assert isinstance(item["class_id"], int)
                assert isinstance(item["label"], str)
                assert isinstance(item["score"], float)
        elif key == "structures":
            assert all(isinstance(token, str) for token in result[key])
            assert isinstance(result["bboxes"], list)
            assert all(isinstance(box, list) and all(isinstance(v, float) for v in box)
                       for box in result["bboxes"])
        else:
            for item in result[key]:
                assert isinstance(item["bbox"], list) and len(item["bbox"]) == 4
                assert all(isinstance(point, list) and len(point) == 2
                           and all(isinstance(v, float) for v in point) for point in item["bbox"])
                assert isinstance(item["score"], float)
                if key == "elements":
                    assert isinstance(item["element_type"], str)
                elif key == "cells":
                    assert isinstance(item["label"], str)
            if key == "elements":
                assert isinstance(result["is_reading_order_sorted"], bool)


@pytest.mark.parametrize("task", [*TASKS, *NEW_TASKS])
def test_all_task_names_reach_explicit_model_loading(task, tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrRuntimeError, match="nonexistent-task-model.onnx"):
        pyocrust.TaskPredictor(task, models=str(tmp_path / "nonexistent-task-model.onnx"))


def test_unknown_task_precedes_explicit_model_loading(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrValueError, match="unknown task 'unknown_task'"):
        pyocrust.TaskPredictor("unknown_task", models=str(tmp_path / "nonexistent-task-model.onnx"))


@pytest.mark.parametrize("shape", [(0, 160), (80, 0)])
def test_zero_input_shape_precedes_model_loading(shape, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrValueError, match="input_shape dimensions must be positive"):
        pyocrust.TaskPredictor(
            "text_line_orientation", models="nonexistent-task-model.onnx", input_shape=shape
        )


@pytest.mark.parametrize("exists", [False, True])
def test_registered_bare_model_path_stays_local(exists, tmp_path, monkeypatch, fuente_modelos):
    import shutil

    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / "empty-cache"
    cache.mkdir()
    monkeypatch.setenv("OAR_HOME", str(cache))
    name = "pp-ocrv6_tiny_det.onnx"
    if exists:
        shutil.copy2(fuente_modelos / name, tmp_path / name)
        result = pyocrust.TaskPredictor("text_detection", models=name).predict(IMAGE.resolve())
        assert isinstance(result["detections"], list)
    else:
        with pytest.raises(pyocrust.PyOcrRuntimeError, match="implicit upstream downloads are disabled"):
            pyocrust.TaskPredictor("text_detection", models=name)
    assert list(cache.iterdir()) == []


@pytest.mark.parametrize("invalid_dict", ["nonexistent-dictionary.txt", None])
def test_dict_path_overrides_invalid_models_dict(invalid_dict, fuente_modelos, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    predictor = pyocrust.TaskPredictor(
        "text_recognition",
        models={"model": str(fuente_modelos / "pp-ocrv6_tiny_rec.onnx"), "dict": invalid_dict},
        dict_path=str(fuente_modelos / "ppocrv6_tiny_dict.txt"),
    )
    result = predictor.predict(IMAGE)
    assert isinstance(result["text"], str) and result["text"]
    assert isinstance(result["score"], float)


def test_table_structure_score_threshold_precedes_model_loading(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    monkeypatch.setenv("OAR_HOME", str(tmp_path))
    with pytest.raises(pyocrust.PyOcrValueError, match="unsupported option 'score_threshold'"):
        pyocrust.TaskPredictor(
            "table_structure_recognition", models="slanext_wired.onnx", score_threshold=0.5
        )
    assert list(tmp_path.iterdir()) == []
