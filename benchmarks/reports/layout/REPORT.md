# Reporte por feature: `layout`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/layout/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `omnidocbench_layout` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/layout/2026-11-07_17-43-49` · **fecha**: `2026-11-07_17-43-49`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | ---: | ---: | ---: | ---: |
| armaggheddon/y11-m | 20 | 0.479 | 0.518 | 433 |
| armaggheddon/y11-n | 20 | 0.426 | 0.481 | 69 |
| armaggheddon/y11-s | 20 | 0.422 | 0.471 | 126 |
| armaggheddon/y26-m (21.8M) | 20 | 0.467 | 0.517 | 329 |
| armaggheddon/y26-n (2.6M) | 20 | 0.460 | 0.511 | 89 |
| armaggheddon/y26-s | 20 | 0.400 | 0.476 | 139 |
| docling-layout-heron-101 (default) | 20 | **0.843** | **0.992** | 1575 |
| hantian/v10-b | 20 | 0.459 | 0.511 | 433 |
| hantian/v10-l | 20 | 0.407 | 0.443 | 604 |
| hantian/v10-m | 20 | 0.499 | 0.580 | 274 |
| hantian/v10-n | 20 | 0.405 | 0.462 | 67 |
| hantian/v10-s | 20 | 0.385 | 0.451 | 154 |
| hantian/v11-l | 20 | 0.420 | 0.468 | 375 |
| hantian/v11-m (21.8M) | 20 | 0.427 | 0.480 | 411 |
| hantian/v11-n (2.6M) | 20 | 0.402 | 0.476 | 68 |
| hantian/v11-s | 20 | 0.429 | 0.482 | 145 |
| hantian/v12-l | 20 | 0.487 | 0.535 | 600 |
| hantian/v12-m | 20 | 0.458 | 0.537 | 412 |
| hantian/v12-n | 20 | 0.477 | 0.530 | 107 |
| hantian/v12-s | 20 | 0.494 | 0.576 | 197 |
| hantian/v8-l | 20 | 0.414 | 0.484 | 763 |
| hantian/v8-m | 20 | 0.385 | 0.437 | 390 |
| hantian/v8-n | 20 | 0.508 | 0.558 | 84 |
| hantian/v8-s | 20 | 0.415 | 0.492 | 160 |
| hantian/v8-x | 20 | 0.497 | 0.566 | 1147 |
| hantian/y26-l | 20 | 0.410 | 0.469 | 431 |
| hantian/y26-m | 20 | 0.394 | 0.451 | 411 |
| hantian/y26-n | 20 | 0.445 | 0.518 | 81 |
| hantian/y26-s | 20 | 0.471 | 0.524 | 128 |
| omoured/v10-b (20.5M) | 20 | 0.344 | 0.390 | 472 |
| omoured/v10-l | 20 | 0.325 | 0.393 | 576 |
| omoured/v10-m | 20 | 0.354 | 0.394 | 285 |
| omoured/v10-n | 20 | 0.437 | 0.506 | 70 |
| omoured/v10-s | 20 | 0.315 | 0.378 | 266 |
| omoured/v10-x (31.7M) | 20 | 0.381 | 0.438 | 741 |
| omoured/v11-l | 20 | 0.231 | 0.257 | 477 |
| omoured/v11-m | 20 | 0.288 | 0.331 | 325 |
| omoured/v11-n | 20 | 0.411 | 0.460 | **66** |
| omoured/v11-s | 20 | 0.379 | 0.442 | 179 |
| omoured/v11-x | 20 | 0.252 | 0.284 | 1000 |
| pp-doclayoutv3 (130M) | 20 | 0.827 | 0.863 | 776 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `layout`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `deformable_detr` — pesos de Aryn/deformable-detr-DocLayNet no estan en la cache HF local (OSError: Can't load image processor for 'Aryn/deformable-detr-DocLayNet'. If you were trying to load it from 'https://huggingface.co/models', make sure you don't have a local directory with the same name. Otherwise, make sure 'Aryn/deformable-detr-DocLayNet' is the correct path to a directory containing a preprocessor_config.json file)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | mAP@IoU 0.5 ↑ (CPU) | mAP@IoU 0.5 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| armaggheddon/y11-m | 0.479 | 0.479 | 433 | 40 | cuda |
| armaggheddon/y11-n | 0.426 | 0.426 | 69 | 35 | cuda |
| armaggheddon/y11-s | 0.422 | 0.422 | 126 | 33 | cuda |
| armaggheddon/y26-m (21.8M) | 0.467 | 0.467 | 329 | 38 | cuda |
| armaggheddon/y26-n (2.6M) | 0.460 | 0.460 | 89 | 31 | cuda |
| armaggheddon/y26-s | 0.400 | 0.400 | 139 | 33 | cuda |
| docling-layout-heron-101 (default) | 0.843 | N/A | 1575 | N/A | n/a (no corre en GPU) |
| hantian/v10-b | 0.459 | 0.459 | 433 | 40 | cuda |
| hantian/v10-l | 0.407 | 0.407 | 604 | 44 | cuda |
| hantian/v10-m | 0.499 | 0.499 | 274 | 43 | cuda |
| hantian/v10-n | 0.405 | 0.405 | 67 | 38 | cuda |
| hantian/v10-s | 0.385 | 0.385 | 154 | 36 | cuda |
| hantian/v11-l | 0.420 | 0.420 | 375 | 42 | cuda |
| hantian/v11-m (21.8M) | 0.427 | 0.427 | 411 | 38 | cuda |
| hantian/v11-n (2.6M) | 0.402 | 0.402 | 68 | 31 | cuda |
| hantian/v11-s | 0.429 | 0.429 | 145 | 32 | cuda |
| hantian/v12-l | 0.487 | 0.487 | 600 | 56 | cuda |
| hantian/v12-m | 0.458 | 0.458 | 412 | 42 | cuda |
| hantian/v12-n | 0.477 | 0.477 | 107 | 36 | cuda |
| hantian/v12-s | 0.494 | 0.494 | 197 | 39 | cuda |
| hantian/v8-l | 0.414 | 0.414 | 763 | 40 | cuda |
| hantian/v8-m | 0.385 | 0.385 | 390 | 35 | cuda |
| hantian/v8-n | 0.508 | 0.508 | 84 | 29 | cuda |
| hantian/v8-s | 0.415 | 0.415 | 160 | 31 | cuda |
| hantian/v8-x | 0.497 | 0.497 | 1147 | 52 | cuda |
| hantian/y26-l | 0.410 | 0.410 | 431 | 42 | cuda |
| hantian/y26-m | 0.394 | 0.394 | 411 | 35 | cuda |
| hantian/y26-n | 0.445 | 0.445 | 81 | 35 | cuda |
| hantian/y26-s | 0.471 | 0.471 | 128 | 30 | cuda |
| omoured/v10-b (20.5M) | 0.344 | 0.344 | 472 | 39 | cuda |
| omoured/v10-l | 0.325 | 0.325 | 576 | 38 | cuda |
| omoured/v10-m | 0.354 | 0.355 | 285 | 32 | cuda |
| omoured/v10-n | 0.437 | 0.437 | 70 | 29 | cuda |
| omoured/v10-s | 0.315 | 0.315 | 266 | 37 | cuda |
| omoured/v10-x (31.7M) | 0.381 | 0.381 | 741 | 50 | cuda |
| omoured/v11-l | 0.231 | 0.231 | 477 | 39 | cuda |
| omoured/v11-m | 0.288 | 0.288 | 325 | 35 | cuda |
| omoured/v11-n | 0.411 | 0.411 | 66 | 30 | cuda |
| omoured/v11-s | 0.379 | 0.379 | 179 | 31 | cuda |
| omoured/v11-x | 0.252 | 0.252 | 1000 | 56 | cuda |
| pp-doclayoutv3 (130M) | 0.827 | 0.827 | 776 | 434 | directml |
| yolo26m (doc-layout) (21.8M) | N/A | 0.467 | N/A | 44 | cuda |
| yolov10b (DocLayNet) (20.5M) | N/A | 0.344 | N/A | 33 | cuda |
| yolov10x (DocLayNet) (31.7M) | N/A | 0.381 | N/A | 44 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

