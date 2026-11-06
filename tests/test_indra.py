"""Contrato Indra offline; usa la caché real sin descargar modelos."""

from pathlib import Path

import pytest

import pyocrust


def test_indra_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOCRUST_OFFLINE", "1")
    estado = pyocrust.models_status()
    artefactos = estado["presets"]["indra"]
    assert len(artefactos) == 9
    assert len({a["name"] for a in artefactos}) == 9
    assert all(a["required"] is True for a in artefactos)
    assert estado["offline"] is True

    with pytest.raises(pyocrust.PyOcrRuntimeError) as error:
        pyocrust.VeloceOCR(
            "indra", custom_path=str(tmp_path),
            license_commercial_use=False, license_acknowledge=True,
        )
    mensaje = str(error.value)
    assert "PYOCRUST_OFFLINE" in mensaje
    assert "VeloceOCR('indra')" in mensaje
    assert all(a["name"] in mensaje for a in artefactos)
    assert not any(tmp_path.iterdir()), "la caché vacía debe seguir vacía"

    faltantes = [a["name"] for a in artefactos if not a["present"]]
    if faltantes:
        pytest.skip(
            f"modelos Indra reales ausentes en {estado['models_dir']}: "
            f"{', '.join(faltantes)}; no se descargan en este test offline. "
            "Desde la raíz en Windows: ./.venv/Scripts/python.exe -c "
            '"import os; import pyocrust; '
            "os.environ.pop('PYOCRUST_OFFLINE', None); "
            f"pyocrust.VeloceOCR('indra', custom_path={estado['models_dir']!r})\""
        )
    datos = Path(__file__).parent / "data"
    ocr = pyocrust.VeloceOCR(
        "indra", custom_path=estado["models_dir"],
        license_commercial_use=False, license_acknowledge=True,
    )

    resultado = ocr.recognize(datos / "sample_text.png")
    assert isinstance(resultado, pyocrust.StructureResult)
    assert resultado.regions
    assert resultado.elements
    assert resultado.to_markdown().strip()

    latex = ocr.recognize(datos / "indra_math.png")
    assert isinstance(latex, pyocrust.StructureResult)
    assert latex.regions
    assert any("$" in region.text for region in latex.regions), (
        "Indra math must preserve inline LaTeX in recognized reading-order lines"
    )
    assert "$" in latex.to_markdown(), "Markdown must retain inline LaTeX delimiters"
