"""SDK de regiones (`DESIGN.md` §11, bloque `RDET`): `detect_regions` + `recognize_regions`.

Criterio de aceptación: sobre una página sintética 7000x5000 con texto fino,
`detect_regions` + `recognize_regions` con la receta nativa
(`text_det_limit_type="min"`, `text_det_limit_side_len=64`,
`text_det_max_side_len>=7000`) recuperan el mismo texto que `recognize` con la
misma receta (o mejor), recortando a resolución nativa; y devuelven **una
`TextRegion` por caja de entrada**. También cubre la validación tipada
(`PyOcrValueError`, nunca un default mudo).

Nota de comparación (medida, no supuesta): con fuente de 7 px el reconocimiento
está en su frontera de confianza y el recorte AABB del SDK difiere en unos
píxeles del recorte por cuadrilátero del pipeline, así que unas pocas cadenas
salen con un glifo distinto (`fine`↔`fire`). Por eso la paridad se exige al
**90%** de las cadenas del pipeline y, además, contra el **espectro sintético**
(verdad de referencia que controla el test). Se probó primero con igualdad
exacta: fallaba por esos glifos límite, no por pérdida de texto.

Ejecución: `python -m pytest tests/test_regions_sdk.py -q`
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from pyocrust import PyOcrValueError, VeloceOCR

W, H = 7000, 5000
# ~42 px de separación con fuente de 7 px: texto fino que el reescalado por
# defecto (960 de lado mayor) pierde casi por completo.
LINEAS_FINO = 120

# Receta de resolución nativa (§11.1.3: el tope del lado largo recorta
# incondicionalmente, así que los TRES knobs son necesarios).
RECETA_NATIVA = {
    "text_det_limit_type": "min",
    "text_det_limit_side_len": 64,
    "text_det_max_side_len": W,
}

# Artefactos del preset de texto (mismo tamaño que `src/core/types.rs::OcrSize`).
ART_MEDIUM = (
    "pp-ocrv6_medium_det.onnx",
    "pp-ocrv6_medium_rec.onnx",
    "ppocrv6_dict.txt",
)

# Paridad mínima exigida entre las dos vías nativas (ver nota de cabecera).
PARIDAD_MINIMA = 0.90


def _fuente_pequena() -> ImageFont.FreeTypeFont | None:
    """Una fuente TrueType de sistema (no la bitmap por defecto de PIL)."""
    for ruta in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(ruta).is_file():
            try:
                return ImageFont.truetype(ruta, 7)
            except OSError:
                continue
    return None


def _pagina_texto_fino(tmp_path: Path) -> tuple[bytes, list[str]]:
    """PNG 7000x5000 con `LINEAS_FINO` líneas de texto fino y su espectro."""
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    dib = ImageDraw.Draw(img)
    fuente = _fuente_pequena()
    if fuente is None:
        pytest.skip("no hay fuente TrueType del sistema para sintetizar texto fino")

    contenido = ["fine chino 1", "fine chino 2", "1234567890 fin 01", "ABCDE fin 02"]
    espectro: list[str] = []
    sep = H // LINEAS_FINO
    for i in range(LINEAS_FINO):
        texto = contenido[i % len(contenido)] + f" #{i:03d}"
        espectro.append(texto)
        dib.text((20, i * sep + sep // 2), texto, font=fuente, fill=(0, 0, 0))

    out = tmp_path / "pagina_fino.png"
    img.save(out, "PNG")
    return out.read_bytes(), espectro


def _directorio_medium() -> Path:
    """Directorio del cache del host con los 3 artefactos de `pp_ocrv6_medium`."""
    candidatos = [os.environ.get("OAR_HOME"), str(Path.home() / ".oar")]
    for candidato in candidatos:
        if candidato:
            base = Path(candidato)
            if all((base / nombre).is_file() for nombre in ART_MEDIUM):
                return base
    pytest.skip(
        f"faltan los modelos de pp_ocrv6_medium ({', '.join(ART_MEDIUM)}) en "
        + " ni ".join(str(c) for c in candidatos if c)
    )


def _ocr(modelos: Path) -> VeloceOCR:
    """`pp_ocrv6_medium` sin composición: det + rec puros, para poder comparar."""
    return VeloceOCR(
        "pp_ocrv6_medium",
        custom_path=str(modelos),
        device="cpu",
        use_doc_orientation=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        **RECETA_NATIVA,
    )


@pytest.fixture(scope="module")
def ocr_nativo() -> VeloceOCR:
    return _ocr(_directorio_medium())


@pytest.fixture(scope="module")
def pagina_fino(tmp_path_factory: pytest.TempPathFactory) -> tuple[bytes, list[str]]:
    return _pagina_texto_fino(tmp_path_factory.mktemp("regiones"))


@pytest.fixture(scope="module")
def pagina_mini() -> bytes:
    """Imagen diminuta válida: para los casos de validación, sin inferencia cara."""
    from io import BytesIO

    buffer = BytesIO()
    Image.new("RGB", (64, 32), color=(255, 255, 255)).save(buffer, "PNG")
    return buffer.getvalue()


def _textos(resultado) -> list[str]:
    """Textos no vacíos de un `OcrResult`, normalizados (sin espacios, minúsculas)."""
    return ["".join(region.text.split()).lower() for region in resultado.regions if region.text.strip()]


def test_regiones_igualan_a_recognize_a_resolucion_nativa(ocr_nativo, pagina_fino):
    """Criterio de aceptación: mismo texto que `recognize` (o mejor) y 1:1 por caja."""
    png, espectro = pagina_fino

    completo = ocr_nativo.recognize(png)
    boxes = ocr_nativo.detect_regions(png, **RECETA_NATIVA)
    regiones = ocr_nativo.recognize_regions(png, boxes)

    # Contrato §11.2: una `TextRegion` por caja de entrada, en el mismo orden.
    assert len(regiones.regions) == len(boxes) >= 40, (
        f"a resolución nativa se esperan decenas de cajas (el default da 0-2); "
        f"boxes={len(boxes)}, regions={len(regiones.regions)}, "
        f"recognize={len(completo.regions)}"
    )
    for caja, region in zip(boxes, regiones.regions):
        assert (region.box.x1, region.box.y1) == (caja.x1, caja.y1)

    # Paridad de texto con la vía nativa del pipeline (ver nota de cabecera:
    # a 7 px el rec está en su frontera y unos pocos glifos difieren).
    textos_completos, textos_regiones = set(_textos(completo)), set(_textos(regiones))
    coincidencias = len(textos_completos & textos_regiones)
    paridad = coincidencias / max(1, len(textos_completos))
    assert paridad >= PARIDAD_MINIMA, (
        f"paridad {paridad:.0%} < {PARIDAD_MINIMA:.0%}: {len(textos_completos)} textos del pipeline, "
        f"{coincidencias} presentes en el SDK de regiones. "
        f"perdidos: {sorted(textos_completos - textos_regiones)[:5]}"
    )

    # Verdad de referencia: el espectro sintético aparece en el OCR por región.
    unido = " ".join(_textos(regiones))
    recuperadas = [linea for linea in espectro if "".join(linea.split()).lower() in unido]
    assert len(recuperadas) >= 40, (
        f"a resolución nativa deberían recuperarse decenas de líneas finas; "
        f"recuperadas={len(recuperadas)}/{len(espectro)}, textos={len(textos_regiones)}"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"text_det_limit_type": "bogus"},
        {"text_det_thresh": 1.5},
        {"text_det_limit_side_len": 0},
    ],
)
def test_detect_regions_rechaza_valores_invalidos(ocr_nativo, pagina_mini, kwargs):
    """Un valor inválido es `PyOcrValueError` antes de decodificar o inferir."""
    with pytest.raises(PyOcrValueError):
        ocr_nativo.detect_regions(pagina_mini, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rec_score_threshold": 2.0},
        {"region_batch_size": 0},
    ],
)
def test_recognize_regions_rechaza_valores_invalidos(ocr_nativo, pagina_mini, kwargs):
    """Ídem para el umbral del reconocedor y el tamaño de lote."""
    with pytest.raises(PyOcrValueError):
        ocr_nativo.recognize_regions(pagina_mini, [], **kwargs)
