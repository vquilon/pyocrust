"""Merge de CSVs de varias corridas de un banco en un unico run-dir.

`features/report.load_run` lee TODOS los `*.csv` de un run-dir, pero el banco
abre un run-dir por invocacion. Con `formula` (12 backends en un solo proceso,
paddle+torch juntos) el proceso murio por presion de memoria; partirlo en dos
invocaciones — una por grupo de modelos — y juntar sus CSV en un run-dir deja el
informe con todas las filas sin cargar todo a la vez.

Uso:
    python benchmarks/_merge_runs.py <feature> <run_dir_destino> <run_dir_1> ...
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    feature, dest, *sources = argv
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    merged_ts = None
    for src in sources:
        src = Path(src)
        csvs = sorted(src.glob("*.csv"))
        if not csvs:
            print(f"[warn] {src} sin CSV")
            continue
        for csv_path in csvs:
            shutil.copy2(csv_path, dest / csv_path.name)
        latest = csvs[-1]
        merged_ts = latest.stem
        # Copia los meta por backend y sus outputs (si los hay).
        for extra in list(src.glob("*.meta.json")) + list(src.glob("*.outputs.json")):
            shutil.copy2(extra, dest / extra.name)
    # summary.json propio: hereda la provenance de nivel superior de la primera
    # fuente (dataset, command, warmup, repeats, device…) y combina los backends
    # de todas. Sin esto el REPORT sale con `dataset: ?` (provenance perdida).
    base: dict = {}
    first_summary = Path(sources[0]) / "summary.json"
    if first_summary.exists():
        base = json.loads(first_summary.read_text(encoding="utf-8"))
    backends: dict = {}
    for src in sources:
        summary_path = Path(src) / "summary.json"
        if summary_path.exists():
            backends.update(json.loads(summary_path.read_text(encoding="utf-8")).get("backends", {}))
    merged = {**base, "timestamp": merged_ts, "feature": feature, "backends": backends}
    (dest / "summary.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    total = sum(1 for _ in dest.glob("*.csv"))
    print(f"[merge] {feature}: {total} CSV en {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
