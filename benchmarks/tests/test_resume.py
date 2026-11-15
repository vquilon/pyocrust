"""Contrato de **guardado parcial + reanudación** (`--resume`) del runner.

Regla dura: matar una corrida a mitad **no puede** perder lo ya medido. El CSV y
el `summary.json` se reescriben tras cada motor (no solo al final) y `--resume`
reusa la corrida incompleta saltando los motores `ok`. Sin esto se perdieron
horas: matar la corrida en el último motor dejaba 6 `<backend>.meta.json`
huérfanos, invisibles para los reporteros (que leen el CSV).
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from common.datasets import Sample
from common.runner import OcrOutput, run_backends
from features._base import FeatureSpec, feature_run_dir

SPEC = FeatureSpec(feature="faketest", summary="x", pyocrust_task=None, metric="m", dataset="d")
_SIG = {"dataset": "d", "n_samples": 1, "warmup": 0, "repeats": 1, "device_requested": "cpu"}


def _sample() -> Sample:
    return Sample("img1", Image.new("RGB", (8, 8)), "hola mundo")


def _factory(text: str, called: list | None = None, tag: str = ""):
    def factory(device: str = "cpu"):
        if called is not None:
            called.append(tag)

        def run(image):
            return OcrOutput(text=text, elapsed_ms=1.0)

        run.provider_effective = "cpu"
        return run

    return factory


def test_guardado_incremental_deja_csv_y_summary(tmp_path: Path) -> None:
    """Una corrida interrumpida a mitad deja CSV + summary legibles (no solo metas)."""
    out, ts, res = feature_run_dir(tmp_path, SPEC, "2026-01-01_00-00-00", None,
                                   resume=False, signature=_SIG)
    run_backends([_sample()], ["fakeA"], "d", out, ts, warmup=0, repeats=1, device="cpu",
                 factories={"fakeA": _factory("hola mundo")}, feature="faketest")
    assert (out / f"{ts}.csv").exists()
    data = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert data["run_signature"] == _SIG
    assert data["backends"]["fakeA"]["status"] == "ok"
    assert res is False


def test_resume_encuentra_corrida_incompleta_por_firma(tmp_path: Path) -> None:
    """`resume` reengancha la incompleta de la MISMA firma; otra firma no casa."""
    run = tmp_path / "faketest" / "2026-01-01_00-00-00"
    run.mkdir(parents=True)
    (run / "summary.json").write_text(json.dumps({
        "timestamp": "2026-01-01_00-00-00", "run_signature": _SIG,
        "backends_requested": ["fakeA", "fakeB"], "backends": {"fakeA": {"status": "ok"}},
    }), encoding="utf-8")
    out, ts, do = feature_run_dir(tmp_path, SPEC, "2026-02-02_00-00-00", None,
                                  resume=True, signature=_SIG)
    assert do is True and ts == "2026-01-01_00-00-00" and out == run
    out2, ts2, do2 = feature_run_dir(tmp_path, SPEC, "2026-02-02_00-00-00", None,
                                     resume=False, signature=_SIG)
    assert do2 is False and ts2 == "2026-02-02_00-00-00" and out2 != run
    _out3, _ts3, do3 = feature_run_dir(tmp_path, SPEC, "2026-02-02_00-00-00", None,
                                       resume=True, signature={**_SIG, "device_requested": "gpu"})
    assert do3 is False, "otra firma (device distinto) no debe reenganchar"


def test_resume_salta_motores_ok_sin_reconstruirlos(tmp_path: Path) -> None:
    """`resume` NO reconstruye un motor ya `ok` (reenganchar cuesta segundos, no horas)."""
    out = tmp_path / "faketest" / "2026-01-01_00-00-00"
    out.mkdir(parents=True)
    (out / "summary.json").write_text(json.dumps({
        "timestamp": "2026-01-01_00-00-00", "run_signature": _SIG,
        "backends_requested": ["fakeA", "fakeB"], "backends": {"fakeA": {"status": "ok"}},
    }), encoding="utf-8")
    called: list[str] = []
    _rows, summary = run_backends(
        [_sample()], ["fakeA", "fakeB"], "d", out, "2026-01-01_00-00-00",
        warmup=0, repeats=1, device="cpu", resume=True, feature="faketest",
        factories={"fakeA": _factory("x", called, "A"), "fakeB": _factory("hola mundo", called, "B")},
    )
    assert called == ["B"], f"fakeA no debía reconstruirse: {called}"
    assert summary["fakeB"]["status"] == "ok"


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    import tempfile

    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            with tempfile.TemporaryDirectory() as _d:
                _fn(Path(_d))
    print("tests/test_resume self-check OK")
