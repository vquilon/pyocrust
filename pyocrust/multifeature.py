"""Un único punto de entrada para una o varias features sobre la misma imagen.

``pipeline_profiles()`` es la fuente de verdad de las features válidas: cinco
presets de documento (``pp_ocrv6_tiny|small|medium``, ``pp_structurev3``,
``indra`` y, con la feature ``vl``, ``glm_ocr``) y once tareas independientes
(``text_detection``, ``layout_detection``, ``formula_recognition``, ...).

Cada feature **conserva su esquema**: un preset devuelve ``OcrResult`` /
``StructureResult`` y una tarea el ``dict`` documentado de
``TaskPredictor.predict``. Con **varias** features el resultado es un
``dict[label, salida]`` (etiquetado por feature, sin aplanar); con **una sola**
es exactamente la salida de hoy, sin envolver.

La inferencia es nativa y libera el GIL (``py.detach``, el antiguo
``py.allow_threads``), así que con ``parallel=True`` las features corren en
hilos y esos tramos se solapan de verdad. Por defecto es **secuencial**:
ADR-008 evita la sobre-suscripción de CPU entre sesiones ORT multihilo.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from os import PathLike
from typing import Any, Callable, Sequence

from ._pyocrust_core import (
    PyOcrValueError,
    TaskPredictor,
    VeloceOCR,
    pipeline_profiles,
)

#: Alias cortos (los nombres con los que se cita cada feature) -> id canónico
#: de ``pipeline_profiles()``. Solo se listan los que no son ambiguos.
FEATURE_ALIASES: dict[str, str] = {
    "text": "text_recognition",
    "layout": "layout_detection",
    "table": "table_structure_recognition",
    "formula": "formula_recognition",
    "structure": "pp_structurev3",
    "full_page": "pp_structurev3",
}

__all__ = ["FEATURE_ALIASES", "recognize"]


def _resolve(features: Sequence[str]) -> tuple[list[str], list[str]]:
    """Etiquetas de la llamada y sus ids canónicos, sin cargar ningún modelo."""
    if features is None or isinstance(features, (str, bytes)):
        raise PyOcrValueError(
            "features must be a sequence of feature names "
            "(a single string is ambiguous; wrap it in a list)"
        )
    try:
        labels = list(features)
    except TypeError as exc:
        raise PyOcrValueError(
            f"features must be a sequence of feature names: {exc}"
        ) from exc
    if not labels:
        raise PyOcrValueError("features must name at least one feature")
    profiles = pipeline_profiles()
    ids: list[str] = []
    for label in labels:
        if not isinstance(label, str):
            raise PyOcrValueError(
                f"feature name must be str, got {type(label).__name__}"
            )
        feature_id = FEATURE_ALIASES.get(label, label)
        if feature_id not in profiles:
            raise PyOcrValueError(
                f"unknown feature '{label}'. Valid features: "
                f"{', '.join(sorted(profiles))}. "
                f"Aliases: {', '.join(sorted(FEATURE_ALIASES))}"
            )
        ids.append(feature_id)
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    if repeated:
        raise PyOcrValueError(f"duplicate feature(s): {', '.join(repeated)}")
    return labels, ids


def _runner(
    feature_id: str,
    profile: dict,
    *,
    device: str,
    custom_path: str | None,
    license_commercial_use: bool,
    license_acknowledge: bool,
) -> Callable[[Any], Any]:
    """Inferencia de una feature: ``predict`` (tarea) o ``recognize`` (preset)."""
    license_kwargs = {
        "license_commercial_use": license_commercial_use,
        "license_acknowledge": license_acknowledge,
    }
    if profile["family"] == "task":
        predictor = TaskPredictor(feature_id, device=device, **license_kwargs)
        return predictor.predict
    engine = VeloceOCR(
        feature_id, custom_path=custom_path, device=device, **license_kwargs
    )
    return engine.recognize


def recognize(
    image: str | bytes | PathLike[str],
    features: Sequence[str],
    *,
    device: str = "cpu",
    custom_path: str | None = None,
    parallel: bool = False,
    max_workers: int | None = None,
    license_commercial_use: bool = True,
    license_acknowledge: bool = False,
) -> Any:
    """Aplica una o varias features de ``pipeline_profiles()`` a la misma imagen.

    Con una sola feature devuelve **exactamente** lo de hoy (``OcrResult`` /
    ``StructureResult`` / el ``dict`` de la tarea), sin envolver; con varias,
    ``{label: salida}`` con la etiqueta que pidió el llamante, en su orden.
    """
    labels, ids = _resolve(features)
    profiles = pipeline_profiles()
    runners = [
        _runner(
            feature_id,
            profiles[feature_id],
            device=device,
            custom_path=custom_path,
            license_commercial_use=license_commercial_use,
            license_acknowledge=license_acknowledge,
        )
        for feature_id in ids
    ]
    if len(runners) == 1:
        return runners[0](image)
    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers or len(runners)) as pool:
            outputs = list(pool.map(lambda runner: runner(image), runners))
    else:
        outputs = [runner(image) for runner in runners]
    return dict(zip(labels, outputs))
