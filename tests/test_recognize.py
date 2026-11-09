"""`recognize` end-to-end (`DESIGN.md` §3.1 y §3.2).

Escenarios que cubre `DESIGN.md`:

* **carga directa** — `VeloceOCR(preset, custom_path=...)` (nivel 1);
* **variable de entorno** — `OAR_HOME` (nivel 2);
* **caché por defecto** — `~/.oar` (nivel 3).

Los tres construyen el pipeline de PP-OCRv6 Tiny y reconocen una imagen real de
texto. Necesitan los 3 artefactos del preset en disco: si el host no los tiene,
los tests se marcan `skip` con el motivo (la suite no descarga nada por su
cuenta).

El escenario de PP-StructureV3 (ADR-003: `StructureResult` con `to_markdown()`)
se ejecuta cuando el host tiene sus artefactos y se marca `skip` con el motivo
cuando no. El test de LaTeX usa `tests/data/sample_formula.png`, una página real
de OmniDocBench con regiones de fórmula que PP-DocLayoutV3 detecta como fórmula.

Ejecución: `python -m pytest tests/test_recognize.py -q`
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pyocrust import (
    OcrResult,
    PyOcrRuntimeError,
    PyOcrValueError,
    StructureResult,
    VeloceOCR,
    available_providers,
)

from conftest import (
    PP_OCRV6_TINY,
    PP_STRUCTUREV3,
    directorios_candidatos,
    fuente_modelos,
)

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"

# Las dos líneas del fixture, reconocidas por PP-OCRv6 Tiny con confianza > 0.97.
LINEAS_ESPERADAS = ("Hola mundo 12345", "Factura 2026-10-25")


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Sin `OAR_HOME`/`OCR_MODELS_CACHE_DIR`: cada escenario fija el suyo."""
    for variable in ("OAR_HOME", "OCR_MODELS_CACHE_DIR"):
        monkeypatch.delenv(variable, raising=False)


def _afirmar_reconocimiento(ocr: VeloceOCR) -> None:
    """Contrato de salida de `recognize`: texto, confianza y cajas válidas."""
    assert IMAGEN.is_file(), "falta el fixture de imagen de tests/data/"

    resultado = ocr.recognize(str(IMAGEN))

    # Un preset de texto devuelve `OcrResult`, nunca `StructureResult`.
    assert isinstance(resultado, OcrResult)
    assert len(resultado.regions) >= len(LINEAS_ESPERADAS)
    for linea in LINEAS_ESPERADAS:
        assert linea in resultado.text
    assert 0.0 < resultado.confidence <= 1.0
    for region in resultado.regions:
        assert region.text
        assert 0.0 < region.confidence <= 1.0
        assert region.box.width > 0
        assert region.box.height > 0


def test_reconocer_con_carga_directa(modelos_tiny):
    """Escenario 1: el nivel 1 (custom_path) es el que se usa."""
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    assert Path(ocr.models_dir) == modelos_tiny
    _afirmar_reconocimiento(ocr)


def test_reconocer_con_variable_de_entorno(modelos_tiny, monkeypatch):
    """Escenario 2: sin `custom_path`, `OAR_HOME` resuelve el directorio."""
    monkeypatch.setenv("OAR_HOME", str(modelos_tiny))

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == modelos_tiny
    _afirmar_reconocimiento(ocr)


def test_reconocer_con_la_cache_por_defecto(tmp_path, monkeypatch, fuente_modelos):
    """Escenario 3: sin `custom_path` ni entorno, la caché es `<home>/.oar`."""
    cache = tmp_path / ".oar"
    cache.mkdir()
    for nombre in PP_OCRV6_TINY:
        shutil.copy2(fuente_modelos / nombre, cache / nombre)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    ocr = VeloceOCR("pp_ocrv6")

    assert Path(ocr.models_dir) == cache
    _afirmar_reconocimiento(ocr)


def test_recognize_acepta_ruta_bytes_y_pathlike(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))
    datos = IMAGEN.read_bytes()

    desde_ruta = ocr.recognize(str(IMAGEN))
    desde_bytes = ocr.recognize(datos)
    desde_pathlike = ocr.recognize(IMAGEN)

    assert desde_ruta.text.count("\n") >= 1
    assert desde_bytes.text == desde_ruta.text
    assert desde_pathlike.text == desde_ruta.text


def test_recognize_rechaza_una_ruta_que_no_existe(modelos_tiny, tmp_path):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrRuntimeError):
        ocr.recognize(str(tmp_path / "no_existe.png"))


def test_recognize_rechaza_bytes_que_no_son_una_imagen(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrRuntimeError):
        ocr.recognize(b"esto no es una imagen")


def test_recognize_rechaza_un_tipo_no_soportado(modelos_tiny):
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    with pytest.raises(PyOcrValueError):
        ocr.recognize(12345)


