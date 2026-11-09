"""Contrato de `pyocrust.enable_cuda()` (helper del search path del runtime CUDA)."""
from __future__ import annotations

import pyocrust


def test_enable_cuda_devuelve_providers_string_e_es_idempotente():
    primero = pyocrust.enable_cuda()
    assert isinstance(primero, list), type(primero)
    assert all(isinstance(p, str) for p in primero), primero
    # Idempotente: repetir no cambia el resultado (y no revienta por repetir el EP).
    assert pyocrust.enable_cuda() == primero
    # Lo que devuelve es lo que registra de verdad el binario instalado.
    assert set(primero) == set(pyocrust.available_providers())
