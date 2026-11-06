# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 20 --device cpu`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-06_22-42-36` · **fecha**: `2026-11-06_22-42-36`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.694** | **0.839** | N/A | 12490 |
| pix2tex (default) | 20 | 0.000 | 0.486 | 0.682 | N/A | 7484 |
| pyocrust_formula (pp-formulanet-s) | 20 | 0.000 | 0.196 | 0.295 | N/A | 3464 |
| pyocrust_formulanet (direct) | 20 | 0.000 | 0.497 | 0.622 | N/A | **979** |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `img2latex` — pip install img2latex
- `nougat` — pip install nougat-ocr
- `pix2text` — pip install pix2text (no forzado: degrada transformers/huggingface_hub y cambia opencv-python-headless→opencv-python)
- `pyocrust_indra` — PyOcrValueError: El preset 'indra': license OpenRAIL-M-Mod. To use it you must pass license_commercial_use=False (non-commercial use) AND license_acknowledge=True (accept attribution) (conditions are cumulative).. Notes: OpenRAIL-M modified by Datalab (pinned revision): §7 attribution, §8 share-alike on the Output, §4 SaaS/API hosting counts as distribution and the restrictions must be passed on; §5 / Attachment A §2 forbids use above USD 20M revenue or funding and competing with any Licensor product or service, with personal/research exceptions.
- `texify` — pip install texify
- `texteller` — pip install texteller
- `unimernet` — pip install unimernet (github.com/opendatalab/UniMERNet)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Similitud LaTeX ↑ (CPU) | Similitud LaTeX ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| paddle_latex_ocr (default) | 0.694 | 0.694 | 12490 | 1187 | cuda |
| pix2tex (default) | 0.486 | N/A | 7484 | N/A | n/a (no corre en GPU) |
| pyocrust_formula (pp-formulanet-s) | 0.196 | N/A | 3464 | N/A | n/a (no corre en GPU) |
| pyocrust_formulanet (direct) | 0.497 | N/A | 979 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

