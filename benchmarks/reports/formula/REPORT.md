# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-09_10-37-15` · **fecha**: `2026-11-09_10-37-15`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.211 | 0.437 | N/A | **146** |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.715** | **0.829** | N/A | 3734 |
| pix2tex (default) | 20 | 0.000 | 0.587 | 0.757 | N/A | 5764 |
| pp-formulanet-s (direct) | 20 | 0.000 | 0.576 | 0.701 | N/A | 854 |
| pp_structurev3 (default) | 20 | 0.000 | 0.399 | 0.560 | N/A | 2193 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | 0.607 | 0.746 | N/A | 2247 |
| unimernet (tiny) | 20 | 0.000 | 0.238 | 0.376 | N/A | 18685 |

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
| indra (math) | 0.211 | 0.211 | 146 | 2813 | directml |
| paddle_latex_ocr (default) | 0.715 | 0.715 | 3734 | 1016 | cuda |
| pix2tex (default) | 0.587 | N/A | 5764 | N/A | n/a (no corre en GPU) |
| pp-formulanet-s (direct) | 0.576 | 0.576 | 854 | 1903 | directml |
| pp_structurev3 (default) | 0.399 | 0.400 | 2193 | 2781 | directml |
| pp_structurev3 (pp-formulanet-s) | 0.607 | 0.607 | 2247 | 3485 | directml |
| unimernet (tiny) | 0.238 | N/A | 18685 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> LaTeX sim **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 7 · estratos cubiertos: 12. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×other_layout` (2), `PPT2PDF×single_column` (1), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (1), `academic_literature×single_column` (3), `book×other_layout` (3), `book×single_column` (2), `colorful_textbook×double_column` (1), `colorful_textbook×other_layout` (1), `exam_paper×double_column` (2), `exam_paper×other_layout` (1), `note×single_column` (1).

### LaTeX sim por estrato

| Motor (variante) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×single_column | book×other_layout | book×single_column | colorful_textbook×double_column | colorful_textbook×other_layout | exam_paper×double_column | exam_paper×other_layout | note×single_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 0.169 | 0.262 | 0.249 | — | 0.377 | 0.167 | 0.288 | 0.288 | 0.054 | 0.110 | 0.070 | 0.185 |
| paddle_latex_ocr (default) | 0.748 | 0.684 | 0.714 | 0.835 | 0.764 | 0.710 | 0.721 | 0.514 | 0.168 | 0.843 | 1.000 | 0.632 |
| pix2tex (default) | 0.723 | 0.643 | 0.484 | 0.720 | 0.638 | 0.516 | 0.677 | 0.810 | 0.314 | 0.791 | 0.233 | 0.207 |
| pp-formulanet-s (direct) | 0.533 | 0.684 | 0.376 | 0.667 | 0.696 | 0.587 | 0.478 | 0.545 | 0.206 | 0.653 | 0.605 | 0.889 |
| pp_structurev3 (default) | 0.279 | 0.410 | 0.352 | 0.667 | 0.615 | 0.514 | 0.350 | 0.308 | 0.149 | 0.486 | 0.093 | 0.259 |
| pp_structurev3 (pp-formulanet-s) | 0.210 | 0.410 | 0.639 | 0.667 | 0.798 | 0.690 | 0.492 | — | — | 0.870 | — | — |
| unimernet (tiny) | 0.137 | 0.328 | 0.247 | 0.432 | 0.262 | 0.275 | 0.218 | 0.187 | 0.235 | 0.245 | 0.161 | 0.105 |