def test_llamar_dos_veces_no_recarga_el_pipeline(modelos_tiny):
    """El modelo queda residente tras el constructor (ADR-002)."""
    ocr = VeloceOCR("pp_ocrv6", custom_path=str(modelos_tiny))

    primero = ocr.recognize(str(IMAGEN))
    segundo = ocr.recognize(str(IMAGEN))

    assert primero.text == segundo.text


def _directorio_structurev3() -> Path:
    """Directorio con los 9 artefactos de PP-StructureV3, o `skip` con el motivo."""
    for directorio in directorios_candidatos():
        if all((directorio / nombre).is_file() for nombre in PP_STRUCTUREV3):
            return directorio

    faltan = [
        nombre
        for nombre in PP_STRUCTUREV3
        if not any((directorio / nombre).is_file() for directorio in directorios_candidatos())
    ]
    pytest.skip(
        f"faltan {len(faltan)} de {len(PP_STRUCTUREV3)} artefactos de PP-StructureV3 "
        f"(~600 MB, p. ej. pp-doclayoutv3 y slanext_wired): {faltan}"
    )


def test_pp_structurev3_devuelve_structure_result_con_markdown():
    """ADR-003: la estructura no se aplana; `to_markdown()` cruza a Python.

    Es la condición `S1.2` del sign-off: con el preset `pp_structurev3` la salida
    es `StructureResult` (Markdown + elementos de layout), no un `OcrResult`
    plano. El LaTeX de una fórmula y el HTML de una tabla dentro de ese Markdown
    los cubre el test unitario de `src/engines/oar_structure.rs`, porque el
    fixture de imagen de esta suite no contiene ni tablas ni fórmulas.
    """
    ocr = VeloceOCR("pp_structurev3", custom_path=str(_directorio_structurev3()))

    resultado = ocr.recognize(str(IMAGEN))

    assert isinstance(resultado, StructureResult)
    assert not isinstance(resultado, OcrResult)

    markdown = resultado.to_markdown()
    assert isinstance(markdown, str)
    assert markdown.strip(), "el Markdown del documento no puede venir vacío"
    assert LINEAS_ESPERADAS[0] in markdown

    assert resultado.elements, "debe exponer los elementos de layout detectados"
    for elemento in resultado.elements:
        assert elemento.kind, "cada elemento lleva su etiqueta de layout"
        assert 0.0 <= elemento.confidence <= 1.0
        assert elemento.box.width >= 0 and elemento.box.height >= 0

    # Segunda llamada: el pipeline sigue residente y devuelve el mismo tipo.
    assert isinstance(ocr.recognize(IMAGEN), StructureResult)


def test_el_latex_de_una_formula_es_accesible_desde_python():
    """LaTeX de las fórmulas viaja al campo `formulas` de `StructureResult`.

    Verifica el requisito `S2.1`: con el preset `pp_structurev3` y los artefactos
    de reconocimiento de fórmulas en disco (`pp-formulanet-s.onnx` + 
    `pp-formulanet-tokenizer.json`), el backend detecta fórmulas y expone su
    representación LaTeX tanto en el Markdown (dentro de `$$...$$`) como en el
    campo estructurado `formulas` de `StructureResult`, accesible desde Python
    sin parsear el Markdown.

    Requiere que el fixture de imagen `IMAGEN` contenga al menos una fórmula
    detectable. Si no hay artefactos de fórmula en disco, el preset sigue
    funcionando (sin fórmulas) y el test se salta.
    """
    try:
        modelos = _directorio_structurev3()
        # Verificar que los artefactos de fórmula están presentes
        if not (modelos / "pp-formulanet-s.onnx").is_file():
            pytest.skip("faltan artefactos de fórmula en disco (pp-formulanet-s.onnx)")
        if not (modelos / "pp-formulanet-tokenizer.json").is_file():
            pytest.skip("faltan artefactos de fórmula en disco (pp-formulanet-tokenizer.json)")
    except pytest.skip.Exception:
        raise
    except Exception:
        # Si _directorio_structurev3() ya saltó, no hay nada más que hacer
        pytest.skip("no hay artefactos de PP-StructureV3 en disco")

    fixture = Path(__file__).parent / "data" / "sample_formula.png"
    if not fixture.is_file():
        pytest.skip("falta el fixture con fórmula (tests/data/sample_formula.png)")

    ocr = VeloceOCR("pp_structurev3", custom_path=str(modelos))
    resultado = ocr.recognize(str(fixture))

    # Verificar que es un StructureResult
    assert isinstance(resultado, StructureResult)

    # Verificar que el Markdown contiene LaTeX (fórmulas entre $$...$$)
    markdown = resultado.to_markdown()
    assert isinstance(markdown, str)
    assert markdown.strip(), "el Markdown del documento no puede venir vacío"

    # Verificar que el campo formulas no está vacío
    assert hasattr(resultado, "formulas"), "StructureResult debe exponer el campo 'formulas'"
    assert isinstance(resultado.formulas, list), "formulas debe ser una lista"
    assert len(resultado.formulas) > 0, "debe detectarse al menos una fórmula en la imagen"

    # Verificar que cada fórmula es una cadena de LaTeX
    for formula in resultado.formulas:
        assert isinstance(formula, str), "cada fórmula debe ser una cadena de texto"
        assert formula.strip(), "el texto de la fórmula no puede estar vacío"

    # Verificar que el Markdown contiene al menos una fórmula en LaTeX
    # (puede que no sea exactamente la misma que en formulas, pero debería haber alguna)
    latex_pattern = r"\$\$.*?\$\$"  # Buscar fórmulas entre doble $
    import re
    assert re.search(latex_pattern, markdown, re.DOTALL) is not None, (
        "el Markdown debe contener al menos una fórmula en LaTeX (entre $$...$$)"
    )


