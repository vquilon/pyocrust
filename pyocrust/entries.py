"""Entradas de alto nivel para imagen única y documentos paginados."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Iterator, Literal
import warnings

from ._pyocrust_core import (
    IncompatibleImageError, IncompatiblePdfError, OcrResult, PyOcrRuntimeError,
    PyOcrValueError, StructureResult, image_dimensions, parse_document,
    pipeline_profiles, render_page,
)
from .multifeature import _probe, _run_features
from .resolver import RouteDecision, TaskSpec, resolve_pipeline, route

Resolution = Literal["default", "balanced", "native", "tiled"]
ImageOutput = OcrResult | StructureResult


@dataclass(frozen=True)
class PageRun:
    index: int
    source: Literal["text_layer", "ocr"]
    output: ImageOutput
    route_decision: RouteDecision | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentResult:
    pages: tuple[PageRun, ...]


def _policy(task: TaskSpec, commercial: bool | None, acknowledge: bool | None) -> tuple[bool, bool]:
    if commercial is not None and type(commercial) is not bool:
        raise TypeError("license_commercial_use must be bool or None")
    if acknowledge is not None and type(acknowledge) is not bool:
        raise TypeError("license_acknowledge must be bool or None")
    return (
        task.license_commercial_use if commercial is None else commercial,
        task.license_acknowledge if acknowledge is None else acknowledge,
    )


def _preflight(requests: Sequence[tuple[str, tuple[bool, bool]]]) -> None:
    profiles = pipeline_profiles()
    for feature_id, (commercial, acknowledge) in requests:
        row = profiles[feature_id]
        if (row["license"] == "Unknown"
                or (commercial and not row["license_commercial_use"])
                or (row["license_acknowledge"] and not acknowledge)):
            requirements = []
            if not row["license_commercial_use"]:
                requirements.append("license_commercial_use=False")
            if row["license_acknowledge"]:
                requirements.append("license_acknowledge=True")
            if row["license"] == "Unknown":
                requirements.append("verify the model license before use")
            raise PyOcrValueError(
                f"feature '{feature_id}' is blocked by license {row['license']}; "
                f"required: {', '.join(requirements)}"
            )


def available_features(
    *, license_commercial_use: bool = True, license_acknowledge: bool = False
) -> list[str]:
    """IDs canónicos permitidos por la política de licencia declarada."""
    if type(license_commercial_use) is not bool:
        raise TypeError("license_commercial_use must be bool")
    if type(license_acknowledge) is not bool:
        raise TypeError("license_acknowledge must be bool")
    return sorted(
        name for name, row in pipeline_profiles().items()
        if row["license"] != "Unknown"
        and (not license_commercial_use or row["license_commercial_use"])
        and (not row["license_acknowledge"] or license_acknowledge)
    )


def _image_bytes(image: str | bytes | os.PathLike[str]) -> bytes:
    if isinstance(image, bytes):
        data = image
    elif isinstance(image, (str, os.PathLike)):
        try:
            data = Path(os.fspath(image)).read_bytes()
        except OSError as exc:
            raise PyOcrRuntimeError(f"could not read image source: {exc}") from exc
    else:
        raise PyOcrValueError("image must be a path string, bytes, or PathLike object")
    if b"%PDF" in data[:1024]:
        raise IncompatibleImageError("el contenido no es una imagen compatible: parece un PDF")
    image_dimensions(data)  # decodifica antes de construir cualquier modelo
    return data


def _task_feature(task: TaskSpec) -> str:
    if not isinstance(task, TaskSpec):
        raise TypeError("task must be TaskSpec")
    return resolve_pipeline(task).id


def _text_preset(feature_id: str) -> bool:
    return feature_id in {"pp_ocrv6", "pp_ocrv6_tiny", "pp_ocrv6_small", "pp_ocrv6_medium"}


def _check_feature_options(feature_id: str, resolution: str, values: dict[str, Any]) -> None:
    if resolution == "tiled" and not _text_preset(feature_id):
        raise PyOcrValueError("resolution='tiled' requires a pp_ocrv6 text preset")
    if not _text_preset(feature_id) and any(value is not None for value in values.values()):
        raise PyOcrValueError("text_det_* options are only supported by pp_ocrv6 text presets")


def _validate_controls(resolution: str, tile_size: int | None, tile_overlap: int | None) -> None:
    if resolution not in ("default", "balanced", "native", "tiled"):
        raise PyOcrValueError(f"invalid resolution: {resolution!r}")
    if resolution == "tiled":
        size = 2048 if tile_size is None else tile_size
        overlap = 256 if tile_overlap is None else tile_overlap
        if type(size) is not int or size < 1:
            raise PyOcrValueError("tile_size must be a positive int")
        if type(overlap) is not int or overlap < 0 or overlap >= size:
            raise PyOcrValueError("tile_overlap must be an int in [0, tile_size)")
    elif tile_size is not None or tile_overlap is not None:
        raise PyOcrValueError("tile_size and tile_overlap require resolution='tiled'")


def _validate_knob_values(values: dict[str, Any]) -> None:
    for name in ("text_det_limit_side_len", "text_det_max_side_len", "text_det_max_candidates"):
        value = values.get(name)
        if value is not None and (type(value) is not int or value < 1):
            raise PyOcrValueError(f"{name} must be a positive int")
    limit_type = values.get("text_det_limit_type")
    if limit_type is not None and limit_type not in ("min", "max"):
        raise PyOcrValueError("text_det_limit_type must be 'min' or 'max'")
    for name in ("text_det_thresh", "text_det_box_thresh"):
        value = values.get(name)
        if value is not None and (type(value) not in (int, float) or not 0 <= value <= 1):
            raise PyOcrValueError(f"{name} must be within [0, 1]")
    value = values.get("text_det_unclip_ratio")
    if value is not None and (type(value) not in (int, float) or value < 0):
        raise PyOcrValueError("text_det_unclip_ratio must be a non-negative number")


def _knobs(resolution: Resolution, width: int, height: int, *, tile_size: int | None,
           tile_overlap: int | None, values: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    _validate_controls(resolution, tile_size, tile_overlap)
    _validate_knob_values(values)
    if resolution == "tiled":
        size = 2048 if tile_size is None else tile_size
    else:
        size = None

    if resolution == "default":
        limit, kind, maximum = 960, "max", 4000
    elif resolution == "tiled":
        limit, kind, maximum = 64, "min", size
    else:  # entradas nuevas: configuración Paddle, sin reducir la imagen/página
        limit, kind, maximum = 64, "min", max(width, height)
    effective = {
        "text_det_limit_side_len": limit,
        "text_det_limit_type": kind,
        "text_det_max_side_len": maximum,
    }
    effective.update({name: value for name, value in values.items() if value is not None})

    check_w, check_h = (size, size) if resolution == "tiled" else (width, height)
    long_side, short_side = max(check_w, check_h), min(check_w, check_h)
    scale = 1.0
    limit, kind = effective["text_det_limit_side_len"], effective["text_det_limit_type"]
    if kind == "max" and long_side > limit:
        scale = min(scale, limit / long_side)
    elif kind == "min" and short_side < limit:
        scale = max(scale, limit / short_side)
    max_side = effective["text_det_max_side_len"]
    cap_applied = long_side * scale > max_side
    if cap_applied:
        scale *= max_side / (long_side * scale)
    shrinks = scale < 1.0 - 1e-9
    if resolution == "native" and shrinks:
        raise PyOcrValueError(
            "resolution='native' cannot reduce input; raise text_det_max_side_len or remove shrinking text_det_* limits"
        )
    notices: list[str] = []
    if shrinks:
        cause = (f"text_det_max_side_len={max_side}" if cap_applied
                 else f"text_det_limit_side_len={limit} ({kind})")
        notices.append(f"resolution={resolution!r} reduces detection input ({check_w}x{check_h}); {cause} limits it")
    elif resolution == "native" and long_side >= 4000:
        notices.append(f"resolution='native' keeps {check_w}x{check_h}; expect higher memory and latency")
    return effective, tuple(notices)


def _run(image: bytes, feature_id: str, *, device: str, custom_path: str | None,
         policy: tuple[bool, bool], det_knobs: dict[str, Any], resolution: Resolution,
         tile_size: int | None, tile_overlap: int | None,
         cache: dict | None = None) -> ImageOutput:
    if resolution == "tiled" and feature_id not in {
        "pp_ocrv6", "pp_ocrv6_tiny", "pp_ocrv6_small", "pp_ocrv6_medium"
    }:
        raise PyOcrValueError("resolution='tiled' requires a pp_ocrv6 text preset")
    return _run_features(
        image, [feature_id], [feature_id], device=device, custom_path=custom_path,
        license_commercial_use=policy[0], license_acknowledge=policy[1],
        det_knobs=det_knobs, tiled=resolution == "tiled",
        tile_size=tile_size, tile_overlap=tile_overlap, cache=cache,
    )


def _notices(values: Sequence[str], stacklevel: int = 3) -> None:
    for value in values:
        warnings.warn(value, RuntimeWarning, stacklevel=stacklevel)


def recognize_image(
    image: str | bytes | os.PathLike[str], *, task: TaskSpec | None = None,
    resolution: Resolution = "balanced", tile_size: int | None = None,
    tile_overlap: int | None = None, text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None, device: str = "cpu",
    custom_path: str | None = None, license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> ImageOutput:
    """Reconoce una imagen y devuelve la salida única del preset seleccionado."""
    data = _image_bytes(image)
    width, height = image_dimensions(data)
    spec = TaskSpec() if task is None else task
    feature = _task_feature(spec)
    policy = _policy(spec, license_commercial_use, license_acknowledge)
    _preflight([(feature, policy)])
    values = {
        "text_det_limit_side_len": text_det_limit_side_len,
        "text_det_limit_type": text_det_limit_type,
        "text_det_max_side_len": text_det_max_side_len,
        "text_det_thresh": text_det_thresh,
        "text_det_box_thresh": text_det_box_thresh,
        "text_det_unclip_ratio": text_det_unclip_ratio,
        "text_det_max_candidates": text_det_max_candidates,
    }
    _validate_controls(resolution, tile_size, tile_overlap)
    _validate_knob_values(values)
    _check_feature_options(feature, resolution, values)
    knobs, notices = _knobs(resolution, width, height, tile_size=tile_size,
                             tile_overlap=tile_overlap, values=values)
    _notices(notices)
    return _run(data, feature, device=device, custom_path=custom_path, policy=policy,
                det_knobs=knobs, resolution=resolution, tile_size=tile_size,
                tile_overlap=tile_overlap)


def _pdf_path(path: str | os.PathLike[str]) -> str:
    if not isinstance(path, (str, os.PathLike)):
        raise PyOcrValueError("document path must be str or PathLike")
    native_path = os.fspath(path)
    try:
        with open(native_path, "rb") as source:
            prefix = source.read(1024)
    except OSError as exc:
        raise PyOcrRuntimeError(f"could not read document: {exc}") from exc
    if b"%PDF" not in prefix:
        raise IncompatiblePdfError("el contenido no es un PDF compatible")
    return native_path


def recognize_document(
    path: str | os.PathLike[str], pages: Sequence[int] | None = None, *,
    task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
    auto_route: bool = False, probe: bool = False, dpi: int = 600,
    text_min_chars: int = 64, resolution: Resolution = "balanced",
    tile_size: int | None = None, tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None, device: str = "cpu",
    custom_path: str | None = None, license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> DocumentResult:
    """Procesa un PDF, devolviendo un PageRun por página seleccionada; None = todas."""
    pdf_path = _pdf_path(path)
    if type(auto_route) is not bool or type(probe) is not bool:
        raise TypeError("auto_route and probe must be bool")
    if type(dpi) is not int or dpi < 1 or type(text_min_chars) is not int or text_min_chars < 1:
        raise PyOcrValueError("dpi and text_min_chars must be positive ints")
    if auto_route and (task is not None or page_tasks is not None):
        raise PyOcrValueError("auto_route cannot be combined with task or page_tasks")
    if page_tasks is not None and not isinstance(page_tasks, Mapping):
        raise PyOcrValueError("page_tasks must map 1-based page indexes to TaskSpec")
    if page_tasks:
        if any(type(index) is not int or index < 1 or not isinstance(spec, TaskSpec)
               for index, spec in page_tasks.items()):
            raise PyOcrValueError("page_tasks keys must be positive 1-based ints and values TaskSpec")

    values = {
        "text_det_limit_side_len": text_det_limit_side_len,
        "text_det_limit_type": text_det_limit_type,
        "text_det_max_side_len": text_det_max_side_len,
        "text_det_thresh": text_det_thresh,
        "text_det_box_thresh": text_det_box_thresh,
        "text_det_unclip_ratio": text_det_unclip_ratio,
        "text_det_max_candidates": text_det_max_candidates,
    }
    _validate_controls(resolution, tile_size, tile_overlap)
    _validate_knob_values(values)

    default_spec = TaskSpec() if task is None else task
    if not isinstance(default_spec, TaskSpec):
        raise TypeError("task must be TaskSpec")
    requests: list[tuple[str, tuple[bool, bool]]] = []
    if auto_route:
        auto_policy = _policy(TaskSpec(), license_commercial_use, license_acknowledge)
        requests.append(("pp_ocrv6_tiny", auto_policy))
        if probe:
            requests.append(("pp_structurev3", auto_policy))
            requests.append(("text_detection", auto_policy))
    else:
        for spec in (default_spec, *(page_tasks or {}).values()):
            requests.append((_task_feature(spec), _policy(spec, license_commercial_use, license_acknowledge)))
    for feature_id, _ in requests:
        _check_feature_options(feature_id, resolution, values)
    _preflight(requests)  # antes de parsear, rasterizar, sondear o crear motores

    try:
        pages_info = parse_document(pdf_path, pages=pages, dpi=dpi, text_min_chars=text_min_chars)
    except PyOcrValueError as exc:
        if "could not open PDF" in str(exc) or "could not load page" in str(exc):
            raise IncompatiblePdfError(f"el contenido no es un PDF compatible: {exc}") from exc
        raise
    selected = {page.index for page in pages_info}
    if page_tasks and not set(page_tasks).issubset(selected):
        raise PyOcrValueError("page_tasks contains a page that is not selected by pages")

    result: list[PageRun] = []
    for info in pages_info:
        if info.has_text_layer:
            result.append(PageRun(info.index, "text_layer", OcrResult(info.text_regions)))
            continue
        raster = render_page(pdf_path, index=info.index, dpi=dpi)
        width, height = image_dimensions(raster)
        decision = None
        if auto_route:
            signals = {"width": width, "height": height}
            if probe:
                signals = _probe(raster, device=device, custom_path=custom_path,
                                 license_commercial_use=auto_policy[0],
                                 license_acknowledge=auto_policy[1])
            decision = route(signals=signals)
            feature = decision.features[0]
            policy = auto_policy
        else:
            spec = (page_tasks or {}).get(info.index, default_spec)
            feature = _task_feature(spec)
            policy = _policy(spec, license_commercial_use, license_acknowledge)
        knobs, notices = _knobs(resolution, width, height, tile_size=tile_size,
                                tile_overlap=tile_overlap, values=values)
        _notices(notices, stacklevel=2)
        output = _run(raster, feature, device=device, custom_path=custom_path,
                      policy=policy, det_knobs=knobs, resolution=resolution,
                      tile_size=tile_size, tile_overlap=tile_overlap)
        result.append(PageRun(info.index, "ocr", output, decision, notices))
    return DocumentResult(tuple(result))


class Session:
    """Sesión síncrona que mantiene los motores entre llamadas y documentos."""

    def __init__(
        self, *, device: str = "cpu", custom_path: str | None = None,
        resolution: Resolution = "balanced", tile_size: int | None = None,
        tile_overlap: int | None = None, text_det_limit_side_len: int | None = None,
        text_det_limit_type: Literal["min", "max"] | None = None,
        text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
        license_commercial_use: bool = True, license_acknowledge: bool = False,
    ) -> None:
        if type(license_commercial_use) is not bool or type(license_acknowledge) is not bool:
            raise TypeError("license flags must be bool")
        if not isinstance(device, str):
            raise TypeError("device must be str")
        if custom_path is not None and not isinstance(custom_path, str):
            raise TypeError("custom_path must be str or None")
        self._device = device
        self._custom_path = custom_path
        self._resolution = resolution
        self._tile_size = tile_size
        self._tile_overlap = tile_overlap
        self._values = {
            "text_det_limit_side_len": text_det_limit_side_len,
            "text_det_limit_type": text_det_limit_type,
            "text_det_max_side_len": text_det_max_side_len,
            "text_det_thresh": text_det_thresh,
            "text_det_box_thresh": text_det_box_thresh,
            "text_det_unclip_ratio": text_det_unclip_ratio,
            "text_det_max_candidates": text_det_max_candidates,
        }
        _validate_controls(resolution, tile_size, tile_overlap)
        _validate_knob_values(self._values)
        self._policy = (license_commercial_use, license_acknowledge)
        self._runners: dict[Any, Any] = {}
        self._active = False
        self._closed = False

    def __enter__(self) -> Session:
        if self._closed or self._active:
            raise PyOcrRuntimeError("session is already active or closed")
        self._active = True
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._runners.clear()
        self._active = False
        self._closed = True
        return None

    def _check_active(self) -> None:
        if not self._active or self._closed:
            raise PyOcrRuntimeError("session methods require an active with block")

    def _spec(self, spec: TaskSpec | None) -> TaskSpec:
        if spec is None:
            return TaskSpec(
                license_commercial_use=self._policy[0],
                license_acknowledge=self._policy[1],
            )
        if not isinstance(spec, TaskSpec):
            raise TypeError("task must be TaskSpec")
        if (spec.license_commercial_use, spec.license_acknowledge) != self._policy:
            raise PyOcrValueError("TaskSpec license flags must match the Session policy")
        return spec

    def purge(self) -> None:
        """Libera los motores residentes y deja la sesión abierta para recargarlos."""
        self._check_active()
        self._runners.clear()

    def recognize_image(self, image: str | bytes | os.PathLike[str], *,
                        task: TaskSpec | None = None) -> ImageOutput:
        self._check_active()
        data = _image_bytes(image)
        width, height = image_dimensions(data)
        spec = self._spec(task)
        feature = _task_feature(spec)
        policy = self._policy
        _preflight([(feature, policy)])
        _check_feature_options(feature, self._resolution, self._values)
        knobs, notices = _knobs(
            self._resolution, width, height, tile_size=self._tile_size,
            tile_overlap=self._tile_overlap, values=self._values,
        )
        _notices(notices)
        return _run(
            data, feature, device=self._device, custom_path=self._custom_path,
            policy=policy, det_knobs=knobs, resolution=self._resolution,
            tile_size=self._tile_size, tile_overlap=self._tile_overlap,
            cache=self._runners,
        )

    def iter_document_pages(
        self, path: str | os.PathLike[str], pages: Sequence[int] | None = None, *,
        task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
        auto_route: bool = False, probe: bool = False, dpi: int = 600,
        text_min_chars: int = 64,
    ) -> Iterator[PageRun]:
        self._check_active()
        pdf_path = _pdf_path(path)
        if type(auto_route) is not bool or type(probe) is not bool:
            raise TypeError("auto_route and probe must be bool")
        if type(dpi) is not int or dpi < 1 or type(text_min_chars) is not int or text_min_chars < 1:
            raise PyOcrValueError("dpi and text_min_chars must be positive ints")
        if auto_route and (task is not None or page_tasks is not None):
            raise PyOcrValueError("auto_route cannot be combined with task or page_tasks")
        if page_tasks is not None and not isinstance(page_tasks, Mapping):
            raise PyOcrValueError("page_tasks must map 1-based page indexes to TaskSpec")
        if page_tasks and any(
            type(index) is not int or index < 1 or not isinstance(spec, TaskSpec)
            for index, spec in page_tasks.items()
        ):
            raise PyOcrValueError("page_tasks keys must be positive 1-based ints and values TaskSpec")

        default_spec = self._spec(task)
        effective_page_tasks = {
            index: self._spec(spec) for index, spec in (page_tasks or {}).items()
        }
        try:
            pages_info = parse_document(
                pdf_path, pages=pages, dpi=dpi, text_min_chars=text_min_chars
            )
        except PyOcrValueError as exc:
            if "could not open PDF" in str(exc) or "could not load page" in str(exc):
                raise IncompatiblePdfError(f"el contenido no es un PDF compatible: {exc}") from exc
            raise
        selected = {page.index for page in pages_info}
        if not set(effective_page_tasks).issubset(selected):
            raise PyOcrValueError("page_tasks contains a page that is not selected by pages")

        requests: list[tuple[str, tuple[bool, bool]]] = []
        if auto_route:
            if any(not info.has_text_layer for info in pages_info):
                requests.append(("pp_ocrv6_tiny", self._policy))
                if probe:
                    requests.extend((("pp_structurev3", self._policy),
                                     ("text_detection", self._policy)))
        else:
            for info in pages_info:
                if info.has_text_layer:
                    continue
                spec = effective_page_tasks.get(info.index, default_spec)
                requests.append((_task_feature(spec), self._policy))
        for feature, _ in requests:
            _check_feature_options(feature, self._resolution, self._values)
        _preflight(requests)

        for info in pages_info:
            self._check_active()
            if info.has_text_layer:
                yield PageRun(info.index, "text_layer", OcrResult(info.text_regions))
                continue
            raster = render_page(pdf_path, index=info.index, dpi=dpi)
            width, height = image_dimensions(raster)
            decision = None
            if auto_route:
                signals = {"width": width, "height": height}
                if probe:
                    signals = _probe(
                        raster, device=self._device, custom_path=self._custom_path,
                        license_commercial_use=self._policy[0],
                        license_acknowledge=self._policy[1], cache=self._runners,
                    )
                decision = route(signals=signals)
                feature = decision.features[0]
            else:
                spec = effective_page_tasks.get(info.index, default_spec)
                feature = _task_feature(spec)
            knobs, notices = _knobs(
                self._resolution, width, height, tile_size=self._tile_size,
                tile_overlap=self._tile_overlap, values=self._values,
            )
            _notices(notices, stacklevel=2)
            output = _run(
                raster, feature, device=self._device, custom_path=self._custom_path,
                policy=self._policy, det_knobs=knobs, resolution=self._resolution,
                tile_size=self._tile_size, tile_overlap=self._tile_overlap,
                cache=self._runners,
            )
            yield PageRun(info.index, "ocr", output, decision, notices)


__all__ = ["DocumentResult", "ImageOutput", "PageRun", "Resolution", "Session",
           "available_features", "recognize_document", "recognize_image"]
