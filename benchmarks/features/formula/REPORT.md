# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 5 --device cpu --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `5` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-02_14-54-49` · **fecha**: `2026-11-02_14-54-49`
- **runtime**: {'python': '3.14.9', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 5 | 0.000 | 0.152 | 0.427 | N/A | **908** |
| pix2tex (default) | 5 | 0.000 | 0.489 | **0.678** | N/A | 2841 |
| pyocrust_formula (pp-formulanet-s) | 5 | 0.000 | 0.419 | 0.526 | N/A | 2938 |
| pyocrust_formulanet (direct) | 5 | 0.000 | **0.550** | 0.627 | N/A | 1049 |
| rapidocr (default) | 5 | 0.000 | 0.104 | 0.298 | N/A | 2813 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

