# Reporte por feature: `layout`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/layout/bank.py --limit 40 --device cpu --output-dir results`
- **dataset**: `omnidocbench_layout` · **n** (por motor): `40` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/layout/2026-11-09_14-32-35` · **fecha**: `2026-11-09_14-32-35`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | ---: | ---: | ---: | ---: |
| armaggheddon/y11-m | 40 | 0.542 | 0.585 | 365 |
| armaggheddon/y11-n | 40 | 0.522 | 0.573 | **65** |
| armaggheddon/y11-s | 40 | 0.516 | 0.567 | 167 |
| armaggheddon/y26-m (21.8M) | 40 | 0.568 | 0.616 | 333 |
| armaggheddon/y26-n (2.6M) | 40 | 0.572 | 0.619 | 69 |
| armaggheddon/y26-s | 40 | 0.476 | 0.518 | 157 |
| docling-layout-heron-101 (default) | 40 | **0.818** | **0.963** | 1005 |
| hantian/v10-b | 40 | 0.484 | 0.533 | 456 |
| hantian/v10-l | 40 | 0.533 | 0.579 | 569 |
| hantian/v10-m | 40 | 0.526 | 0.576 | 332 |
| hantian/v10-n | 40 | 0.461 | 0.504 | 66 |
| hantian/v10-s | 40 | 0.495 | 0.546 | 131 |
| hantian/v11-l | 40 | 0.502 | 0.572 | 422 |
| hantian/v11-m (21.8M) | 40 | 0.520 | 0.576 | 342 |
| hantian/v11-n (2.6M) | 40 | 0.520 | 0.555 | 67 |
| hantian/v11-s | 40 | 0.473 | 0.528 | 163 |
| hantian/v12-l | 40 | 0.550 | 0.589 | 711 |
| hantian/v12-m | 40 | 0.523 | 0.587 | 447 |
| hantian/v12-n | 40 | 0.547 | 0.584 | 88 |
| hantian/v12-s | 40 | 0.542 | 0.606 | 180 |
| hantian/v8-l | 40 | 0.486 | 0.552 | 699 |
| hantian/v8-m | 40 | 0.494 | 0.557 | 364 |
| hantian/v8-n | 40 | 0.545 | 0.590 | 68 |
| hantian/v8-s | 40 | 0.495 | 0.543 | 207 |
| hantian/v8-x | 40 | 0.490 | 0.561 | 1025 |
| hantian/y26-l | 40 | 0.508 | 0.543 | 433 |
| hantian/y26-m | 40 | 0.492 | 0.542 | 353 |
| hantian/y26-n | 40 | 0.499 | 0.545 | 69 |
| hantian/y26-s | 40 | 0.492 | 0.538 | 150 |
| omoured/v10-b (20.5M) | 40 | 0.382 | 0.440 | 415 |
| omoured/v10-l | 40 | 0.366 | 0.405 | 550 |
| omoured/v10-m | 40 | 0.381 | 0.427 | 292 |
| omoured/v10-n | 40 | 0.485 | 0.525 | 70 |
| omoured/v10-s | 40 | 0.427 | 0.462 | 140 |
| omoured/v10-x (31.7M) | 40 | 0.451 | 0.523 | 748 |
| omoured/v11-l | 40 | 0.350 | 0.387 | 481 |
| omoured/v11-m | 40 | 0.392 | 0.444 | 354 |
| omoured/v11-n | 40 | 0.448 | 0.493 | 137 |
| omoured/v11-s | 40 | 0.406 | 0.452 | 144 |
| omoured/v11-x | 40 | 0.331 | 0.374 | 849 |
| pp-doclayoutv3 (130M) | 40 | 0.796 | 0.817 | 2219 |
| pp_structurev3 (default) | 40 | 0.751 | 0.765 | 7111 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `layout`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `deformable_detr` — pesos de Aryn/deformable-detr-DocLayNet no estan en la cache HF local (OSError: Can't load image processor for 'Aryn/deformable-detr-DocLayNet'. If you were trying to load it from 'https://huggingface.co/models', make sure you don't have a local directory with the same name. Otherwise, make sure 'Aryn/deformable-detr-DocLayNet' is the correct path to a directory containing a preprocessor_config.json file)

## Procedencia de las alternativas

- `armaggheddon/y26-m (21.8M)` — modelo **independiente** (otro proyecto/checkpoint)
- `armaggheddon/y26-n (2.6M)` — modelo **independiente** (otro proyecto/checkpoint)
- `docling-layout-heron-101 (default)` — modelo **independiente** (otro proyecto/checkpoint)
- `hantian/v11-m (21.8M)` — modelo **independiente** (otro proyecto/checkpoint)
- `hantian/v11-n (2.6M)` — modelo **independiente** (otro proyecto/checkpoint)
- `omoured/v10-b (20.5M)` — modelo **independiente** (otro proyecto/checkpoint)
- `omoured/v10-x (31.7M)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | mAP@IoU 0.5 ↑ (CPU) | mAP@IoU 0.5 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| armaggheddon/y11-m | 0.542 | 0.542 | 365 | 42 | cuda |
| armaggheddon/y11-n | 0.522 | 0.522 | 65 | 30 | cuda |
| armaggheddon/y11-s | 0.516 | 0.516 | 167 | 29 | cuda |
| armaggheddon/y26-m (21.8M) | 0.568 | 0.568 | 333 | 31 | cuda |
| armaggheddon/y26-n (2.6M) | 0.572 | 0.572 | 69 | 29 | cuda |
| armaggheddon/y26-s | 0.476 | 0.476 | 157 | 30 | cuda |
| docling-layout-heron-101 (default) | 0.818 | N/A | 1005 | N/A | n/a (no corre en GPU) |
| hantian/v10-b | 0.484 | 0.484 | 456 | 33 | cuda |
| hantian/v10-l | 0.533 | 0.533 | 569 | 36 | cuda |
| hantian/v10-m | 0.526 | 0.526 | 332 | 41 | cuda |
| hantian/v10-n | 0.461 | 0.461 | 66 | 30 | cuda |
| hantian/v10-s | 0.495 | 0.495 | 131 | 30 | cuda |
| hantian/v11-l | 0.502 | 0.502 | 422 | 48 | cuda |
| hantian/v11-m (21.8M) | 0.520 | 0.520 | 342 | 40 | cuda |
| hantian/v11-n (2.6M) | 0.520 | 0.520 | 67 | 33 | cuda |
| hantian/v11-s | 0.473 | 0.473 | 163 | 35 | cuda |
| hantian/v12-l | 0.550 | 0.550 | 711 | 53 | cuda |
| hantian/v12-m | 0.523 | 0.523 | 447 | 42 | cuda |
| hantian/v12-n | 0.547 | 0.547 | 88 | 34 | cuda |
| hantian/v12-s | 0.542 | 0.542 | 180 | 31 | cuda |
| hantian/v8-l | 0.486 | 0.486 | 699 | 37 | cuda |
| hantian/v8-m | 0.494 | 0.494 | 364 | 33 | cuda |
| hantian/v8-n | 0.545 | 0.545 | 68 | 25 | cuda |
| hantian/v8-s | 0.495 | 0.495 | 207 | 27 | cuda |
| hantian/v8-x | 0.490 | 0.490 | 1025 | 47 | cuda |
| hantian/y26-l | 0.508 | 0.506 | 433 | 37 | cuda |
| hantian/y26-m | 0.492 | 0.492 | 353 | 32 | cuda |
| hantian/y26-n | 0.499 | 0.499 | 69 | 29 | cuda |
| hantian/y26-s | 0.492 | 0.492 | 150 | 32 | cuda |
| omoured/v10-b (20.5M) | 0.382 | 0.382 | 415 | 33 | cuda |
| omoured/v10-l | 0.366 | 0.366 | 550 | 36 | cuda |
| omoured/v10-m | 0.381 | 0.381 | 292 | 33 | cuda |
| omoured/v10-n | 0.485 | 0.485 | 70 | 28 | cuda |
| omoured/v10-s | 0.427 | 0.427 | 140 | 28 | cuda |
| omoured/v10-x (31.7M) | 0.451 | 0.451 | 748 | 54 | cuda |
| omoured/v11-l | 0.350 | 0.350 | 481 | 45 | cuda |
| omoured/v11-m | 0.392 | 0.392 | 354 | 38 | cuda |
| omoured/v11-n | 0.448 | 0.448 | 137 | 36 | cuda |
| omoured/v11-s | 0.406 | 0.406 | 144 | 43 | cuda |
| omoured/v11-x | 0.331 | 0.331 | 849 | 55 | cuda |
| pp-doclayoutv3 (130M) | 0.796 | 0.796 | 2219 | 488 | cuda |
| pp_structurev3 (default) | 0.751 | 0.751 | 7111 | 2938 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> mAP@IoU 0.5 **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 42 · estratos cubiertos: 17. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (2), `PPT2PDF×other_layout` (4), `PPT2PDF×single_column` (3), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (4), `academic_literature×other_layout` (2), `academic_literature×single_column` (4), `academic_literature×three_column` (1), `book×1andmore_column` (1), `book×double_column` (3), `book×other_layout` (4), `book×single_column` (4), `book×three_column` (1), `colorful_textbook×1andmore_column` (2), `colorful_textbook×double_column` (1), `colorful_textbook×other_layout` (1).

