"""Router automático RAUTO (``DESIGN.md`` §12): ``route()`` + ``auto_recognize()``.

Cubre los **6 ejemplos de aceptación de §12.3** (entrada -> ``features`` +
``reason``) y el caso común con ``probe=False``: nada declarado y geometría OK
devuelve texto ``tiny`` sin cargar ningún modelo de estructura (los dobles
registran qué se construye: se prueba el *efecto*, no se asume).

Nota sobre ``features`` del camino de texto (desviación consciente de la tabla
de §12.3): las filas de texto escriben ``("text_recognition",)``, pero eso
ejecutaría la **tarea** de rec y devolvería su ``dict`` ``{text, score}`` — no
``OcrResult`` (que §12.4 exige para R1/R2'/R3) ni un tamaño. R1 dice
``pp_ocrv6_tiny`` y R3 "el tamaño que elija ``resolve_pipeline(TaskSpec())``",
así que el router emite el **id del preset** resuelto (``pp_ocrv6_tiny``), que es
lo que ``recognize`` necesita para devolver ``OcrResult`` y lo que hace cierta
la frase "devuelve texto tiny" del criterio de aceptación.

Ejecución: ``python -m pytest tests/test_route.py -q``
"""

from __future__ import annotations

import pytest

import pyocrust
from pyocrust import PyOcrValueError, RouteDecision, route
from pyocrust import multifeature


# --------------------------------------------------------------------------
# route(): los 6 ejemplos de aceptación de §12.3
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("declared", "signals", "features", "reason"),
    [
        (pyocrust.TaskSpec(tables=True), None, ("pp_structurev3",), "declared"),
        (["layout"], None, ("layout_detection",), "declared"),
        (None, {"W": 40, "H": 40}, ("pp_ocrv6_tiny",), "geometry"),
        (None, {"n_regions": 5, "ink_ratio": 0.05}, ("pp_ocrv6_tiny",), "probe"),
        (None, {"n_regions": 31, "ink_ratio": 0.90}, ("pp_structurev3",), "probe"),
        (None, None, ("pp_ocrv6_tiny",), "default-text"),
    ],
)
def test_ejemplos_de_aceptacion_de_12_3(declared, signals, features, reason):
    decision = route(declared, signals)

    assert isinstance(decision, RouteDecision)
    assert decision.features == features
    assert decision.reason == reason


def test_r0_declara_y_no_re_deriva():
    """Lo declarado gana: el router delega y no vuelve a decidir el mapeo."""
    # TaskSpec -> resolve_pipeline; su `id` es el preset listo para VeloceOCR.
    assert route(pyocrust.TaskSpec(tables=True)) == RouteDecision(
        preset="pp_structurev3",
        size=None,
        features=("pp_structurev3",),
        reason="declared",
        artifacts=tuple(pyocrust.pipeline_profiles()["pp_structurev3"]["artifacts"]),
    )
    # features explícitas -> se delega tal cual (alias -> id canónico, en orden).
    assert route(["layout", "table"]).features == (
        "layout_detection",
        "table_structure_recognition",
    )
    assert route(["layout", "table"]).preset is None
    # Un TaskSpec de texto/escaneado también delega, con su tamaño resuelto.
    escaneado = route(pyocrust.TaskSpec(document_kind="scanned"))
    assert (escaneado.preset, escaneado.size) == ("pp_ocrv6", "tiny")
    assert escaneado.features == ("pp_ocrv6_tiny",)


def test_texto_tiny_lleva_los_artefactos_del_preset_y_ninguno_de_estructura():
    perfiles = pyocrust.pipeline_profiles()
    for reason, signals in (
        ("geometry", {"W": 10, "H": 10}),
        ("probe", {"n_regions": 1, "ink_ratio": 0.0}),
        ("default-text", None),
    ):
        decision = route(None, signals)
        assert decision.reason == reason
        assert (decision.preset, decision.size) == ("pp_ocrv6", "tiny")
        assert decision.features == ("pp_ocrv6_tiny",)
        assert decision.artifacts == tuple(perfiles["pp_ocrv6_tiny"]["artifacts"])
        assert len(decision.artifacts) == 3  # det + rec + dict, no el preset de 11


