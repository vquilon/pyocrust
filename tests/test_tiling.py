"""Troceado con solapamiento (`DESIGN.md` §3.4, ADR-009).

`FullPageTiling` es una utilidad **opt-in** del core: mosaicos de 512x512 con
64px de solapamiento por defecto. La fachada `pyocrust/__init__.py` no la
re-exporta (el pipeline general usa `ScaleDown`), así que los tests la importan
del módulo nativo.

La función expuesta recibe una imagen codificada y devuelve la geometría de cada
mosaico como `(x, y, ancho, alto)` en coordenadas de la imagen original.

Ejecución: `python -m pytest tests/test_tiling.py -q`
"""

from __future__ import annotations

import pytest

from pyocrust import PyOcrRuntimeError, PyOcrValueError
from pyocrust._pyocrust_core import full_page_tiling

MOSAICO = 512
SOLAPE = 64
# Avance = 512 - 64 = 448; el último mosaico se realinea con el borde.
ESPERADOS_1200x900 = [
    (0, 0, 512, 512),
    (448, 0, 512, 512),
    (688, 0, 512, 512),
    (0, 388, 512, 512),
    (448, 388, 512, 512),
    (688, 388, 512, 512),
]


def test_1200x900_con_512_y_64_produce_exactamente_los_mosaicos_esperados(png_factory):
    mosaicos = full_page_tiling(png_factory(1200, 900), MOSAICO, SOLAPE)

    assert mosaicos == ESPERADOS_1200x900


def test_los_valores_por_defecto_son_mosaico_512_y_solapamiento_64(png_factory):
    imagen = png_factory(1200, 900)

    assert full_page_tiling(imagen) == ESPERADOS_1200x900


def test_el_solapamiento_nunca_queda_por_debajo_de_lo_pedido(png_factory):
    mosaicos = full_page_tiling(png_factory(1200, 900), MOSAICO, SOLAPE)

    filas: dict[int, list[int]] = {}
    columnas: dict[int, list[int]] = {}
    for x, y, _ancho, _alto in mosaicos:
        filas.setdefault(y, []).append(x)
        columnas.setdefault(x, []).append(y)

    for offsets in filas.values():
        for izquierda, derecha in zip(sorted(offsets), sorted(offsets)[1:]):
            solape = MOSAICO - (derecha - izquierda)
            assert solape >= SOLAPE, f"solape horizontal de {solape}px entre {izquierda} y {derecha}"

    for offsets in columnas.values():
        for arriba, abajo in zip(sorted(offsets), sorted(offsets)[1:]):
            solape = MOSAICO - (abajo - arriba)
            assert solape >= SOLAPE, f"solape vertical de {solape}px entre {arriba} y {abajo}"


def test_los_mosaicos_cubren_la_imagen_entera_sin_huecos(png_factory):
    mosaicos = full_page_tiling(png_factory(1200, 900), MOSAICO, SOLAPE)

    filas: dict[int, list[tuple[int, int]]] = {}
    columnas: dict[int, list[tuple[int, int]]] = {}
    for x, y, ancho, alto in mosaicos:
        filas.setdefault(y, []).append((x, ancho))
        columnas.setdefault(x, []).append((y, alto))

    for y, tramos in filas.items():
        cursor = 0
        for x, ancho in sorted(tramos):
            assert x <= cursor, f"hueco entre {cursor} y {x} en la fila y={y}"
            cursor = x + ancho
        assert cursor == 1200, f"la fila y={y} no llega al borde derecho"

    for x, tramos in columnas.items():
        cursor = 0
        for y, alto in sorted(tramos):
            assert y <= cursor, f"hueco entre {cursor} y {y} en la columna x={x}"
            cursor = y + alto
        assert cursor == 900, f"la columna x={x} no llega al borde inferior"


def test_ningun_mosaico_supera_el_tamano_de_mosaico(png_factory):
    mosaicos = full_page_tiling(png_factory(1200, 900), MOSAICO, SOLAPE)

    assert mosaicos
    for _x, _y, ancho, alto in mosaicos:
        assert 0 < ancho <= MOSAICO
        assert 0 < alto <= MOSAICO


def test_una_imagen_menor_que_un_mosaico_da_un_unico_mosaico(png_factory):
    assert full_page_tiling(png_factory(300, 200), MOSAICO, SOLAPE) == [(0, 0, 300, 200)]


def test_una_imagen_del_tamano_exacto_de_un_mosaico_da_un_unico_mosaico(png_factory):
    assert full_page_tiling(png_factory(512, 512), MOSAICO, SOLAPE) == [(0, 0, 512, 512)]


@pytest.mark.parametrize("solape", [512, 600, 1024])
def test_un_solapamiento_mayor_o_igual_que_el_mosaico_se_rechaza(png_factory, solape):
    """ADR-009 exige rechazarlo: el avance sería cero y el bucle no terminaría."""
    with pytest.raises(PyOcrValueError) as fallo:
        full_page_tiling(png_factory(1200, 900), MOSAICO, solape)

    assert "overlap" in str(fallo.value)


def test_un_mosaico_de_tamano_cero_se_rechaza(png_factory):
    with pytest.raises(PyOcrValueError) as fallo:
        full_page_tiling(png_factory(1200, 900), 0, 0)

    assert "tile size" in str(fallo.value)


def test_bytes_que_no_son_una_imagen_se_rechazan():
    with pytest.raises(PyOcrRuntimeError):
        full_page_tiling(b"esto no es un png", MOSAICO, SOLAPE)


def test_solapamiento_alto_no_agota_memoria_y_resuelve_en_milisegundos(png_factory):
    """Condición S1.1: overlap=511 con tile_size=512 no materializa búferes innecesarios."""
    import time

    imagen = png_factory(600, 600)
    t0 = time.perf_counter()
    mosaicos = full_page_tiling(imagen, 512, 511)
    duracion = time.perf_counter() - t0

    # 600x600 con tile_size 512 y avance 1 produce 89 offsets por eje = 7921 mosaicos
    assert len(mosaicos) == 7921
    assert duracion < 1.0, f"debe tardar milisegundos, tardó {duracion:.2f}s"
    assert mosaicos[0] == (0, 0, 512, 512)
    assert mosaicos[-1] == (88, 88, 512, 512)