def test_cuda_pp_formulanet_da_el_mismo_latex_no_vacio_en_inferencias_seguidas():
    """Regresión onnxruntime#4829: bajo CUDA, dos inferencias seguidas del MISMO
    motor sobre la MISMA imagen deben dar el mismo LaTeX no vacío.

    Antes del arreglo, la 1ª inferencia de un motor PP-FormulaNet recién
    construido devolvía el LaTeX correcto y **todas las siguientes salían
    vacías** (estado por sesión, determinista): `pyocrust` sondeaba el EP CUDA
    (`resolve_auto`) al resolver `device` —inicializando el contexto— *antes* de
    que el crate aplicase su workaround `CUDA_LAUNCH_BLOCKING=1`, que la runtime
    CUDA solo lee al arrancar el contexto. Con el workaround adelantado a la
    resolución de `device`, la 2ª inferencia vuelve a coincidir con la 1ª.

    Se marca `skip` cuando ningún EP CUDA registra: la regresión es específica de
    la ruta CUDA (CPU nunca se degradó).
    """
    if "cuda" not in available_providers():
        pytest.skip("ningún EP CUDA registra en este host; regresión específica de CUDA")

    modelos = _directorio_structurev3()
    fixture = Path(__file__).parent / "data" / "sample_formula.png"
    if not fixture.is_file():
        pytest.skip("falta el fixture con fórmula (tests/data/sample_formula.png)")

    ocr = VeloceOCR("pp_structurev3", custom_path=str(modelos), device="cuda")
    assert ocr.provider_effective == "cuda", "el escenario real debe correr en CUDA"

    primero = ocr.recognize(str(fixture))
    segundo = ocr.recognize(str(fixture))

    assert primero.formulas, "la 1ª inferencia CUDA debe emitir LaTeX de fórmula"
    assert all(f.strip() for f in primero.formulas), (
        f"LaTeX vacío ya en la 1ª inferencia: {primero.formulas!r}"
    )
    assert segundo.formulas == primero.formulas, (
        "la 2ª inferencia por sesión devuelve LaTeX vacío o distinto "
        f"(onnxruntime#4829): 1ª={primero.formulas!r} 2ª={segundo.formulas!r}"
    )


def test_indra_devuelve_markdown_bloques_y_regiones():
    """Indra cruza Markdown, bloques, líneas y LaTeX inline a Python."""
    modelos_root = next(
        (
            root
            for root in directorios_candidatos()
            if (root / "indra").is_dir()
        ),
        None,
    )
    if modelos_root is None:
        pytest.skip(
            "no existe el directorio <models_dir>/indra; para descargar/verificar "
            "los artefactos: ./.venv/Scripts/python.exe -c "
            "\"import pyocrust; pyocrust.VeloceOCR('indra')\""
        )

    from pyocrust import models_status

    estado = models_status(custom_path=str(modelos_root))
    artefactos_requeridos = estado["presets"]["indra"]
    invalidos = [item["name"] for item in artefactos_requeridos if item["required"] and not item["present"]]
    if invalidos:
        pytest.skip(
            f"artefactos Indra ausentes o con SHA-256 inválido: {invalidos}; "
            "para descargarlos/verificarlos: ./.venv/Scripts/python.exe -c "
            "\"import pyocrust; pyocrust.VeloceOCR('indra')\""
        )

    ocr = VeloceOCR(
        "indra", custom_path=str(modelos_root),
        license_commercial_use=False, license_acknowledge=True,
    )
    resultado = ocr.recognize(IMAGEN)

    assert isinstance(resultado, StructureResult)
    assert resultado.to_markdown().strip()
    assert resultado.elements
    assert resultado.regions

    formula = Path(__file__).parent / "data" / "indra_math.png"
    if not formula.is_file():
        pytest.skip("falta el fixture tests/data/indra_math.png con fórmula conocida")
    resultado_math = ocr.recognize(formula)
    assert isinstance(resultado_math, StructureResult)
    assert any("$" in region.text for region in resultado_math.regions), (
        "Indra debe conservar delimitadores LaTeX inline en las líneas"
    )
    assert "$" in resultado_math.to_markdown()
