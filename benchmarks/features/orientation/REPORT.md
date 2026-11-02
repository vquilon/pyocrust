# Reporte por feature: `orientation`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/orientation/bank.py --limit 8 --backends pyocrust_orientation,lcnet_doc_ori --device cpu`
- **dataset**: `synthetic_orientation` · **n** (por motor): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/orientation/2026-11-02_17-50-19` · **fecha**: `2026-11-02_17-50-19`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | accuracy ↑ | ms/página ↓ |
| :--- | ---: | ---: | ---: |
| lcnet_doc_ori (onnxruntime) | 8 | 100.0% | **4** |
| pyocrust_orientation (6.8M) | 8 | 100.0% | 702 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `orientation`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | accuracy ↑ (CPU) | accuracy ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| lcnet_doc_ori (onnxruntime) | 1.000 | N/A | 4 | N/A | n/a (no corre en GPU) |
| pyocrust_orientation (6.8M) | 1.000 | 1.000 | 702 | 720 | directml |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

