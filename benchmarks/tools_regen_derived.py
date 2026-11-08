"""Regenera los informes derivados de `benchmarks` en el orden correcto.

`features.report --all` escribe los `REPORT.md` por feature y `CPU_VS_GPU.md`;
estos cuatro se escriben **después**, o el test de frescura
(`test_artefactos_derivados_no_son_mas_viejos_que_los_report`) falla.

Uso:  .venv/Scripts/python.exe benchmarks/tools_regen_derived.py
"""

import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
MODULOS = ("features.summary", "features.scoreboard", "features.quality_vs_time", "features.overview")

for modulo in MODULOS:
    r = subprocess.run([sys.executable, "-m", modulo], cwd=BENCH, capture_output=True, text=True)
    tail = (r.stdout or r.stderr or "").strip().splitlines()[-2:]
    print(f"{modulo:28s} rc={r.returncode} :: {' | '.join(tail)}")
