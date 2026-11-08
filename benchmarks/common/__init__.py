"""Capa común de los bancos de `benchmarks/` (reorganización por feature).

Reúne lo que comparten todos los bancos:

* `common.metrics`   — CER/WER/F1, Markdown/bloques, cajas (IoU) y LaTeX.
* `common.datasets`  — FUNSD, OmniDocBench, recortes de fórmula, manifests.
* `common.runner`    — adaptadores, `run_benchmark`, `run_backends`, CSV de 28
  columnas y el `main` genérico.

Aquí solo se reexporta la API pública para que los bancos y los tests importen
de un sitio estable (`from common import run_backends, load_dataset, ...`).
"""

from __future__ import annotations

from common.datasets import (  # noqa: F401
    DATA_CACHE,
    DATASETS,
    DATASETS_MANIFEST,
    LAYOUT_DOCLAYNET_LABEL_TO_GT,
    LAYOUT_MODEL_TO_GT,
    ODB_CATEGORY_TO_KIND,
    OMNIDOCBENCH_REPO,
    OMNIDOCBENCH_REVISION,
    PROVENANCE_DATASET,
    PROVENANCE_FIXTURE,
    DatasetOffline,
    DatasetUnavailable,
    Sample,
    fixture_provenance,
    layout_gt_classes,
    load_dataset,
    load_funsd,
    load_local,
    load_manifest,
    load_omnidocbench,
    load_omnidocbench_formulas,
    load_omnidocbench_full_page,
    load_omnidocbench_layout,
    load_omnidocbench_tables,
    load_synthetic_orientation,
    load_synthetic_rectification,
    load_synthetic_text_line,
    prepare_datasets,
    verify_file,
)
from common.metrics import (  # noqa: F401
    block_f1,
    box_metrics,
    cer,
    cer_ord,
    detection_map,
    html_tags,
    image_ssim,
    iou,
    latex_exact,
    latex_similarity,
    latex_token_f1,
    levenshtein,
    markdown_f1,
    normalize,
    normalize_latex,
    table_teds,
    wer,
    wer_ord,
    word_f1,
)
from common.runner import (  # noqa: F401
    BENCHMARKS_ROOT,
    CSV_FIELDS,
    DEFAULT_RESULTS_DIR,
    FEATURE_TYPES,
    FORMULA_BACKENDS_EXCLUDED,
    GPU_PROVIDERS,
    LICENSES,
    MODEL_NAMES,
    OcrOutput,
    BACKENDS,
    PROVIDERS,
    ProviderUnavailable,
    TASK_TYPES,
    applicable_rows,
    available_providers,
    device_outcome,
    main,
    module_available,
    pyocrust_device_arg,
    run_backends,
    run_benchmark,
    select_device_rows,
    write_csv,
)

__all__ = [
    # datasets
    "DATA_CACHE", "DATASETS", "DATASETS_MANIFEST", "LAYOUT_DOCLAYNET_LABEL_TO_GT",
    "LAYOUT_MODEL_TO_GT", "ODB_CATEGORY_TO_KIND", "layout_gt_classes",
    "OMNIDOCBENCH_REPO", "OMNIDOCBENCH_REVISION", "load_manifest", "verify_file",
    "prepare_datasets",
    "PROVENANCE_DATASET", "PROVENANCE_FIXTURE", "fixture_provenance",
    "DatasetOffline", "DatasetUnavailable", "Sample", "load_dataset",
    "load_funsd", "load_local", "load_omnidocbench", "load_omnidocbench_formulas",
    "load_omnidocbench_full_page", "load_omnidocbench_layout", "load_omnidocbench_tables",
    "load_synthetic_orientation", "load_synthetic_rectification", "load_synthetic_text_line",
    # metrics
    "block_f1", "box_metrics", "cer", "cer_ord", "detection_map", "html_tags",
    "image_ssim", "iou", "latex_exact",
    "latex_similarity", "latex_token_f1", "levenshtein", "markdown_f1",
    "normalize", "normalize_latex", "table_teds", "wer", "wer_ord", "word_f1",
    # runner
    "BENCHMARKS_ROOT", "CSV_FIELDS", "DEFAULT_RESULTS_DIR", "FEATURE_TYPES",
    "GPU_PROVIDERS", "LICENSES", "MODEL_NAMES", "OcrOutput", "BACKENDS", "PROVIDERS", "ProviderUnavailable",
    "TASK_TYPES", "available_providers", "device_outcome", "main", "module_available",
    "pyocrust_device_arg", "run_backends",
    "run_benchmark", "select_device_rows", "write_csv",
]
