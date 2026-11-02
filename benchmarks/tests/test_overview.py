"""Tests de las gráficas de resumen: por feature (`REPORT.png`) y global.

Sin datasets, modelos ni red: la gráfica por feature se construye con un reporte
sintético y la global con un catálogo de dos entradas. Se verifica que:

* la matriz de cobertura **no inventa ceros** (celda no cubierta = vacía);
* las capacidades del eje **existen en el catálogo real** de `pyocrust`;
* `FEATURES_OVERVIEW.md` enumera la cobertura y la **autogestión**;
* ambas gráficas se escriben (PNG+SVG) y **ninguna etiqueta se solapa**.
"""

from __future__ import annotations

import pytest

from features import overview


def _texts(fig):
    items = []
    for ax in fig.axes:
        items += list(ax.get_xticklabels()) + list(ax.get_yticklabels())
        items += [ax.title, ax.xaxis.label, ax.yaxis.label]
        if ax.get_legend():
            items += list(ax.get_legend().get_texts())
        items += list(ax.texts)
    items += list(fig.texts)
    for legend in fig.legends:
        items += list(legend.get_texts())
    return [t for t in items if t.get_text().strip()]


def _max_text_overlap(fig):
    """Área de solape máxima (px²) entre textos: 0 = ninguna etiqueta se pisa."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in _texts(fig)]
    worst = 0.0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
            iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
            worst = max(worst, ix * iy)
    return worst


def _statuses():
    return {f: {"estado": "medido" if f in ("text", "formula") else "esqueleto",
                "references": f in ("text", "formula")} for f in overview.FEATURE_ORDER}


def test_matriz_de_cobertura_no_inventa_ceros():
    matrix = overview.build_matrix(_statuses(), overview.CAPABILITY_ORDER)
    assert len(matrix) == len(overview.FEATURE_ORDER)
    # (feature, capacidad) no cubierto -> None (celda vacía), nunca un 0 espurio.
    assert all(v is None or v in (1.0, 2.0) for row in matrix for v in row)
    covered = [sum(v is not None for v in row) for row in matrix]
    # `full_page` es la fila «todo en uno»: cubre más capacidades que ninguna otra.
    assert covered[overview.FEATURE_ORDER.index("full_page")] == max(covered)


def test_capacidades_del_eje_existen_en_el_catalogo_real():
    catalog = overview.load_catalog()
    if not catalog:  # entorno sin pyocrust: no se puede verificar, se omite
        pytest.skip("pyocrust.model_catalog() no disponible")
    real = set(overview.catalog_tasks(catalog))
    for feature, caps in overview.FEATURE_CAPABILITIES.items():
        assert set(caps) <= real, f"{feature}: capacidad inventada -> {set(caps) - real}"


def test_overview_md_enumera_cobertura_y_autogestion():
    catalog = {"pp-ocrv6_tiny_det.onnx": {"task": "text_detection", "size_bytes": 1780590},
               "det.onnx": {"task": "indra", "size_bytes": None}}
    md = overview.render_markdown(_statuses(), catalog, list(overview.CAPABILITY_ORDER))
    for needle in ("Autogestión", "ensure_models", "feature × capacidad", "medido",
                   "esqueleto", "referencia"):
        assert needle in md, f"falta {needle!r} en FEATURES_OVERVIEW.md"
    for feature in overview.FEATURE_ORDER:
        assert f"**{feature}**" in md


def test_feature_report_plot_escribe_sin_solape(tmp_path, monkeypatch):
    import matplotlib.pyplot as plt

    from features import report as reporter

    plt.close("all")
    monkeypatch.setattr(plt, "close", lambda *a, **k: None)
    report = {
        "pyocrust (tiny)": {"n": 5, "word_f1": 0.734, "mean_ms": 1129.0},
        "rapidocr (default)": {"n": 5, "word_f1": 0.660, "mean_ms": 8659.0},
        "easyocr (default)": {"n": 5, "word_f1": 0.384, "mean_ms": 8648.0},
    }
    summary = {"origen": "medido", "dataset": "funsd", "timestamp": "test"}
    reporter.plot_feature("text", report, summary, tmp_path / "REPORT")
    assert (tmp_path / "REPORT.png").is_file() and (tmp_path / "REPORT.svg").is_file()
    assert _max_text_overlap(plt.figure(plt.get_fignums()[-1])) <= 1.0


def test_overview_plot_escribe_sin_solape(tmp_path, monkeypatch):
    import matplotlib.pyplot as plt

    plt.close("all")
    monkeypatch.setattr(plt, "close", lambda *a, **k: None)
    catalog = {"a.onnx": {"task": "text_detection", "size_bytes": 1780590},
               "b.onnx": {"task": "formula_recognition", "size_bytes": None}}
    overview.plot_overview(_statuses(), catalog, list(overview.CAPABILITY_ORDER),
                           tmp_path / "FEATURES_OVERVIEW")
    assert (tmp_path / "FEATURES_OVERVIEW.png").is_file()
    assert (tmp_path / "FEATURES_OVERVIEW.svg").is_file()
    assert _max_text_overlap(plt.figure(plt.get_fignums()[-1])) <= 1.0
