"""Resolvedor de pipeline (S3.1): la tabla de decisión, comprobada rama a rama.

Tarjeta `S3.2`. Cada rama documentada de `TaskSpec` debe producir el
`PipelineChoice` que dice la tarjeta `S3.1`; un valor fuera de enum debe lanzar
en vez de devolver basura; `hardware=None` debe delegar en `detect_hardware()`.

Ejecución: `python -m pytest tests/ -q`
"""

from __future__ import annotations

import pytest

import pyocrust

GIB = 1024**3

# Nombres de tarea canónicos de oar-ocr (tarjeta S3.1, punto 3).
FORMULA_TASK = "formula_recognition"
ORIENTACION = "document_orientation"
RECTIFICACION = "document_rectification"


# --------------------------------------------------------------------------
# Constructores
# --------------------------------------------------------------------------


def spec(**overrides):
    """`TaskSpec` con todos los descriptores explícitos; `overrides` los pisa."""
    base = dict(
        document_kind="digital",
        ocr_only=True,
        formulas="none",
        tables=False,
        quality="speed",
        output_format="text",
    )
    base.update(overrides)
    return pyocrust.TaskSpec(**base)


def hardware(ram_gib: float = 16.0, cpus: int = 8, gpu=None):
    return pyocrust.HardwareProfile(cpu_count=cpus, ram_bytes=int(ram_gib * GIB), gpu=gpu)


def elegir(task, hw=None):
    return pyocrust.resolve_pipeline(task) if hw is None else pyocrust.resolve_pipeline(task, hw)


def etapas(choice):
    """Las etapas/etiquetas recomendadas, sea cual sea el nombre del atributo."""
    for attr in ("tasks", "stages", "steps", "task_list", "recommendations", "extra_tasks"):
        valor = getattr(choice, attr, None)
        if valor is not None:
            return [str(x) for x in valor]
    raise AssertionError(
        "PipelineChoice no expone las etapas recomendadas en ninguno de los nombres "
        f"documentados ('tasks', 'stages', 'steps', …). Atributos: {sorted(dir(choice))}"
    )


@pytest.fixture
def gpu_8gib():
    """Un `GpuInfo` de 8 GiB, si su constructor lo permite."""
    if not hasattr(pyocrust, "GpuInfo"):
        pytest.skip("pyocrust no exporta GpuInfo: no se puede construir el escenario de GPU")
    for kwargs in ({"vram_bytes": 8 * GIB}, {"name": "test", "vram_bytes": 8 * GIB}):
        try:
            return pyocrust.GpuInfo(**kwargs)
        except TypeError:
            continue
    pytest.skip("no se pudo construir un GpuInfo de 8 GiB con los nombres documentados")


# --------------------------------------------------------------------------
# Tabla de decisión — pp_ocrv6 y su tamaño
# --------------------------------------------------------------------------


def test_ocr_only_speed_elige_pp_ocrv6_tiny():
    eleccion = elegir(spec(ocr_only=True, quality="speed"), hardware(ram_gib=16))
    assert eleccion.preset == "pp_ocrv6", f"preset={eleccion.preset!r}, se esperaba 'pp_ocrv6'"
    assert eleccion.size == "tiny", f"size={eleccion.size!r}, se esperaba 'tiny'"


def test_ocr_only_balanced_elige_small():
    eleccion = elegir(spec(ocr_only=True, quality="balanced"), hardware(ram_gib=16))
    assert eleccion.preset == "pp_ocrv6"
    assert eleccion.size == "small", f"size={eleccion.size!r}, se esperaba 'small'"
    assert eleccion.id == "pp_ocrv6_small"


def test_ocr_only_accuracy_con_ram_suficiente_elige_medium():
    eleccion = elegir(spec(ocr_only=True, quality="accuracy"), hardware(ram_gib=16))
    assert eleccion.preset == "pp_ocrv6"
    assert eleccion.size == "medium", f"size={eleccion.size!r}, se esperaba 'medium'"
    assert eleccion.id == "pp_ocrv6_medium"


