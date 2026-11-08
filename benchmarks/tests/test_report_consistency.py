"""Regresiones de seleccion CPU/GPU, graficas por motor y coherencia de informes."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from features import quality_vs_time, report, summary

BENCH = Path(__file__).resolve().parent.parent


def _write_run(run_dir: Path, device: str, rows: list[dict]) -> Path:
    """Crea una run con `summary.json` + `<name>.csv` y devuelve el directorio."""
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({
        "device_requested": device,
        "dataset": "fixture_gt",
        "backends": {},
    }), encoding="utf-8")
    fields = sorted({key for row in rows for key in row})
    with (run_dir / f"{run_dir.name}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return run_dir


def _row(backend: str, device: str, provider: str, elapsed_ms: int, quality: float = 0.8) -> dict:
    return {
        "backend": backend,
        "device_requested": device,
        "provider_effective": provider,
        "model_variant": "default",
        "elapsed_ms": elapsed_ms,
        "layout_map": quality,
        "status": "ok",
    }


def test_resumen_yolo_mejor_por_version_cruzando_autores(monkeypatch):
    """El resumen se queda con el mejor de cada versión, sea de quien sea."""
    scores = {
        "hantian_v8n": 0.41, "hantian_v8s": 0.52,
        "hantian_v10n": 0.61, "omoured_v10x": 0.63,
        "armaggheddon_y11n": 0.72, "omoured_v11x": 0.71,
        "hantian_v12n": 0.80, "hantian_v12s": 0.82,
        "armaggheddon_y26n": 0.91, "hantian_y26m": 0.90,
        "yolov10x": 0.99,
    }
    rows = {
        ("layout", "cpu", backend): [{
            "dataset": "omnidocbench_layout", "layout_map": str(score),
        }]
        for backend, score in scores.items()
    }
    monkeypatch.setattr(summary, "_collect_rows", lambda: rows)
    monkeypatch.setattr(summary, "size_matched_yolo_layout_backend", lambda rows=None: None)

    # Un ganador por versión, sin filtrar por autor: v8 -> hantian_v8s (0.52) y no
    # hantian_v8n; v10 -> omoured_v10x (0.63) pese a que hantian tambien tiene v10;
    # v11 y y26 -> armaggheddon; v12 -> hantian_v12s. `yolov10x` no es parte del
    # inventario verificado de 39 (alias legado) y queda fuera.
    expected = {"hantian_v8s", "omoured_v10x", "armaggheddon_y11n",
                "hantian_v12s", "armaggheddon_y26n"}
    assert summary.summary_yolo_layout_backends(rows) == expected
    selected = summary.collect_rows()
    assert {backend for (feature, _device, backend) in selected if feature == "layout"} == expected


def test_el_yolo_de_tamano_similar_a_pyocrust_entra_en_el_resumen(monkeypatch):
    """Aunque repita versión, el YOLO de tamaño parecido a `pyocrust` se añade."""
    rows = {
        ("layout", "cpu", "hantian_v8n"): [
            {"dataset": "omnidocbench_layout", "layout_map": "0.51"}],
        ("layout", "cpu", "hantian_v8x"): [
            {"dataset": "omnidocbench_layout", "layout_map": "0.49"}],
    }
    monkeypatch.setattr(summary, "_collect_rows", lambda: rows)
    monkeypatch.setattr(summary, "size_matched_yolo_layout_backend",
                        lambda rows=None: "hantian_v8x")

    assert summary.summary_yolo_layout_backends(rows) == {"hantian_v8n", "hantian_v8x"}


def test_panel_filtra_por_device():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    quality_vs_time._panel(ax, [
        ("cpu_model", 100.0, 0.7, "cpu"),
        ("gpu_model", 10.0, 0.8, "gpu"),
    ], "layout", "cpu")
    offsets = ax.collections[0].get_offsets()
    assert len(offsets) == 1
    assert tuple(offsets[0]) == (100.0, 0.7)
    assert "device: cpu" in ax.get_title()
    plt.close(fig)


def test_artefactos_quality_vs_time_separados_por_device():
    for device in ("CPU", "GPU"):
        for extension in ("png", "svg"):
            assert (BENCH / "figures" / f"SUMMARY_QUALITY_VS_TIME_{device}.{extension}").is_file()
    assert not (BENCH / "SUMMARY_QUALITY_VS_TIME.png").exists()
    assert not (BENCH / "SUMMARY_QUALITY_VS_TIME.svg").exists()


def test_quality_vs_time_table_muestra_un_yolo_por_version():
    layout = False
    versions: dict[str, set[str]] = {}
    for line in (BENCH / "reports" / "QUALITY_VS_TIME.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            layout = line.startswith("## layout —")
        elif layout and line.startswith("|") and "Device" not in line and not set(line.strip("| ")) <= set(":-| "):
            motor = line.strip("|").split("|")[0].strip().strip("*")
            match = re.search(r"/(?:v|y)(8|10|11|12|26)-?[a-z]", motor)
            if match:
                versions.setdefault(match.group(1), set()).add(motor)

    assert set(versions) == {"8", "10", "11", "12", "26"}
    # uno por versión, más el de tamaño similar a `pyocrust` (hantian/v8-x, 130 MB)
    assert all(1 <= len(models) <= 2 for models in versions.values()), versions
    assert any("v8-x" in motor for motor in versions["8"]), versions["8"]


def test_latest_run_filtra_device_de_referencia(tmp_path):
    results = tmp_path / "results"
    feature = results / "layout"
    cpu = _write_run(feature / "2026-11-06_cpu", "cpu", [
        _row("cpu_engine", "cpu", "cpu", 100),
    ])
    _write_run(feature / "2026-11-07_gpu", "gpu", [
        _row("gpu_engine", "gpu", "cuda", 10),
    ])

    assert report.latest_run("layout", results, device="cpu") == cpu
    assert report.latest_run("layout", results, device="gpu").name == "2026-11-07_gpu"


def test_load_gpu_toma_ultima_run_por_motor(tmp_path, monkeypatch):
    results = tmp_path / "results"
    feature = results / "layout"
    _write_run(feature / "2026-11-06", "gpu", [
        _row("engine_a", "gpu", "cuda", 50, 0.7),
        _row("engine_b", "gpu", "cuda", 40, 0.6),
    ])
    _write_run(feature / "2026-11-07", "gpu", [
        _row("engine_b", "gpu", "cuda", 20, 0.9),
        _row("yolov10x", "gpu", "cuda", 5, 0.99),
        _row("fallback", "gpu", "cpu", 30, 0.5),
    ])
    monkeypatch.setattr(report, "RESULTS_DIR", results)
    monkeypatch.setattr(report, "GPU_RESULTS_DIR", results / "_gpu")

    loaded = report.load_gpu("layout")

    assert loaded is not None
    gpu_report, gpu_summary = loaded
    # Todos los motores medidos entran; solo se descarta el fallback CPU.
    assert set(gpu_report) == {"engine_a (default)", "engine_b (default)", "yolov10x (default)"}
    assert gpu_report["engine_a (default)"]["mean_ms"] == 50
    assert gpu_report["engine_b (default)"]["mean_ms"] == 20
    assert gpu_report["engine_b (default)"]["layout_map"] == 0.9
    assert gpu_report["yolov10x (default)"]["mean_ms"] == 5
    assert gpu_summary["backends"]["engine_b"]["provider_effective"] == "cuda"


def test_load_gpu_lee_la_jerarquia_designada(tmp_path, monkeypatch):
    """`results/_gpu/<feature>/` y la ruta CPU: hay runs GPU escritas sin --output-dir."""
    results = tmp_path / "results"
    _write_run(results / "layout" / "2026-11-06", "gpu", [_row("old_engine", "gpu", "cuda", 50)])
    _write_run(results / "_gpu" / "layout" / "2026-11-07", "gpu", [_row("new_engine", "gpu", "cuda", 10)])
    monkeypatch.setattr(report, "RESULTS_DIR", results)
    monkeypatch.setattr(report, "GPU_RESULTS_DIR", results / "_gpu")

    gpu_report, _ = report.load_gpu("layout")

    assert set(gpu_report) == {"old_engine (default)", "new_engine (default)"}


def test_quality_vs_time_incluye_gpu_real(tmp_path, monkeypatch):
    feature_dir = tmp_path / "reports" / "layout"
    feature_dir.mkdir(parents=True)
    (feature_dir / "REPORT.md").write_text("""# Reporte por feature: `layout`

