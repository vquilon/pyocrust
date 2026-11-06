"""Pure pipeline recommendations: no downloads, model loads or subprocess server."""
from __future__ import annotations

from dataclasses import dataclass
import os

from .hardware import HardwareProfile, detect_hardware
from ._pyocrust_core import pipeline_profiles, resolve_models_dir


@dataclass(frozen=True)
class TaskSpec:
    document_kind: str = "digital"
    ocr_only: bool = True
    formulas: str = "none"
    tables: bool = False
    quality: str = "speed"
    output_format: str = "text"
    license_commercial_use: bool = True
    license_acknowledge: bool = False

    def __post_init__(self):
        for name, allowed in (
            ("document_kind", ("scanned", "digital", "mixed")),
            ("formulas", ("none", "with_text", "only")),
            ("quality", ("speed", "balanced", "accuracy")),
            ("output_format", ("text", "markdown", "html", "json")),
        ):
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} must be one of {allowed}")
        if type(self.ocr_only) is not bool or type(self.tables) is not bool:
            raise TypeError("ocr_only and tables must be bool")
        if type(self.license_commercial_use) is not bool:
            raise TypeError("license_commercial_use must be bool")
        if type(self.license_acknowledge) is not bool:
            raise TypeError("license_acknowledge must be bool")


@dataclass(frozen=True)
class PipelineChoice:
    preset: str
    size: str | None
    tasks: tuple[str, ...]
    models_dir: str
    offline: bool

    @property
    def id(self) -> str:
        return f"pp_ocrv6_{self.size}" if self.preset == "pp_ocrv6" else self.preset


def _license_allows(profile_id: str, commercial_intent: bool, acknowledge: bool) -> bool:
    """True si la licencia del perfil permite la política declarada.

    Consulta el catálogo nativo (`pipeline_profiles()`), no una tabla local:
    `commercial_intent` es lo que declara el usuario y `acknowledge` su
    aceptación de la atribución. Una licencia restringida exige ambas.
    """
    row = pipeline_profiles()[profile_id]
    if commercial_intent and not row["license_commercial_use"]:
        return False
    if row["license_acknowledge"] and not acknowledge:
        return False
    return True


def resolve_pipeline(task: TaskSpec, hardware: HardwareProfile | None = None) -> PipelineChoice:
    """Choose a valid VeloceOCR preset ID without loading it.

    Formulas/tables/Markdown (also HTML or non-OCR-only JSON) take precedence
    over plain text and select pp_structurev3. Otherwise speed, unknown RAM or
    RAM below 4 GiB selects Tiny; balanced or RAM below 8 GiB selects Small;
    accuracy with at least 8 GiB selects Medium. Scanned/mixed documents add
    orientation and rectification. Accuracy with >=8 GiB VRAM mentions Indra as
    an alternative, not as a claim of available CUDA support or cached models.

    models_dir uses the existing native resolution (OAR_HOME before
    OCR_MODELS_CACHE_DIR, then ~/.oar); explicit VeloceOCR custom_path still wins.
    PYOCRUST_OFFLINE is false for unset/empty/0/false/no, case insensitive;
    whitespace is significant, matching the native storage implementation.
    Recommendations do not execute the listed tasks automatically.

    License polarity: `task.license_commercial_use` is what the USER declares
    (commercial intent), not what the model allows; `task.license_acknowledge`
    is the user's acceptance of attribution. A restricted profile (Indra,
    OpenRAIL-M-Mod) is only recommended when the declared policy satisfies its
    catalog license (`pipeline_profiles()[id]`), and building it still requires
    passing the same flags to `VeloceOCR`.
    """
    if not isinstance(task, TaskSpec):
        raise TypeError("task must be TaskSpec")
    if hardware is None:
        hardware = detect_hardware()
    elif not isinstance(hardware, HardwareProfile):
        raise TypeError("hardware must be HardwareProfile")
    structure = task.formulas != "none" or task.tables or task.output_format in ("markdown", "html", "json") or not task.ocr_only
    size = None
    if not structure:
        ram = hardware.ram_bytes
        if task.quality == "speed" or ram is None or ram < 4 * 1024**3:
            size = "tiny"
        elif task.quality == "balanced" or ram < 8 * 1024**3:
            size = "small"
        else:
            size = "medium"
    tasks = []
    if task.document_kind in ("scanned", "mixed"):
        tasks.extend(("document_orientation", "document_rectification"))
    if (task.quality == "accuracy" and hardware.gpu is not None
            and (hardware.gpu.vram_bytes or 0) >= 8 * 1024**3
            and _license_allows("indra", task.license_commercial_use, task.license_acknowledge)):
        tasks.append("indra")
    offline = os.environ.get("PYOCRUST_OFFLINE", "").lower() not in ("", "0", "false", "no")
    return PipelineChoice(
        preset="pp_structurev3" if structure else "pp_ocrv6", size=size,
        tasks=tuple(tasks), models_dir=resolve_models_dir(), offline=offline,
    )
