"""El resumen global no publica dos veces el MISMO peso por otra via (sin duplicados).

La senal es `ALTERNATIVE_PROVENANCE` (`mismo_peso_otra_via`), no el nombre: solo
es duplicado lo que el propio registro declara como el mismo checkpoint por otro
runtime. Un motor independiente con nombre parecido se conserva.
"""
from __future__ import annotations

import common.runner as runner  # noqa: F401  (registro cargado)
from features.summary import _dedupe_same_model, _model_key


def _row(backend: str, model: str, variant: str, quality: float, feature: str = "orientation") -> dict:
    col = {"orientation": "ori_acc", "full_page": "markdown_f1", "text": "word_f1"}[feature]
    return {"backend": backend, "model_name": model, "model_variant": variant,
            "status": "ok", "device_requested": "cpu", col: str(quality)}


def test_colapsa_el_mismo_peso_por_otra_via_y_gana_pyocrust():
    rows = {
        ("orientation", "cpu", "pyocrust_orientation"): [
            _row("pyocrust_orientation", "pp-lcnet_x1_0_doc_ori", "6.8M", 1.0)],
        ("orientation", "cpu", "lcnet_doc_ori"): [
            _row("lcnet_doc_ori", "pp-lcnet_x1_0_doc_ori", "onnxruntime", 1.0)],
    }
    assert set(_dedupe_same_model(rows)) == {("orientation", "cpu", "pyocrust_orientation")}


def test_no_toca_un_motor_independiente_con_nombre_parecido():
    # pp_structurev3 (propio) vs PP-StructureV3 (PaddleOCR externo): cifras
    # distintas -> otro modelo, no un duplicado.
    rows = {
        ("full_page", "cpu", "pyocrust_structure"): [
            _row("pyocrust_structure", "pp_structurev3", "default", 0.530, "full_page")],
        ("full_page", "cpu", "pp_structurev3_api"): [
            _row("pp_structurev3_api", "PP-StructureV3", "paddleocr", 0.427, "full_page")],
    }
    assert len(_dedupe_same_model(rows)) == 2


def test_dos_tamanos_del_mismo_motor_no_son_duplicado():
    # pp_ocrv6 (tiny, pyocrust) vs PP-OCRv6 (medium, PaddleOCR): checkpoints distintos.
    rows = {
        ("text", "cpu", "pyocrust"): [_row("pyocrust", "pp_ocrv6", "tiny", 0.70, "text")],
        ("text", "cpu", "paddleocr"): [_row("paddleocr", "PP-OCRv6", "medium", 0.80, "text")],
    }
    assert len(_dedupe_same_model(rows)) == 2


def test_model_key_normaliza_separadores_y_caja():
    assert _model_key("PP-StructureV3", "pp_structurev3_api") == \
        _model_key("pp_structurev3", "pyocrust_structure")
