#!/usr/bin/env python
"""Prepara (puebla) el cache del dataset de `benchmarks/` — paso explicito.

    python benchmarks/prepare_datasets.py --fetch          # descarga + verifica
    python benchmarks/prepare_datasets.py --fetch --update-manifest  # refresca el sha256

Sin red y con el cache vacio, falla con UN error claro y accionable (no deja N
muestras en `skipped`). Con red, descarga la anotacion pinnada por revision,
verifica su sha256 contra `benchmarks/datasets_manifest.json` y reporta el estado.

El cache ya poblado de esta maquina sigue valido: la verificacion es de lectura.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    DATASETS_MANIFEST,
    DatasetOffline,
    DatasetUnavailable,
    load_manifest,
    prepare_datasets,
)


def _update_manifest(sha256: str, size: int) -> Path:
    """Reescribe `datasets_manifest.json` con el sha256/tamano observados."""
    manifest = load_manifest()
    manifest.setdefault("files", {})["OmniDocBench.json"] = {"sha256": sha256, "size": size}
    DATASETS_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return DATASETS_MANIFEST


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara el cache de datasets de benchmark")
    parser.add_argument("--fetch", action="store_true",
                        help="descarga + verifica el dataset pinnado (requiere red la 1a vez)")
    parser.add_argument("--update-manifest", action="store_true",
                        help="reescribe datasets_manifest.json con el sha256 observado")
    args = parser.parse_args(argv)
    if not args.fetch:
        parser.error("nada que hacer: usa --fetch para poblar el cache")

    try:
        info = prepare_datasets()
    except DatasetOffline as exc:
        # UN solo error, claro y accionable: esto es el criterio de la tarjeta.
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    except DatasetUnavailable as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if args.update_manifest:
        path = _update_manifest(info["sha256"], Path(info["annotation"]).stat().st_size)
        print(f"[manifest] actualizado: {path}")
    print(f"[ok] anotacion: {info['annotation']}")
    print(f"[ok] revision:  {info['revision']}")
    print(f"[ok] sha256:    {info['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
