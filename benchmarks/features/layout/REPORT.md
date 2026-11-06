# Reporte por feature: `layout`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/layout/bank.py --limit 8`
- **dataset**: `omnidocbench_layout` · **n** (por motor): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/layout/2026-11-02_19-50-24` · **fecha**: `2026-11-02_19-50-24`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | ---: | ---: | ---: | ---: |
| docling_heron_101 (default) | 8 | 0.792 | **0.986** | 816 |
| pyocrust_layout (130M) | 8 | **0.811** | 0.851 | 1947 |
| yolo26m (21.8M) | 8 | 0.386 | 0.442 | **331** |
| yolov10b (20.5M) | 8 | 0.290 | 0.338 | 455 |
| yolov10x (31.7M) | 8 | 0.312 | 0.408 | 732 |

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
| docling_heron_101 (default) | 0.792 | N/A | 816 | N/A | n/a (no corre en GPU) |
| pyocrust_layout (130M) | 0.811 | 0.811 | 1947 | 1925 | directml |
| yolo26m (21.8M) | 0.386 | N/A | 331 | N/A | n/a (no corre en GPU) |
| yolov10b (20.5M) | 0.290 | N/A | 455 | N/A | n/a (no corre en GPU) |
| yolov10x (31.7M) | 0.312 | N/A | 732 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