@pytest.mark.parametrize("ram", [None, 4 * GIB, 8 * GIB - 1, 8 * GIB])
def test_accuracy_respeta_umbral_ram(ram):
    eleccion = elegir(spec(quality="accuracy"), pyocrust.HardwareProfile(cpu_count=2, ram_bytes=ram))
    esperado = "tiny" if ram is None else "small" if ram < 8 * GIB else "medium"
    assert eleccion.size == esperado
    assert eleccion.id == f"pp_ocrv6_{esperado}"


def test_ocr_only_accuracy_con_poca_ram_cae_a_tiny():
    """`ram_bytes < 4 GiB` manda sobre la calidad pedida."""
    eleccion = elegir(spec(ocr_only=True, quality="accuracy"), hardware(ram_gib=2))
    assert eleccion.preset == "pp_ocrv6"
    assert eleccion.size == "tiny", f"size={eleccion.size!r} con 2 GiB, se esperaba 'tiny'"


def test_ocr_only_speed_con_mucha_ram_sigue_tiny():
    eleccion = elegir(spec(ocr_only=True, quality="speed"), hardware(ram_gib=64))
    assert eleccion.preset == "pp_ocrv6"
    assert eleccion.size == "tiny"


# --------------------------------------------------------------------------
# Tabla de decisión — pp_structurev3
# --------------------------------------------------------------------------


def test_formulas_with_text_elige_pp_structurev3():
    eleccion = elegir(spec(formulas="with_text"), hardware())
    assert eleccion.preset == "pp_structurev3", f"preset={eleccion.preset!r}"


def test_tablas_eligen_pp_structurev3():
    eleccion = elegir(spec(tables=True), hardware())
    assert eleccion.preset == "pp_structurev3", f"preset={eleccion.preset!r}"


def test_output_markdown_elige_pp_structurev3():
    eleccion = elegir(spec(output_format="markdown", ocr_only=False), hardware())
    assert eleccion.preset == "pp_structurev3", f"preset={eleccion.preset!r}"


def test_output_text_elige_pp_ocrv6():
    eleccion = elegir(spec(output_format="text", ocr_only=True), hardware())
    assert eleccion.preset == "pp_ocrv6", f"preset={eleccion.preset!r}"


def test_formulas_only_va_a_reconocimiento_de_formulas():
    """`formulas='only'` enruta a `formula_recognition` (sin layout) o a la página entera."""
    eleccion = elegir(spec(formulas="only", ocr_only=False), hardware())
    enruta = eleccion.preset == "pp_structurev3" or FORMULA_TASK in etapas(eleccion)
    assert enruta, (
        f"formulas='only' no enruta a {FORMULA_TASK} ni a pp_structurev3: "
        f"preset={eleccion.preset!r}, etapas={etapas(eleccion)}"
    )


# --------------------------------------------------------------------------
# Documentos escaneados: etapas previas de orientación y rectificación
# --------------------------------------------------------------------------


def test_escaneado_anade_orientacion_y_rectificacion():
    eleccion = elegir(spec(document_kind="scanned"), hardware())
    recomendadas = etapas(eleccion)
    assert ORIENTACION in recomendadas, f"falta {ORIENTACION} en {recomendadas}"
    assert RECTIFICACION in recomendadas, f"falta {RECTIFICACION} en {recomendadas}"


def test_digital_no_anade_las_etapas_de_escaneado():
    eleccion = elegir(spec(document_kind="digital"), hardware())
    recomendadas = etapas(eleccion)
    assert ORIENTACION not in recomendadas, f"{ORIENTACION} no debería aparecer en digital: {recomendadas}"
    assert RECTIFICACION not in recomendadas, f"{RECTIFICACION} no debería aparecer en digital: {recomendadas}"


# --------------------------------------------------------------------------
# Valores fuera de enum: error, no basura
# --------------------------------------------------------------------------


def test_quality_fuera_de_enum_lanza():
    with pytest.raises((ValueError, TypeError)):
        elegir(spec(quality="ultra"), hardware())