- **dataset**: `fixture_gt` · **device**: `cpu`

## Comparativa (media por motor)

| Motor (variante) | mAP@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | ---: | ---: |
| pyocrust_layout (default) | 0.800 | 100 |
| other_layout (default) | 0.990 | 5 |

## CPU vs GPU (`device_requested` vs `provider_effective`)

| Motor (variante) | mAP@IoU 0.5 ↑ (CPU) | mAP@IoU 0.5 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| pyocrust_layout (default) | 0.800 | 0.800 | 100 | 30 | cuda |
| fallback (default) | 0.500 | 0.500 | 60 | 60 | n/a (no corre en GPU) |
| other_layout (default) | 0.990 | 0.990 | 5 | 4 | cuda |
""", encoding="utf-8")
    monkeypatch.setattr(quality_vs_time, "REPORTS", tmp_path / "reports")

    points, device, unit = quality_vs_time.parse_quality_time("layout", "mAP@IoU 0.5")

    assert device == "cpu+gpu"
    assert unit == "ms/imagen ↓"
    assert {(name, point_device) for name, _ms, _q, point_device in points} == {
        ("pyocrust_layout (default)", "cpu"),
        ("pyocrust_layout (default)", "gpu"),
        ("fallback (default)", "cpu"),
        ("other_layout (default)", "cpu"),
        ("other_layout (default)", "gpu"),
    }
    assert ("pyocrust_layout (default)", 30.0, 0.8, "gpu") in points


def test_render_cpu_gpu_incluye_todos_los_medidos():
    lines = report.render_cpu_gpu(
        "layout",
        {"pyocrust_layout": {"layout_map": 0.8, "mean_ms": 100},
         "yolov10x (31.7M)": {"layout_map": 0.9, "mean_ms": 10}},
        {"dataset": "fixture_gt"},
        {"pyocrust_layout": {"layout_map": 0.8, "mean_ms": 30},
         "yolov10x (31.7M)": {"layout_map": 0.9, "mean_ms": 4}},
        {"dataset": "fixture_gt", "backends": {"pyocrust_layout": {"provider_effective": "cuda"}}},
    )
    table = "\n".join(lines)
    assert "pyocrust_layout" in table
    assert "yolov10x" in table


def test_render_cpu_gpu_resuelve_provider_por_nombre_canonico():
    lines = report.render_cpu_gpu(
        "layout",
        {"hantian/v8-n": {"layout_map": 0.508, "mean_ms": 80}},
        {"dataset": "fixture_gt"},
        {"hantian/v8-n": {"layout_map": 0.508, "mean_ms": 33}},
        {"dataset": "fixture_gt", "backends": {
            "hantian_v8n": {"model_name": "hantian/v8-n",
                           "model_variant": None,
                           "provider_effective": "cuda"},
        }},
    )

    assert any("hantian/v8-n" in line and "| cuda |" in line for line in lines)


def test_render_cpu_gpu_sin_model_name_no_inventa_provider():
    """Sin `model_name` en el summary no hay puente: el provider sale `n/a`."""
    lines = report.render_cpu_gpu(
        "layout",
        {"hantian/v8-n": {"layout_map": 0.508, "mean_ms": 80}},
        {"dataset": "fixture_gt"},
        {"hantian/v8-n": {"layout_map": 0.508, "mean_ms": 33}},
        {"dataset": "fixture_gt", "backends": {
            "hantian_v8n": {"provider_effective": "cuda"},
        }},
    )

    assert any("hantian/v8-n" in line and "| n/a |" in line for line in lines)


def _summary_medidos() -> dict[tuple[str, str], tuple[float, int]]:
    """{(feature, motor): (valor, n)} de SUMMARY.md (una fila por motor, sin device)."""
    out: dict[tuple[str, str], tuple[float, int]] = {}
    feature = None
    for line in (BENCH / "reports" / "SUMMARY.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            feature = line[3:].split(" — ")[0].strip()
        elif line.startswith("|") and feature:
            cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
            if len(cells) == 5 and cells[2].isdigit() and cells[3] == "medido":
                out[(feature, cells[0])] = (float(cells[1]), int(cells[2]))
    return out


def _scoreboard_filas() -> dict[tuple[str, str, str], tuple[float, int]]:
    """{(feature, motor, device): (calidad, n)} del SCOREBOARD.md."""
    out: dict[tuple[str, str, str], tuple[float, int]] = {}
    for line in (BENCH / "reports" / "SCOREBOARD.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7 or cells[0] == "Feature":
            continue
        try:
            calidad, n = float(cells[6]), int(cells[5])
        except ValueError:  # fila separadora `| :--- | ... |`
            continue
        out[(cells[0], cells[1], cells[4])] = (calidad, n)
    return out


def test_resumen_contiene_un_yolo_por_version():
    versions: dict[str, set[str]] = {}
    for (feature, motor) in _summary_medidos():
        if feature != "layout":
            continue
        match = re.search(r"/(?:v|y)(8|10|11|12|26)-?[a-z]", motor)
        if match:
            versions.setdefault(match.group(1), set()).add(motor)

    assert set(versions) == {"8", "10", "11", "12", "26"}
    # uno por versión, más el de tamaño similar a `pyocrust` (hantian/v8-x, 130 MB)
    assert all(1 <= len(models) <= 2 for models in versions.values()), versions
    assert any("v8-x" in motor for motor in versions["8"]), versions["8"]


def test_los_ocr_de_texto_no_entran_en_formula():
    """`rapidocr`/`easyocr` no emiten LaTeX: no son equiparables en `formula`."""
    report = (BENCH / "reports" / "formula" / "REPORT.md").read_text(encoding="utf-8")
    for line in report.splitlines():
        if line.startswith("|"):
            assert "rapidocr" not in line and "easyocr" not in line, line
    panel = (BENCH / "reports" / "SUMMARY.md").read_text(encoding="utf-8").split("## formula", 1)[1]
    assert "rapidocr" not in panel.split("## ", 1)[0]
    assert "easyocr" not in panel.split("## ", 1)[0]


def test_applicable_rows_filtra_solo_formula():
    from common.runner import applicable_rows

    rows = [{"backend": "rapidocr"}, {"backend": "pyocrust_formula"}]
    assert [r["backend"] for r in applicable_rows("formula", rows)] == ["pyocrust_formula"]
    # En el resto de features sí son motores válidos (p. ej. `text`).
    assert applicable_rows("text", rows) == rows


def test_report_de_layout_conserva_los_39_yolo_medidos():
    """El filtro del resumen no toca los informes por feature."""
    texto = (BENCH / "reports" / "layout" / "REPORT.md").read_text(encoding="utf-8")
    comparativa = texto.split("## Comparativa", 1)[1].split("## CPU vs GPU", 1)[0]
    motores = set()
    for line in comparativa.splitlines():
        if not line.startswith("|"):
            continue
        motor = line.strip("|").split("|")[0].strip()
        if re.search(r"/(?:v|y)(8|10|11|12|26)-?[a-z]", motor):
            motores.add(motor)
    assert len(motores) == 39, len(motores)


def test_summary_y_scoreboard_listan_los_mismos_motores():
    summary = _summary_medidos()
    board = _scoreboard_filas()
    assert summary, "SUMMARY.md sin filas medidos"
    assert board, "SCOREBOARD.md sin filas"
    # El SUMMARY publica **una fila por motor** (CPU manda); el SCOREBOARD, por
    # device. La igualdad es por (feature, motor).
    board_motors = {(f, m) for (f, m, _device) in board}
    assert set(summary) == board_motors, set(summary) ^ board_motors
    for key, (valor, n) in summary.items():
        cand = board.get((key[0], key[1], "cpu")) or board.get((key[0], key[1], "gpu"))
        assert cand is not None, key
        board_valor, board_n = cand
        assert n == board_n, f"{key}: n SUMMARY={n}, SCOREBOARD={board_n}"
        assert abs(valor - board_valor) < 1e-6, (key, valor, board_valor)


def test_tabla_consolidada_resuelve_provider_por_model_name():
    """`CPU_VS_GPU.md` no puede publicar `n/a` con un `ms GPU` medido.

    La tabla consolidada etiqueta por `model_name` pero el `summary.json`
    indexa por `backend`; sin el puente correcto el provider sale `n/a` y la
    fila miente sobre el acelerador que corrió.
    """
    for line in (BENCH / "reports" / "CPU_VS_GPU.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        _feature, _motor, _calidad, ms_cpu, ms_gpu, provider = cells[:6]
        if ms_gpu != "N/A":
            assert provider != "n/a", (
                f"fila con ms GPU medido ({ms_gpu}) pero provider n/a: {line}")


def test_artefactos_derivados_no_son_mas_viejos_que_los_report():
    reports = sorted(BENCH.glob("reports/*/REPORT.md"))
    assert reports, "no hay REPORT.md por feature"
    derived = [BENCH / "reports" / name for name in
               ("SUMMARY.md", "SCOREBOARD.md", "QUALITY_VS_TIME.md", "CPU_VS_GPU.md")]
    for art in derived:
        assert art.exists(), art
        for rep in reports:
            assert art.stat().st_mtime >= rep.stat().st_mtime, (
                f"{art.name} es mas viejo que {rep.name}: regenera los informes derivados")


# --- Criterio de aceptación t_a62cc581: no se publica calidad entre datasets ---

def test_ningun_informe_publica_filas_de_referencia_externa():
    """Ningún artefacto publicado mezcla calidad de otro dataset/GT como referencia.

    Las `REFERENCES.md` documentan *candidatos* y no llevan cifras; ninguna puede
    aparecer como fila `referencia` con valor en un informe generado.
    """
    for report_md in sorted(BENCH.glob("reports/**/*.md")):
        for lineno, line in enumerate(report_md.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert "referencia" not in cells, (
                f"{report_md.name}:{lineno}: fila con origen `referencia` publicada: {line}")


def test_el_resumen_no_lleva_maquinaria_de_referencias_externas():
    """El generador de SUMMARY no parsea ni pinta referencias externas."""
    assert not hasattr(summary, "REF_NOTE"), "REF_NOTE sigue vivo en features/summary.py"
    assert not hasattr(summary, "parse_references"), (
        "parse_references sigue vivo en features/summary.py")
    texto = (BENCH / "reports" / "SUMMARY.md").read_text(encoding="utf-8")
    for needle in ("ref:", "external reference", "barra rayada", "otro dataset/GT)"):
        assert needle not in texto, f"SUMMARY.md publica framing de referencia: {needle!r}"
    svg = (BENCH / "figures" / "SUMMARY.svg").read_text(encoding="utf-8")
    # El gris de "external reference" no debe volver a la figura.
    assert "b0bec5" not in svg, "SUMMARY.svg pinta barras de referencia externa"


def test_los_references_no_publican_valores():
    """`REFERENCES.md` solo documenta fuentes; si trae un valor, deja de ser referencia.

    Se admite una cifra únicamente como texto contextual en prosa, nunca como
    celda `Valor` de la tabla (que es lo que un informe parsearía y publicaría).
    """
    for refs_md in sorted(BENCH.glob("features/*/REFERENCES.md")):
        header, rows = None, []
        for line in refs_md.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set(":-"):
                continue
            if header is None:
                header = [c.lower() for c in cells]
                continue
            rows.append(cells)
        if header is None:
            continue
        vi = next((i for i, h in enumerate(header) if h.startswith("valor")), None)
        if vi is not None:
            for cells in rows:
                if vi < len(cells):
                    assert "—" in cells[vi] or cells[vi] in ("", "-"), (
                        f"{refs_md.name}: fila con valor publicable {cells[vi]!r}: {cells}")


def test_las_versiones_en_no_filtran_prosa_en_castellano():
    """Un `.en.md` publicable no debe llevar prosa en castellano sin traducir.

    El mapa de `_localization.english_markdown` traduce frase a frase; una frase
    nueva sin entrada se cuela tal cual (ya pasó con la nota de `QUALITY_VS_TIME`).
    """
    # Palabras funcionales inequívocamente castellanas (nunca aparecen en datos,
    # nombres de motor ni rutas) que delatarían una frase sin traducir.
    leaks = ("referencias", "medido", "medidos", "calidad", "dispositivo",
             "misma calidad", "otro dataset", "no es comparable", "sin datos")
    for en_md in sorted(BENCH.glob("reports/**/*.en.md")):
        texto = en_md.read_text(encoding="utf-8")
        for needle in leaks:
            assert needle not in texto, (
                f"{en_md.relative_to(BENCH)}: prosa castellana sin traducir: {needle!r}")




def _table_cells(md: str, header_prefix: str) -> dict[str, list[str]]:
    """{motor: celdas} de la tabla Markdown cuya cabecera empieza por `header_prefix`."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header_prefix):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            body, out = lines[i + 2:], {}
            for row in body:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                out[cells[0]] = cells
            return out
    return {}