### mAP@IoU 0.5 por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout | academic_literature×single_column | academic_literature×three_column | book×1andmore_column | book×double_column | book×other_layout | book×single_column | book×three_column | colorful_textbook×1andmore_column | colorful_textbook×double_column | colorful_textbook×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| armaggheddon/y11-m | 0.257 | 0.361 | 0.088 | 0.267 | 0.841 | 0.709 | 0.648 | 0.760 | 0.897 | 0.729 | 0.530 | 0.627 | 0.498 | 0.833 | 0.494 | 0.500 | 0.669 |
| armaggheddon/y11-n | 0.233 | 0.241 | 0.131 | 0.332 | 0.823 | 0.710 | 0.676 | 0.780 | 0.761 | 0.625 | 0.607 | 0.401 | 0.500 | 0.667 | 0.733 | 0.271 | 0.463 |
| armaggheddon/y11-s | 0.287 | 0.228 | 0.130 | 0.389 | 0.884 | 0.602 | 0.540 | 0.766 | 0.692 | 0.604 | 0.638 | 0.626 | 0.458 | 0.500 | 0.487 | 0.542 | 0.345 |
| armaggheddon/y26-m (21.8M) | 0.350 | 0.350 | 0.156 | 0.375 | 0.825 | 0.686 | 0.700 | 0.820 | 0.995 | 0.750 | 0.536 | 0.629 | 0.417 | 0.667 | 0.780 | 0.554 | 0.541 |
| armaggheddon/y26-n (2.6M) | 0.567 | 0.475 | 0.210 | 0.404 | 0.901 | 0.740 | 0.629 | 0.878 | 0.897 | 0.750 | 0.609 | 0.443 | 0.417 | 0.667 | 0.568 | 0.314 | 0.736 |
| armaggheddon/y26-s | 0.065 | 0.415 | 0.121 | 0.225 | 0.896 | 0.646 | 0.567 | 0.780 | 0.894 | 0.750 | 0.527 | 0.339 | 0.424 | 0.622 | 0.496 | 0.181 | 0.297 |
| docling-layout-heron-101 (default) | 0.877 | 0.639 | 0.784 | 0.775 | 0.918 | 0.862 | 0.975 | 0.953 | 0.999 | 0.875 | 0.772 | 0.852 | 0.767 | 1.000 | 0.637 | 0.481 | 0.638 |
| hantian/v10-b | 0.020 | 0.367 | 0.035 | 0.108 | 0.839 | 0.752 | 0.702 | 0.773 | 0.894 | 0.750 | 0.494 | 0.431 | 0.417 | 0.833 | 0.417 | 0.500 | 0.259 |
| hantian/v10-l | 0.140 | 0.196 | 0.137 | 0.207 | 0.827 | 0.770 | 0.731 | 0.720 | 0.997 | 1.000 | 0.566 | 0.509 | 0.425 | 0.833 | 0.704 | 0.596 | 0.291 |
| hantian/v10-m | 0.153 | 0.212 | 0.019 | 0.200 | 0.825 | 0.656 | 0.727 | 0.770 | 0.947 | 1.000 | 0.608 | 0.431 | 0.482 | 0.833 | 0.745 | 0.559 | 0.651 |
| hantian/v10-n | 0.267 | 0.271 | 0.005 | 0.167 | 0.679 | 0.513 | 0.560 | 0.722 | 0.792 | 0.750 | 0.618 | 0.478 | 0.375 | 0.667 | 0.600 | 0.375 | 0.651 |
| hantian/v10-s | 0.252 | 0.227 | 0.024 | 0.125 | 0.798 | 0.677 | 0.733 | 0.684 | 0.794 | 0.750 | 0.575 | 0.534 | 0.500 | 0.833 | 0.534 | 0.375 | 0.452 |
| hantian/v11-l | 0.020 | 0.337 | 0.161 | 0.136 | 0.825 | 0.734 | 0.668 | 0.751 | 0.899 | 0.750 | 0.522 | 0.489 | 0.299 | 0.833 | 0.497 | 0.552 | 0.676 |
| hantian/v11-m (21.8M) | 0.317 | 0.141 | 0.150 | 0.280 | 0.838 | 0.639 | 0.689 | 0.692 | 0.884 | 0.750 | 0.620 | 0.559 | 0.433 | 0.833 | 0.609 | 0.571 | 0.297 |
| hantian/v11-n (2.6M) | 0.333 | 0.397 | 0.126 | 0.383 | 0.776 | 0.611 | 0.717 | 0.656 | 0.685 | 0.750 | 0.599 | 0.553 | 0.415 | 0.667 | 0.711 | 0.127 | 0.648 |
| hantian/v11-s | 0.173 | 0.382 | 0.039 | 0.200 | 0.657 | 0.599 | 0.605 | 0.656 | 0.789 | 0.750 | 0.578 | 0.502 | 0.486 | 0.833 | 0.468 | 0.361 | 0.322 |
| hantian/v12-l | 0.220 | 0.395 | 0.079 | 0.258 | 0.835 | 0.765 | 0.841 | 0.751 | 0.897 | 0.750 | 0.618 | 0.665 | 0.296 | 1.000 | 0.511 | 0.542 | 0.586 |
| hantian/v12-m | 0.308 | 0.304 | 0.138 | 0.508 | 0.825 | 0.563 | 0.682 | 0.794 | 0.900 | 0.750 | 0.598 | 0.514 | 0.379 | 0.833 | 0.459 | 0.292 | 0.434 |
| hantian/v12-n | 0.517 | 0.355 | 0.044 | 0.335 | 0.825 | 0.673 | 0.851 | 0.685 | 0.797 | 0.750 | 0.689 | 0.383 | 0.479 | 1.000 | 0.753 | 0.438 | 0.672 |
| hantian/v12-s | 0.458 | 0.187 | 0.149 | 0.492 | 0.835 | 0.639 | 0.867 | 0.751 | 0.998 | 0.750 | 0.544 | 0.502 | 0.407 | 0.833 | 0.509 | 0.292 | 0.641 |
| hantian/v8-l | 0.500 | 0.211 | 0.077 | 0.035 | 0.776 | 0.614 | 0.602 | 0.720 | 0.987 | 1.000 | 0.577 | 0.502 | 0.392 | 0.602 | 0.485 | 0.562 | 0.587 |
| hantian/v8-m | 0.145 | 0.277 | 0.112 | 0.094 | 0.766 | 0.595 | 0.730 | 0.718 | 0.779 | 1.000 | 0.558 | 0.506 | 0.378 | 0.833 | 0.764 | 0.491 | 0.233 |
| hantian/v8-n | 0.373 | 0.417 | 0.090 | 0.192 | 0.831 | 0.716 | 0.746 | 0.724 | 0.786 | 0.750 | 0.487 | 0.633 | 0.608 | 0.667 | 0.666 | 0.252 | 0.547 |
| hantian/v8-s | 0.383 | 0.399 | 0.080 | 0.133 | 0.711 | 0.607 | 0.723 | 0.799 | 0.482 | 0.750 | 0.584 | 0.525 | 0.383 | 0.667 | 0.741 | 0.268 | 0.377 |
| hantian/v8-x | 0.379 | 0.232 | 0.026 | 0.197 | 0.713 | 0.611 | 0.668 | 0.685 | 0.894 | 1.000 | 0.595 | 0.491 | 0.478 | 0.667 | 0.489 | 0.360 | 0.568 |
| hantian/y26-l | 0.233 | 0.296 | 0.060 | 0.233 | 0.764 | 0.689 | 0.693 | 0.790 | 0.896 | 1.000 | 0.573 | 0.390 | 0.443 | 0.833 | 0.430 | 0.375 | 0.698 |
| hantian/y26-m | 0.340 | 0.312 | 0.152 | 0.083 | 0.719 | 0.629 | 0.813 | 0.758 | 0.886 | 1.000 | 0.538 | 0.338 | 0.340 | 0.833 | 0.685 | 0.167 | 0.654 |
| hantian/y26-n | 0.483 | 0.306 | 0.044 | 0.254 | 0.782 | 0.652 | 0.612 | 0.790 | 0.784 | 0.625 | 0.540 | 0.459 | 0.482 | 0.500 | 0.747 | 0.292 | 0.287 |
| hantian/y26-s | 0.272 | 0.181 | 0.144 | 0.203 | 0.774 | 0.657 | 0.710 | 0.834 | 0.909 | 0.750 | 0.521 | 0.493 | 0.350 | 0.833 | 0.476 | 0.250 | 0.299 |
| omoured/v10-b (20.5M) | 0.100 | 0.152 | 0.016 | 0.070 | 0.651 | 0.642 | 0.450 | 0.756 | 0.691 | 0.750 | 0.524 | 0.153 | 0.224 | 0.352 | 0.735 | 0.250 | 0.223 |
| omoured/v10-l | 0.014 | 0.120 | 0.093 | 0.019 | 0.641 | 0.599 | 0.389 | 0.629 | 0.560 | 0.667 | 0.389 | 0.307 | 0.292 | 0.259 | 0.708 | 0.125 | 0.408 |
| omoured/v10-m | 0.000 | 0.140 | 0.111 | 0.004 | 0.753 | 0.556 | 0.393 | 0.683 | 0.687 | 0.633 | 0.505 | 0.190 | 0.308 | 0.306 | 0.688 | 0.298 | 0.451 |
| omoured/v10-n | 0.307 | 0.283 | 0.061 | 0.283 | 0.670 | 0.621 | 0.571 | 0.863 | 0.783 | 1.000 | 0.521 | 0.439 | 0.354 | 0.667 | 0.597 | 0.250 | 0.395 |
| omoured/v10-s | 0.229 | 0.209 | 0.043 | 0.067 | 0.780 | 0.657 | 0.677 | 0.769 | 0.583 | 0.750 | 0.496 | 0.374 | 0.250 | 0.667 | 0.427 | 0.125 | 0.459 |
| omoured/v10-x (31.7M) | 0.249 | 0.235 | 0.074 | 0.049 | 0.707 | 0.654 | 0.483 | 0.836 | 0.788 | 0.750 | 0.541 | 0.362 | 0.312 | 0.659 | 0.562 | 0.250 | 0.647 |
| omoured/v11-l | 0.025 | 0.213 | 0.012 | 0.083 | 0.732 | 0.545 | 0.375 | 0.669 | 0.690 | 0.250 | 0.381 | 0.208 | 0.121 | 0.806 | 0.688 | 0.265 | 0.333 |
| omoured/v11-m | 0.092 | 0.196 | 0.058 | 0.039 | 0.574 | 0.677 | 0.482 | 0.749 | 0.704 | 0.417 | 0.478 | 0.188 | 0.273 | 0.593 | 0.720 | 0.255 | 0.333 |
| omoured/v11-n | 0.137 | 0.172 | 0.032 | 0.172 | 0.711 | 0.639 | 0.506 | 0.894 | 0.587 | 0.750 | 0.403 | 0.421 | 0.392 | 0.667 | 0.646 | 0.377 | 0.108 |
| omoured/v11-s | 0.267 | 0.122 | 0.088 | 0.067 | 0.553 | 0.645 | 0.683 | 0.629 | 0.681 | 0.625 | 0.442 | 0.320 | 0.289 | 0.622 | 0.687 | 0.201 | 0.354 |
| omoured/v11-x | 0.033 | 0.136 | 0.139 | 0.022 | 0.605 | 0.572 | 0.400 | 0.596 | 0.753 | 0.375 | 0.228 | 0.201 | 0.191 | 0.433 | 0.740 | 0.125 | 0.196 |
| pp-doclayoutv3 (130M) | 0.800 | 0.579 | 0.707 | 0.675 | 0.825 | 0.847 | 0.896 | 1.000 | 0.964 | 0.700 | 0.871 | 0.710 | 0.774 | 1.000 | 0.913 | 0.700 | 0.459 |
| pp_structurev3 (default) | 0.783 | 0.349 | 0.610 | 0.613 | 0.828 | 0.809 | 0.958 | 0.990 | 0.784 | 0.700 | 0.852 | 0.630 | 0.764 | 1.000 | 0.890 | 0.700 | 0.422 |

