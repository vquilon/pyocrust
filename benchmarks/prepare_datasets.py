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
from common.datasets import (  # noqa: E402
    ODB_EN_LANGUAGES,
    ODB_EN_SAMPLE_N,
    OMNIDOCBENCH_REPO,
    _odb_full_page_pool,
    odb_composition,
)

# Referencias **externas** de la comparativa de parse: otros benchmarks sobre otro
# dataset y otra metrica. Se declaran aqui como `referencia` (nunca `medido` por
# nosotros) para que nadie cite sus cifras como si fueran nuestras; no se
# descargan ni entran en ninguna tabla.
EXTERNAL_REFERENCES = {
    "comment": (
        "Benchmarks externos de parse documental. Sus cifras son `referencia` "
        "(paper/leaderboard), nunca `medido` por nosotros: otro dataset, otro GT y "
        "otra metrica. No se descargan ni se publican en las tablas."
    ),
    "parsebench": {
        "name": "ParseBench (LlamaIndex)",
        "repo": "run-llama/ParseBench",
        "dataset": "llamaindex/ParseBench",
        "note": (
            "el mismo banco que publican LightOnOCR y GLM-OCR: ~2.078 paginas "
            "verificadas de documentos de empresa, cinco dimensiones con su propia "
            "metrica (GTRM/ChartDataPointMatch/...), no comparable 1:1 con nuestro "
            "`markdown_f1`."
        ),
    },
    "fr-bench-pdf2md": {
        "name": "fr-bench-pdf2md (Probayes/OpenValue)",
        "dataset": "pulsia/fr-bench-pdf2md",
        "note": (
            "PDF->Markdown en frances con evaluacion estilo unit-test; cubre el "
            "idioma frances, que OmniDocBench no anota (solo `english` es latino)."
        ),
    },
}


def _update_composition(n: int = ODB_EN_SAMPLE_N) -> Path:
    """Declara en el manifiesto la composicion de la muestra **no china** (sin red).

    Pool completo (paginas `english` con Markdown GT, en el orden estratificado) y
    la muestra de `n` paginas que sirve el loader: misma seleccion, **sin
    descargar ninguna imagen**. Se cruza cada `image_id` con su
    `page_info.page_attribute` (`odb_composition`), asi que la declaracion es
    reproducible sin red a partir de la anotacion cacheada.
    """
    pool = _odb_full_page_pool(languages=ODB_EN_LANGUAGES)
    sample = pool[:n]
    manifest = load_manifest()
    manifest["samples"] = {
        "omnidocbench_full_page_en": {
            "declared_n": n,
            "provenance": "medido",
            "source": (
                f"{OMNIDOCBENCH_REPO} (HF), `page_info.page_attribute.language` en "
                f"{list(ODB_EN_LANGUAGES)}; misma revision pinnada y mismo checksum "
                f"que el resto de OmniDocBench"
            ),
            "pool": odb_composition(pool),
            "sample": odb_composition(sample, [p["page_info"]["image_path"] for p in sample]),
        }
    }
    manifest["external_references"] = EXTERNAL_REFERENCES
    DATASETS_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return DATASETS_MANIFEST


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
    parser.add_argument("--composition", action="store_true",
                        help="declara (sin red) la composicion de la muestra no china en el manifiesto")
    args = parser.parse_args(argv)
    if args.composition:
        try:
            path = _update_composition()
        except DatasetOffline as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2
        manifest = load_manifest()
        declared = manifest["samples"]["omnidocbench_full_page_en"]
        print(f"[composition] {path}")
        print(f"[composition] pool: {declared['pool']['pages']} paginas "
              f"{declared['pool']['language']}")
        print(f"[composition] muestra n={declared['declared_n']}: "
              f"{declared['sample']['data_source']}")
        return 0
    if not args.fetch:
        parser.error("nada que hacer: usa --fetch (o --composition) para poblar el cache")

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
