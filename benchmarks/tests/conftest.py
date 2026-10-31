"""Comparte `benchmarks/` en `sys.path` para poder importar el harness."""

from __future__ import annotations

import sys
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent
if str(BENCHMARKS_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARKS_DIR))
