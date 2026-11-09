# Reporte por feature: `full_page`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --limit 6 --device cpu --output-dir benchmarks/results`
- **dataset**: `omnidocbench_full_page` · **n** (por motor): `6` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/full_page/2026-11-09_17-15-04` · **fecha**: `2026-11-09_17-15-04`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['cuda']}

## Comparativa (media por motor)

| Motor (variante) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 6 | 0.086 | N/A | N/A | **0.957** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2.494 | 124261 |
| docling-default (pipeline) | 6 | **0.204** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **1.119** | 27542 |
| indra (math) | 6 | 0.029 | N/A | N/A | 0.276 | N/A | N/A | N/A | N/A | N/A | 0.190 | N/A | N/A | N/A | N/A | N/A | N/A | 3.102 | **200** |
| pp_structurev3 (default) | 6 | 0.083 | 0.524 | 0.561 | 0.678 | 0.255 | 0.944 | 1.000 | 0.536 | 0.857 | **0.764** | 0.167 | 0.333 | 0.875 | 1.000 | 0.000 | 0.417 | 5.737 | 2181 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `full_page`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- (ninguno)

## Procedencia de las alternativas

- `PP-StructureV3 (paddleocr)` — modelo **independiente** (otro proyecto/checkpoint)
- `docling-default (pipeline)` — modelo **independiente** (otro proyecto/checkpoint)

> El motor de referencia (`pyocrust`) no se lista: es el que define el resultado base. Una alternativa con **mismo peso, distinta vía** mide el mismo modelo con otro runtime; **no** aporta un competidor independiente y así queda declarado.

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | Markdown F1 ↑ (CPU) | Markdown F1 ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| PP-StructureV3 (paddleocr) | 0.086 | N/A | 124261 | N/A | n/a (no corre en GPU) |
| docling-default (pipeline) | 0.204 | N/A | 27542 | N/A | n/a (no corre en GPU) |
| indra (math) | 0.029 | 0.029 | 200 | 1118 | cuda |
| pp_structurev3 (default) | 0.083 | 0.085 | 2181 | 1805 | cuda |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `F1 bloques` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la tabla esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS tabla` = estructura HTML de tabla (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de fórmula. Una tabla **mal estructurada con el texto correcto** baja `TEDS tabla` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`F1 bloques` sólo ven el **texto** y el **tipo** de la figura, nunca su posición ni si la caption quedó ligada: una página con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la página/el motor no aporta GT o no emite esa modalidad (p. ej. un motor sin fórmulas separadas), nunca un `0.0`.

## Por estrato (`data_source × layout`)

> Markdown F1 **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 4 · estratos cubiertos: 3. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (2), `PPT2PDF×other_layout` (3).

### Markdown F1 por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout |
| :--- | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 0.100 | 0.017 | 0.128 |
| docling-default (pipeline) | 0.438 | 0.188 | 0.138 |
| indra (math) | 0.025 | 0.028 | 0.031 |
| pp_structurev3 (default) | 0.115 | 0.000 | 0.127 |

## Por tipología de página (`digital` / `escaneada` / `manuscrita`)

> Markdown F1 **por motor y tipología de página**. La tipología se deriva de `page_info.page_attribute` de OmniDocBench: `manuscrita` = `handwriting` en `special_issue` o `data_source=note`; `escaneada` = `fuzzy_scan` en `special_issue` o `data_source=historical_document`; `digital` = el resto. OmniDocBench **no** anota un tipo de adquisición explícito: la clasificación es una derivación declarada, no una etiqueta original. Motores medidos: 4. `N/A` = sin páginas medidas de esa tipología (nunca `0.0`); `—` = el motor no tiene medición sobre esas páginas.

> **Páginas por tipología en la muestra**: `digital` (6), `escaneada` (0), `manuscrita` (0).

> **Sin datos** para `escaneada`, `manuscrita` en la muestra de esta feature (columna `N/A`): el muestreo no incluyó páginas de esa tipología, así que no se inventa la fila.

| Motor (variante) | digital | escaneada | manuscrita |
| :--- | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 0.086 (n=6) | N/A | N/A |
| docling-default (pipeline) | 0.204 (n=6) | N/A | N/A |
| indra (math) | 0.029 (n=6) | N/A | N/A |
| pp_structurev3 (default) | 0.083 (n=6) | N/A | N/A |

## Cobertura de títulos y jerarquía (no medible)

> La métrica de **títulos/índice** solo se evalúa en las páginas que la anotación marca con `category_type=title`; en el resto queda `N/A` y **no** entra en la media (no se diluye en un promedio global). El dataset `OmniDocBench` (v1.6, 1651 páginas) anota `title` en **1179** páginas (el **71.4 %**); el resto no tiene GT de títulos.

> **La jerarquía de títulos (h1/h2/h3) NO es medible con esta anotación**: el campo `attribute` está **siempre vacío** en OmniDocBench, no hay nivel jerárquico anotado. Por eso esta tarjeta mide **presencia, posición, texto y secuencia**, y **no** emite un `0.0` por profundidad ni finge un índice anidado: donde el dataset no anota, el informe lo dice.

| Motor (variante) | páginas medidas | páginas con GT de títulos | cobertura títulos |
| :--- | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 6 | 4 | 67% |
| docling-default (pipeline) | 6 | 4 | 67% |
| indra (math) | 6 | 4 | 67% |
| pp_structurev3 (default) | 6 | 4 | 67% |

## Cobertura de figuras y lo no emitible (máscaras)

> La métrica de **figuras/captions** solo se evalúa en las páginas que la anotación marca con `category_type=figure`; en el resto queda `N/A` y **no** entra en la media (no se diluye en un promedio global). El dataset `OmniDocBench` (v1.6, 1651 páginas) anota `figure` en **613** páginas (el **37.1 %**; 1385 instancias de `figure` en total); el resto no tiene GT de figuras.

> **Las máscaras (`*_mask`) NO son emitibles por el pipeline** y por eso **no se puntúan**: `chart_mask`, `table_mask`, `algorithm_mask`, `organic_chemical_formula_mask`, `text_mask`, `need_mask`, `abandon`, `unknown_mask` se **ignoran** al puntuar (quedan fuera del GT de bloques, ver `_odb_content_blocks`); **nunca** cuentan como `0.0` por no emitirlas, igual que `page_number`/`reference` en `layout`. Un motor que no las emite no se penaliza.

> La **asociación figura↔caption** (`asoc. fig↔caption`) exige que, además de detectar la figura, se localice su caption compañera: una página con las figuras detectadas pero **sin** sus captions baja esa columna aunque su `figuras recall` sea `1.0`, así que no puede puntuar igual que una completa.

| Motor (variante) | páginas medidas | páginas con GT de figuras | cobertura figuras |
| :--- | ---: | ---: | ---: |
| PP-StructureV3 (paddleocr) | 6 | 3 | 50% |
| docling-default (pipeline) | 6 | 3 | 50% |
| indra (math) | 6 | 3 | 50% |
| pp_structurev3 (default) | 6 | 3 | 50% |

