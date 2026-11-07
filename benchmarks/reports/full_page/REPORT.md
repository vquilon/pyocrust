# Reporte por feature: `full_page`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_full_page` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/full_page/2026-11-06_23-31-43` · **fecha**: `2026-11-06_23-31-43`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparativa (media por motor)

| Motor (variante) | n | Markdown F1 ↑ | F1 bloques ↑ | CER ↓ | ms/página ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | **0.231** | 0.000 | **0.996** | **1547** |
| pp_structurev3 (default) | 20 | 0.211 | **0.849** | 3.743 | 10033 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `full_page`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `pdf_extract_kit` — pip install pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; pesos en cache HF, adaptador pendiente)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.231 | 0.242 | 1547 | 10503 | directml |
| pp_structurev3 (default) | 0.211 | 0.210 | 10033 | 17198 | directml |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

