"""Campaña definitiva: pata GPU feature a feature, **en serie** (un banco a la vez).

Por cada feature lanza su banco con `--limit` uniforme (el mismo de la run CPU de
referencia; `layout`=40, resto 20) y `--device gpu`. Al terminar todas, regenera la
cadena de informes en el orden que exige `test_artefactos_derivados...`, pasa el
verde de pytest y comprueba el criterio con `validez_medicion.py`.

Aborta de entrada si ya hay un banco corriendo: dos bancos a la vez invalidan la
medida (regla 7 del criterio).

Uso:  .venv/Scripts/python.exe benchmarks/campana_gpu.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "Scripts" / "python.exe"
BENCH = REPO / "benchmarks"
# Límites del banco estratificado (t_4d2155d3, features/sample_banks.py::BANKS);
# el resto conserva su banco de 20. Deben casar con la run CPU de referencia.
LIMIT = {"formula": 10, "table": 8, "full_page": 6, "layout": 40}  # el resto, 20
FEATURES = ["text", "formula", "layout", "orientation", "rectification", "text_line", "seal", "table", "full_page"]


def pyd_sha256() -> str:
    """sha256 del `.pyd` desplegado: deja constancia de QUÉ binario se midió."""
    import hashlib

    pyd = REPO / "pyocrust" / "_pyocrust_core.pyd"
    h = hashlib.sha256(pyd.read_bytes()).hexdigest() if pyd.exists() else "AUSENTE"
    print(f"[binario] {pyd.name} sha256={h} mtime={pyd.stat().st_mtime if pyd.exists() else '-'}", flush=True)
    return h


def bancos_vivos() -> int:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
         "Where-Object { $_.CommandLine -match 'bank\\.py' }).Count"],
        capture_output=True, text=True).stdout
    m = re.search(r"\d+", out or "")
    return int(m.group()) if m else -1


vivos = bancos_vivos()
if vivos != 0:
    raise SystemExit(f"ABORTADO: hay {vivos} banco(s) corriendo; el criterio exige uno a la vez")

pyd_sha256()

# El binario desplegado tiene que traer el EP acelerador compilado. Sin él cada
# banco sale con las `pyocrust*` en `skipped` (regla 8) y la campaña son horas
# tiradas: medido 2026-11-14 — otra tarjeta recompiló el `.pyd` con las features
# por defecto y las dos `pyocrust_*` de `full_page` salieron `skipped`.
_r = subprocess.run(
    [str(PY), "-c", "import pyocrust; print(','.join(pyocrust.available_providers()))"],
    cwd=REPO, capture_output=True, text=True)
PROVIDERS = [p for p in (_r.stdout or "").strip().split(",") if p]
if not PROVIDERS:
    raise SystemExit(
        "ABORTADO: el .pyd desplegado no registra ningún EP acelerador "
        "(available_providers()=[]). Recompílalo con CUDA antes de la campaña:\n"
        "  .venv/Scripts/maturin develop --release --features cuda"
    )
print(f"[binario] available_providers={PROVIDERS}", flush=True)

for feature in FEATURES:
    n = LIMIT.get(feature, 20)
    cmd = [str(PY), str(BENCH / "features" / feature / "bank.py"),
           "--limit", str(n), "--device", "gpu", "--output-dir", "benchmarks/results/_gpu"]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    tail = [ln for ln in (r.stdout or r.stderr or "").strip().splitlines() if ln.strip()][-6:]
    print(f"[{feature}] --limit {n} rc={r.returncode} {time.time()-t0:.0f}s", flush=True)
    for ln in tail:
        print("    " + ln.strip(), flush=True)

print("\n=== cadena de informes ===", flush=True)
for cmd in ([str(BENCH / "features" / "report.py"), "--all"], [str(BENCH / "tools_regen_derived.py")]):
    r = subprocess.run([str(PY), *cmd], cwd=REPO, capture_output=True, text=True)
    print(f"{Path(cmd[0]).name} rc={r.returncode}", flush=True)

r = subprocess.run([str(PY), "-m", "pytest", str(BENCH / "tests"), "-q", "--no-header",
                    "-p", "no:cacheprovider"], cwd=REPO, capture_output=True, text=True)
print("pytest:", [ln for ln in (r.stdout or "").strip().splitlines() if ln.strip()][-1], flush=True)

r = subprocess.run([str(PY), str(BENCH / "validez_medicion.py")], cwd=REPO, capture_output=True, text=True)
print(r.stdout.strip(), flush=True)