def test_tabla_publicable_coincide_con_el_report_celda_a_celda():
    """`benchmark_table.md` y `REPORT.md` de cada feature salen del mismo agregado.

    La tabla publicable se genera con `report.render_table` sobre el MISMO `report`
    que pinta el informe; si una celda diverge, es que se rompió la fuente única.
    Se comprueban las features con runs medidos en `results/`.
    """
    for feature in sorted(report.FEATURE_COLUMNS):
        run = report.latest_run(feature)
        if run is None:
            continue
        rep, summ = report.analyze(feature, run)
        table_md, table_tex = report.render_table(feature, rep, summ)
        # Cabecera: mismas columnas que el informe + license.
        rep_md = report.render_md(feature, rep, summ, run)
        rep_cells = _table_cells(rep_md, "| Motor (variante) |")
        tab_cells = _table_cells(table_md, "| Motor (variante/tamaño) |")
        assert tab_cells, f"{feature}: benchmark_table.md sin filas"
        for motor, cells in tab_cells.items():
            assert motor in rep_cells, f"{feature}: {motor} en tabla pero no en REPORT"
            rep_row = rep_cells[motor]
            # Compara los valores de las métricas presentes en ambas (las de la
            # tabla son el mismo `fmt.format` que las del informe, sin negritas).
            for key, _label, fmt, _higher in report.FEATURE_COLUMNS[feature]:
                value = rep.get(motor, {}).get(key)
                expected = "N/A" if value is None else fmt.format(value)
                plain = [re.sub(r"</?u>", "", c).strip("*_ ") for c in cells]
                assert expected in plain, (
                    f"{feature}/{motor}/{key}: tabla={cells} no contiene {expected!r}")
        assert r"\begin{tabular}" in table_tex, f"{feature}: LaTeX sin tabular"
        for motor in tab_cells:
            assert report._tex_escape(motor) in table_tex, f"{feature}: {motor} ausente del LaTeX"


