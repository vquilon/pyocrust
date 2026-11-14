"""API multi-feature: ``pyocrust.recognize(image, features=[...])`` (t_b64b78d9).

Contrato que fija la tarjeta:

* **una** feature -> exactamente la salida de hoy (``OcrResult`` /
  ``StructureResult`` / el ``dict`` de la tarea), sin envolver (retrocompatible);
* **varias** features -> ``{etiqueta: salida}``, etiquetado por feature y con el
  esquema propio de cada una, sin aplanar salidas distintas en una.

Los casos de contrato usan dobles de ``TaskPredictor``/``VeloceOCR`` (no cargan
ningún modelo); los dos últimos ejercitan inferencia real y se marcan ``skip``
con el motivo cuando el host no tiene los artefactos de PP-StructureV3.

Ejecución: ``python -m pytest tests/test_multifeature.py -q``
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

import pyocrust
from pyocrust import (
    FEATURE_ALIASES,
    PyOcrValueError,
    StructureResult,
    pipeline_profiles,
)
from pyocrust import multifeature

from conftest import PP_STRUCTUREV3, directorios_candidatos

IMAGEN = Path(__file__).parent / "data" / "sample_text.png"
# Página real de OmniDocBench: PP-DocLayoutV3 detecta layout en ella (el fixture
# de texto son dos líneas y con el umbral por defecto no hay elementos).
PAGINA = Path(__file__).parent / "data" / "sample_formula.png"

# Una tarea (esquema `{elements, is_reading_order_sorted}`) y otra
# (`{structures, bboxes}`): dos esquemas distintos que no deben aplanarse.
TAREA_LAYOUT = "layout_detection"
TAREA_TABLA = "table_structure_recognition"


class _DobleTarea:
    """Doble de ``TaskPredictor``: registra construcción e inferencia.

    Devuelve el esquema **propio de cada tarea** (como el predictor real), para
    que el test pueda exigir que dos features no se aplanen en una sola salida.
    """

    construidos: list[tuple] = []
    inferencias: list[tuple] = []
    # Cuando se fija una barrera, `predict` espera en ella: con `parallel=True`
    # las dos features tienen que estar dentro a la vez o la barrera rompe.
    barrera: threading.Barrier | None = None

    ESQUEMAS = {
        TAREA_LAYOUT: {"elements": [], "is_reading_order_sorted": False},
        TAREA_TABLA: {"structures": [], "bboxes": []},
    }

    def __init__(self, task, device="cpu", **opciones):
        type(self).construidos.append((task, device, opciones))
        self.task = task

    def predict(self, image):
        type(self).inferencias.append((self.task, image, threading.current_thread().name))
        if type(self).barrera is not None:
            type(self).barrera.wait(timeout=30)
        return dict(type(self).ESQUEMAS[self.task])


class _DoblePreset:
    """Doble de ``VeloceOCR``: registra construcción e inferencia."""

    construidos: list[tuple] = []
    inferencias: list[tuple] = []

    def __init__(self, preset, custom_path=None, device="cpu", **opciones):
        type(self).construidos.append((preset, custom_path, device, opciones))
        self.preset = preset

    def recognize(self, image):
        type(self).inferencias.append((self.preset, image, threading.current_thread().name))
        return {"preset": self.preset}


@pytest.fixture
def dobles(monkeypatch):
    for doble in (_DobleTarea, _DoblePreset):
        doble.construidos = []
        doble.inferencias = []
    _DobleTarea.barrera = None
    monkeypatch.setattr(multifeature, "TaskPredictor", _DobleTarea)
    monkeypatch.setattr(multifeature, "VeloceOCR", _DoblePreset)
    return _DobleTarea, _DoblePreset


def test_una_sola_feature_devuelve_la_salida_de_hoy_sin_envolver(dobles):
    tarea, _ = dobles

    salida = pyocrust.recognize(str(IMAGEN), [TAREA_LAYOUT])

    # El mismo `dict` que devuelve hoy `TaskPredictor.predict`, no `{feature: ...}`.
    assert salida == {"elements": [], "is_reading_order_sorted": False}
    assert tarea.construidos[0][0] == TAREA_LAYOUT


def test_varias_features_devuelven_un_dict_etiquetado_y_en_orden(dobles):
    salida = pyocrust.recognize(str(IMAGEN), [TAREA_LAYOUT, TAREA_TABLA, "pp_ocrv6_tiny"])

    assert isinstance(salida, dict)
    assert list(salida) == [TAREA_LAYOUT, TAREA_TABLA, "pp_ocrv6_tiny"]
    # Cada feature conserva su esquema: no se aplanan en una salida común.
    assert set(salida[TAREA_LAYOUT]) == {"elements", "is_reading_order_sorted"}
    assert set(salida[TAREA_TABLA]) == {"structures", "bboxes"}
    assert salida["pp_ocrv6_tiny"] == {"preset": "pp_ocrv6_tiny"}


def test_las_etiquetas_son_las_del_llamante_y_los_alias_resuelven_al_id_canonico(dobles):
    tarea, preset = dobles

    salida = pyocrust.recognize(str(IMAGEN), ["layout", "table", "full_page"])

    assert list(salida) == ["layout", "table", "full_page"]
    assert [c[0] for c in tarea.construidos] == [TAREA_LAYOUT, TAREA_TABLA]
    assert [c[0] for c in preset.construidos] == ["pp_structurev3"]


def test_secuencial_por_defecto(dobles):
    tarea, _ = dobles

    pyocrust.recognize(str(IMAGEN), [TAREA_LAYOUT, TAREA_TABLA])

    # Secuencial = sin hilos: las dos inferencias van en el hilo del llamante.
    assert {hilo for _, _, hilo in tarea.inferencias} == {threading.current_thread().name}


def test_paralelo_solapa_de_verdad_y_conserva_el_etiquetado(dobles):
    """Con `parallel=True` las features corren a la vez (barrera de dos hilos).

    Los dobles esperan en una `threading.Barrier(2)`: si las inferencias fueran
    secuenciales, la barrera rompería por `timeout` y el test fallaría.
    """
    tarea, _ = dobles
    tarea.barrera = threading.Barrier(2)
    try:
        paralelo = pyocrust.recognize(
            str(IMAGEN), [TAREA_LAYOUT, TAREA_TABLA], parallel=True
        )
    finally:
        tarea.barrera = None

    assert list(paralelo) == [TAREA_LAYOUT, TAREA_TABLA]
    assert set(paralelo[TAREA_LAYOUT]) == {"elements", "is_reading_order_sorted"}
    assert set(paralelo[TAREA_TABLA]) == {"structures", "bboxes"}
    assert len({hilo for _, _, hilo in tarea.inferencias}) == 2


@pytest.mark.parametrize(
    ("features", "mensaje"),
    [
        ("layout_detection", "a single string is ambiguous"),
        (b"layout_detection", "a single string is ambiguous"),
        ([], "at least one feature"),
        (["no_existe"], "unknown feature 'no_existe'"),
        ([TAREA_LAYOUT, "layout"], "duplicate feature"),
        ([1], "feature name must be str"),
        (42, "features must be a sequence of feature names"),
    ],
)
def test_features_invalidas_fallan_antes_de_cargar_modelos(features, mensaje, monkeypatch):
    def _no_deberia_cargar(*_args, **_kwargs):
        raise AssertionError("no se debe construir ningún modelo con features inválidas")

    monkeypatch.setattr(multifeature, "TaskPredictor", _no_deberia_cargar)
    monkeypatch.setattr(multifeature, "VeloceOCR", _no_deberia_cargar)

    with pytest.raises(PyOcrValueError, match=mensaje):
        pyocrust.recognize(str(IMAGEN), features)


def test_los_alias_apuntan_a_ids_del_catalogo():
    perfiles = pipeline_profiles()
    assert FEATURE_ALIASES
    assert all(destino in perfiles for destino in FEATURE_ALIASES.values())


def _directorio_structurev3() -> Path:
    """Directorio del host con los artefactos de PP-StructureV3, o ``skip``."""
    for directorio in directorios_candidatos():
        if all((directorio / nombre).is_file() for nombre in PP_STRUCTUREV3):
            return directorio
    faltan = [
        nombre
        for nombre in PP_STRUCTUREV3
        if not any((directorio / nombre).is_file() for directorio in directorios_candidatos())
    ]
    pytest.skip(f"faltan artefactos de PP-StructureV3 ({', '.join(faltan)})")


def test_caso_real_dos_features_conservan_su_esquema():
    """Inferencia real: `["layout", "table"]` sobre la misma página, etiquetado."""
    modelos = _directorio_structurev3()
    if not PAGINA.is_file():
        pytest.skip(f"falta el fixture de página real {PAGINA.name}")

    salida = pyocrust.recognize(str(PAGINA), ["layout", "table"], custom_path=str(modelos))

    assert list(salida) == ["layout", "table"]

    layout = salida["layout"]
    assert isinstance(layout, dict)
    assert layout["elements"], "PP-DocLayoutV3 debe detectar elementos en la página"
    for elemento in layout["elements"]:
        assert elemento["element_type"] and isinstance(elemento["score"], float)
        assert len(elemento["bbox"]) == 4
    assert isinstance(layout["is_reading_order_sorted"], bool)

    tabla = salida["table"]
    assert isinstance(tabla, dict)
    assert all(isinstance(token, str) for token in tabla["structures"])
    assert isinstance(tabla["bboxes"], list)

    # Dos esquemas distintos: no se han aplanado en una salida común.
    assert set(layout) != set(tabla)


def test_caso_real_una_sola_feature_es_retrocompatible():
    """Una sola feature devuelve el objeto de hoy, idéntico; dos, el etiquetado."""
    modelos = _directorio_structurev3()

    sola = pyocrust.recognize(str(IMAGEN), ["pp_structurev3"], custom_path=str(modelos))
    hoy = pyocrust.VeloceOCR("pp_structurev3", custom_path=str(modelos)).recognize(str(IMAGEN))

    assert isinstance(sola, StructureResult)
    assert sola.to_markdown().strip()
    assert sola.to_markdown() == hoy.to_markdown()

    etiquetadas = pyocrust.recognize(
        str(IMAGEN), ["pp_structurev3", TAREA_LAYOUT], custom_path=str(modelos)
    )
    assert list(etiquetadas) == ["pp_structurev3", TAREA_LAYOUT]
    assert isinstance(etiquetadas["pp_structurev3"], StructureResult)
    assert isinstance(etiquetadas[TAREA_LAYOUT], dict)
