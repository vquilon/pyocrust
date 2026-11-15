"""Contrato de la serie `vl`: subcarpeta de variante **bajo** cada feature.

La comparativa con el motor `vl` (el propio `pyocrust` con `--features vl` mas los
VLMs documentales) vive bajo la feature (`results/<feature>/vl/<run>/`) y escribe
sus informes en `reports|figures/<feature>/vl/`: la serie normal no se toca y el
guard de mtime de los derivados globales (que globa `reports/*/REPORT.md`, un
solo nivel) no la ve.
"""

from __future__ import annotations

import json
from pathlib import Path

import features.report as report
from common.runner import (FEATURE_TYPES, GPU_ONLY_BACKENDS, MODEL_NAMES, PROVIDERS,
                          STRUCTURE_CHANNELS, TASK_TYPES, emitted_channels)
from features._base import FeatureSpec, feature_out_dir

SPEC = FeatureSpec(feature="full_page", summary="x", pyocrust_task=None, metric="m", dataset="d")


def _run_dir(tmp_path: Path, variant: str | None, ts: str, backend: str,
             device: str = "cpu") -> Path:
    """Fabricar una run mínima (CSV de 1 fila + summary) en la jerarquía pedida."""
    run = tmp_path / "full_page" / variant / ts if variant else tmp_path / "full_page" / ts
    run.mkdir(parents=True)
    (run / f"{ts}.csv").write_text(
        "backend,status,device_requested,image_id\n"
        f"{backend},ok,{device},page-1\n",
        encoding="utf-8",
    )
    (run / "summary.json").write_text(json.dumps({
        "timestamp": ts, "feature": "full_page", "dataset": "d",
        "device_requested": device, "n_samples": 1, "command": ["python", "bank.py"],
        "backends": {backend: {"status": "ok"}},
    }), encoding="utf-8")
    return run


def test_feature_out_dir_pone_la_variante_bajo_la_feature(tmp_path: Path) -> None:
    assert feature_out_dir(tmp_path, SPEC, "vl") == tmp_path / "full_page" / "vl"
    assert feature_out_dir(tmp_path, SPEC) == tmp_path / "full_page"


def test_latest_run_de_la_variante_no_ve_la_serie_normal(tmp_path: Path) -> None:
    normal = _run_dir(tmp_path, None, "2026-01-01_00-00-00", "pyocrust_structure")
    vl = _run_dir(tmp_path, "vl", "2026-01-02_00-00-00", "pyocrust_vl")
    assert report.latest_run("full_page", root=tmp_path, variant="vl") == vl
    assert report.latest_run("full_page", root=tmp_path) == normal


def test_el_informe_de_variante_escribe_bajo_la_feature(tmp_path: Path, monkeypatch) -> None:
    """`--variant vl` lee/y escribe en `.../full_page/vl/`, nunca en la serie normal."""
    run = _run_dir(tmp_path, "vl", "2026-01-02_00-00-00", "pyocrust_vl")
    monkeypatch.setattr(report, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(report, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(report, "analyze", lambda feature, run: ({}, {}))
    monkeypatch.setattr(report, "render_md", lambda *a, **k: "# md")
    monkeypatch.setattr(report, "render_table", lambda *a, **k: ("| t |", "tex"))
    fig: dict = {}
    monkeypatch.setattr(report, "plot_feature",
                        lambda feature, rep, summ, out, gpu_report=None: fig.__setitem__("out", out))

    rc = report.main(["--feature", "full_page", "--variant", "vl",
                      "--run", str(run), "--no-gpu"])

    assert rc == 0
    base = tmp_path / "reports" / "full_page"
    assert (base / "vl" / "REPORT.md").is_file()
    assert (base / "vl" / "REPORT.en.md").is_file()
    assert (base / "vl" / "benchmark_table.md").is_file()
    assert (base / "vl" / "benchmark_table.tex").is_file()
    assert not (base / "REPORT.md").exists(), "la variante no toca la serie normal"
    assert fig["out"] == tmp_path / "figures" / "full_page" / "vl" / "REPORT"


def test_variant_sin_run_cpu_usa_la_de_gpu_como_referencia(tmp_path: Path, monkeypatch) -> None:
    """Una variante GPU-only (VLM externos en layout/table/formula) igual tiene subcarpeta."""
    gpu = _run_dir(tmp_path / "_gpu", "vl", "2026-01-03_00-00-00", "glm_ocr", device="gpu")
    monkeypatch.setattr(report, "GPU_RESULTS_DIR", tmp_path / "_gpu")
    monkeypatch.setattr(report, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(report, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(report, "analyze", lambda feature, run: ({}, {}))
    monkeypatch.setattr(report, "render_md", lambda *a, **k: "# md")
    monkeypatch.setattr(report, "render_table", lambda *a, **k: ("| t |", "tex"))
    monkeypatch.setattr(report, "plot_feature", lambda *a, **k: None)

    assert report.latest_run("full_page", root=tmp_path) is None
    assert report.latest_run("full_page", root=tmp_path / "_gpu", device="gpu",
                             variant="vl") == gpu
    assert report.main(["--feature", "full_page", "--variant", "vl", "--no-gpu"]) == 0
    assert (tmp_path / "reports" / "full_page" / "vl" / "REPORT.md").is_file()


def test_variant_exige_feature(tmp_path: Path) -> None:
    """`--variant` sin `--feature`/con `--all` es un error de uso, no un informe suelto."""
    import pytest

    with pytest.raises(SystemExit):
        report.main(["--all", "--variant", "vl"])


def test_el_reporte_de_variante_no_entra_en_el_guard_de_mtime(tmp_path: Path) -> None:
    """El guard globa `reports/*/REPORT.md` (un nivel); la variante vive dos abajo."""
    vl_rep = tmp_path / "reports" / "full_page" / "vl" / "REPORT.md"
    vl_rep.parent.mkdir(parents=True)
    vl_rep.write_text("x", encoding="utf-8")
    assert sorted(tmp_path.glob("reports/*/REPORT.md")) == []


def test_pyocrust_vl_registrado_como_variante_vl() -> None:
    assert MODEL_NAMES["pyocrust_vl"] == ("pyocrust", "vl")
    assert TASK_TYPES["pyocrust_vl"] == "full_page"
    assert FEATURE_TYPES["pyocrust_vl"] == "full_page"
    assert "pyocrust_vl" in PROVIDERS
    assert STRUCTURE_CHANNELS["pyocrust_vl"] == frozenset()
    assert emitted_channels("pyocrust_vl") == frozenset()


def test_pyocrust_vl_no_es_gpu_only_los_vlm_externos_si() -> None:
    """`pyocrust_vl` corre sobre Candle, que tambien corre en CPU (t_7e787468)."""
    assert "pyocrust_vl" not in GPU_ONLY_BACKENDS
    assert {"lightonocr", "glm_ocr", "paddleocr_vl"} <= GPU_ONLY_BACKENDS
