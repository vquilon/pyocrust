# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/formula/bank.py --variant vl --limit 10 --device gpu --output-dir results/_gpu --backends glm_ocr,paddleocr_vl,lightonocr,lightonocr3_08b,lightonocr3_4b`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `10` · **warmup**: `1` · **repeats**: `1` · **device**: `gpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/_gpu/formula/vl/2026-11-15_19-06-25` · **fecha**: `2026-11-15_19-06-25`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 10 | 0.000 | **0.748** | **0.881** | N/A | 18719 |
| LightOnOCR-2-1B (1B) | 10 | 0.000 | 0.597 | 0.777 | N/A | 20186 |
| LightOnOCR-3 (0.8B) | 10 | 0.000 | 0.550 | 0.749 | N/A | 24073 |
| LightOnOCR-3 (4B) | 10 | 0.000 | 0.612 | 0.780 | N/A | 30950 |
| PaddleOCR-VL (0.9B) | 10 | 0.000 | 0.614 | 0.843 | N/A | **17524** |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

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

| Motor (variante) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | 0.748 | 0.748 | 18719 | 18719 | n/a |
| LightOnOCR-2-1B (1B) | 0.597 | 0.597 | 20186 | 20186 | n/a |
| LightOnOCR-3 (0.8B) | 0.550 | 0.550 | 24073 | 24073 | n/a |
| LightOnOCR-3 (4B) | 0.612 | 0.612 | 30950 | 30950 | n/a |
| PaddleOCR-VL (0.9B) | 0.614 | 0.614 | 17524 | 17524 | n/a |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> LaTeX sim **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 5 · estratos cubiertos: 5. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×other_layout` (3), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (2), `academic_literature×double_column` (2), `academic_literature×other_layout` (1).

### LaTeX sim por estrato

| Motor (variante) | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout |
| :--- | ---: | ---: | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.590 | 0.814 | 0.705 | 0.860 | 0.956 |
| LightOnOCR-2-1B (1B) | 0.517 | 0.823 | 0.544 | 0.526 | 0.637 |
| LightOnOCR-3 (0.8B) | 0.456 | 0.516 | 0.508 | 0.625 | 0.835 |
| LightOnOCR-3 (4B) | 0.481 | 0.738 | 0.598 | 0.643 | 0.725 |
| PaddleOCR-VL (0.9B) | 0.518 | 0.620 | 0.681 | 0.626 | 0.736 |

## Por tipología de página (`digital` / `escaneada` / `manuscrita`)

> LaTeX sim **por motor y tipología de página**. La tipología se deriva de `page_info.page_attribute` de OmniDocBench: `manuscrita` = `handwriting` en `special_issue` o `data_source=note`; `escaneada` = `fuzzy_scan` en `special_issue` o `data_source=historical_document`; `digital` = el resto. OmniDocBench **no** anota un tipo de adquisición explícito: la clasificación es una derivación declarada, no una etiqueta original. Motores medidos: 5. `N/A` = sin páginas medidas de esa tipología (nunca `0.0`); `—` = el motor no tiene medición sobre esas páginas.

> **Páginas por tipología en la muestra**: `digital` (10), `escaneada` (0), `manuscrita` (0).

> **Sin datos** para `escaneada`, `manuscrita` en la muestra de esta feature (columna `N/A`): el muestreo no incluyó páginas de esa tipología, así que no se inventa la fila.

| Motor (variante) | digital | escaneada | manuscrita |
| :--- | ---: | ---: | ---: |
| GLM-OCR (0.9B) | 0.748 (n=10) | N/A | N/A |
| LightOnOCR-2-1B (1B) | 0.597 (n=10) | N/A | N/A |
| LightOnOCR-3 (0.8B) | 0.550 (n=10) | N/A | N/A |
| LightOnOCR-3 (4B) | 0.612 (n=10) | N/A | N/A |
| PaddleOCR-VL (0.9B) | 0.614 (n=10) | N/A | N/A |

