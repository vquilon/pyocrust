"""El verificador de filas compara **sets de `image_id`**, no solo `n`.

Dos corridas con `n=20` midiendo páginas distintas han de marcarse: el recuento
`n` no basta. Se fabrican runs sintéticas (CSV + `summary.json`) para ejercitar
`probe`/`estado` sin tocar `results/`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from validez_medicion import estado, muestras_disjuntas, probe

RUN = "2026-01-01_00-00-00"
_FIELDS = ["run_timestamp", "backend", "image_id", "status", "device_requested"]


def _write_run(results: Path, feature: str, device: str, rows: list[tuple[str, str]]) -> None:
    """Crea `results[/_gpu]/<feature>/<run>/` con un CSV de filas `(backend, image_id)` `ok`."""
    run = (results if device == "cpu" else results / "_gpu") / feature / RUN
    run.mkdir(parents=True)
    with (run / f"{RUN}.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FIELDS)
        writer.writeheader()
        for backend, image_id in rows:
            writer.writerow({"run_timestamp": RUN, "backend": backend, "image_id": image_id,
                             "status": "ok", "device_requested": device})
    (run / "summary.json").write_text(
        json.dumps({"device_requested": device, "timestamp": RUN}), encoding="utf-8")


def _probe(results: Path, feature: str, device: str) -> dict:
    got = probe(feature, device, results=results)
    assert got is not None
    return got


def test_motor_con_set_distinto_se_marca(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _write_run(results, "text", "cpu", [
        ("pyocrust", "page-a"), ("pyocrust", "page-b"), ("pyocrust", "page-c"),
        ("easyocr", "page-a"), ("easyocr", "page-b"),          # le falta `page-c`
    ])
    _write_run(results, "text", "gpu", [("pyocrust", "page-a"), ("pyocrust", "page-b")])
    cpu = _probe(results, "text", "cpu")
    assert muestras_disjuntas(cpu["sets"]) == ["easyocr"]
    veredicto = estado(cpu, _probe(results, "text", "gpu"))
    assert veredicto.startswith("REHACER") and "easyocr" in veredicto


def test_muestras_parejas_es_valida(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _write_run(results, "text", "cpu", [("pyocrust", "page-a"), ("pyocrust", "page-b"),
                                        ("easyocr", "page-a"), ("easyocr", "page-b")])
    _write_run(results, "text", "gpu", [("pyocrust", "page-a"), ("pyocrust", "page-b")])
    assert estado(_probe(results, "text", "cpu"), _probe(results, "text", "gpu")) == "VALIDA"


def test_muestras_cpu_y_gpu_distintas_se_marcan(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _write_run(results, "text", "cpu", [("pyocrust", "page-a"), ("pyocrust", "page-b")])
    _write_run(results, "text", "gpu", [("pyocrust", "page-a"), ("pyocrust", "page-c")])
    veredicto = estado(_probe(results, "text", "cpu"), _probe(results, "text", "gpu"))
    assert veredicto.startswith("REHACER") and "CPU y GPU" in veredicto


def test_sufijo_sintetico_se_compara_entero(tmp_path: Path) -> None:
    # El `image_id` de las features sintéticas lleva sufijo (`::rot0`, `::rot180`):
    # recortarlo haría pasar por iguales dos filas distintas.
    results = tmp_path / "results"
    _write_run(results, "orientation", "cpu", [
        ("pyocrust_orientation", "page-a::rot0"),
        ("pyocrust_orientation", "page-a::rot180"),
        ("easyocr_rotation", "page-a::rot0"),                  # le falta `::rot180`
    ])
    assert muestras_disjuntas(_probe(results, "orientation", "cpu")["sets"]) == ["easyocr_rotation"]


def test_motor_gpu_only_no_rompe_la_paridad(tmp_path: Path) -> None:
    # Un VLM documental (GPU-only) que mide las mismas filas no desempareja la pata.
    results = tmp_path / "results"
    _write_run(results, "full_page", "cpu", [("docling", "p1"), ("pyocrust_structure", "p1")])
    _write_run(results, "full_page", "gpu", [("docling", "p1"), ("pyocrust_structure", "p1"),
                                             ("glm_ocr", "p1")])
    assert estado(_probe(results, "full_page", "cpu"), _probe(results, "full_page", "gpu")) == "VALIDA"


def test_un_motor_o_ninguno_no_marca() -> None:
    # Un solo motor no tiene "resto" con el que discrepar; sin motores tampoco.
    assert muestras_disjuntas({"pyocrust": frozenset({"page-a", "page-b"})}) == []
    assert muestras_disjuntas({}) == []


def test_sin_pata_gpu_es_pendiente(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _write_run(results, "text", "cpu", [("pyocrust", "page-a")])
    assert estado(_probe(results, "text", "cpu"), None).startswith("PENDIENTE")
