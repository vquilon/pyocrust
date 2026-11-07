# Benchmark: layout

| Motor (variante/tamaño) | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ | license |
| :--- | ---: | ---: | ---: | ---: | :--- |
| armaggheddon/y11-m | 20 | 0.479 | 0.518 | 433 | MIT |
| armaggheddon/y11-n | 20 | 0.426 | 0.481 | 69 | MIT |
| armaggheddon/y11-s | 20 | 0.422 | 0.471 | 126 | MIT |
| armaggheddon/y26-m (21.8M) | 20 | 0.467 | 0.517 | 329 | MIT |
| armaggheddon/y26-n (2.6M) | 20 | 0.460 | 0.511 | 89 | MIT |
| armaggheddon/y26-s | 20 | 0.400 | 0.476 | 139 | MIT |
| deformable_detr / deformable-detr-DocLayNet (default) | N/A | N/A | N/A | N/A | N/A |
| docling_heron_101 / docling-layout-heron-101 (default) | 20 | **0.843** | **0.992** | 1575 | Apache-2.0 |
| hantian/v10-b | 20 | 0.459 | 0.511 | 433 | AGPL-3.0 |
| hantian/v10-l | 20 | 0.407 | 0.443 | 604 | AGPL-3.0 |
| hantian/v10-m | 20 | 0.499 | 0.580 | 274 | AGPL-3.0 |
| hantian/v10-n | 20 | 0.405 | 0.462 | 67 | AGPL-3.0 |
| hantian/v10-s | 20 | 0.385 | 0.451 | 154 | AGPL-3.0 |
| hantian/v11-l | 20 | 0.420 | 0.468 | 375 | AGPL-3.0 |
| hantian/v11-m (21.8M) | 20 | 0.427 | 0.480 | 411 | AGPL-3.0 |
| hantian/v11-n (2.6M) | 20 | 0.402 | 0.476 | 68 | AGPL-3.0 |
| hantian/v11-s | 20 | 0.429 | 0.482 | 145 | AGPL-3.0 |
| hantian/v12-l | 20 | 0.487 | 0.535 | 600 | AGPL-3.0 |
| hantian/v12-m | 20 | 0.458 | 0.537 | 412 | AGPL-3.0 |
| hantian/v12-n | 20 | 0.477 | 0.530 | 107 | AGPL-3.0 |
| hantian/v12-s | 20 | 0.494 | 0.576 | 197 | AGPL-3.0 |
| hantian/v8-l | 20 | 0.414 | 0.484 | 763 | AGPL-3.0 |
| hantian/v8-m | 20 | 0.385 | 0.437 | 390 | AGPL-3.0 |
| hantian/v8-n | 20 | 0.508 | 0.558 | 84 | AGPL-3.0 |
| hantian/v8-s | 20 | 0.415 | 0.492 | 160 | AGPL-3.0 |
| hantian/v8-x | 20 | 0.497 | 0.566 | 1147 | AGPL-3.0 |
| hantian/y26-l | 20 | 0.410 | 0.469 | 431 | AGPL-3.0 |
| hantian/y26-m | 20 | 0.394 | 0.451 | 411 | AGPL-3.0 |
| hantian/y26-n | 20 | 0.445 | 0.518 | 81 | AGPL-3.0 |
| hantian/y26-s | 20 | 0.471 | 0.524 | 128 | AGPL-3.0 |
| omoured/v10-b (20.5M) | 20 | 0.344 | 0.390 | 472 | AGPL-3.0 |
| omoured/v10-l | 20 | 0.325 | 0.393 | 576 | AGPL-3.0 |
| omoured/v10-m | 20 | 0.354 | 0.394 | 285 | AGPL-3.0 |
| omoured/v10-n | 20 | 0.437 | 0.506 | 70 | AGPL-3.0 |
| omoured/v10-s | 20 | 0.315 | 0.378 | 266 | AGPL-3.0 |
| omoured/v10-x (31.7M) | 20 | 0.381 | 0.438 | 741 | AGPL-3.0 |
| omoured/v11-l | 20 | 0.231 | 0.257 | 477 | AGPL-3.0 |
| omoured/v11-m | 20 | 0.288 | 0.331 | 325 | AGPL-3.0 |
| omoured/v11-n | 20 | 0.411 | 0.460 | **66** | AGPL-3.0 |
| omoured/v11-s | 20 | 0.379 | 0.442 | 179 | AGPL-3.0 |
| omoured/v11-x | 20 | 0.252 | 0.284 | 1000 | AGPL-3.0 |
| pyocrust_layout / pp-doclayoutv3 (130M) | 20 | 0.827 | 0.863 | 776 | Apache-2.0 |

> Métricas copiadas de `REPORT.md` (run CPU `2026-11-07_17-43-49`), con `n=20` por motor. `deformable_detr` quedó `skipped` por falta de pesos y se muestra como `N/A` (nunca `0.0`). Licencias informativas.