def test_estructura_lleva_los_11_artefactos_del_preset():
    decision = route(None, {"n_regions": 24, "ink_ratio": 0.0})

    assert decision.features == ("pp_structurev3",)
    assert decision.artifacts == tuple(pyocrust.pipeline_profiles()["pp_structurev3"]["artifacts"])
    assert len(decision.artifacts) == 11


# --------------------------------------------------------------------------
# Fronteras de las constantes de política (§12.3)
# --------------------------------------------------------------------------

def test_frontera_de_geometria():
    assert route(None, {"W": 63, "H": 1000}).reason == "geometry"
    # min(W,H) == GEOM_MIN_SIDE_PX no dispara R1 (la condición es estricta).
    assert route(None, {"W": 64, "H": 1000}).reason == "default-text"


def test_frontera_de_la_sonda():
    dentro = {"n_regions": pyocrust.ROUTE_MIN_REGIONS, "ink_ratio": 0.0}
    fuera = {"n_regions": pyocrust.ROUTE_MIN_REGIONS - 1, "ink_ratio": pyocrust.ROUTE_MIN_DENSITY - 0.01}
    denso = {"n_regions": 0, "ink_ratio": pyocrust.ROUTE_MIN_DENSITY}

    assert route(None, dentro).features == ("pp_structurev3",)
    assert route(None, denso).features == ("pp_structurev3",)
    assert route(None, fuera).features == ("pp_ocrv6_tiny",)
    assert route(None, fuera).reason == "probe"  # R2' también es la sonda


def test_la_geometria_gana_a_la_sonda():
    """Primera regla que casa: una imagen minúscula manda aunque la sonda vea mucho."""
    assert route(None, {"W": 40, "H": 40, "n_regions": 99, "ink_ratio": 0.99}).reason == "geometry"


def test_signals_admite_el_nombre_largo():
    assert route(None, {"width": 40, "height": 40}).reason == "geometry"


# --------------------------------------------------------------------------
# Pureza: `route` recomienda, no ejecuta
# --------------------------------------------------------------------------

def test_route_no_construye_ningun_modelo(monkeypatch):
    def _no_deberia(*_args, **_kwargs):
        raise AssertionError("route() es pura: no debe construir ningún modelo")

    monkeypatch.setattr(multifeature, "TaskPredictor", _no_deberia)
    monkeypatch.setattr(multifeature, "VeloceOCR", _no_deberia)

    for declared, signals in (
        (pyocrust.TaskSpec(tables=True), None),
        (["layout"], None),
        (None, {"n_regions": 31, "ink_ratio": 0.9}),
        (None, None),
    ):
        assert isinstance(route(declared, signals), RouteDecision)


def test_declared_invalido_falla_antes_de_cualquier_cosa():
    with pytest.raises(PyOcrValueError, match="unknown feature 'no_existe'"):
        route(["no_existe"])


# --------------------------------------------------------------------------
# La sonda: señales puras + una sola sesión
# --------------------------------------------------------------------------

def test_senales_de_la_sonda_cuentan_regiones_y_densidad():
    salida = {
        "detections": [
            {"bbox": [[0, 0], [10, 0], [10, 5], [0, 5]], "score": 0.9},
            {"bbox": [[0, 0], [20, 0], [20, 10], [0, 10]], "score": 0.8},
        ]
    }

    signals = multifeature._detection_signals(salida, 100, 100)

    assert signals["n_regions"] == 2
    assert signals["width"] == 100 and signals["height"] == 100
    # ink_ratio = Σ área(AABB) / área(imagen) = (10*5 + 20*10) / 10000
    assert signals["ink_ratio"] == pytest.approx((10 * 5 + 20 * 10) / (100 * 100))


