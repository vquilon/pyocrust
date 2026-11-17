"""Construye la fixture versionada de **esquematicos** (feature OCR de diagramas).

Muestrea `N_PAGES` filas de `bshada/open-schematics` (317 GB) por el endpoint
`/rows` del *datasets-server* de HF con la revision **pinnada** — nunca se baja
el dataset entero — y escribe `benchmarks/fixtures/schematics_mini/`:

* `images/<id>.png` — el PNG renderizado (`schematic_image`) a resolucion
  original: es la pagina que ve el OCR (referencia real del caso del companero);
* `manifest.json` — `{dataset, revision, license, note, pages:[...]}`, y por
  pagina `id`/`image`/`name`/`text` (GT de texto) + `strings` (trazabilidad) +
  `sha256` del PNG.

GT de texto: el texto **visible** del esquematico, extraido del fuente
`.kicad_sch` (S-expr de KiCad 8) — referencia y valor no ocultos de cada
simbolo, propiedades no ocultas de cada hoja, items `(text ...)`, etiquetas
(`label`/`global_label`/`hierarchical_label`) y el `title_block`. Los **pines**
(nombres/numeros) no se incluyen: viven en la definicion de libreria con su
propia visibilidad (a menudo ocultos) y no aportan al caso de reconocimiento de
rotulos. Ver `fixtures/README.md`.

Uso puntual (una vez, con red): `python benchmarks/build_schematics_fixture.py`.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent
OUT = BENCH / "fixtures" / "schematics_mini"

DATASET = "bshada/open-schematics"
# Revision **inmutable** (commit HF): fija que revision se muestrea para que dos
# builds partan de los mismos bytes. El fixture commiteado es la fuente de verdad.
REVISION = "5c74c3648d22e73426bbeb4691397d9cc8053e34"
N_PAGES = 10
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    f"?dataset={DATASET}&config=default&split=train&offset=0&length={N_PAGES}"
)
USER_AGENT = "pyocrust-fixture"


# ---------------------------------------------------------------------------
# Parser S-expr minimo (KiCad `.kicad_sch`) + extraccion del texto visible
# ---------------------------------------------------------------------------


def parse_sexpr(text: str):
    """S-expr -> arbol de listas; hojas = str (comillas ya resueltas)."""
    i, n = 0, len(text)

    def parse():
        nonlocal i
        while i < n and text[i] in " \t\r\n":
            i += 1
        if text[i] == "(":
            i += 1
            out = []
            while True:
                while i < n and text[i] in " \t\r\n":
                    i += 1
                if text[i] == ")":
                    i += 1
                    return out
                out.append(parse())
        if text[i] == '"':
            i += 1
            buf = []
            while True:
                c = text[i]
                if c == "\\":
                    k = text[i + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}.get(k, k))
                    i += 2
                elif c == '"':
                    i += 1
                    return "".join(buf)
                else:
                    buf.append(c)
                    i += 1
        j = i
        while j < n and text[j] not in ' \t\r\n()"':
            j += 1
        tok = text[i:j]
        i = j
        return tok

    return parse()


def _kids(node, tag: str) -> list:
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def _one(node, tag: str):
    found = _kids(node, tag)
    return found[0] if found else None


def _pos(at) -> tuple[float, float] | None:
    if isinstance(at, list) and len(at) >= 3:
        try:
            return float(at[1]), float(at[2])
        except (TypeError, ValueError):
            return None
    return None


def _hidden(effects) -> bool:
    """`hide` suelto (KiCad 7) o `(hide yes)` (KiCad 8) marcan el texto como oculto."""
    if not isinstance(effects, list):
        return False
    for c in effects:
        if c == "hide":
            return True
        if isinstance(c, list) and c and c[0] == "hide" and (
            len(c) < 2 or str(c[1]).lower() in ("yes", "true")
        ):
            return True
    return False


def _render(value: str) -> str:
    """Texto **renderizado** de una cadena de KiCad.

    KiCad marca overbar/subindice/superindice con `~{x}`/`_{x}`/`^{x}` y la barra
    con `{slash}`; en la pagina se dibuja solo `x` (o `/`). El GT de OCR es lo
    que se ve, no el marcado. Un valor `~` (o vacio) no se dibuja: se descarta.
    """
    value = re.sub(r"[~^_]\{([^{}]*)\}", r"\1", value)
    value = value.replace("{slash}", "/")
    return value.strip()


def extract_visible_text(sch: str) -> list[str]:
    """Texto visible del esquematico, en orden de lectura aproximado (y, x).

    Recorre el cuerpo del esquematico (no `lib_symbols`, cuyas propiedades son
    plantillas que no se renderizan) y recoge lo que KiCad dibuja.
    """
    root = parse_sexpr(sch)
    items: list[tuple[float, float, str]] = []

    def add(node_at, value) -> None:
        rendered = _render(value) if isinstance(value, str) else ""
        if rendered and rendered != "~":
            pos = _pos(node_at) or (1e9, 0.0)
            items.append((pos[0], pos[1], rendered))

    tb = _one(root, "title_block")
    if tb:
        for tag in ("title", "date", "rev", "company"):
            field = _one(tb, tag)
            if isinstance(field, list) and len(field) > 1:
                add(None, field[1])
        for comment in _kids(tb, "comment"):
            if len(comment) > 2:
                add(None, comment[2])

    # Simbolos e hojas (propiedades visibles: Reference/Value/Sheetname/...).
    for node in _kids(root, "symbol") + _kids(root, "sheet"):
        if node and node[0] == "symbol" and _one(node, "lib_id") is None:
            continue  # definicion de libreria suelta: no se renderiza aqui
        for prop in _kids(node, "property"):
            if len(prop) > 2 and not _hidden(_one(prop, "effects")):
                add(_one(prop, "at"), prop[2])

    for text_node in _kids(root, "text"):
        if len(text_node) > 1 and not _hidden(_one(text_node, "effects")):
            add(_one(text_node, "at"), text_node[1])

    for tag in ("label", "global_label", "hierarchical_label"):
        for label in _kids(root, tag):
            if len(label) > 1:
                add(_one(label, "at"), label[1])

    items.sort(key=lambda it: (it[0], it[1]))
    return [value for _, _, value in items]


def _slug(name: str) -> str:
    """`owner/repo` -> `owner__repo` (id legible y estable); fallback estable."""
    return name.replace("/", "__").replace("\\", "__").strip() or "page"


# ---------------------------------------------------------------------------
# Muestreo + escritura de la fixture
# ---------------------------------------------------------------------------


def _fetch_rows() -> list[dict]:
    req = urllib.request.Request(ROWS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["rows"]


def _fetch_image(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def main() -> None:
    rows = _fetch_rows()
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    pages = []
    for index, row in enumerate(rows):
        data = row["row"]
        name = str(data.get("name") or f"row-{index}")
        image_id = _slug(name)
        if any(p["id"] == image_id for p in pages):  # colision de nombre: desambigua
            image_id = f"{image_id}-{index}"
        png = _fetch_image(data["schematic_image"]["src"])
        image_name = f"{image_id}.png"
        (OUT / "images" / image_name).write_bytes(png)
        strings = extract_visible_text(data["schematic"])
        pages.append({
            "id": image_id,
            "image": image_name,
            "name": name,
            "source_row": index,
            "text": " ".join(strings),
            "strings": strings,
            "sha256": hashlib.sha256(png).hexdigest(),
        })
    manifest = {
        "dataset": DATASET,
        "revision": REVISION,
        "license": "CC-BY-4.0",
        "note": (
            "Muestra offline de esquematicos (PNG renderizado + texto visible del "
            ".kicad_sch). GT = texto visible sin pines; ver benchmarks/fixtures/README.md."
        ),
        "pages": pages,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(pages)} paginas, {total / 1e6:.2f} MB -> {OUT}")


def _self_check() -> None:
    sch = (
        '(kicad_sch (version 20231120) (paper "A4")\n'
        ' (title_block (title "Board") (company "ACME") (comment 1 "rev B"))\n'
        ' (lib_symbols (symbol "Device:R" (property "Reference" "R" (at 0 0 0))))\n'
        ' (symbol (lib_id "Device:R") (at 10 20 0)\n'
        '  (property "Reference" "R1" (at 10 18 0) (effects (font (size 1.27 1.27))))\n'
        '  (property "Value" "10k" (at 10 22 0) (effects (font (size 1.27 1.27))))\n'
        '  (property "Footprint" "" (at 0 0 0) (effects (hide yes))))\n'
        ' (text "Power supply" (at 5 5 0) (effects (font (size 1.27 1.27))))\n'
        ' (text "~{RESET} Vcc{slash}2" (at 6 6 0) (effects (font (size 1.27 1.27))))\n'
        ' (global_label "VCC" (at 1 2 0))\n'
        ' (sheet (at 30 30 0) (property "Sheetname" "Regs" (at 30 29 0))\n'
        '  (property "Sheetfile" "regs.kicad_sch" (at 30 40 0) (effects (hide yes)))))\n'
    )
    got = extract_visible_text(sch)
    # Orden por (y, x): texto de hoja, textos, R1/10k, etiquetas, y el title_block al final.
    assert "R1" in got and "10k" in got, got
    assert "Footprint" not in got, got                    # oculto: fuera
    assert "Sheetfile" not in got, got                    # oculto: fuera
    assert "R" not in got, got                            # plantilla de libreria: fuera
    assert {"Power supply", "VCC", "Regs", "Board", "ACME", "rev B"} <= set(got), got
    # Marcado de KiCad -> texto renderizado (lo que dibuja la pagina).
    assert "RESET Vcc/2" in got and not any("~{" in g or "{slash}" in g for g in got), got
    assert got.index("Power supply") < got.index("Board"), got  # title_block al final
    print("build_schematics_fixture self-check OK")


if __name__ == "__main__":
    import sys

    if "--self-check" in sys.argv:
        _self_check()
    else:
        main()