def test_full_page_informe_separa_contenido_de_estructura():
    """El informe de `full_page` explicita la separación contenido vs estructura."""
    run = report.latest_run("full_page")
    if run is None:
        return
    rep, summ = report.analyze("full_page", run)
    md = report.render_md("full_page", rep, summ, run)
    assert "Contenido vs estructura/posición" in md
    assert "TEDS tabla" in md and "layout mAP" in md and "Markdown F1" in md
    # Figuras y captions como métrica propia + cobertura declarada (el subset no
    # se disuelve en la media global) y nota de máscaras no emitibles.
    assert "Cobertura de figuras" in md
    assert "asoc. fig↔caption" in md
    assert "máscaras" in md and "613" in md


def test_cobertura_de_titulos_es_de_la_pagina_no_del_motor():
    """Un motor que no emite la estructura (docling) no rebaja la cobertura del GT.

    El GT de títulos/figuras es una propiedad de la PÁGINA (del dataset), idéntica
    para todos los motores: contarlo por la métrica de un motor que no la emite
    marcaría `0%` y mentiría sobre la muestra.
    """
    rows = [
        {"backend": "docling", "model_name": "docling", "model_variant": "pipeline",
         "image_id": "a", "title_recall": None, "figure_recall": None},
        {"backend": "pyocrust_structure", "model_name": "pp_structurev3", "model_variant": "default",
         "image_id": "a", "title_recall": 1.0, "figure_recall": 1.0},
        {"backend": "docling", "model_name": "docling", "model_variant": "pipeline",
         "image_id": "b", "title_recall": None, "figure_recall": None},
        {"backend": "pyocrust_structure", "model_name": "pp_structurev3", "model_variant": "default",
         "image_id": "b", "title_recall": None, "figure_recall": None},
    ]
    lines = report.render_title_coverage("full_page", rows)
    docling = next(line for line in lines if line.startswith("| docling"))
    pp = next(line for line in lines if line.startswith("| pp_structurev3"))
    assert docling.endswith("| 2 | 1 | 50% |")   # 1 de 2 paginas anota titulos
    assert pp.endswith("| 2 | 1 | 50% |")        # misma cobertura: es de la pagina, no del motor


