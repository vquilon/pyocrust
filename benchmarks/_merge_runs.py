"""Merge / filtrado de CSVs de una o varias corridas en un run-dir.

`features/report.load_run` lee TODOS los `*.csv` de un run-dir, pero el banco
abre un run-dir por invocacion. Dos usos:

1. **Merge** (partir una feature por presion de memoria): `formula` con 12
   backends en un proceso murio; partirlo en dos invocaciones —una por grupo de
   modelos— y juntar sus CSV en un run-dir deja el informe con todas las filas.
2. **Regrupar la serie `vl`** (`--backends`): de la run de referencia de una
   feature se extrae **solo** el subconjunto de motores VLM a la subcarpeta de
   variante (`results/<feature>/vl/<ts>/`), sin re-medir nada. La run resultante
   declara `variant` y `regrouped_from`: es una vista derivada, no una corrida.

Uso:
    python benchmarks/_merge_runs.py <feature> <run_dir_destino> <run_dir_1> ...
    python benchmarks/_merge_runs.py <feature> <dest> <src> --backends a,b,c --variant vl
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Merge/filtrado de runs de un banco")
    parser.add_argument("feature")
    parser.add_argument("dest")
    parser.add_argument("sources", nargs="*", type=Path)
    parser.add_argument("--backends", default=None,
                        help="filtra las filas a estos backends (separados por comas): "
                             "regrupa la serie `vl` sin re-medir")
    parser.add_argument("--variant", default=None,
                        help="marca la run resultante con esta variante (p. ej. `vl`)")
    args = parser.parse_args(argv)

    feature, dest = args.feature, Path(args.dest)
    sources: list[Path] = list(args.sources)
    keep = set(filter(None, (args.backends or "").split(","))) if args.backends else None
    dest.mkdir(parents=True, exist_ok=True)
    merged_ts: str | None = None
    header: str | None = None
    rows: list[str] = []
    for src in sources:
        csvs = sorted(src.glob("*.csv"))
        if not csvs:
            print(f"[warn] {src} sin CSV")
            continue
        for csv_path in csvs:
            lines = csv_path.read_text(encoding="utf-8").splitlines()
            if not lines:
                continue
            header = header or lines[0]
            backend_col = header.split(",").index("backend")
            for line in lines[1:]:
                if not line.strip():
                    continue
                if keep is None or line.split(",")[backend_col] in keep:
                    rows.append(line)
            merged_ts = csv_path.stem
        # Copia los meta por backend y sus outputs (si los hay).
        for extra in list(src.glob("*.meta.json")) + list(src.glob("*.outputs.json")):
            if keep is not None and extra.name.split(".meta.json")[0] not in keep:
                continue
            shutil.copy2(extra, dest / extra.name)
    # UN solo CSV: `run_csv`/`validez_medicion` exigen exactamente uno; con varios
    # de nombres distintos ninguno casa con el timestamp y la run no se publica
    # (y validez solo veria los motores de uno).
    if header is not None and merged_ts:
        (dest / f"{merged_ts}.csv").write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    # summary.json propio: hereda la provenance de nivel superior de la primera
    # fuente (dataset, command, warmup, repeats, device…) y combina los backends
    # de todas. Sin esto el REPORT sale con `dataset: ?` (provenance perdida).
    base: dict = {}
    first_summary = sources[0] / "summary.json"
    if first_summary.exists():
        base = json.loads(first_summary.read_text(encoding="utf-8"))
    backends: dict = {}
    for src in sources:
        summary_path = src / "summary.json"
        if summary_path.exists():
            for backend, meta in json.loads(summary_path.read_text(encoding="utf-8")).get("backends", {}).items():
                if keep is None or backend in keep:
                    backends[backend] = meta
    merged = {**base, "timestamp": merged_ts, "feature": feature, "backends": backends}
    if keep is not None:
        # Vista derivada: se declara de donde sale, que backends pedia y COMO se
        # obtuvo (el `command` heredado nombra la corrida fuente y mentiria).
        merged["regrouped_from"] = [src.as_posix() for src in sources]
        merged["backends_requested"] = sorted(keep)
        merged["command"] = ["python", "benchmarks/_merge_runs.py", feature, dest.as_posix(),
                             *[src.as_posix() for src in sources],
                             "--backends", ",".join(sorted(keep))]
    if args.variant:
        merged["variant"] = args.variant
    (dest / "summary.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    total = sum(1 for _ in dest.glob("*.csv"))
    print(f"[merge] {feature}: {len(rows)} filas en {total} CSV -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
