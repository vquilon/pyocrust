"""Tests funcionales de pyocrust sobre un dataset real (FUNSD).

Ejercitan **todas** las funcionalidades expuestas a Python por `pyocrust`
(`__init__.py` / `__init__.pyi`) contra imágenes reales con ground truth, y
verifican además que el harness de benchmarking cumple su contrato de CSV.

    ./.venv/Scripts/python.exe -m pytest benchmarks/tests -q
"""

from __future__ import annotations

import pytest

import pyocrust
from run_benchmarks import (
    CSV_FIELDS,
    cer,
    levenshtein,
    normalize,
    run_benchmark,
    wer,
    word_f1,
)


def to_bytes(image):
    """`VeloceOCR.recognize` acepta ruta/bytes/PathLike, no un PIL.Image."""
    import io

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Fixtures: dataset real
# ---------------------------------------------------------------------------

FUNSD_LIMIT = 5


@pytest.fixture(scope="module")
def samples():
    from run_benchmarks import load_funsd

    return load_funsd(split="train", limit=FUNSD_LIMIT)


# ---------------------------------------------------------------------------
# Métricas (base de todo el benchmark)
# ---------------------------------------------------------------------------

def test_la_normalizacion_colapsa_espacios_y_casing():
    assert normalize("  Hola\tMUNDO  ") == "hola mundo"


def test_levenshtein_casos_base():
    assert levenshtein("", "") == 0
    assert levenshtein("abc", "abc") == 0
    assert levenshtein("abc", "abd") == 1
    assert levenshtein("", "abc") == 3


def test_cer_y_wer_castigan_y_perdonan_lo_esperado():
    assert cer("hola mundo", "hola mundo") == 0.0
    assert cer("hola mundo", "hola mund") == pytest.approx(1 / 10)
    assert wer("hola mundo", "hola mundo") == 0.0
    assert wer("hola mundo", "hola") == pytest.approx(0.5)
    assert cer("hola", "HOLA") == 0.0, "el casing no debe contar como error"


def test_word_f1_es_independiente_del_orden_de_lectura():
    assert word_f1("a b c", "c b a") == pytest.approx(1.0)
    assert word_f1("a b c", "a b") == pytest.approx(0.8)
    assert word_f1("a b", "") == 0.0


def test_cer_con_ground_truth_vacio_no_explota():
    assert cer("", "") == 0.0
    assert cer("", "algo") == 1.0


# ---------------------------------------------------------------------------
# Funcionalidades de pyocrust sobre imágenes reales
# ---------------------------------------------------------------------------

def test_reconoce_texto_no_vacio_en_todas_las_imagenes(samples):
    engine = pyocrust.VeloceOCR()
    for sample in samples:
        result = engine.recognize(to_bytes(sample.image))
        assert isinstance(result, pyocrust.OcrResult), type(result).__name__
        assert result.text.strip(), f"{sample.image_id}: texto vaciio"
        assert len(result) > 0


def test_la_calidad_sobre_el_dataset_real_supera_el_umbral(samples):
    """Umbral holgado pero real: un OCR roto no lo pasa (F1 ~ 0)."""
    engine = pyocrust.VeloceOCR()
    f1s = [word_f1(s.gt_text, engine.recognize(to_bytes(s.image)).text) for s in samples]
    assert sum(f1s) / len(f1s) > 0.3, f"F1 medio {sum(f1s) / len(f1s):.3f} demasiado bajo"


def test_las_cajas_son_validas_y_la_confianza_esta_en_rango(samples):
    engine = pyocrust.VeloceOCR()
    for sample in samples:
        for region in engine.recognize(to_bytes(sample.image)).regions:
            box = region.box
            assert box.x2 > box.x1 and box.y2 > box.y1, (box.x1, box.y1, box.x2, box.y2)
            assert 0.0 <= region.confidence <= 1.0


def test_el_texto_reconocido_es_acumulable_y_medible(samples):
    engine = pyocrust.VeloceOCR()
    for sample in samples:
        result = engine.recognize(to_bytes(sample.image))
        assert len(result.text) > 0
        assert result.confidence > 0.0


def test_resolve_models_dir_apunta_al_directorio_de_modelos():
    import pathlib

    models_dir = pyocrust.resolve_models_dir()
    assert pathlib.Path(models_dir).is_dir()
    # los artefactos del preset por defecto (Tiny) tienen que estar en disco
    assert list(pathlib.Path(models_dir).glob("*.onnx")), "sin modelos .onnx"