def test_load_run_no_enmascara_metricas_evaluadas_de_otras_features(tmp_path):
    """`FULL_PAGE_METRIC_CHANNEL` es un mapa de `full_page`: no toca `formula`.

    `pyocrust_indra` no emite el canal `formulas`, pero en `formula` el scorer
    calcula `latex_sim`/`latex_token_f1` desde el **texto** del motor
    (`formula/bank.py::_formula_latex`). Aplicar el mapa a todas las features
    publicaba como `N/A` una metrica ya evaluada (regresion de la run
    2026-11-08_16-01-52). Este test lo comprueba contra el CSV crudo, no contra
    otro informe generado con `load_run`.
    """
    _write_run(tmp_path / "run", "cpu", [
        {"backend": "pyocrust_indra", "feature": "formula", "device_requested": "cpu",
         "status": "ok", "latex_sim": "0.243", "latex_token_f1": "0.505"},
        {"backend": "pyocrust_indra", "feature": "full_page", "device_requested": "cpu",
         "status": "ok", "layout_map": "0.0", "latex_sim": "0.0"},
    ])

    rows, _ = report.load_run(tmp_path / "run")
    by_feature = {row["feature"]: row for row in rows}

    # formula: metricas evaluadas desde el texto -> conservadas (no N/A).
    assert by_feature["formula"]["latex_sim"] == 0.243
    assert by_feature["formula"]["latex_token_f1"] == 0.505
    # full_page: indra no emite `layout`/`formulas` -> el 0.0 guardado es N/A.
    assert by_feature["full_page"]["layout_map"] is None
    assert by_feature["full_page"]["latex_sim"] is None
