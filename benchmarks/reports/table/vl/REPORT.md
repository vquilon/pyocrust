# Reporte por feature: `table`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --variant vl --limit 8 --device gpu --output-dir results/_gpu --backends glm_ocr,paddleocr_vl,lightonocr,lightonocr3_08b,lightonocr3_4b`
- **dataset**: `omnidocbench_table` · **n** (por motor): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `gpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/_gpu/table/vl/2026-11-15_18-13-46` · **fecha**: `2026-11-15_18-13-46`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | TEDS estrut. ↑ | ms/tabla ↓ |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 8 | 0.919 | **34191** |
| LightOnOCR-2-1B (1B) | 8 | 0.858 | 58834 |
| LightOnOCR-3 (0.8B) | 8 | 0.926 | 162056 |
| LightOnOCR-3 (4B) | 8 | 0.847 | 76940 |
| PaddleOCR-VL (0.9B) | 8 | **0.933** | 35839 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `table`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `GLM-OCR (0.9B)` — modelo **independiente** (otro proyecto/checkpoint)
- `LightOnOCR-2-1B (1B)` — modelo **independiente** (otro proyecto/checkpoint)
- `LightOnOCR-3 (0.8B)` — modelo **independiente** (otro proyecto/checkpoint)
- `LightOnOCR-3 (4B)` — modelo **independiente** (otro proyecto/checkpoint)
- `PaddleOCR-VL (0.9B)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=gpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | 0.919 | 0.919 | 34191 | 34191 | n/a |
| LightOnOCR-2-1B (1B) | 0.858 | 0.858 | 58834 | 58834 | n/a |
| LightOnOCR-3 (0.8B) | 0.926 | 0.926 | 162056 | 162056 | n/a |
| LightOnOCR-3 (4B) | 0.847 | 0.847 | 76940 | 76940 | n/a |
| PaddleOCR-VL (0.9B) | 0.933 | 0.933 | 35839 | 35839 | n/a |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> TEDS tabla **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 5 · estratos cubiertos: 6. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (2).

### TEDS tabla por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | — | 1.000 | 1.000 | 0.757 | 1.000 | 1.000 |
| LightOnOCR-2-1B (1B) | 0.985 | 0.990 | 0.986 | 0.750 | 0.567 | 0.980 |
| LightOnOCR-3 (0.8B) | 1.000 | 1.000 | 1.000 | 0.750 | 0.973 | 0.967 |
| LightOnOCR-3 (4B) | 0.985 | 1.000 | 1.000 | 0.674 | 0.514 | 0.967 |
| PaddleOCR-VL (0.9B) | 1.000 | 0.979 | 1.000 | 0.833 | 0.851 | — |

## Por tipología de página (`digital` / `escaneada` / `manuscrita`)

> TEDS tabla **por motor y tipología de página**. La tipología se deriva de `page_info.page_attribute` de OmniDocBench: `manuscrita` = `handwriting` en `special_issue` o `data_source=note`; `escaneada` = `fuzzy_scan` en `special_issue` o `data_source=historical_document`; `digital` = el resto. OmniDocBench **no** anota un tipo de adquisición explícito: la clasificación es una derivación declarada, no una etiqueta original. Motores medidos: 5. `N/A` = sin páginas medidas de esa tipología (nunca `0.0`); `—` = el motor no tiene medición sobre esas páginas.

> **Páginas por tipología en la muestra**: `digital` (8), `escaneada` (0), `manuscrita` (0).

> **Sin datos** para `escaneada`, `manuscrita` en la muestra de esta feature (columna `N/A`): el muestreo no incluyó páginas de esa tipología, así que no se inventa la fila.

| Motor (variante) | digital | escaneada | manuscrita |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.919 (n=8) | N/A | N/A |
| LightOnOCR-2-1B (1B) | 0.858 (n=8) | N/A | N/A |
| LightOnOCR-3 (0.8B) | 0.926 (n=8) | N/A | N/A |
| LightOnOCR-3 (4B) | 0.847 (n=8) | N/A | N/A |
| PaddleOCR-VL (0.9B) | 0.933 (n=8) | N/A | N/A |