def test_el_preset_de_estructura_informa_cuando_faltan_modelos():
    """Sin los 9 artefactos de PP-StructureV3 debe fallar con un mensaje claro."""
    try:
        pyocrust.VeloceOCR(preset="pp_structurev3")
    except pyocrust.PyOcrError as exc:
        assert "missing" in str(exc) or "artifact" in str(exc), str(exc)
        return
    pytest.skip("los modelos de PP-StructureV3 están presentes; no aplica el chequeo")


def test_preset_desconocido_da_error_de_valor():
    with pytest.raises(pyocrust.PyOcrValueError):
        pyocrust.VeloceOCR(preset="no_existe")


def test_la_jerarquia_de_excepciones_esta_bien_formada():
    assert issubclass(pyocrust.PyOcrValueError, pyocrust.PyOcrError)
    assert issubclass(pyocrust.PyOcrRuntimeError, pyocrust.PyOcrError)


def test_el_tipo_estructura_tiene_markdown_cuando_hay_modelos():
    try:
        engine = pyocrust.VeloceOCR(preset="pp_structurev3")
    except pyocrust.PyOcrError:
        pytest.skip("faltan los modelos de PP-StructureV3")
    result = engine.recognize(samples_image_bytes())
    assert hasattr(result, "to_markdown")
    assert isinstance(result.to_markdown(), str)


def samples_image_bytes():
    from run_benchmarks import load_funsd

    from PIL import Image
    import io

    sample = load_funsd(split="train", limit=1)[0]
    buf = io.BytesIO()
    sample.image.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Contrato del harness de benchmarking
# ---------------------------------------------------------------------------

def test_el_runner_produce_filas_con_el_contrato_completo(samples):
    rows, meta = run_benchmark(samples, "pyocrust", "funsd", warmup=1)
    assert meta["status"] != "skipped"
    # el warmup ya no consume muestras: se evalúan todas las cargadas
    assert meta["n_ok"] == len(samples)
    assert rows, "no se produjeron filas"
    for row in rows:
        assert set(CSV_FIELDS) - {"run_timestamp"} <= set(row.keys())
        assert row["status"] == "ok"


def test_el_backend_informe_que_se_ejecuto_de_verdad(samples):
    rows, meta = run_benchmark(samples, "pyocrust", "funsd", warmup=0)
    assert meta["n_error"] == 0
    assert all(row["elapsed_ms"] > 0 for row in rows)


def test_backend_sin_instalar_se_marca_skipped_no_como_fallido(samples):
    # `tesseract` no está instalado en este entorno: debe quedar como skipped
    rows, meta = run_benchmark(samples, "tesseract", "funsd")
    assert meta["status"] == "skipped", meta
    assert rows == [], "un backend no disponible no puede producir filas"
    assert "tesseract" in meta["reason"] or "pytesseract" in meta["reason"]


# B7: deterministic runner/report regressions; no datasets, models or network.
@pytest.fixture
def b7_sample():
    from PIL import Image
    from run_benchmarks import Sample

    return Sample("local", Image.new("RGB", (3, 2)), "hola", "# hola", ("title",))


@pytest.mark.parametrize("backend", ["pyocrust", "pyocrust_structure"])
def test_b7_csv_contract_and_optional_markdown(b7_sample, tmp_path, backend):
    import csv
    from run_benchmarks import OcrOutput, Sample, write_csv
    from report_benchmarks import aggregate, load_rows, render_markdown

    sample = b7_sample if backend == "pyocrust" else Sample(
        "local", b7_sample.image, "hola"
    )
    rows, meta = run_benchmark(
        [sample], backend, "local", warmup=0,
        backend_factory=lambda: lambda image: OcrOutput("hola", elapsed_ms=2),
    )
    expected = [
        "run_timestamp", "backend", "dataset", "image_id", "cer", "wer",
        "cer_ord", "wer_ord", "word_f1", "exact_match", "elapsed_ms",
        "n_regions", "mean_confidence", "n_chars_gt", "n_chars_pred",
        "status", "error", "task_type", "model_name", "model_variant",
        "markdown_f1", "block_f1",
    ]
    assert CSV_FIELDS == expected
    assert set(rows[0]) == set(expected) - {"run_timestamp"}
    assert rows[0]["markdown_f1"] == rows[0]["block_f1"] == ""
    assert meta["markdown_quality"] == "not_evaluated"
    assert meta["device_requested"] == "cpu"
    assert meta["provider_effective"] == "unverified"
    path = write_csv(rows, tmp_path, "b7")
    with path.open(encoding="utf-8", newline="") as stream:
        assert next(csv.reader(stream)) == expected
    loaded = load_rows(tmp_path)
    assert loaded[0]["markdown_f1"] is loaded[0]["block_f1"] is None
    report = aggregate(loaded)
    data = next(iter(report.values()))
    assert data["markdown_f1"] is data["block_f1"] is None
    assert "N/A | N/A" in render_markdown(report)


