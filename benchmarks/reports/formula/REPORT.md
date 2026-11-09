# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/formula/bank.py --limit 10 --device cpu --output-dir results`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `10` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-09_14-13-57` · **fecha**: `2026-11-09_14-13-57`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 10 | 0.000 | 0.326 | 0.575 | N/A | **141** |
| paddle_latex_ocr (default) | 10 | 0.000 | **0.653** | **0.799** | N/A | 16326 |
| pix2tex (default) | 10 | 0.000 | 0.552 | 0.777 | N/A | 5500 |
| pp-formulanet-s (direct) | 10 | 0.000 | 0.499 | 0.652 | N/A | 998 |
| pp_structurev3 (default) | 10 | 0.000 | 0.398 | 0.613 | N/A | 2774 |
| pp_structurev3 (pp-formulanet-s) | 10 | 0.000 | 0.497 | 0.708 | N/A | 2474 |
| unimernet (tiny) | 10 | 0.000 | 0.260 | 0.385 | N/A | 17493 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `unimernet (tiny)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.326 | 0.326 | 141 | 460 | cuda |
| paddle_latex_ocr (default) | 0.653 | 0.653 | 16326 | 2763 | cuda |
| pix2tex (default) | 0.552 | N/A | 5500 | N/A | n/a (no corre en GPU) |
| pp-formulanet-s (direct) | 0.499 | N/A | 998 | 1910 | cuda |
| pp_structurev3 (default) | 0.398 | 0.128 | 2774 | 2236 | cuda |
| pp_structurev3 (pp-formulanet-s) | 0.497 | N/A | 2474 | 2254 | cuda |
| unimernet (tiny) | 0.260 | N/A | 17493 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> LaTeX sim **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 7 · estratos cubiertos: 5. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×other_layout` (3), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (2), `academic_literature×other_layout` (1).

### LaTeX sim por estrato

| Motor (variante) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 0.197 | 0.243 | 0.249 | 0.366 | 0.989 |
| paddle_latex_ocr (default) | 0.401 | 0.700 | 0.714 | 0.838 | 0.824 |
| pix2tex (default) | 0.449 | 0.397 | 0.525 | 0.779 | 0.777 |
| pp-formulanet-s (direct) | 0.382 | 0.447 | 0.376 | 0.764 | 0.670 |
| pp_structurev3 (default) | 0.300 | 0.354 | 0.352 | 0.764 | 0.143 |
| pp_structurev3 (pp-formulanet-s) | 0.300 | 0.410 | 0.639 | 0.764 | — |
| unimernet (tiny) | 0.218 | 0.233 | 0.247 | 0.338 | 0.305 |

