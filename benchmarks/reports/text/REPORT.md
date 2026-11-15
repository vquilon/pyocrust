# Reporte por feature: `text`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/text/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `funsd` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/text/2026-11-15_12-06-10` · **fecha**: `2026-11-15_12-06-10`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | box recall ↑ | IoU medio ↑ | ms/img ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-OCRv6 (medium) | 20 | 0.796 | 0.266 | 0.473 | 0.644 | 0.039 | 0.115 | 19163 |
| easyocr (default) | 20 | 0.401 | 0.693 | 0.527 | 0.798 | **0.068** | **0.156** | 3167 |
| pp_ocrv6 (medium) | 20 | **0.800** | **0.260** | **0.472** | **0.643** | 0.042 | 0.116 | 2223 |
| pp_ocrv6 (small) | 20 | 0.784 | 0.280 | 0.472 | 0.650 | 0.042 | 0.117 | 866 |
| pp_ocrv6 (tiny) | 20 | 0.717 | 0.360 | 0.483 | 0.675 | 0.047 | 0.120 | **336** |
| rapidocr (default) | 20 | 0.585 | 0.512 | 0.476 | 0.701 | 0.037 | 0.108 | 4286 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `text`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `tesseract` — pip install pytesseract + binario Tesseract

## Procedencia de las alternativas

- `PP-OCRv6 (medium)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Word F1 ↑ (CPU) | Word F1 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| PP-OCRv6 (medium) | 0.796 | N/A | 19163 | N/A | n/a (no corre en GPU) |
| easyocr (default) | 0.401 | 0.399 | 3167 | 1263 | cuda |
| pp_ocrv6 (medium) | 0.800 | N/A | 2223 | N/A | n/a (no corre en GPU) |
| pp_ocrv6 (small) | 0.784 | N/A | 866 | N/A | n/a (no corre en GPU) |
| pp_ocrv6 (tiny) | 0.717 | 0.684 | 336 | 330 | cuda |
| rapidocr (default) | 0.585 | 0.585 | 4286 | 5842 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