@pytest.mark.parametrize("failure", ["unavailable", "constructor", "gpu"])
def test_b7_skipped_backend_never_produces_rows(b7_sample, failure):
    from run_benchmarks import ProviderUnavailable

    calls = []

    def factory():
        calls.append("load")
        if failure == "unavailable":
            raise ProviderUnavailable("not installed")
        raise RuntimeError("missing model")

    rows, meta = run_benchmark(
        [b7_sample], "pyocrust_structure", "local", backend_factory=factory,
        device="gpu" if failure == "gpu" else "cpu",
    )
    assert rows == []
    assert meta["status"] == "skipped"
    assert meta["reason"]
    assert meta["task_type"] == "structure"
    assert (meta["model_name"], meta["model_variant"]) == ("pp_structurev3", "default")
    assert meta["provider_effective"] == "unverified"
    assert meta["device_requested"] == ("gpu" if failure == "gpu" else "cpu")
    assert calls == ([] if failure == "gpu" else ["load"])


def test_b7_unknown_backend_summary_is_skipped(tmp_path, monkeypatch):
    import csv
    import json
    import run_benchmarks as runner

    manifest = tmp_path / "samples.json"
    manifest.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(runner, "_describe_runtime", lambda: {"test": "offline"})
    assert runner.main([
        "--manifest", str(manifest), "--backends", "b7_unknown",
        "--output-dir", str(tmp_path / "results"),
    ]) == 0
    run_dir, = (tmp_path / "results").iterdir()
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["backends"]["b7_unknown"] == {
        "status": "skipped", "reason": "no registrado",
    }
    csv_path, = run_dir.glob("*.csv")
    with csv_path.open(encoding="utf-8", newline="") as stream:
        assert list(csv.DictReader(stream)) == []


@pytest.mark.parametrize("mode", ["warmup", "all_error", "empty"])
def test_b7_no_success_is_not_ok(b7_sample, mode):
    calls = []

    def fail(image):
        calls.append(image.size)
        raise RuntimeError("inference failed")

    rows, meta = run_benchmark(
        [] if mode == "empty" else [b7_sample], "pyocrust", "local",
        warmup=1 if mode == "warmup" else 0, backend_factory=lambda: fail,
    )
    assert meta["status"] == ("empty" if mode == "empty" else "error")
    assert calls == ([] if mode == "empty" else [(3, 2)])
    if mode == "warmup":
        assert rows == []
        assert "warmup: RuntimeError: inference failed" in meta["reason"]
    else:
        assert meta["n_ok"] == 0
        assert meta["n_error"] == (1 if mode == "all_error" else 0)
        assert meta["inference_ms"] == []
        assert meta["p95_ms"] is meta["mean_ms"] is meta["mean_cer"] is None
        assert len(rows) == (1 if mode == "all_error" else 0)
        assert all(row["status"] == "error" for row in rows)


def test_b7_repeats_keep_raw_timings_and_exclude_warmup(b7_sample):
    from run_benchmarks import OcrOutput

    times = iter([999, 888, 2, 4, 9])
    calls = []

    def infer(image):
        calls.append(image)
        return OcrOutput("hola", elapsed_ms=next(times))

    rows, meta = run_benchmark(
        [b7_sample], "pyocrust", "local", warmup=2, repeats=3,
        backend_factory=lambda: infer,
    )
    assert len(calls) == 5
    assert all(image is not b7_sample.image for image in calls)
    assert len(rows) == meta["n_ok"] == meta["n_images"] == 1
    assert rows[0]["elapsed_ms"] == 5
    assert meta["mean_ms"] == 5
    assert meta["inference_ms"] == [2, 4, 9]
    assert meta["p95_ms"] == 9
    assert meta["repeats"] == 3
    assert meta["warmup"] == 2
    assert meta["image_sizes"] == {"local": [3, 2]}


@pytest.mark.parametrize("warmup,repeats", [(-1, 1), (0, 0), (0, -1)])
def test_b7_invalid_repeat_limits_reject_before_loading(warmup, repeats):
    def factory():
        pytest.fail("invalid limits must not load a model")

    with pytest.raises(ValueError):
        run_benchmark([], "pyocrust", "local", warmup=warmup,
                      repeats=repeats, backend_factory=factory)


