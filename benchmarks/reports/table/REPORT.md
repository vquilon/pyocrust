# Reporte por feature: `table`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `omnidocbench_table` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/table/2026-11-09_11-00-34` · **fecha**: `2026-11-09_11-00-34`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | TEDS estrut. ↑ | ms/tabla ↓ |
| :--- | ---: | ---: | ---: |
| SLANet_plus (paddleocr) | 20 | **0.828** | **87** |
| pp_structurev3 (default) | 20 | 0.608 | 3245 |
| slanet_plus (default) | 20 | 0.780 | 848 |
| table-transformer-structure-recognition (default) | 20 | 0.698 | 198 |
| tableformer (docling) | 20 | 0.807 | 35699 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `table`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `SLANet_plus (paddleocr)` — modelo **independiente** (otro proyecto/checkpoint)
- `table-transformer-structure-recognition (default)` — modelo **independiente** (otro proyecto/checkpoint)
- `tableformer (docling)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| SLANet_plus (paddleocr) | 0.828 | N/A | 87 | N/A | n/a (no corre en GPU) |
| pp_structurev3 (default) | 0.608 | 0.608 | 3245 | 5429 | directml |
| slanet_plus (default) | 0.780 | 0.780 | 848 | 1023 | directml |
| table-transformer-structure-recognition (default) | 0.698 | N/A | 198 | N/A | n/a (no corre en GPU) |
| tableformer (docling) | 0.807 | N/A | 35699 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

