"""Comprueba el criterio férreo de medición (ver `CRITERIO_MEDICION.md`).

Para cada (feature, device) localiza la run de referencia publicable, comprueba
que tiene UN solo CSV, que todas sus filas son de ese device y que TODOS los
motores miden el **mismo conjunto de `image_id`** —no solo el mismo `n`: dos
corridas con `n=20` midiendo páginas distintas pasaban como parejas—; y que el
conjunto de `image_id` de la pata CPU coincide con el de la GPU.

Uso:  .venv/Scripts/python.exe benchmarks/validez_medicion.py
Sale 0 si TODOS los features cumplen; 1 si alguno hay que rehacer (lista cuáles).
"""

import csv
import sys
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from common.runner import GPU_ONLY_BACKENDS, device_outcome  # noqa: E402
from features.report import latest_run, run_csv  # noqa: E402
from features.summary import FEATURES  # noqa: E402

RESULTS = BENCH / "results"


def probe(feature: str, device: str, results: Path = RESULTS) -> dict | None:
    """Muestra de la run de referencia de `(feature, device)`: `image_id` por motor.

    Solo lectura de CSVs: nada de inferencia. Devuelve `sets` (backend ->
    `frozenset` de `image_id` con `status=ok` de ese device) y `motors` (backend
    -> recuento de filas), o `None` si no hay run.
    """
    root = results if device == "cpu" else results / "_gpu"
    run = latest_run(feature, root=root, device=device)
    if run is None:
        return None
    csv_path = run_csv(run)
    if csv_path is None:
        return {"run": run.name, "csv": "AMBIGUO", "sets": {}, "motors": {}}
    ids: dict[str, set[str]] = {}
    with open(csv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("status") != "ok" or (row.get("device_requested") or device) != device:
                continue
            # Un motor GPU-only (VLM documental) NO tiene pata CPU: si una run
            # vieja le dejo filas CPU parciales, se ignoran en vez de romper la paridad.
            if device == "cpu" and row["backend"] in GPU_ONLY_BACKENDS:
                continue
            ids.setdefault(row["backend"], set()).add(row["image_id"])
    sets = {backend: frozenset(images) for backend, images in ids.items()}
    return {"run": run.name, "csv": csv_path.name,
            "sets": sets, "motors": {b: len(s) for b, s in sets.items()}}


def muestras_disjuntas(sets: dict[str, frozenset[str]]) -> list[str]:
    """Motores cuyo set de `image_id` NO es el mayoritario dentro de su device.

    Se compara el id **entero**, con su sufijo sintético (`::rot0`, `::persp`,
    `::box-<id>::rot180`): recortarlo haría pasar por iguales filas distintas.
    Devuelve `[]` si todos coinciden (o si mide uno solo: no hay "resto" con el
    que discrepar).
    """
    if len(sets) < 2:
        return []
    modal = Counter(sets.values()).most_common(1)[0][0]
    return sorted(backend for backend, images in sets.items() if images != modal)


def union(sets: dict[str, frozenset[str]]) -> frozenset[str]:
    """Set de `image_id` medidos por una pata (`frozenset()` si no midió nada)."""
    return frozenset().union(*sets.values()) if sets else frozenset()


def faltan_sobran(cpu_motors, gpu_motors) -> tuple[list[str], list[str]]:
    """Motores que faltan en GPU y motores GPU sobrantes respecto a la run CPU.

    Un motor CPU-only —el que `device_outcome(..., "gpu")` marca con motivo— no
    puede tener fila GPU. Simetricamente, un motor **GPU-only**
    (`GPU_ONLY_BACKENDS`: los VLM documentales) puede faltar en CPU sin ser un
    desemparejamiento. Ya **no** lo llama `estado` (la paridad se mide por
    `image_id`), pero se conserva: lo cubre `tests/test_validez_gpu_only.py`.
    """
    esperados = {m for m in cpu_motors if device_outcome(m, "gpu")[1] is None}
    return (sorted(esperados - set(gpu_motors)),
            sorted(m for m in set(gpu_motors) - set(cpu_motors) if m not in GPU_ONLY_BACKENDS))


def estado(cpu: dict | None, gpu: dict | None) -> str:
    """Estado del par `(feature, device)` por el set de `image_id` medido.

    `VALIDA` si ningún motor mide un set distinto del resto dentro de su device y
    el set de la pata CPU coincide con el de la GPU; si no, `REHACER: …` con el
    motivo. La paridad de **motores** ya no decide: lo que importa es que las
    **filas** (los `image_id`) sean las mismas — un motor ausente cuyas filas mide
    otro motor no cambia la muestra medida.
    """
    if not cpu or not gpu:
        return "PENDIENTE: falta " + ("CPU" if not cpu else "GPU")
    for tag, d in (("CPU", cpu), ("GPU", gpu)):
        raros = muestras_disjuntas(d["sets"])
        if raros:
            return f"REHACER: {raros[0]} mide otro set de image_id en {tag}"
    if union(cpu["sets"]) != union(gpu["sets"]):
        return "REHACER: muestras CPU y GPU distintas (image_id)"
    return "VALIDA"


def main() -> int:
    print("| feature | run CPU | n | motores | run GPU | n | motores | par CPU/GPU | estado |")
    print("| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |")
    pendientes = []
    for feature, _titular in FEATURES:
        cpu, gpu = probe(feature, "cpu"), probe(feature, "gpu")
        base = estado(cpu, gpu)
        par = "OK" if (cpu and gpu and union(cpu["sets"]) == union(gpu["sets"])) else "NO"
        nc = len(union(cpu["sets"])) if cpu else "-"
        ng = len(union(gpu["sets"])) if gpu else "-"
        texto = base
        if base == "VALIDA":
            # La paridad de MOTORES ya no invalida (ver `estado`), pero se deja
            # visible la cobertura: un motor sin fila en la otra pata no pasa
            # inadvertido. Ver `tests/test_validez_gpu_only.py`.
            faltan, sobran = faltan_sobran(cpu["motors"], gpu["motors"])
            if faltan or sobran:
                texto += f" · nota: motores sin par CPU/GPU {', '.join(faltan + sobran)}"
        else:
            pendientes.append(feature)
        print(f"| {feature} | {cpu['run'] if cpu else '-'} | {nc} | {len(cpu['motors']) if cpu else 0} "
              f"| {gpu['run'] if gpu else '-'} | {ng} | {len(gpu['motors']) if gpu else 0} "
              f"| {par} | {texto} |")
    print(f"\n{'TODOS los features cumplen' if not pendientes else 'REHACER: ' + ', '.join(pendientes)}")
    return 1 if pendientes else 0


if __name__ == "__main__":
    raise SystemExit(main())
