#!/usr/bin/env python
"""Scatter plot of every verified DocLayNet YOLO plus the layout baselines."""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[1]
RESULTS = BENCH / "results"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from common.runner import MODEL_NAMES, YOLO_LAYOUT_MODELS  # noqa: E402

EXTRA_MODELS = {"pyocrust_layout", "docling_heron_101"}
EXPECTED_MODELS = set(YOLO_LAYOUT_MODELS) | EXTRA_MODELS
GPU_PROVIDERS = {"cuda", "directml", "tensorrt", "coreml", "openvino", "webgpu", "rocm", "mps"}
COLORS = {
    "hantian": "#2878b5",
    "omoured": "#d97706",
    "armaggheddon": "#7b61a8",
    "pyocrust": "#238b57",
    "docling": "#c44536",
}


def _owner(backend: str) -> str:
    if backend.startswith("pyocrust_"):
        return "pyocrust"
    if backend == "docling_heron_101":
        return "docling"
    return backend.split("_", 1)[0]


def _latest_measurements(device: str) -> dict[str, dict]:
    root = RESULTS / ("_gpu" if device == "gpu" else "") / "layout"
    latest: dict[str, tuple[str, list[dict], Path]] = {}
    for path in root.glob("**/*.csv"):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            grouped: dict[str, list[dict]] = defaultdict(list)
            for row in csv.DictReader(stream):
                if (row.get("status") != "ok"
                        or row.get("dataset") != "omnidocbench_layout"
                        or row.get("device_requested") != device
                        or row.get("backend") not in EXPECTED_MODELS):
                    continue
                if device == "gpu" and row.get("provider_effective", "").lower() not in GPU_PROVIDERS:
                    continue
                grouped[row["backend"]].append(row)
        stamp = path.parent.name
        for backend, rows in grouped.items():
            if backend not in latest or stamp > latest[backend][0]:
                latest[backend] = (stamp, rows, path)

    output = {}
    for backend, (stamp, rows, path) in latest.items():
        valid = [r for r in rows if r.get("elapsed_ms") and r.get("layout_map")]
        if not valid:
            continue
        name, variant = MODEL_NAMES[backend]
        label = f"{name} ({variant})" if variant and variant != "default" else name
        output[backend] = {
            "backend": backend,
            "label": label,
            "owner": _owner(backend),
            "device": device,
            "n": len(valid),
            "ms": sum(float(r["elapsed_ms"]) for r in valid) / len(valid),
            "map50": sum(float(r["layout_map"]) for r in valid) / len(valid),
            "run": stamp,
            "csv": path,
            "providers": sorted({r.get("provider_effective", "") for r in valid}),
        }
    return output


