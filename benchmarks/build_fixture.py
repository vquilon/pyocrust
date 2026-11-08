"""Construye la fixture minima versionada de OmniDocBench.

Uso puntual (no forma parte del suite): lee la anotacion cacheada de
`benchmarks/data_cache`, elige ~10 paginas deterministas que cubren las
categorias que las 9 features necesitan y escribe `benchmarks/fixtures/
omnidocbench_mini/` con el MISMO esquema que la release de HF (un
`OmniDocBench.json` recortado + `images/<name>`), para que los loaders lo
consuman sin cambios.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
BENCH = ROOT
CACHE = BENCH / "data_cache" / "datasets--opendatalab--OmniDocBench"
OUT = BENCH / "fixtures" / "omnidocbench_mini"

REQUIRED = {
    "text_block", "title", "equation_isolated", "table", "figure",
    "figure_caption", "header", "footer", "page_number", "page_footnote",
    "reference", "list_group",
}


def _cats(page: dict) -> set[str]:
    return {d["category_type"] for d in page["layout_dets"] if not d.get("ignore")}


# Lado mayor maximo de las imagenes de la fixture: la release trae paginas de
# hasta 8225px (17 MB una sola). Se reescalan y se reescalan tambien sus `poly`
# para que el GT siga siendo coherente con la imagen (el harness usa pixeles).
MAX_SIDE = 2400


def _trim(page: dict, scale: float = 1.0) -> dict:
    """Recorta la anotacion de una pagina al minimo que consume el harness."""
    page = dict(page)
    dets = []
    for det in page["layout_dets"]:
        kept = {k: det[k] for k in ("category_type", "order", "ignore", "text",
                                    "latex", "html", "anno_id") if k in det}
        if "poly" in det:
            kept["poly"] = [round(float(v) * scale, 3) for v in det["poly"]]
        if "bbox" in det:
            kept["bbox"] = [round(float(v) * scale, 3) for v in det["bbox"]]
        dets.append(kept)
    page["layout_dets"] = dets
    info = dict(page["page_info"])
    if scale != 1.0:
        info["width"] = round(info["width"] * scale)
        info["height"] = round(info["height"] * scale)
    page["page_info"] = info
    return page


def main() -> None:
    snap = sorted(CACHE.glob("snapshots/*"))[0]
    ann = json.loads((snap / "OmniDocBench.json").read_text(encoding="utf-8"))
    # Solo paginas cuya imagen esta realmente cacheada (HF descarga bajo demanda):
    # la fixture debe poder construirse offline desde el cache existente.
    cached = {p.name for p in (snap / "images").glob("*") if p.is_file()}

    cand = []
    for i, page in enumerate(ann):
        if page["page_info"]["image_path"] not in cached:
            continue
        cats = _cats(page)
        has_tbl = "table" in cats and any(
            d["category_type"] == "table" and d.get("html") and not d.get("ignore")
            for d in page["layout_dets"])
        has_eq = any(
            d["category_type"] == "equation_isolated" and d.get("latex") and not d.get("ignore")
            for d in page["layout_dets"])
        cand.append((i, cats, has_tbl, has_eq, page))
    # Determinista: ricas (tabla, formula) primero, luego cobertura, luego anotacion.
    ordered = sorted(
        cand, key=lambda x: (-int(x[2]), -int(x[3]), -len(x[1].intersection(REQUIRED)), x[0]))

    picked: list[dict] = []
    picked_idx: set[int] = set()
    seen_cats: set[str] = set()
    # Fase 1: cubrir categorias raras (una pagina por categoria sin cubrir).
    while seen_cats != REQUIRED:
        gain = [c for c in ordered if c[0] not in picked_idx
                and c[1].intersection(REQUIRED) - seen_cats]
        if not gain:
            break
        best = max(gain, key=lambda c: (len(c[1].intersection(REQUIRED) - seen_cats),
                                        -int(c[2]), -int(c[3]), -c[0]))
        picked.append(best[4]); picked_idx.add(best[0]); seen_cats.update(best[1])
    # Fase 2: rellenar hasta 10 con las mas ricas (>=2 muestras por feature).
    for i, cats, _t, _e, page in ordered:
        if len(picked) >= 10:
            break
        if i not in picked_idx:
            picked.append(page); picked_idx.add(i); seen_cats.update(cats)

    missing = REQUIRED - seen_cats
    if missing:
        print(f"[aviso] categorias raras ausentes en la fixture: {sorted(missing)}")

    img_dir = OUT / "images"
    if OUT.exists():
        shutil.rmtree(OUT)
    img_dir.mkdir(parents=True)
    kept_ann = []
    for page in picked:
        name = page["page_info"]["image_path"]
        src = snap / "images" / name
        image = Image.open(src).convert("RGB")
        scale = min(1.0, MAX_SIDE / max(image.size))
        if scale < 1.0:
            image = image.resize((max(1, round(image.width * scale)),
                                  max(1, round(image.height * scale))))
        # PNG sin perdida y con el nombre/extensión ORIGINALES: los loaders
        # localizan la imagen por `image_path` de la anotación, así que el nombre
        # debe coincidir; el reescalado a MAX_SIDE basta para quedar < 20 MB.
        image.save(img_dir / name, format="PNG", optimize=True)
        kept_ann.append(_trim(page, scale))
    (OUT / "OmniDocBench.json").write_text(
        json.dumps(kept_ann, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(kept_ann)} paginas, {total/1e6:.2f} MB -> {OUT}")


if __name__ == "__main__":
    main()
