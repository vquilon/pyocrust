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
from .resolver import RouteDecision, route

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

__all__ = ["FEATURE_ALIASES", "auto_recognize", "recognize"]


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
    det_knobs: dict | None = None,
    tiled: bool = False,
    tile_size: int | None = None,
    tile_overlap: int | None = None,
) -> Callable[[Any], Any]:
    """Inferencia de una feature: ``predict`` (tarea) o ``recognize`` (preset).

    ``det_knobs`` son los ``text_det_*`` del mando de resolucion; solo los acepta
    el preset de texto, nunca una tarea (``TaskPredictor`` tiene su propia
    whitelist y lanzaria ``PyOcrValueError``).
    """
    license_kwargs = {
        "license_commercial_use": license_commercial_use,
        "license_acknowledge": license_acknowledge,
    }
    if profile["family"] == "task":
        predictor = TaskPredictor(feature_id, device=device, **license_kwargs)
        return predictor.predict
    engine = VeloceOCR(
        feature_id,
        custom_path=custom_path,
        device=device,
        **(det_knobs or {}),
        **license_kwargs,
    )
    if tiled:
        return lambda image: engine.recognize_tiled(
            image,
            tile_size=tile_size or 2048,
            tile_overlap=tile_overlap if tile_overlap is not None else 256,
            **(det_knobs or {}),
        )
    return engine.recognize


def _run_features(
    image: str | bytes | PathLike[str],
    labels: Sequence[str],
    ids: Sequence[str],
    *,
    device: str,
    custom_path: str | None,
    license_commercial_use: bool,
    license_acknowledge: bool,
    parallel: bool = False,
    max_workers: int | None = None,
    det_knobs: dict | None = None,
    cache: dict | None = None,
    tiled: bool = False,
    tile_size: int | None = None,
    tile_overlap: int | None = None,
) -> Any:
    """Nucleo compartido por ``recognize`` y por las entradas de ``entries``.

    ``cache`` (opcional) es el estado del modo con estado: un dict
    ``clave -> runner`` que reutiliza los motores ya construidos. La clave
    incluye los ``det_knobs`` porque un motor se construye **con** su politica
    de resolucion: reutilizarlo con otra daria un resultado enganoso.
    """
    profiles = pipeline_profiles()
    runners = []
    for feature_id in ids:
        if cache is None:
            runners.append(
                _runner(
                    feature_id,
                    profiles[feature_id],
                    device=device,
                    custom_path=custom_path,
                    license_commercial_use=license_commercial_use,
                    license_acknowledge=license_acknowledge,
                    det_knobs=det_knobs,
                    tiled=tiled,
                    tile_size=tile_size,
                    tile_overlap=tile_overlap,
                )
            )
            continue
        key = (
            feature_id,
            tuple(sorted((det_knobs or {}).items())),
            tiled,
            tile_size,
            tile_overlap,
        )
        if key not in cache:
            cache[key] = _runner(
                feature_id,
                profiles[feature_id],
                device=device,
                custom_path=custom_path,
                license_commercial_use=license_commercial_use,
                license_acknowledge=license_acknowledge,
                det_knobs=det_knobs,
                tiled=tiled,
                tile_size=tile_size,
                tile_overlap=tile_overlap,
            )
        runners.append(cache[key])
    if len(runners) == 1:
        return runners[0](image)
    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers or len(runners)) as pool:
            outputs = list(pool.map(lambda runner: runner(image), runners))
    else:
        outputs = [runner(image) for runner in runners]
    return dict(zip(labels, outputs))


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
    return _run_features(
        image,
        labels,
        ids,
        device=device,
        custom_path=custom_path,
        license_commercial_use=license_commercial_use,
        license_acknowledge=license_acknowledge,
        parallel=parallel,
        max_workers=max_workers,
    )


def _image_size(image: Any) -> tuple[int, int]:
    """Ancho/alto de la imagen leyendo solo la cabecera (sin cargar modelos)."""
    try:
        from io import BytesIO
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - Pillow es opcional
        raise PyOcrValueError(
            "probe=True necesita Pillow para medir el área de la imagen"
        ) from exc
    source = BytesIO(bytes(image)) if isinstance(image, (bytes, bytearray, memoryview)) else image
    with Image.open(source) as opened:
        return opened.width, opened.height


def _detection_signals(output: Any, width: int, height: int) -> dict:
    """Señales de la sonda: ``n_regions`` e ``ink_ratio`` (§12.3).

    ``ink_ratio = Σ área(AABB de cada caja) / (width * height)``: las cajas de
    detección vienen mapeadas a coordenadas de la imagen original (§11.1.1), así
    que el denominador es el área nativa. AABB, no el cuadrilátero: es la misma
    colapsación que usa el resto del paquete (§11.2).
    """
    detections = output.get("detections", ()) if isinstance(output, dict) else ()
    ink_ratio = 0.0
    if width and height:
        covered = 0.0
        for detection in detections:
            points = detection.get("bbox") or ()
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            if xs and ys:
                covered += max(0.0, max(xs) - min(xs)) * max(0.0, max(ys) - min(ys))
        ink_ratio = covered / float(width * height)
    return {
        "width": width, "height": height,
        "n_regions": len(detections), "ink_ratio": ink_ratio,
    }


def _probe(
    image: str | bytes | PathLike[str],
    *,
    device: str,
    custom_path: str | None,
    license_commercial_use: bool = True,
    license_acknowledge: bool = False,
    cache: dict | None = None,
) -> dict:
    """Sonda de detección: **una** sesión ``TaskPredictor("text_detection")``."""
    width, height = _image_size(image)
    key = ("__probe_text_detection__", device, custom_path,
           license_commercial_use, license_acknowledge)
    if cache is not None and key in cache:
        predict = cache[key]
    else:
        predict = TaskPredictor(
            "text_detection",
            models=custom_path,
            device=device,
            license_commercial_use=license_commercial_use,
            license_acknowledge=license_acknowledge,
        ).predict
        if cache is not None:
            cache[key] = predict
    return _detection_signals(predict(image), width, height)


def auto_recognize(
    image: str | bytes | PathLike[str],
    *,
    declared: Any = None,
    probe: bool = False,
    device: str = "cpu",
    custom_path: str | None = None,
    parallel: bool = False,
    max_workers: int | None = None,
    license_commercial_use: bool = True,
    license_acknowledge: bool = False,
) -> tuple[Any, RouteDecision]:
    """``route()`` + ``recognize()``; el único ejecutor es ``recognize`` (§12.3).

    Devuelve ``(salida, decision)``: la salida es **exactamente** la de
    ``recognize`` (``OcrResult`` / ``StructureResult`` / el ``dict`` de la
    tarea), y ``decision`` lleva el porqué aparte, sin mezclarlo en el resultado
    (§12.4). ``probe=True`` añade la sonda de detección (una sesión extra, opt-in).
    """
    signals = (
        _probe(
            image,
            device=device,
            custom_path=custom_path,
            license_commercial_use=license_commercial_use,
            license_acknowledge=license_acknowledge,
        )
        if probe
        else {}
    )
    decision = route(declared, signals)
    result = recognize(
        image,
        list(decision.features),
        device=device,
        custom_path=custom_path,
        parallel=parallel,
        max_workers=max_workers,
        license_commercial_use=license_commercial_use,
        license_acknowledge=license_acknowledge,
    )
    return result, decision