### recall@IoU 0.5 por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout | academic_literature×single_column | academic_literature×three_column | book×1andmore_column | book×double_column | book×other_layout | book×single_column | book×three_column | colorful_textbook×1andmore_column | colorful_textbook×double_column | colorful_textbook×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| armaggheddon/y11-m | 0.367 | 0.417 | 0.088 | 0.333 | 0.939 | 0.726 | 0.800 | 0.805 | 0.900 | 0.750 | 0.536 | 0.654 | 0.500 | 1.000 | 0.593 | 0.500 | 0.706 |
| armaggheddon/y11-n | 0.333 | 0.311 | 0.186 | 0.406 | 0.928 | 0.740 | 0.800 | 0.784 | 0.800 | 0.625 | 0.638 | 0.432 | 0.542 | 0.667 | 0.824 | 0.375 | 0.539 |
| armaggheddon/y11-s | 0.467 | 0.358 | 0.131 | 0.456 | 0.919 | 0.640 | 0.667 | 0.766 | 0.700 | 0.625 | 0.665 | 0.650 | 0.500 | 0.667 | 0.593 | 0.625 | 0.402 |
| armaggheddon/y26-m (21.8M) | 0.567 | 0.431 | 0.160 | 0.417 | 0.930 | 0.707 | 0.733 | 0.867 | 1.000 | 0.750 | 0.594 | 0.642 | 0.417 | 0.833 | 0.862 | 0.792 | 0.569 |
| armaggheddon/y26-n (2.6M) | 0.567 | 0.558 | 0.235 | 0.544 | 0.939 | 0.798 | 0.767 | 0.882 | 0.900 | 0.750 | 0.642 | 0.459 | 0.417 | 0.833 | 0.612 | 0.458 | 0.794 |
| armaggheddon/y26-s | 0.200 | 0.467 | 0.122 | 0.300 | 0.930 | 0.676 | 0.600 | 0.784 | 0.900 | 0.750 | 0.539 | 0.363 | 0.500 | 0.833 | 0.530 | 0.333 | 0.372 |
| docling-layout-heron-101 (default) | 1.000 | 0.975 | 0.957 | 0.983 | 0.965 | 0.942 | 1.000 | 1.000 | 1.000 | 1.000 | 0.967 | 1.000 | 0.875 | 1.000 | 0.981 | 0.833 | 0.882 |
| hantian/v10-b | 0.100 | 0.436 | 0.060 | 0.233 | 0.930 | 0.773 | 0.750 | 0.805 | 0.900 | 0.750 | 0.528 | 0.448 | 0.458 | 1.000 | 0.535 | 0.500 | 0.314 |
| hantian/v10-l | 0.267 | 0.300 | 0.144 | 0.267 | 0.930 | 0.794 | 0.767 | 0.721 | 1.000 | 1.000 | 0.608 | 0.575 | 0.433 | 1.000 | 0.747 | 0.792 | 0.343 |
| hantian/v10-m | 0.267 | 0.247 | 0.056 | 0.289 | 0.930 | 0.721 | 0.750 | 0.805 | 0.990 | 1.000 | 0.621 | 0.449 | 0.517 | 1.000 | 0.804 | 0.708 | 0.676 |
| hantian/v10-n | 0.400 | 0.294 | 0.005 | 0.167 | 0.793 | 0.601 | 0.700 | 0.729 | 0.800 | 0.750 | 0.640 | 0.506 | 0.375 | 0.667 | 0.804 | 0.375 | 0.706 |
| hantian/v10-s | 0.400 | 0.250 | 0.056 | 0.233 | 0.909 | 0.726 | 0.800 | 0.721 | 0.800 | 0.750 | 0.594 | 0.550 | 0.542 | 1.000 | 0.612 | 0.375 | 0.510 |
| hantian/v11-l | 0.100 | 0.403 | 0.199 | 0.300 | 0.930 | 0.763 | 0.717 | 0.784 | 0.990 | 0.750 | 0.589 | 0.509 | 0.417 | 1.000 | 0.593 | 0.708 | 0.676 |
| hantian/v11-m (21.8M) | 0.400 | 0.181 | 0.166 | 0.339 | 0.939 | 0.669 | 0.750 | 0.729 | 0.890 | 0.750 | 0.650 | 0.631 | 0.433 | 1.000 | 0.824 | 0.792 | 0.343 |
| hantian/v11-n (2.6M) | 0.400 | 0.472 | 0.144 | 0.383 | 0.814 | 0.629 | 0.767 | 0.729 | 0.700 | 0.750 | 0.611 | 0.570 | 0.458 | 0.667 | 0.804 | 0.208 | 0.676 |
| hantian/v11-s | 0.333 | 0.464 | 0.112 | 0.233 | 0.762 | 0.638 | 0.733 | 0.659 | 0.800 | 0.750 | 0.604 | 0.527 | 0.492 | 1.000 | 0.593 | 0.542 | 0.372 |
| hantian/v12-l | 0.300 | 0.536 | 0.102 | 0.300 | 0.930 | 0.789 | 0.850 | 0.784 | 0.900 | 0.750 | 0.638 | 0.687 | 0.342 | 1.000 | 0.554 | 0.625 | 0.618 |
| hantian/v12-m | 0.633 | 0.453 | 0.197 | 0.550 | 0.919 | 0.581 | 0.733 | 0.867 | 1.000 | 0.750 | 0.658 | 0.527 | 0.425 | 1.000 | 0.516 | 0.375 | 0.480 |
| hantian/v12-n | 0.633 | 0.375 | 0.088 | 0.361 | 0.919 | 0.731 | 0.900 | 0.721 | 0.800 | 0.750 | 0.713 | 0.392 | 0.500 | 1.000 | 0.824 | 0.500 | 0.676 |
| hantian/v12-s | 0.700 | 0.250 | 0.198 | 0.617 | 0.930 | 0.661 | 0.900 | 0.805 | 1.000 | 0.750 | 0.604 | 0.536 | 0.467 | 1.000 | 0.612 | 0.375 | 0.706 |
| hantian/v8-l | 0.500 | 0.283 | 0.191 | 0.200 | 0.805 | 0.641 | 0.633 | 0.784 | 0.990 | 1.000 | 0.629 | 0.564 | 0.475 | 0.667 | 0.535 | 0.625 | 0.676 |
| hantian/v8-m | 0.300 | 0.467 | 0.159 | 0.167 | 0.794 | 0.627 | 0.767 | 0.721 | 0.790 | 1.000 | 0.612 | 0.522 | 0.475 | 1.000 | 0.804 | 0.875 | 0.284 |
| hantian/v8-n | 0.500 | 0.472 | 0.120 | 0.250 | 0.939 | 0.734 | 0.833 | 0.729 | 0.800 | 0.750 | 0.554 | 0.653 | 0.633 | 0.667 | 0.728 | 0.333 | 0.706 |
| hantian/v8-s | 0.500 | 0.489 | 0.136 | 0.133 | 0.814 | 0.642 | 0.750 | 0.833 | 0.500 | 0.750 | 0.612 | 0.544 | 0.392 | 0.667 | 0.824 | 0.500 | 0.647 |
| hantian/v8-x | 0.500 | 0.467 | 0.061 | 0.300 | 0.814 | 0.630 | 0.700 | 0.721 | 0.900 | 1.000 | 0.696 | 0.506 | 0.533 | 0.667 | 0.593 | 0.750 | 0.676 |
| hantian/y26-l | 0.233 | 0.369 | 0.102 | 0.233 | 0.805 | 0.722 | 0.700 | 0.791 | 0.900 | 1.000 | 0.592 | 0.396 | 0.533 | 1.000 | 0.497 | 0.500 | 0.706 |
| hantian/y26-m | 0.467 | 0.500 | 0.167 | 0.083 | 0.784 | 0.652 | 0.833 | 0.791 | 0.890 | 1.000 | 0.592 | 0.368 | 0.433 | 1.000 | 0.747 | 0.250 | 0.676 |
| hantian/y26-n | 0.600 | 0.319 | 0.051 | 0.306 | 0.822 | 0.681 | 0.750 | 0.826 | 0.800 | 0.625 | 0.550 | 0.465 | 0.558 | 0.667 | 0.843 | 0.375 | 0.372 |
| hantian/y26-s | 0.500 | 0.208 | 0.171 | 0.300 | 0.814 | 0.673 | 0.767 | 0.867 | 1.000 | 0.750 | 0.543 | 0.521 | 0.392 | 1.000 | 0.530 | 0.250 | 0.372 |
| omoured/v10-b (20.5M) | 0.100 | 0.208 | 0.042 | 0.100 | 0.759 | 0.659 | 0.517 | 0.802 | 0.800 | 0.750 | 0.546 | 0.300 | 0.321 | 0.389 | 0.766 | 0.375 | 0.255 |
| omoured/v10-l | 0.100 | 0.139 | 0.111 | 0.067 | 0.669 | 0.617 | 0.433 | 0.699 | 0.600 | 0.667 | 0.449 | 0.342 | 0.292 | 0.556 | 0.708 | 0.125 | 0.480 |
| omoured/v10-m | 0.000 | 0.208 | 0.125 | 0.033 | 0.775 | 0.619 | 0.467 | 0.721 | 0.800 | 0.750 | 0.574 | 0.190 | 0.350 | 0.333 | 0.708 | 0.583 | 0.451 |
| omoured/v10-n | 0.367 | 0.369 | 0.097 | 0.283 | 0.803 | 0.684 | 0.700 | 0.867 | 0.800 | 1.000 | 0.536 | 0.450 | 0.375 | 0.667 | 0.704 | 0.250 | 0.422 |
| omoured/v10-s | 0.300 | 0.297 | 0.083 | 0.067 | 0.900 | 0.689 | 0.700 | 0.805 | 0.600 | 0.750 | 0.596 | 0.377 | 0.250 | 0.667 | 0.458 | 0.125 | 0.510 |
| omoured/v10-x (31.7M) | 0.400 | 0.417 | 0.102 | 0.133 | 0.747 | 0.664 | 0.600 | 0.867 | 0.890 | 0.750 | 0.600 | 0.411 | 0.375 | 1.000 | 0.728 | 0.375 | 0.647 |
| omoured/v11-l | 0.100 | 0.264 | 0.019 | 0.083 | 0.820 | 0.545 | 0.383 | 0.714 | 0.700 | 0.250 | 0.517 | 0.208 | 0.125 | 1.000 | 0.708 | 0.500 | 0.333 |
| omoured/v11-m | 0.167 | 0.233 | 0.083 | 0.089 | 0.599 | 0.727 | 0.583 | 0.791 | 0.800 | 0.458 | 0.565 | 0.188 | 0.333 | 0.889 | 0.750 | 0.333 | 0.333 |
| omoured/v11-n | 0.300 | 0.189 | 0.032 | 0.200 | 0.899 | 0.662 | 0.550 | 0.902 | 0.700 | 0.750 | 0.493 | 0.531 | 0.392 | 0.667 | 0.646 | 0.458 | 0.118 |
| omoured/v11-s | 0.300 | 0.181 | 0.097 | 0.067 | 0.600 | 0.695 | 0.733 | 0.714 | 0.800 | 0.625 | 0.456 | 0.325 | 0.333 | 0.667 | 0.728 | 0.500 | 0.480 |
| omoured/v11-x | 0.100 | 0.208 | 0.139 | 0.067 | 0.704 | 0.607 | 0.433 | 0.677 | 0.890 | 0.375 | 0.232 | 0.219 | 0.226 | 0.722 | 0.750 | 0.125 | 0.196 |
| pp-doclayoutv3 (130M) | 0.800 | 0.607 | 0.726 | 0.717 | 0.847 | 0.866 | 0.958 | 1.000 | 0.992 | 0.700 | 0.910 | 0.742 | 0.777 | 1.000 | 0.915 | 0.700 | 0.490 |
| pp_structurev3 (default) | 0.800 | 0.405 | 0.613 | 0.639 | 0.847 | 0.809 | 0.958 | 1.000 | 0.817 | 0.700 | 0.875 | 0.647 | 0.777 | 1.000 | 0.890 | 0.700 | 0.471 |