def test_b7_legacy_missing_metrics_are_not_fake_zero(tmp_path):
    import csv
    from report_benchmarks import aggregate, load_rows, render_markdown

    fields = [field for field in CSV_FIELDS if field not in {
        "cer_ord", "wer_ord", "task_type", "model_name", "model_variant",
        "markdown_f1", "block_f1",
    }]
    with (tmp_path / "legacy.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"backend": "legacy", "status": "ok", "cer": 0.2,
                         "wer": 0.3, "word_f1": 0.7, "elapsed_ms": 10})
        writer.writerow({"backend": "legacy", "status": "error"})
    rows = load_rows(tmp_path)
    assert len(rows) == 1
    report = aggregate(rows)
    data = report["legacy (legacy; text)"]
    assert data["cer"] == 0.2
    for metric in ("cer_ord", "wer_ord", "markdown_f1", "block_f1"):
        assert rows[0][metric] is data[metric] is None
    assert "N/A | N/A" in render_markdown(report)


def test_b7_markdown_lcs_order_case_and_math():
    from run_benchmarks import markdown_f1

    assert markdown_f1("Alpha Beta Gamma", " gamma BETA alpha ") == pytest.approx(1 / 3)
    assert markdown_f1("Alpha Beta Gamma", "alpha GAMMA") == pytest.approx(0.8)
    assert markdown_f1("# Hola\n\nMUNDO", "# HOLA   mundo") == 1
    assert markdown_f1("$X$", "$x$") == 0
    assert markdown_f1("$$X$$", "$$x$$") == 0
    assert markdown_f1("Texto $X$", "TEXTO $X$") == 1
    assert markdown_f1("", "") == 1
    assert markdown_f1("hola", "") == 0


def test_b7_cer_ord_is_character_error_not_word_error():
    from run_benchmarks import cer_ord, wer_ord

    assert cer_ord("abcdefghij z", "z abcdefghik") == pytest.approx(1 / 12)
    assert wer_ord("abcdefghij z", "z abcdefghik") == pytest.approx(0.5)
    assert cer_ord("hola mundo", "MUNDO hola") == 0
    assert cer_ord("", "") == 0
    assert cer_ord("", "hola") == 1


@pytest.mark.parametrize("current", [False, True], ids=["legacy17", "current22"])
def test_b7_legacy_word_level_cer_ord_is_not_relabelled(tmp_path, current):
    import csv
    from report_benchmarks import aggregate, load_rows

    fields = CSV_FIELDS if current else CSV_FIELDS[:17]
    with (tmp_path / "metrics.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        row = {"backend": "local", "status": "ok", "cer_ord": 0.5,
               "wer_ord": 0.5}
        if current:
            row.update(task_type="text", model_variant="tiny")
        writer.writerow(row)
    rows = load_rows(tmp_path)
    data, = aggregate(rows).values()
    assert rows[0]["wer_ord"] == data["wer_ord"] == 0.5
    if current:
        assert rows[0]["cer_ord"] == data["cer_ord"] == 0.5
    else:
        assert rows[0]["cer_ord"] is data["cer_ord"] is None


def test_b7_optional_none_does_not_dilute_measured_quality(tmp_path):
    from run_benchmarks import write_csv
    from report_benchmarks import aggregate, load_rows, render_latex

    base = {"backend": "local", "status": "ok", "task_type": "structure",
            "model_variant": "default"}
    write_csv([
        dict(base, cer_ord=None, wer_ord=None, markdown_f1=None, block_f1=None),
        dict(base, cer_ord=0.2, wer_ord=0.4, markdown_f1=0.8, block_f1=0.6),
    ], tmp_path, "b7")
    rows = load_rows(tmp_path)
    report = aggregate(rows)
    data, = report.values()
    assert data["n"] == 2
    for key, expected in (("cer_ord", 0.2), ("wer_ord", 0.4),
                          ("markdown_f1", 0.8), ("block_f1", 0.6)):
        assert rows[0][key] is None
        assert data[key] == expected
    missing = aggregate(rows[:1])
    assert "N/A" in render_latex(missing)
    assert next(iter(missing.values()))["markdown_f1"] is None


