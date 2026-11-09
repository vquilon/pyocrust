# Reporte por feature: `rectification`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/rectification/bank.py --limit 20 --device cpu`
- **dataset**: `synthetic_rectification` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/rectification/2026-11-08_19-53-54` · **fecha**: `2026-11-08_19-53-54`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparativa (media por motor)

| Motor (variante) | n | SSIM ↑ | ms/página ↓ |
| :--- | ---: | ---: | ---: |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 20 | 0.491 | **11** |
| uvdoc (31.7M) | 20 | 0.597 | 297 |
| uvdoc (onnxruntime) | 20 | **0.604** | 78 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `rectification`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `perspective-4corner (baseline (OpenCV, sin pesos))` — **línea base clásica** sin pesos (no es un modelo aprendido ni un SOTA: suelo de comparación)
- `uvdoc (onnxruntime)` — **mismo peso, distinta vía** (el MISMO `.onnx` de PaddleOCR por otro runtime — NO es un modelo distinto)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | SSIM ↑ (CPU) | SSIM ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| perspective-4corner (baseline (OpenCV, sin pesos)) | 0.491 | N/A | 11 | N/A | n/a (no corre en GPU) |
| uvdoc (31.7M) | 0.597 | 0.597 | 297 | 298 | directml |
| uvdoc (onnxruntime) | 0.604 | N/A | 78 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