def test_senales_de_la_sonda_sin_detecciones_ni_imagen():
    assert multifeature._detection_signals({"detections": []}, 0, 0) == {
        "width": 0, "height": 0, "n_regions": 0, "ink_ratio": 0.0,
    }


# --------------------------------------------------------------------------
# auto_recognize(): route + el único ejecutor, y `probe=False` no toca estructura
# --------------------------------------------------------------------------

class _DoblePreset:
    """Doble de ``VeloceOCR``: registra qué preset se construye."""

    construidos: list[tuple] = []

    def __init__(self, preset, custom_path=None, device="cpu", **opciones):
        type(self).construidos.append((preset, custom_path, device, opciones))
        self.preset = preset

    def recognize(self, image):
        return {"preset": self.preset}


class _DobleTarea:
    """Doble de ``TaskPredictor``: registra qué tarea se construye."""

    construidos: list[tuple] = []
    detecciones: list[dict] = []

    def __init__(self, task, models=None, device="cpu", **opciones):
        type(self).construidos.append((task, models, device, opciones))

    def predict(self, image):
        return {"detections": list(type(self).detecciones)}


@pytest.fixture
def dobles(monkeypatch):
    _DoblePreset.construidos = []
    _DobleTarea.construidos = []
    _DobleTarea.detecciones = []
    monkeypatch.setattr(multifeature, "TaskPredictor", _DobleTarea)
    monkeypatch.setattr(multifeature, "VeloceOCR", _DoblePreset)
    return _DoblePreset, _DobleTarea


def test_caso_comun_probe_false_es_texto_tiny_sin_modelo_de_estructura(dobles):
    """Criterio de aceptación: nada declarado + geometría OK -> texto tiny."""
    preset, tarea = dobles

    salida, decision = pyocrust.auto_recognize("pagina.png", probe=False)

    assert decision.features == ("pp_ocrv6_tiny",)
    assert (decision.preset, decision.size) == ("pp_ocrv6", "tiny")
    assert decision.reason == "default-text"
    # El único modelo construido es el del preset de texto: ni estructura ni sonda.
    assert [c[0] for c in preset.construidos] == ["pp_ocrv6_tiny"]
    assert tarea.construidos == []
    assert salida == {"preset": "pp_ocrv6_tiny"}


def test_probe_false_ignora_declared_y_delega(dobles):
    preset, _ = dobles

    _, decision = pyocrust.auto_recognize("pagina.png", declared=pyocrust.TaskSpec(tables=True))

    assert decision.reason == "declared"
    assert [c[0] for c in preset.construidos] == ["pp_structurev3"]


def test_probe_true_es_una_sesion_y_su_senal_decide(dobles, png_factory):
    """La sonda emite n_regions/ink_ratio y `route` decide con ella (sin modelos)."""
    preset, tarea = dobles
    imagen = png_factory(200, 100)
    # Una caja 200x50 -> ink_ratio = 0.5 >= ROUTE_MIN_DENSITY -> estructura.
    tarea.detecciones = [{"bbox": [[0, 0], [200, 0], [200, 50], [0, 50]], "score": 1.0}]

    _, decision = pyocrust.auto_recognize(imagen, probe=True)

    assert [c[0] for c in tarea.construidos] == ["text_detection"]
    assert decision.reason == "probe"
    assert decision.features == ("pp_structurev3",)
    assert [c[0] for c in preset.construidos] == ["pp_structurev3"]


def test_probe_true_con_poca_tinta_deja_texto(dobles, png_factory):
    preset, tarea = dobles
    imagen = png_factory(1000, 1000)
    tarea.detecciones = [{"bbox": [[0, 0], [10, 0], [10, 10], [0, 10]], "score": 1.0}]

    _, decision = pyocrust.auto_recognize(imagen, probe=True)

    assert decision.reason == "probe"
    assert decision.features == ("pp_ocrv6_tiny",)
    assert [c[0] for c in preset.construidos] == ["pp_ocrv6_tiny"]
