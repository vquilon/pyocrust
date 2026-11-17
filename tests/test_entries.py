from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

import pyocrust
from pyocrust import entries
import pyocrust.multifeature as multifeature


def _png(size=(32, 24)):
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_invalid_content_has_distinct_image_and_pdf_errors(tmp_path):
    source = tmp_path / "not-a-format.dat"
    source.write_bytes(b"not a PDF or image")

    with pytest.raises(pyocrust.IncompatibleImageError, match="no es una imagen compatible"):
        pyocrust.recognize_image(source)
    with pytest.raises(pyocrust.IncompatiblePdfError, match="no es un PDF compatible"):
        pyocrust.recognize_document(source)


def test_pdf_bytes_are_rejected_as_an_image_by_content():
    with pytest.raises(pyocrust.IncompatibleImageError):
        pyocrust.recognize_image(b"%PDF-1.7\nnot an image")


def test_available_features_obeys_declared_license():
    assert "indra" not in pyocrust.available_features()
    assert "indra" in pyocrust.available_features(
        license_commercial_use=False, license_acknowledge=True
    )


def test_license_preflight_happens_before_model_runner(monkeypatch):
    original = entries.pipeline_profiles

    def restricted_profiles():
        rows = original()
        rows["pp_ocrv6_tiny"]["license_commercial_use"] = False
        return rows

    monkeypatch.setattr(entries, "pipeline_profiles", restricted_profiles)
    monkeypatch.setattr(entries, "_run_features", lambda *a, **k: pytest.fail("model runner called"))
    with pytest.raises(pyocrust.PyOcrValueError, match="license_commercial_use=False"):
        pyocrust.recognize_image(_png())


def test_balanced_keeps_large_input_native_but_default_warns():
    values = {name: None for name in (
        "text_det_limit_side_len", "text_det_limit_type", "text_det_max_side_len",
        "text_det_thresh", "text_det_box_thresh", "text_det_unclip_ratio",
        "text_det_max_candidates",
    )}
    native_knobs, notices = entries._knobs(
        "balanced", 7000, 5000, tile_size=None, tile_overlap=None, values=values
    )
    assert native_knobs["text_det_limit_type"] == "min"
    assert native_knobs["text_det_limit_side_len"] == 64
    assert native_knobs["text_det_max_side_len"] == 7000
    assert notices == ()

    _, notices = entries._knobs(
        "default", 7000, 5000, tile_size=None, tile_overlap=None, values=values
    )
    assert notices and "text_det_limit_side_len=960" in notices[0]

    capped = {**values, "text_det_max_side_len": 4000}
    _, notices = entries._knobs(
        "balanced", 7000, 5000, tile_size=None, tile_overlap=None, values=capped
    )
    assert notices and "text_det_max_side_len=4000" in notices[0]
    with pytest.raises(pyocrust.PyOcrValueError, match="text_det_max_side_len"):
        entries._knobs("native", 7000, 5000, tile_size=None, tile_overlap=None, values=capped)


