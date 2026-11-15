# Reporte por feature: `table`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/table/bank.py --limit 8 --device cpu`
- **dataset**: `omnidocbench_table` · **n** (por motor): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/table/2026-11-15_20-06-20` · **fecha**: `2026-11-15_20-06-20`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | TEDS estrut. ↑ | ms/tabla ↓ |
| :--- | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 8 | 0.882 | 1900 |
| SLANet_plus (paddleocr) | 8 | 0.889 | 247 |
| pp_structurev3 (default) | 8 | 0.753 | 1128 |
| slanet_plus (7.8M) | 8 | 0.868 | **52** |
| slanext_wired (367M) | 8 | **0.914** | 577 |
| table-transformer-structure-recognition (default) | 8 | 0.790 | 718 |
| tableformer (docling) | 8 | 0.905 | 27457 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `table`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `SLANeXt_wired (paddleocr)` — **mismo peso, distinta vía** (el MISMO `.onnx` de PaddleOCR por otro runtime — NO es un modelo distinto)
- `SLANet_plus (paddleocr)` — **mismo peso, distinta vía** (el MISMO `.onnx` de PaddleOCR por otro runtime — NO es un modelo distinto)
- `table-transformer-structure-recognition (default)` — modelo **independiente** (otro proyecto/checkpoint)
- `tableformer (docling)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Structural TEDS ↑ (CPU) | Structural TEDS ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| SLANeXt_wired (paddleocr) | 0.882 | N/A | 1900 | N/A | n/a (no corre en GPU) |
| SLANet_plus (paddleocr) | 0.889 | 0.889 | 247 | 99 | cuda |
| pp_structurev3 (default) | 0.753 | 0.753 | 1128 | 2214 | cuda |
| slanet_plus (7.8M) | 0.868 | 0.868 | 52 | 484 | cuda |
| slanext_wired (367M) | 0.914 | 0.914 | 577 | 202 | cuda |
| table-transformer-structure-recognition (default) | 0.790 | 0.790 | 718 | 47 | cuda |
| tableformer (docling) | 0.905 | 0.905 | 27457 | 19140 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Por estrato (`data_source × layout`)

> TEDS tabla **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 7 · estratos cubiertos: 6. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (2), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (2).

### TEDS tabla por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 1.000 | 1.000 | 1.000 | 0.732 | 0.946 | 0.823 |
| SLANet_plus (paddleocr) | 1.000 | 1.000 | 1.000 | 0.757 | 0.934 | 0.833 |
| pp_structurev3 (default) | 1.000 | 0.980 | 0.407 | 0.560 | 0.934 | 0.791 |
| slanet_plus (7.8M) | 1.000 | 0.990 | 0.943 | 0.724 | 0.934 | 0.815 |
| slanext_wired (367M) | 1.000 | 1.000 | 1.000 | 0.668 | 0.997 | 0.990 |
| table-transformer-structure-recognition (default) | 1.000 | 0.889 | 0.857 | 0.628 | 0.791 | 0.762 |
| tableformer (docling) | 1.000 | 1.000 | 1.000 | 0.669 | 1.000 | 1.000 |

## Por tipología de página (`digital` / `escaneada` / `manuscrita`)

> TEDS tabla **por motor y tipología de página**. La tipología se deriva de `page_info.page_attribute` de OmniDocBench: `manuscrita` = `handwriting` en `special_issue` o `data_source=note`; `escaneada` = `fuzzy_scan` en `special_issue` o `data_source=historical_document`; `digital` = el resto. OmniDocBench **no** anota un tipo de adquisición explícito: la clasificación es una derivación declarada, no una etiqueta original. Motores medidos: 7. `N/A` = sin páginas medidas de esa tipología (nunca `0.0`); `—` = el motor no tiene medición sobre esas páginas.

> **Páginas por tipología en la muestra**: `digital` (8), `escaneada` (0), `manuscrita` (0).

> **Sin datos** para `escaneada`, `manuscrita` en la muestra de esta feature (columna `N/A`): el muestreo no incluyó páginas de esa tipología, así que no se inventa la fila.

| Motor (variante) | digital | escaneada | manuscrita |
| :--- | ---: | ---: | ---: |
| SLANeXt_wired (paddleocr) | 0.882 (n=8) | N/A | N/A |
| SLANet_plus (paddleocr) | 0.889 (n=8) | N/A | N/A |
| pp_structurev3 (default) | 0.753 (n=8) | N/A | N/A |
| slanet_plus (7.8M) | 0.868 (n=8) | N/A | N/A |
| slanext_wired (367M) | 0.914 (n=8) | N/A | N/A |
| table-transformer-structure-recognition (default) | 0.790 (n=8) | N/A | N/A |
| tableformer (docling) | 0.905 (n=8) | N/A | N/A |

