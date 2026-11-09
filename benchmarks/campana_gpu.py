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
LIMIT = {"layout": 40}  # el resto, 20
FEATURES = ["text", "formula", "layout", "orientation", "rectification", "text_line", "seal", "table", "full_page"]


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
