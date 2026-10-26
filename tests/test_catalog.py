"""Catálogo (S3.0) visto desde fuera: los campos existen y los tamaños no mienten.

Tarjeta `S3.2`. `pyocrust.model_catalog()` y `pyocrust.pipeline_profiles()` se
contrastan contra el registro de `oar-ocr` 0.10.1, que es la fuente que el
catálogo Rust declara leer (`oar_ocr::download::find(name).size`). Ese registro
vive en `oar-ocr-core-0.10.1/src/core/download/registry.rs`, en el checkout de
Cargo; el test lo parsea en vez de repetir los números, para no duplicar la
fuente de verdad. Un modelo ausente del registro debe salir con
`size_bytes is None`, jamás con un número inventado.

Ejecución: `python -m pytest tests/ -q`
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

import pyocrust

MODEL_FIELDS = ("name", "task", "description", "params", "size_bytes", "env_vars")
PIPELINE_FIELDS = (
    "id",
    "family",
    "quality",
    "output_format",
    "disk_bytes",
    "ram_bytes",
    "artifacts",
    "description",
)

GIB = 1024**3


# --------------------------------------------------------------------------
# El registro de oar-ocr, leído de su fuente (no copiado)
# --------------------------------------------------------------------------


def _registry_file() -> Path:
    """Localiza `oar-ocr-core-*/src/core/download/registry.rs` en el checkout de Cargo."""
    raices = []
    if os.environ.get("CARGO_HOME"):
        raices.append(Path(os.environ["CARGO_HOME"]) / "registry" / "src")
    raices.append(Path.home() / ".cargo" / "registry" / "src")
    for raiz in raices:
        if not raiz.is_dir():
            continue
        encontrados = sorted(raiz.glob("*/oar-ocr-core-*/src/core/download/registry.rs"))
        if encontrados:
            return encontrados[-1]
    pytest.skip(
        "no se encontró el fuente de oar-ocr-core en ~/.cargo/registry/src: "
        "sin él no hay contra qué contrastar los tamaños del catálogo"
    )


_ENTRY_RE = re.compile(
    r'Entry\s*\{\s*name:\s*"([^"]+)"\s*,\s*sha256:\s*"[^"]+"\s*,\s*size:\s*(\d+)\s*\}'
)


def _registro() -> dict[str, int]:
    """`{nombre_de_artefacto: tamaño_en_bytes}` del registro de oar-ocr."""
    texto = _registry_file().read_text(encoding="utf-8")
    entradas = {m.group(1): int(m.group(2)) for m in _ENTRY_RE.finditer(texto)}
    assert entradas, "el registro de oar-ocr no expuso ninguna entrada: ¿cambió el formato?"
    return entradas


def _valores(contenedor: object, nombre_funcion: str) -> list[dict]:
    """Los dicts de modelo/pipeline, exigiendo la forma documentada `dict -> dict`."""
    assert isinstance(contenedor, dict), (
        f"{nombre_funcion}() debe devolver un dict, no {type(contenedor).__name__}"
    )
    valores = list(contenedor.values())
    assert valores, f"{nombre_funcion}() está vacío"
    for valor in valores:
        assert isinstance(valor, dict), (
            f"{nombre_funcion}() debe mapear a dicts, no a {type(valor).__name__}"
        )
    return valores


# --------------------------------------------------------------------------
# model_catalog()
# --------------------------------------------------------------------------


def test_model_catalog_campos_documentados():
    for entrada in _valores(pyocrust.model_catalog(), "model_catalog"):
        faltan = [c for c in MODEL_FIELDS if c not in entrada]
        assert not faltan, f"modelo {entrada.get('name')!r}: faltan campos {faltan}"
        assert isinstance(entrada["name"], str) and entrada["name"], "name debe ser str no vacío"
        assert isinstance(entrada["task"], str) and entrada["task"], "task debe ser str no vacío"
        assert isinstance(entrada["description"], str) and entrada["description"], (
            f"{entrada['name']}: description vacía"
        )
        assert entrada["env_vars"] is not None, f"{entrada['name']}: env_vars no puede ser None"


def test_model_sizes_coinciden_con_el_registro():
    """Un `size_bytes` numérico debe ser exactamente el del registro; si no está, None."""
    registro = _registro()
    contrastados = 0
    inventados = []
    for entrada in _valores(pyocrust.model_catalog(), "model_catalog"):
        nombre = entrada["name"]
        if nombre in registro:
            if entrada["size_bytes"] != registro[nombre]:
                inventados.append(
                    f"{nombre}: catálogo={entrada['size_bytes']} registro={registro[nombre]}"
                )
            else:
                contrastados += 1
        elif entrada["size_bytes"] is not None:
            inventados.append(f"{nombre}: no está en el registro y aun así declara {entrada['size_bytes']}")

    assert not inventados, "size_bytes no coincide con el registro de oar-ocr:\n  " + "\n  ".join(inventados)
    assert contrastados > 0, (
        "ningún modelo del catálogo existe en el registro de oar-ocr: la comprobación no probó nada"
    )


def test_model_catalog_no_declara_tamano_sin_registro():
    """El complemento explícito del anterior, para dejar claro el contrato de `None`."""
    registro = _registro()
    no_registrados = [
        (e["name"], e["size_bytes"])
        for e in _valores(pyocrust.model_catalog(), "model_catalog")
        if e["name"] not in registro
    ]
    malos = [(n, s) for n, s in no_registrados if s is not None]
    assert not malos, f"modelos no registrados con tamaño inventado: {malos}"


# --------------------------------------------------------------------------
# pipeline_profiles()
# --------------------------------------------------------------------------


def test_pipeline_profiles_campos_documentados():
    perfiles = _valores(pyocrust.pipeline_profiles(), "pipeline_profiles")
    for perfil in perfiles:
        faltan = [c for c in PIPELINE_FIELDS if c not in perfil]
        assert not faltan, f"pipeline {perfil.get('id')!r}: faltan campos {faltan}"
        assert isinstance(perfil["id"], str) and perfil["id"], "id debe ser str no vacío"
        assert isinstance(perfil["disk_bytes"], int) or perfil["disk_bytes"] is None, (
            f"{perfil['id']}: disk_bytes debe ser int o None"
        )
        assert isinstance(perfil["ram_bytes"], int) or perfil["ram_bytes"] is None, (
            f"{perfil['id']}: ram_bytes debe ser int o None"
        )
        assert isinstance(perfil["artifacts"], (list, tuple)) and perfil["artifacts"], (
            f"{perfil['id']}: artifacts debe ser una lista no vacía"
        )
    assert any(p["disk_bytes"] for p in perfiles), "ningún pipeline declara disk_bytes real"


def test_pipeline_disk_bytes_es_la_suma_de_sus_artefactos_registrados():
    """`disk_bytes` no se inventa: si todos los artefactos están registrados, es su suma."""
    registro = _registro()
    discrepancias = []
    comprobados = 0
    for perfil in _valores(pyocrust.pipeline_profiles(), "pipeline_profiles"):
        artefactos = list(perfil["artifacts"])
        if not artefactos or any(a not in registro for a in artefactos):
            continue
        esperado = sum(registro[a] for a in artefactos)
        comprobados += 1
        if perfil["disk_bytes"] != esperado:
            discrepancias.append(
                f"{perfil['id']}: disk_bytes={perfil['disk_bytes']} suma_de_artefactos={esperado}"
            )
    assert not discrepancias, (
        "disk_bytes no cuadra con la suma de los artefactos registrados:\n  "
        + "\n  ".join(discrepancias)
    )
    if comprobados == 0:
        pytest.skip("ningún pipeline tiene todos sus artefactos en el registro de oar-ocr")
