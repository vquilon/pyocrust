# Reporte por feature: `layout`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/layout/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_layout` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/layout/2026-11-06_23-00-51` · **fecha**: `2026-11-06_23-00-51`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparativa (media por motor)

| Motor (variante) | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | ---: | ---: | ---: | ---: |
| docling_heron_101 (default) | 20 | **0.843** | **0.992** | 1071 |
| pyocrust_layout (130M) | 20 | 0.827 | 0.863 | 1987 |
| yolo26m (21.8M) | 20 | 0.467 | 0.517 | **294** |
| yolov10b (20.5M) | 20 | 0.344 | 0.390 | 383 |
| yolov10x (31.7M) | 20 | 0.381 | 0.438 | 658 |

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
| docling_heron_101 (default) | 0.843 | N/A | 1071 | N/A | n/a (no corre en GPU) |
| pyocrust_layout (130M) | 0.827 | N/A | 1987 | N/A | n/a (no corre en GPU) |
| yolo26m (21.8M) | 0.467 | 0.467 | 294 | 44 | cuda |
| yolov10b (20.5M) | 0.344 | 0.344 | 383 | 33 | cuda |
| yolov10x (31.7M) | 0.381 | 0.381 | 658 | 44 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