def test_large_image_entry_matches_full_resolution_recipe(monkeypatch):
    """The public default must retain at least as many boxes as Paddle's native recipe."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    if not font_path.is_file():
        pytest.skip("Arial TrueType font is unavailable")
    models = Path("D:/Environments/cache/oar")
    required = (
        "pp-ocrv6_medium_det.onnx", "pp-ocrv6_medium_rec.onnx", "ppocrv6_tiny_dict.txt",
        "pp-lcnet_x1_0_doc_ori.onnx", "uvdoc.onnx", "pp-lcnet_x1_0_textline_ori.onnx",
    )
    if not all((models / name).is_file() for name in required):
        pytest.skip("PP-OCRv6 medium models are unavailable")
    monkeypatch.setattr(entries, "_task_feature", lambda task: "pp_ocrv6_medium")

    image = Image.new("RGB", (7000, 5000), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_path), 7)
    content = [
        "fine chino 1", "fine chino 2", "fine chino 3", "fine chino 4", "fine chino 5",
        "fine chino 6", "fine chino 7", "fine chino 8", "1234567890 fin 01", "1234567890 fin 02",
    ]
    for index in range(112):
        draw.text((20, 22 + index * 44), f"{content[index % len(content)]} #{index:03d}",
                  fill="black", font=font)
    encoded = BytesIO()
    image.save(encoded, format="PNG")
    png = encoded.getvalue()

    recipe = {
        "text_det_limit_type": "min",
        "text_det_limit_side_len": 64,
        "text_det_max_side_len": 7000,
    }
    engine = pyocrust.VeloceOCR(
        "pp_ocrv6_medium", custom_path=str(models), device="cpu",
        use_doc_orientation=False, use_doc_unwarping=False, use_textline_orientation=False,
    )
    reference = engine.detect_regions(png, **recipe)

    def detect_from_entry(image, labels, ids, **kwargs):
        boxes = engine.detect_regions(image, **kwargs["det_knobs"])
        return pyocrust.OcrResult([pyocrust.TextRegion("", 0.0, box) for box in boxes])

    monkeypatch.setattr(entries, "_run_features", detect_from_entry)
    actual = pyocrust.recognize_image(png, custom_path=str(models), device="cpu")

    assert reference, "the full-resolution recipe must detect the synthetic fine text"
    assert len(actual.regions) >= len(reference), (
        f"balanced default returned {len(actual.regions)} regions; native recipe returned "
        f"{len(reference)}"
    )


def test_tiled_mode_calls_rust_tiled_path_with_detection_policy(monkeypatch):
    captured = {}

    def fake_runner(image, labels, ids, **kwargs):
        captured.update(kwargs)
        return pyocrust.OcrResult([])

    monkeypatch.setattr(entries, "_run_features", fake_runner)
    result = pyocrust.recognize_image(_png(), resolution="tiled", tile_size=512, tile_overlap=64)
    assert isinstance(result, pyocrust.OcrResult)
    assert captured["tiled"] is True
    assert captured["tile_size"] == 512
    assert captured["tile_overlap"] == 64
    assert captured["det_knobs"]["text_det_limit_type"] == "min"


def test_tiled_entry_runs_the_native_rust_path(modelos_tiny, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    result = pyocrust.recognize_image(
        _png((640, 300)), resolution="tiled", tile_size=512, tile_overlap=128,
        custom_path=str(modelos_tiny), device="cpu",
    )
    assert isinstance(result, pyocrust.OcrResult)


def test_document_pages_reuse_text_layer_and_ocr_only_scan(monkeypatch):
    fixture = Path(__file__).parent / "data" / "mixed_text_and_scan.pdf"
    library = None
    try:
        import pypdfium2_raw
        library = Path(pypdfium2_raw.__file__).parent / "pdfium.dll"
    except ImportError:
        pytest.skip("pdfium.dll is unavailable")
    if not library.is_file():
        pytest.skip("pdfium.dll is unavailable")
    monkeypatch.setenv("PYOCRUST_PDFIUM_LIB", str(library))
    calls = []

    def fake_run(image, feature, **kwargs):
        calls.append((image, feature))
        return pyocrust.OcrResult([])

    monkeypatch.setattr(entries, "_run", fake_run)
    result = pyocrust.recognize_document(fixture, dpi=200, device="cpu")
    assert [page.index for page in result.pages] == [1, 2]
    text_page, scan_page = result.pages
    assert text_page.source == "text_layer"
    assert text_page.output.text == (
        "Este PDF es un fixture sintetico de pyocrust:\n"
        "la pagina 1 lleva una capa de texto real,\n"
        "de sobra para superar text_min_chars."
    )
    assert scan_page.source == "ocr"
    assert isinstance(scan_page.output, pyocrust.OcrResult)
    assert len(calls) == 1 and calls[0][1] == "pp_ocrv6_tiny"
    assert calls[0][0][:8] == b"\x89PNG\r\n\x1a\n"


def test_pages_none_means_all_and_explicit_selection_is_preserved(monkeypatch):
    fixture = Path(__file__).parent / "data" / "mixed_text_and_scan.pdf"
    try:
        import pypdfium2_raw
        library = Path(pypdfium2_raw.__file__).parent / "pdfium.dll"
    except ImportError:
        pytest.skip("pdfium.dll is unavailable")
    if not library.is_file():
        pytest.skip("pdfium.dll is unavailable")
    monkeypatch.setenv("PYOCRUST_PDFIUM_LIB", str(library))
    monkeypatch.setattr(entries, "_run", lambda *a, **k: pyocrust.OcrResult([]))

    all_pages = pyocrust.recognize_document(fixture, dpi=200)
    only_scan = pyocrust.recognize_document(fixture, pages=[2], dpi=200)
    assert [page.index for page in all_pages.pages] == [1, 2]
    assert [page.index for page in only_scan.pages] == [2]
    assert only_scan.pages[0].source == "ocr"


def test_session_reuses_one_runner_across_documents_and_releases_it(monkeypatch, tmp_path):
    fixture = Path(__file__).parent / "data" / "mixed_text_and_scan.pdf"
    try:
        import pypdfium2_raw
        library = Path(pypdfium2_raw.__file__).parent / "pdfium.dll"
    except ImportError:
        pytest.skip("pdfium.dll is unavailable")
    if not library.is_file():
        pytest.skip("pdfium.dll is unavailable")
    monkeypatch.setenv("PYOCRUST_PDFIUM_LIB", str(library))
    documents = [tmp_path / "first.pdf", tmp_path / "second.pdf"]
    for path in documents:
        path.write_bytes(fixture.read_bytes())

    constructed = []
    released = []

    class Runner:
        def __call__(self, image):
            return pyocrust.OcrResult([])

        def __del__(self):
            released.append(True)

    def make_runner(feature_id, *args, **kwargs):
        constructed.append(feature_id)
        return Runner()

    monkeypatch.setattr(multifeature, "_runner", make_runner)
    session = pyocrust.Session(device="cpu")
    with session:
        for path in documents:
            pages = session.iter_document_pages(path, dpi=200)
            assert next(pages).source == "text_layer"
            assert pyocrust.parse_document(path, pages=[1], dpi=200)
            scan = next(pages)
            assert scan.source == "ocr"
            assert isinstance(scan.output, pyocrust.OcrResult)
            assert next(pages, None) is None
        assert constructed == ["pp_ocrv6_tiny"]
        assert len(session._runners) == 1
    assert released == [True]
    assert not session._runners
    with pytest.raises(pyocrust.PyOcrRuntimeError, match="active with block"):
        session.recognize_image(_png())


def test_session_purge_releases_runners_and_allows_reload(monkeypatch):
    constructed = []
    released = []

    class Runner:
        def __call__(self, image):
            return pyocrust.OcrResult([])

        def __del__(self):
            released.append(True)

    def make_runner(feature_id, *args, **kwargs):
        constructed.append(feature_id)
        return Runner()

    monkeypatch.setattr(multifeature, "_runner", make_runner)
    with pyocrust.Session(device="cpu") as session:
        session.recognize_image(_png())
        assert len(session._runners) == 1
        session.purge()
        assert not session._runners
        assert released == [True]
        session.recognize_image(_png())
        assert constructed == ["pp_ocrv6_tiny", "pp_ocrv6_tiny"]
    assert released == [True, True]