def test_document_kind_fuera_de_enum_lanza():
    with pytest.raises((ValueError, TypeError)):
        elegir(spec(document_kind="papel"), hardware())


# --------------------------------------------------------------------------
# hardware=None delega en detect_hardware()
# --------------------------------------------------------------------------


def test_hardware_none_usa_detect_hardware(monkeypatch):
    import importlib

    fijo = hardware(ram_gib=16, cpus=4)
    llamadas = []

    def falso(*_args, **_kwargs):
        llamadas.append(1)
        return fijo

    destino = None
    for nombre in ("pyocrust.resolver", "pyocrust"):
        try:
            modulo = importlib.import_module(nombre)
        except ImportError:
            continue
        if hasattr(modulo, "resolve_pipeline") and hasattr(modulo, "detect_hardware"):
            destino = nombre
            break
    if destino is None:
        pytest.fail("ningún módulo expone resolve_pipeline y detect_hardware juntos")

    monkeypatch.setattr(f"{destino}.detect_hardware", falso)
    elegir(spec(ocr_only=True, quality="balanced"))
    assert llamadas, "resolve_pipeline(task) sin hardware no llamó a detect_hardware()"
    # con un perfil explícito no debe detectar nada
    llamadas.clear()
    elegir(spec(ocr_only=True, quality="balanced"), hardware(ram_gib=16))
    assert not llamadas, "resolve_pipeline(task, hardware) no debe llamar a detect_hardware()"


# --------------------------------------------------------------------------
# Rama de GPU / indra
# --------------------------------------------------------------------------


def test_accuracy_con_gpu_de_8_gib_filtra_indra_segun_politica(gpu_8gib):
    hw = hardware(ram_gib=32, gpu=gpu_8gib)
    comercial = elegir(spec(ocr_only=True, quality="accuracy"), hw)
    no_comercial = elegir(
        spec(ocr_only=True, quality="accuracy", license_commercial_use=False), hw
    )
    con_atribucion = elegir(
        spec(ocr_only=True, quality="accuracy", license_commercial_use=False,
             license_acknowledge=True), hw
    )

    assert "indra" not in etapas(comercial)
    assert "indra" not in etapas(no_comercial), (
        "sin aceptar la atribución (§7) Indra no debe recomendarse"
    )
    assert "indra" in etapas(con_atribucion)


# --------------------------------------------------------------------------
# El id del resolvedor debe ser un preset válido para VeloceOCR
# --------------------------------------------------------------------------


def test_el_id_del_resolvedor_es_un_preset_no_vacio():
    eleccion = elegir(spec(ocr_only=True, quality="speed"), hardware())
    assert isinstance(eleccion.id, str) and eleccion.id, (
        f"PipelineChoice.id debe ser str no vacío, es {eleccion.id!r}"
    )


# --------------------------------------------------------------------------
# Prioridad de las variables de entorno
# --------------------------------------------------------------------------


@pytest.mark.parametrize("offline", [None, "", "0", "FALSE", " FALSE ", "no", "1", "true"])
def test_resolve_pipeline_prioriza_las_variables_de_entorno(monkeypatch, offline):
    from pathlib import Path

    oar = Path.cwd() / "modelos-oar-regresion"
    cache = Path.cwd() / "modelos-cache-regresion"
    monkeypatch.setenv("OAR_HOME", str(oar))
    monkeypatch.setenv("OCR_MODELS_CACHE_DIR", str(cache))
    if offline is None:
        monkeypatch.delenv("PYOCRUST_OFFLINE", raising=False)
    else:
        monkeypatch.setenv("PYOCRUST_OFFLINE", offline)
    eleccion = elegir(spec(), hardware())
    assert Path(eleccion.models_dir) == oar
    assert eleccion.offline is (offline in (" FALSE ", "1", "true"))
    assert eleccion.offline is pyocrust.models_status()["offline"]
    monkeypatch.delenv("OAR_HOME")
    assert Path(elegir(spec(), hardware()).models_dir) == cache
