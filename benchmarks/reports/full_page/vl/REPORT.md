# Reporte por feature: `full_page`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --dataset omnidocbench_full_page_en --limit 6 --warmup 1 --device cpu --variant vl --backends pyocrust_vl --output-dir benchmarks/results`
- **dataset**: `omnidocbench_full_page_en` · **n** (por motor): `6` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/full_page/vl/2026-11-15_17-04-26` · **fecha**: `2026-11-15_17-04-26`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pyocrust (vl) | 6 | 0.534 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2.590 | 141693 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `full_page`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| GLM-OCR (0.9B) | N/A | 0.559 | N/A | 30716 | cuda |
| LightOnOCR-2-1B (1B) | N/A | 0.588 | N/A | 44737 | cuda |
| LightOnOCR-3 (0.8B) | N/A | 0.625 | N/A | 320707 | cuda |
| LightOnOCR-3 (4B) | N/A | 0.590 | N/A | 72249 | cuda |
| PaddleOCR-VL (0.9B) | N/A | 0.597 | N/A | 60907 | cuda |
| pyocrust (vl) | 0.534 | N/A | 141693 | N/A | n/a (no corre en GPU) |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `F1 bloques` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la tabla esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS tabla` = estructura HTML de tabla (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de fórmula. Una tabla **mal estructurada con el texto correcto** baja `TEDS tabla` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`F1 bloques` sólo ven el **texto** y el **tipo** de la figura, nunca su posición ni si la caption quedó ligada: una página con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la página/el motor no aporta GT o no emite esa modalidad (p. ej. un motor sin fórmulas separadas), nunca un `0.0`.

## Por estrato (`data_source × layout`)

> Markdown F1 **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 1 · estratos cubiertos: 4. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×other_layout` (2), `PPT2PDF×single_column` (1), `academic_literature×1andmore_column` (2).

### Markdown F1 por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column |
| :--- | ---: | ---: | ---: | ---: |
| pyocrust (vl) | 0.721 | 0.674 | 0.077 | 0.528 |

## Por tipología de página (`digital` / `escaneada` / `manuscrita`)

> Markdown F1 **por motor y tipología de página**. La tipología se deriva de `page_info.page_attribute` de OmniDocBench: `manuscrita` = `handwriting` en `special_issue` o `data_source=note`; `escaneada` = `fuzzy_scan` en `special_issue` o `data_source=historical_document`; `digital` = el resto. OmniDocBench **no** anota un tipo de adquisición explícito: la clasificación es una derivación declarada, no una etiqueta original. Motores medidos: 1. `N/A` = sin páginas medidas de esa tipología (nunca `0.0`); `—` = el motor no tiene medición sobre esas páginas.

> **Páginas por tipología en la muestra**: `digital` (6), `escaneada` (0), `manuscrita` (0).

> **Sin datos** para `escaneada`, `manuscrita` en la muestra de esta feature (columna `N/A`): el muestreo no incluyó páginas de esa tipología, así que no se inventa la fila.

| Motor (variante) | digital | escaneada | manuscrita |
| :--- | ---: | ---: | ---: |
| pyocrust (vl) | 0.534 (n=6) | N/A | N/A |

