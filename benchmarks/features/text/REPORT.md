# Reporte por feature: `text`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/text/bank.py --limit 5 --backends pyocrust,rapidocr,easyocr --device cpu`
- **dataset**: `funsd` · **n** (por motor): `5` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/text/2026-11-02_17-46-20` · **fecha**: `2026-11-02_17-46-20`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | box recall ↑ | IoU medio ↑ | ms/img ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 5 | 0.384 | 0.709 | 0.467 | 0.789 | **0.056** | **0.155** | 3915 |
| pyocrust (tiny) | 5 | **0.734** | **0.340** | 0.402 | **0.628** | 0.042 | 0.116 | **786** |
| rapidocr (default) | 5 | 0.659 | 0.431 | **0.402** | 0.654 | 0.040 | 0.107 | 6733 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `text`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | F1 palabra ↑ (CPU) | F1 palabra ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| easyocr (default) | 0.384 | N/A | 3915 | N/A | n/a (no corre en GPU) |
| pyocrust (tiny) | 0.734 | 0.715 | 786 | 1161 | directml |
| rapidocr (default) | 0.659 | N/A | 6733 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

