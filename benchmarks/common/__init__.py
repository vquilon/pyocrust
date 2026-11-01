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
    DatasetUnavailable,
    Sample,
    load_dataset,
    load_funsd,
    load_local,
    load_omnidocbench,
    load_omnidocbench_formulas,
)
from common.metrics import (  # noqa: F401
    block_f1,
    box_metrics,
    cer,
    cer_ord,
    iou,
    latex_exact,
    latex_similarity,
    latex_token_f1,
    levenshtein,
    markdown_f1,
    normalize,
    normalize_latex,
    wer,
    wer_ord,
    word_f1,
)
from common.runner import (  # noqa: F401
    BENCHMARKS_ROOT,
    CSV_FIELDS,
    DEFAULT_RESULTS_DIR,
    FEATURE_TYPES,
    MODEL_NAMES,
    OcrOutput,
    PROVIDERS,
    ProviderUnavailable,
    TASK_TYPES,
    main,
    module_available,
    run_backends,
    run_benchmark,
    write_csv,
)

__all__ = [
    # datasets
    "DATA_CACHE", "DATASETS", "DatasetUnavailable", "Sample", "load_dataset",
    "load_funsd", "load_local", "load_omnidocbench", "load_omnidocbench_formulas",
    # metrics
    "block_f1", "box_metrics", "cer", "cer_ord", "iou", "latex_exact",
    "latex_similarity", "latex_token_f1", "levenshtein", "markdown_f1",
    "normalize", "normalize_latex", "wer", "wer_ord", "word_f1",
    # runner
    "BENCHMARKS_ROOT", "CSV_FIELDS", "DEFAULT_RESULTS_DIR", "FEATURE_TYPES",
    "MODEL_NAMES", "OcrOutput", "PROVIDERS", "ProviderUnavailable", "TASK_TYPES",
    "main", "module_available", "run_backends", "run_benchmark", "write_csv",
]
