"""Comprueba el criterio férreo de medición (ver `CRITERIO_MEDICION.md`).

Para cada (feature, device) localiza la run de referencia publicable, comprueba
que tiene UN solo CSV, que todas sus filas son de ese device y que TODOS los
motores traen el mismo `n`; y que el par CPU/GPU empareja en `n` y en motores.

Uso:  .venv/Scripts/python.exe benchmarks/validez_medicion.py
Sale 0 si TODOS los features cumplen; 1 si alguno hay que rehacer (lista cuáles).
"""

import csv
import sys
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from features.report import latest_run, run_csv  # noqa: E402
from features.summary import FEATURES  # noqa: E402

RESULTS = BENCH / "results"


def probe(feature: str, device: str) -> dict | None:
    root = RESULTS if device == "cpu" else RESULTS / "_gpu"
    run = latest_run(feature, root=root, device=device)
    if run is None:
        return None
    csv_path = run_csv(run)
    if csv_path is None:
        return {"run": run.name, "csv": "AMBIGUO", "n": set(), "motors": {}}
    motors: Counter = Counter()
    with open(csv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("status") == "ok" and (row.get("device_requested") or device) == device:
                motors[row["backend"]] += 1
    return {"run": run.name, "csv": csv_path.name, "n": set(motors.values()), "motors": dict(motors)}


def main() -> int:
    print("| feature | run CPU | n | motores | run GPU | n | motores | par CPU/GPU | estado |")
    print("| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |")
    pendientes = []
    for feature, _titular in FEATURES:
        cpu, gpu = probe(feature, "cpu"), probe(feature, "gpu")
        nc = "/".join(str(x) for x in sorted(cpu["n"])) if cpu else "-"
        ng = "/".join(str(x) for x in sorted(gpu["n"])) if gpu else "-"
        same_n = bool(cpu and gpu and cpu["n"] == gpu["n"] and len(cpu["n"]) == 1)
        uniform = all(len(d["n"]) == 1 for d in (cpu, gpu) if d)
        if not cpu or not gpu:
            estado = "PENDIENTE: falta " + ("CPU" if not cpu else "GPU")
        elif not same_n:
            estado = "REHACER: n distinto CPU/GPU"
        elif not uniform:
            estado = "REHACER: n dispar dentro del device"
        else:
            faltan = set(cpu["motors"]) ^ set(gpu["motors"])
            estado = "VALIDA" if not faltan else f"REHACER: motor desemparejado ({sorted(faltan)[0]})"
        if estado != "VALIDA":
            pendientes.append(feature)
        print(f"| {feature} | {cpu['run'] if cpu else '-'} | {nc} | {len(cpu['motors']) if cpu else 0} "
              f"| {gpu['run'] if gpu else '-'} | {ng} | {len(gpu['motors']) if gpu else 0} "
              f"| {'OK' if same_n else 'NO'} | {estado} |")
    print(f"\n{'TODOS los features cumplen' if not pendientes else 'REHACER: ' + ', '.join(pendientes)}")
    return 1 if pendientes else 0


if __name__ == "__main__":
    raise SystemExit(main())
