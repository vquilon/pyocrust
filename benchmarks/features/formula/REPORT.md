# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 5 --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr --device cpu`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `5` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-02_17-47-46` · **fecha**: `2026-11-02_17-47-46`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 5 | 0.000 | 0.152 | 0.427 | N/A | **743** |
| pix2tex (default) | 5 | 0.000 | 0.486 | **0.670** | N/A | 2451 |
| pyocrust_formula (pp-formulanet-s) | 5 | 0.000 | 0.419 | 0.526 | N/A | 2795 |
| pyocrust_formulanet (direct) | 5 | 0.000 | **0.550** | 0.627 | N/A | 1015 |
| rapidocr (default) | 5 | 0.000 | 0.104 | 0.298 | N/A | 3026 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Similitud LaTeX ↑ (CPU) | Similitud LaTeX ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| easyocr (default) | 0.152 | N/A | 743 | N/A | n/a (no corre en GPU) |
| pix2tex (default) | 0.486 | N/A | 2451 | N/A | n/a (no corre en GPU) |
| pyocrust_formula (pp-formulanet-s) | 0.419 | 0.419 | 2795 | 4983 | directml |
| pyocrust_formulanet (direct) | 0.550 | 0.550 | 1015 | 2600 | directml |
| rapidocr (default) | 0.104 | N/A | 3026 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