def test_b7_formula_adapter_extracts_latex_not_page_markdown(b7_sample, monkeypatch):
    from types import SimpleNamespace
    from run_benchmarks import PROVIDERS

    calls = []

    class Result:
        formulas = [r"X^2", r"\frac{a}{b}"]

        def to_markdown(self):
            pytest.fail("formula adapter must not render page Markdown")

        @property
        def text(self):
            pytest.fail("formula adapter must not read page text")

    def recognize(data):
        assert isinstance(data, bytes) and data.startswith(b"\x89PNG\r\n\x1a\n")
        calls.append("recognize")
        return Result()

    def factory(*, preset):
        calls.append(preset)
        return SimpleNamespace(recognize=recognize)

    monkeypatch.setattr(pyocrust, "VeloceOCR", factory)
    rows, meta = run_benchmark(
        [b7_sample], "pyocrust_formula", "local", warmup=0,
        backend_factory=PROVIDERS["pyocrust_formula"],
    )
    assert calls == ["pp_structurev3", "recognize"]
    assert meta["status"] == "ok" and meta["n_ok"] == 1
    assert rows[0]["task_type"] == "formula"
    assert rows[0]["n_chars_pred"] == len(normalize("X^2\n" + r"\frac{a}{b}"))
    # Inspect the actual adapter output as well as the runner's metrics.
    output = PROVIDERS["pyocrust_formula"]()(b7_sample.image)
    assert output.text == "X^2\n" + r"\frac{a}{b}"


def test_b7_quality_plots_exclude_nontext(tmp_path, monkeypatch):
    from unittest.mock import MagicMock
    import report_benchmarks as reporter

    plt = MagicMock()
    fig, ax = MagicMock(), MagicMock()
    plt.subplots.return_value = (fig, ax)
    monkeypatch.setattr(reporter, "_pyplot", lambda: plt)
    text = "local (tiny; text)"
    report = {text: {"cer_ord": None, "word_f1": 0.8, "pages_per_s": 2}}
    # No text metrics: accidentally plotting these tasks fails at the boundary.
    report.update({f"local (default; {task})": {} for task in
                   ("structure", "formula", "full_page")})
    reporter.plot_quality(report, tmp_path / "quality.png")
    ax.set_xticklabels.assert_called_once_with([text])
    assert ax.bar.call_count == 2
    import math
    assert math.isnan(ax.bar.call_args_list[0].args[1][0])
    assert ax.bar.call_args_list[1].args[1] == [0.8]
    ax.reset_mock()
    reporter.plot_quality_vs_speed(report, tmp_path / "scatter.png")
    ax.scatter.assert_called_once_with(2, 0.8, s=140, label=text, zorder=3)
    ax.annotate.assert_called_once()
    assert fig.savefig.call_count == 2


# B6: fairness — todos los adaptadores entregan a su motor los MISMOS bytes PNG.
# (easyocr comparte la ruta de rapidocr; importarlo arrastra torch, así que no entra
# en la suite focal: se cubre por el mismo `_image_bytes` y por el CSV de la run.)
@pytest.mark.parametrize("backend", ["pyocrust", "rapidocr"])
def test_b6_adapters_feed_identical_png_bytes(backend, b7_sample, monkeypatch):
    import types
    from run_benchmarks import PROVIDERS, _image_bytes

    expected = _image_bytes(b7_sample.image)
    seen: list[bytes] = []

    if backend == "pyocrust":
        import pyocrust as native
        stub = types.SimpleNamespace(
            recognize=lambda data: (seen.append(data), types.SimpleNamespace(text=""))[1]
        )
        monkeypatch.setattr(native, "VeloceOCR", lambda **_kw: stub)
    else:
        import rapidocr_onnxruntime as rapidocr
        monkeypatch.setattr(
            rapidocr, "RapidOCR",
            lambda: lambda data: (seen.append(data), (None, 0.0))[1],
        )

    PROVIDERS[backend]()(b7_sample.image)
    assert seen == [expected]
    assert expected.startswith(b"\x89PNG")


def test_b6_tesseract_adapter_decodes_the_same_png_bytes(b7_sample, monkeypatch):
    import io
    import sys
    import types
    from PIL import Image
    from run_benchmarks import PROVIDERS, _image_bytes

    expected = _image_bytes(b7_sample.image)
    seen: list = []
    fake = types.SimpleNamespace(image_to_string=lambda image: (seen.append(image), "")[1])
    monkeypatch.setitem(sys.modules, "pytesseract", fake)

    PROVIDERS["tesseract"]()(b7_sample.image)
    assert len(seen) == 1
    decoded = Image.open(io.BytesIO(expected)).convert("RGB")
    assert list(seen[0].convert("RGB").getdata()) == list(decoded.getdata())
