"""Construye la fixture minima versionada de FUNSD (para la feature `text`).

Uso puntual: lee el split cacheado de `nielsr/funsd` y escribe
`benchmarks/fixtures/funsd_mini/` con un `manifest.json` (id, words, bboxes) +
`images/<id>.jpg`, para que `load_funsd` pueda servir texto + cajas GT sin red.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

BENCH = Path(__file__).resolve().parent
CACHE = BENCH / "data_cache"
OUT = BENCH / "fixtures" / "funsd_mini"
N_PAGES = 5
MAX_SIDE = 1600


def main() -> None:
    from datasets import load_dataset

    ds = load_dataset("nielsr/funsd", split="train", cache_dir=str(CACHE))
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "images").mkdir(parents=True)
    manifest = []
    for row in ds.select(range(min(N_PAGES, len(ds)))):
        image = row["image"].convert("RGB")
        scale = min(1.0, MAX_SIDE / max(image.size))
        if scale < 1.0:
            image = image.resize((round(image.width * scale), round(image.height * scale)))
        name = f"{row['id']}.jpg"
        image.save(OUT / "images" / name, format="JPEG", quality=85)
        manifest.append({
            "id": str(row["id"]),
            "image": name,
            "words": [str(w) for w in row["words"]],
            "bboxes": [[round(float(v) * scale, 2) for v in box] for box in row["bboxes"]],
        })
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(manifest)} paginas, {total/1e6:.2f} MB -> {OUT}")


if __name__ == "__main__":
    main()
