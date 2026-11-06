"""Política de licencia en las entradas públicas; sin descargas de modelos."""

from pathlib import Path

import pytest

import pyocrust


def test_veloceocr_blocks_commercial_indra_before_model_preflight(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrValueError, match="OpenRAIL-M-Mod") as error:
        pyocrust.VeloceOCR("indra", custom_path=str(tmp_path))

    assert "license_commercial_use=False" in str(error.value)
    assert "20M" in str(error.value)
    assert list(tmp_path.iterdir()) == []


def test_veloceocr_noncommercial_policy_reaches_model_preflight(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrRuntimeError, match="PYOCRUST_OFFLINE") as error:
        pyocrust.VeloceOCR(
            "indra", custom_path=str(tmp_path),
            license_commercial_use=False, license_acknowledge=True,
        )

    assert "det.onnx" in str(error.value)
    assert list(tmp_path.iterdir()) == []


def test_veloceocr_indra_requires_attribution_even_noncommercial(tmp_path, monkeypatch):
    """§7 del LICENSE de Indra exige atribución: sin `license_acknowledge` se bloquea."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrValueError, match="license_acknowledge=True"):
        pyocrust.VeloceOCR(
            "indra", custom_path=str(tmp_path), license_commercial_use=False
        )


def test_veloceocr_allows_indra_with_noncommercial_policy(monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    # OAR_HOME puede llegar con comillas literales (inyección de entorno de
    # Hermes) y romper la ruta resuelta; el fallback `~/.oar` es el que
    # contrasta la aceptación y hace el test independiente de OAR_HOME.
    monkeypatch.delenv("OAR_HOME", raising=False)
    status = pyocrust.models_status()
    indra = status["presets"]["indra"]
    missing = [item["name"] for item in indra if not item["present"]]
    if missing:
        pytest.skip(f"faltan modelos Indra locales: {', '.join(missing)}")

    ocr = pyocrust.VeloceOCR(
        "indra", custom_path=status["models_dir"],
        license_commercial_use=False, license_acknowledge=True,
    )
    assert ocr.license["license"] == "OpenRAIL-M-Mod"
    assert ocr.license["license_commercial_use"] is False
    assert ocr.license["license_acknowledge"] is True


def test_task_spec_license_flags_require_strict_bool():
    with pytest.raises(TypeError, match="license_commercial_use must be bool"):
        pyocrust.TaskSpec(license_commercial_use="yes")

    with pytest.raises(TypeError, match="license_acknowledge must be bool"):
        pyocrust.TaskSpec(license_acknowledge=1)


def test_resolver_filters_indra_by_commercial_license_policy():
    hardware = pyocrust.HardwareProfile(
        cpu_count=8,
        ram_bytes=16 * 1024**3,
        gpu=pyocrust.GpuInfo(name="test", vram_bytes=8 * 1024**3),
    )
    default = pyocrust.resolve_pipeline(
        pyocrust.TaskSpec(quality="accuracy"), hardware
    )
    noncommercial = pyocrust.resolve_pipeline(
        pyocrust.TaskSpec(
            quality="accuracy", license_commercial_use=False, license_acknowledge=True
        ),
        hardware,
    )

    assert "indra" not in default.tasks
    assert "indra" not in pyocrust.resolve_pipeline(
        pyocrust.TaskSpec(quality="accuracy", license_commercial_use=False), hardware
    ).tasks, "sin aceptar la atribución (§7) Indra no debe recomendarse"
    assert "indra" in noncommercial.tasks


def test_explicit_task_models_are_not_blocked_by_catalog_license(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    with pytest.raises(pyocrust.PyOcrRuntimeError, match="existing local file"):
        pyocrust.TaskPredictor(
            "text_detection",
            models=str(tmp_path / "user-model.onnx"),
            license_commercial_use=True,
        )


def test_explicit_task_models_report_unknown_license(monkeypatch):
    """Con `models` explícito el getter no afirma la licencia del catálogo."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    monkeypatch.delenv("OAR_HOME", raising=False)
    model = Path(pyocrust.models_status()["models_dir"]) / "pp-ocrv6_tiny_det.onnx"
    if not model.is_file():
        pytest.skip("falta pp-ocrv6_tiny_det.onnx en la caché")
    predictor = pyocrust.TaskPredictor("text_detection", models=str(model))
    assert predictor.license["license"] == "Unknown"
    assert predictor.license["license_restricted"] is True


def test_model_catalog_classifies_indra_and_pp_licenses():
    """`model_catalog()` clasifica Indra como no comercial y PP como comercial."""
    catalog = pyocrust.model_catalog()

    indra = catalog["det.onnx"]
    assert indra["license"] == "OpenRAIL-M-Mod"
    assert indra["license_commercial_use"] is False
    assert indra["license_restricted"] is True

    pp = catalog["pp-ocrv6_tiny_det.onnx"]
    assert pp["license"] == "Apache-2.0"
    assert pp["license_commercial_use"] is True
    assert pp["license_restricted"] is False


def test_pipeline_profiles_expose_commercial_license_flags():
    """`pipeline_profiles()` refleja la política comercial por preset."""
    profiles = pyocrust.pipeline_profiles()

    indra = profiles["indra"]
    assert indra["license"] == "OpenRAIL-M-Mod"
    assert indra["license_commercial_use"] is False
    assert indra["license_restricted"] is True

    for preset in ("pp_ocrv6_tiny", "pp_structurev3"):
        profile = profiles[preset]
        assert profile["license"] == "Apache-2.0"
        assert profile["license_commercial_use"] is True
        assert profile["license_restricted"] is False


def test_veloceocr_pp_ocrv6_builds_with_apache_license(monkeypatch):
    """`VeloceOCR("pp_ocrv6")` construye y su licencia es Apache-2.0 comercial."""
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    monkeypatch.delenv("OAR_HOME", raising=False)
    status = pyocrust.models_status()
    missing = [i["name"] for i in status["presets"]["pp_ocrv6_tiny"] if not i["present"]]
    if missing:
        pytest.skip(f"faltan modelos PP-OCRv6 locales: {', '.join(missing)}")

    ocr = pyocrust.VeloceOCR("pp_ocrv6")
    assert ocr.license["license"] == "Apache-2.0"
    assert ocr.license["license_commercial_use"] is True
    assert ocr.license["license_restricted"] is False