def collect_points() -> dict[str, dict[str, dict]]:
    if len(YOLO_LAYOUT_MODELS) != 39:
        raise AssertionError(f"Expected 39 registered DocLayNet YOLO models, got {len(YOLO_LAYOUT_MODELS)}")
    cpu, gpu = _latest_measurements("cpu"), _latest_measurements("gpu")
    required_cpu = EXPECTED_MODELS
    required_gpu = set(YOLO_LAYOUT_MODELS) | {"pyocrust_layout"}
    missing_cpu, missing_gpu = required_cpu - set(cpu), required_gpu - set(gpu)
    if missing_cpu or missing_gpu:
        raise RuntimeError(f"Missing successful data; CPU={sorted(missing_cpu)}, GPU={sorted(missing_gpu)}")
    if len({cpu[b]["label"] for b in YOLO_LAYOUT_MODELS}) != 39:
        raise AssertionError("DocLayNet YOLO labels are not unique")
    return {backend: {"cpu": cpu[backend], **({"gpu": gpu[backend]} if backend in gpu else {})}
            for backend in sorted(EXPECTED_MODELS)}


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.fonttype"] = "none"
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    models = collect_points()
    y_values = [point["map50"] for pair in models.values() for point in pair.values()]
    ylo, yhi = max(0.0, min(y_values) - 0.035), min(1.0, max(y_values) + 0.035)
    ordered = sorted(models, key=lambda b: (sum(p["map50"] for p in models[b].values()) / len(models[b]), b))
    row_y = {backend: ylo + (yhi - ylo) * (i + 0.5) / len(ordered)
             for i, backend in enumerate(ordered)}

    fig = plt.figure(figsize=(28, 19), facecolor="white")
    ax = fig.add_axes([0.075, 0.105, 0.56, 0.79])
    labels = fig.add_axes([0.67, 0.105, 0.31, 0.79], sharey=ax)
    labels.set_xlim(0, 1)
    labels.axis("off")
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(ylo, yhi)
    labels.set_ylim(ylo, yhi + (yhi - ylo) * 0.06)
    ax.set_xlabel("Mean inference time (ms / image, log scale)", fontsize=12)
    ax.set_ylabel("mAP@0.5 on OmniDocBench", fontsize=12)
    ax.grid(True, which="major", alpha=0.22)
    ax.grid(True, which="minor", axis="x", alpha=0.08)
    ax.spines[["top", "right"]].set_visible(False)

    for backend, pair in models.items():
        color = COLORS[_owner(backend)]
        for device, marker in (("cpu", "o"), ("gpu", "^") ):
            point = pair.get(device)
            if point:
                ax.scatter(point["ms"], point["map50"], marker=marker, s=72,
                           color=color, edgecolor="white", linewidth=0.8, zorder=4)

    handles = [
        Line2D([], [], marker="o", linestyle="", color="#333333", label="CPU"),
        Line2D([], [], marker="^", linestyle="", color="#333333", label="GPU (CUDA / DirectML)"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=True, fontsize=9, title="Device marker")

    labels.text(0.00, yhi + (yhi - ylo) * 0.025, "MODEL (author / version / size)",
                fontsize=8.5, fontweight="bold", va="bottom", color="#222222")
    for x, header in ((0.62, "CPU mAP"), (0.73, "GPU mAP"), (0.85, "CPU ms"), (0.98, "GPU ms")):
        labels.text(x, yhi + (yhi - ylo) * 0.025, header, fontsize=7.5,
                    fontweight="bold", va="bottom", ha="right", color="#222222")
    for backend in ordered:
        pair = models[backend]
        cpu, gpu = pair["cpu"], pair.get("gpu")
        labels.text(0.00, row_y[backend], cpu["label"],
                    fontsize=7.6, va="center", color=COLORS[_owner(backend)])
        for x, value in ((0.62, f"{cpu['map50']:.3f}"),
                         (0.73, f"{gpu['map50']:.3f}" if gpu else "—"),
                         (0.85, f"{cpu['ms']:.0f}"),
                         (0.98, f"{gpu['ms']:.0f}" if gpu else "—")):
            labels.text(x, row_y[backend], value, fontsize=7.5,
                        va="center", ha="right", color="#333333")

    family_handles = [
        Line2D([], [], marker="o", linestyle="", color=color, label=owner)
        for owner, color in COLORS.items()
    ]
    fig.legend(handles=family_handles, loc="upper center", bbox_to_anchor=(0.54, 0.955),
               ncol=5, frameon=False, title="Color: model family", fontsize=8.5, title_fontsize=9)
    fig.suptitle("DocLayNet layout models — accuracy vs. inference time", y=0.985,
                 fontsize=17, fontweight="bold")
    gpu_missing = "docling_heron_101" not in models or "gpu" not in models["docling_heron_101"]
    footnote = (
        "All 39 YOLO checkpoints are DocLayNet fine-tunes (11 classes), verified via model.names. "
        "Points use the latest successful OmniDocBench layout CSV per model/device; the side labels list every model and both times."
    )
    if gpu_missing:
        footnote += " docling_heron_101 is CPU-only in this benchmark; no GPU result is plotted."
    fig.text(0.5, 0.052, footnote, ha="center", va="center", fontsize=8.5, color="#444444", wrap=True)
    fig.text(0.5, 0.028,
             "Circle = CPU · triangle = GPU · color = model family · time is mean inference ms/image (model load excluded).",
             ha="center", va="center", fontsize=8, color="#666666")

    output = BENCH / "figures" / "layout" / "LAYOUT_ALL_MODELS"
    output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(output.with_suffix(f".{extension}"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[LAYOUT_ALL_MODELS] models={len(models)} CPU={sum('cpu' in p for p in models.values())} "
          f"GPU={sum('gpu' in p for p in models.values())}; heron_gpu={'missing' if gpu_missing else 'present'}")
    print(f"[LAYOUT_ALL_MODELS] -> {output.with_suffix('.png')}")
    print(f"[LAYOUT_ALL_MODELS] -> {output.with_suffix('.svg')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
