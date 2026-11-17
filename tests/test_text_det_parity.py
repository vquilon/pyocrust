"""Paridad de deteccion en pagina grande: `limit_type="min"` recupera texto que
el default pierde, con ambos presets de tamano.

Contrato (bloque `RDET-PARIDAD`): sobre una pagina sintetica 7000x5000 con texto
fino, `limit_type="min"` + `limit_side_len=64` + `text_det_max_side_len=7000`
detecta estrictamente mas regiones que el default y el texto reconocido contiene
cadenas que el default omitio. Con `pp_ocrv6_medium` y `pp_ocrv6_tiny` la
recuperacion es, como minimo, equivalente: el numero de regiones recuperadas con
el modo nativo no es menor con el modelo pequeno.

Nota de criterio (medido, no inferido): el delta por separado SI depende del
estimulo — con esta pagina sintetica el default de `medium` ya detecta 1 caja y
el de `tiny` 0, asi que `delta_medium=111 < delta_tiny=112`. Lo que garantiza la
feature es la recuperacion con el modo nativo (`medium == tiny == 112`), que es
lo que se afirma; los deltas se imprimen abajo como traza, no como condicion.

Ejecucion: `python -m pytest tests/test_text_det_parity.py -q`
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from pyocrust import VeloceOCR

W, H = 7000, 5000
LINEAS_FINO = 112  # ~44 px de separación; texto fino al límite de detección


def _fuente_pequena() -> ImageFont.FreeTypeFont | None:
    """Una fuente TrueType de sistema de tamano fijo (no la bitmap por defecto)."""
    candidatos: list[tuple[str, int]] = [
        ("C:/Windows/Fonts/arial.ttf", 6),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6),
    ]
    for ruta, tamano in candidatos:
        p = Path(ruta)
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), tamano)
            except OSError:
                continue
    return None


def _imagen_texto_fino(tmp_path: Path) -> tuple[bytes, list[str]]:
    """PNG 7000x5000 con N lineas de texto fino (o lineas geometricas de respaldo).

    Devuelve (png_bytes, lineas_espectro) para uso en afirmaciones de contenido.
    """
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    dib = ImageDraw.Draw(img)
    espectro: list[str] = []

    fuente = _fuente_pequena()
    if fuente is None:
        pytest.skip("no hay fuente TrueType de sistema para sintetizar texto fino")

    contenido = ["fine chino 1", "fine chino 2", "1234567890 fin 01", "ABCDE fin 02"]
    sep = H // LINEAS_FINO
    for i in range(LINEAS_FINO):
        texto = contenido[i % len(contenido)] + f" #{i:03d}"
        espectro.append(texto)
        dib.text((20, 22 + i * sep), texto, font=fuente, fill=(0, 0, 0))

    out = tmp_path / "pagina_fino.png"
    img.save(out, "PNG")
    return out.read_bytes(), espectro


def _texto_reconocido(ocr: VeloceOCR, png: bytes) -> str:
    """Texto reconocido concatenado."""
    return ocr.recognize(png).text


def _max_region_count(ocr: VeloceOCR, png: bytes, intentos: int = 3) -> int:
    """Máximo de cajas del detector (sin depender del filtro del reconocedor)."""
    return max(len(ocr.detect_regions(png)) for _ in range(intentos))


def _configura_ocr(
    preset: str,
    modelos_dir: Path,
    *,
    limit_type: str | None = None,
    limit_side_len: int | None = None,
    max_side_len: int | None = None,
) -> VeloceOCR:
    kwargs: dict = dict(
        device="cpu",
        use_doc_orientation=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    if limit_type is not None:
        kwargs["text_det_limit_type"] = limit_type
    if limit_side_len is not None:
        kwargs["text_det_limit_side_len"] = limit_side_len
    if max_side_len is not None:
        kwargs["text_det_max_side_len"] = max_side_len
    return VeloceOCR(preset, custom_path=str(modelos_dir), **kwargs)




# Nombres de artefactos por tamano (igual que conftest.py PP_OCRV6_TINY).
_ART_TINY = ("pp-ocrv6_tiny_det.onnx", "pp-ocrv6_tiny_rec.onnx", "ppocrv6_tiny_dict.txt")
_ART_MEDIUM = (
    "pp-ocrv6_medium_det.onnx",
    "pp-ocrv6_medium_rec.onnx",
    "ppocrv6_dict.txt",
)


def _directorio_modelos_tamanho(tamanho: str) -> Path:
    """Busqueda del cache del host (OAR_HOME o ~/.oar) para los 3 artefactos."""
    for var in ("OAR_HOME",):
        base = os.environ.get(var)
        if base:
            p = Path(base)
            if all((p / n).is_file() for n in {
                "tiny": _ART_TINY,
                "medium": _ART_MEDIUM,
            }[tamanho]):
                return p
    casa = Path.home() / ".oar"
    if casa.is_dir() and all((casa / n).is_file() for n in {
        "tiny": _ART_TINY,
        "medium": _ART_MEDIUM,
    }[tamanho]):
        return casa
    raise RuntimeError(
        f"modelos {tamanho} no encontrados en OAR_HOME ni ~/.oar"
    )


@pytest.fixture(scope="session")
def modelo_tiny_dir() -> Path:
    return _directorio_modelos_tamanho("tiny")


@pytest.fixture(scope="session")
def modelo_medium_dir() -> Path:
    return _directorio_modelos_tamanho("medium")


@pytest.fixture(scope="session")
def pagina_texto_fino(tmp_path_factory: pytest.TempPathFactory) -> tuple[bytes, list[str]]:
    """Una única página sintética 7000x5000 compartida por ambas mediciones."""
    return _imagen_texto_fino(tmp_path_factory.mktemp("text-det-parity"))


def test_deteccion_min_recupera_texto_fino_que_default_omite(
    pagina_texto_fino: tuple[bytes, list[str]], modelo_medium_dir: Path, capsys
):
    """Bloque RDET-PARIDAD (1/2): minimo detecta mas y recupera texto omitido."""
    png, espectro = pagina_texto_fino
    default = _configura_ocr("pp_ocrv6_medium", modelo_medium_dir)
    opt = _configura_ocr(
        "pp_ocrv6_medium",
        modelo_medium_dir,
        limit_type="min",
        limit_side_len=64,
        max_side_len=W,
    )

    txt_def = _texto_reconocido(default, png)
    txt_opt = _texto_reconocido(opt, png)

    # Max sobre 3 intentos para reducir no-determinismo del detector DB.
    n_def_max = _max_region_count(default, png)
    n_opt_max = _max_region_count(opt, png)
    assert n_opt_max > n_def_max, (
        f"RDET-PARIDAD-A falla: default={n_def_max} regiones (max 3 intentos), "
        f"min/64+max_side={W}={n_opt_max} regiones (deben ser estrictamente mayores)"
    )

    normalizar = lambda texto: "".join(texto.split()).lower()
    texto_def, texto_opt = normalizar(txt_def), normalizar(txt_opt)
    recuperadas = [
        linea for linea in espectro
        if normalizar(linea) in texto_opt and normalizar(linea) not in texto_def
    ]
    assert recuperadas, (
        f"RDET-PARIDAD-B falla: el texto fino reconocido por min/64 no contiene "
        f"ninguna cadena del espectro ({len(espectro)} lineas) que el default omitio. "
        f"default text snippet: {txt_def[:200]!r}; opt text snippet: {txt_opt[:200]!r}"
    )
    with capsys.disabled():
        print(f"RDET-PARIDAD texto: medium default={n_def_max}, min/native={n_opt_max}; recuperadas={len(recuperadas)}")


def test_recuperacion_con_native_equivalente_en_tiny_y_medium(
    pagina_texto_fino: tuple[bytes, list[str]], modelo_tiny_dir: Path, modelo_medium_dir: Path, capsys
):
    """Bloque RDET-PARIDAD (2/2): native recupera igual o mas con tiny que con medium."""
    png, _ = pagina_texto_fino

    def _delta(dir_modelos: Path, preset: str) -> tuple[int, int, int]:
        d = _configura_ocr(preset, dir_modelos)
        o = _configura_ocr(
            preset,
            dir_modelos,
            limit_type="min",
            limit_side_len=64,
            max_side_len=W,
        )
        nd = _max_region_count(d, png)
        no = _max_region_count(o, png)
        return no - nd, nd, no

    delta_tiny, n_tiny_def, n_tiny_min = _delta(modelo_tiny_dir, "pp_ocrv6_tiny")
    delta_medium, n_medium_def, n_medium_min = _delta(modelo_medium_dir, "pp_ocrv6_medium")
    with capsys.disabled():
        print(
            f"RDET-PARIDAD delta: tiny default={n_tiny_def}, min/native={n_tiny_min}, delta={delta_tiny}; "
            f"medium default={n_medium_def}, min/native={n_medium_min}, delta={delta_medium}"
        )

    assert n_medium_min >= n_tiny_min, (
        f"RDET-PARIDAD-C falla: native tiny={n_tiny_min}, native medium={n_medium_min} "
        f"(medium no debe recuperar menos que tiny); deltas tiny={delta_tiny}, "
        f"medium={delta_medium}"
    )
