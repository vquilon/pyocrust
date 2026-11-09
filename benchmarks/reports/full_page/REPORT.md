# Reporte por feature: `full_page`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe features/full_page/bank.py --limit 20 --device cpu --output-dir results`
- **dataset**: `omnidocbench_full_page` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/full_page/2026-11-09_12-43-20` · **fecha**: `2026-11-09_12-43-20`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': ['directml']}

## Comparativa (media por motor)

| Motor (variante) | n | Markdown F1 ↑ | F1 bloques ↑ | layout mAP ↑ | TEDS tabla ↑ | LaTeX sim ↑ | títulos recall ↑ | títulos prec. ↑ | F1 texto títulos ↑ | secuencia títulos τ ↑ | orden lectura τ ↑ | figuras recall ↑ | figuras prec. ↑ | captions recall ↑ | captions prec. ↑ | asoc. fig↔caption ↑ | F1 texto captions ↑ | CER ↓ | ms/página ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | **0.354** | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **0.518** | 33257 |
| indra (math) | 20 | 0.265 | N/A | N/A | 0.361 | N/A | N/A | N/A | N/A | N/A | **0.747** | N/A | N/A | N/A | N/A | N/A | N/A | 1.231 | **2006** |
| pp_structurev3 (default) | 20 | 0.270 | 0.700 | 0.677 | **0.674** | 0.351 | 0.702 | 0.652 | 0.649 | 0.750 | 0.661 | 0.500 | 0.500 | 1.000 | 1.000 | 0.000 | 0.500 | 2.190 | 11054 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `full_page`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `pdf_extract_kit` — pip install pdf-extract-kit (opendatalab/PDF-Extract-Kit-1.0; pesos en cache HF, adaptador pendiente)

## Procedencia de las alternativas

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
| docling-default (pipeline) | 0.354 | N/A | 33257 | N/A | n/a (no corre en GPU) |
| indra (math) | 0.265 | 0.265 | 2006 | 8901 | directml |
| pp_structurev3 (default) | 0.270 | 0.267 | 11054 | 14053 | directml |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

## Contenido vs estructura/posición

> Las columnas del informe **no son redundantes**: miden fallos distintos y por eso se publican juntas.

> **Contenido** (lo que ya se publicaba, comparable con las series previas): `Markdown F1` = LCS de tokens en orden de lectura (conserva el LaTeX); `F1 bloques` = multiconjunto de **tipos** de bloque (ignora posición y contenido); `CER` = reconocimiento sobre texto plano. Un `Markdown F1` alto **no** garantiza que la tabla esté bien armada: si el texto de las celdas es correcto, el LCS lo da por bueno aunque la estructura esté mal.

> **Estructura/posición** (desgranado nuevo): `layout mAP` = posición de las cajas contra el `poly` anotado; `TEDS tabla` = estructura HTML de tabla (filas/columnas/fusiones, **sin** el texto de celda); `LaTeX sim` = similitud del LaTeX de fórmula. Una tabla **mal estructurada con el texto correcto** baja `TEDS tabla` y **no** `Markdown F1`: por eso se distinguen.

> **Figuras** (desgranado propio): `figuras recall/prec.` = detección de las cajas `figure` (IoU@0.5, como `layout`); `captions recall/prec.` = detección de las cajas de caption; `asoc. fig↔caption` = fracción de figuras detectadas cuya caption compañera también se localizó; `F1 texto captions` = F1 del texto de la caption. `Markdown F1`/`F1 bloques` sólo ven el **texto** y el **tipo** de la figura, nunca su posición ni si la caption quedó ligada: una página con las figuras detectadas pero **sin** sus captions baja `asoc. fig↔caption` sin que `Markdown F1` lo note.

> `N/A` = la página/el motor no aporta GT o no emite esa modalidad (p. ej. un motor sin fórmulas separadas), nunca un `0.0`.

## Por estrato (`data_source × layout`)

> Markdown F1 **por motor y estrato** de la página (muestra estratificada, `page_info.page_attribute`). Motores medidos: 3 · estratos cubiertos: 20. `—` = ese motor no tiene medición en ese estrato.

> **Estratos (n de páginas en la muestra)**: `PPT2PDF×1andmore_column` (1), `PPT2PDF×double_column` (1), `PPT2PDF×other_layout` (1), `PPT2PDF×single_column` (1), `academic_literature×1andmore_column` (1), `academic_literature×double_column` (1), `academic_literature×other_layout` (1), `academic_literature×single_column` (1), `academic_literature×three_column` (1), `book×1andmore_column` (1), `book×double_column` (1), `book×other_layout` (1), `book×single_column` (1), `book×three_column` (1), `colorful_textbook×1andmore_column` (1), `colorful_textbook×double_column` (1), `colorful_textbook×other_layout` (1), `colorful_textbook×single_column` (1), `colorful_textbook×three_column` (1), `exam_paper×1andmore_column` (1).

### Markdown F1 por estrato

| Motor (variante) | PPT2PDF×1andmore_column | PPT2PDF×double_column | PPT2PDF×other_layout | PPT2PDF×single_column | academic_literature×1andmore_column | academic_literature×double_column | academic_literature×other_layout | academic_literature×single_column | academic_literature×three_column | book×1andmore_column | book×double_column | book×other_layout | book×single_column | book×three_column | colorful_textbook×1andmore_column | colorful_textbook×double_column | colorful_textbook×other_layout | colorful_textbook×single_column | colorful_textbook×three_column | exam_paper×1andmore_column |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| docling-default (pipeline) | 0.438 | 0.341 | 0.149 | 0.000 | 0.220 | 0.524 | 0.098 | 0.442 | 0.904 | 0.038 | 0.872 | 0.075 | 0.455 | 0.684 | 0.031 | 0.828 | 0.049 | 0.029 | 0.245 | 0.648 |
| indra (math) | 0.025 | 0.056 | 0.000 | 0.223 | 0.269 | 0.272 | 0.054 | 0.355 | 0.908 | 0.000 | 0.837 | 0.018 | 0.453 | 0.139 | 0.054 | 0.847 | 0.075 | 0.013 | 0.073 | 0.624 |
| pp_structurev3 (default) | 0.115 | 0.000 | 0.070 | 0.029 | 0.155 | 0.392 | 0.112 | 0.392 | 0.777 | 0.069 | 0.772 | 0.040 | 0.424 | 0.624 | 0.047 | 0.606 | 0.043 | 0.038 | 0.165 | 0.532 |

## Cobertura de títulos y jerarquía (no medible)

> La métrica de **títulos/índice** solo se evalúa en las páginas que la anotación marca con `category_type=title`; en el resto queda `N/A` y **no** entra en la media (no se diluye en un promedio global). El dataset `OmniDocBench` (v1.6, 1651 páginas) anota `title` en **1179** páginas (el **71.4 %**); el resto no tiene GT de títulos.

> **La jerarquía de títulos (h1/h2/h3) NO es medible con esta anotación**: el campo `attribute` está **siempre vacío** en OmniDocBench, no hay nivel jerárquico anotado. Por eso esta tarjeta mide **presencia, posición, texto y secuencia**, y **no** emite un `0.0` por profundidad ni finge un índice anidado: donde el dataset no anota, el informe lo dice.

| Motor (variante) | páginas medidas | páginas con GT de títulos | cobertura títulos |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | 14 | 70% |
| indra (math) | 20 | 14 | 70% |
| pp_structurev3 (default) | 20 | 14 | 70% |

## Cobertura de figuras y lo no emitible (máscaras)

> La métrica de **figuras/captions** solo se evalúa en las páginas que la anotación marca con `category_type=figure`; en el resto queda `N/A` y **no** entra en la media (no se diluye en un promedio global). El dataset `OmniDocBench` (v1.6, 1651 páginas) anota `figure` en **613** páginas (el **37.1 %**; 1385 instancias de `figure` en total); el resto no tiene GT de figuras.

> **Las máscaras (`*_mask`) NO son emitibles por el pipeline** y por eso **no se puntúan**: `chart_mask`, `table_mask`, `algorithm_mask`, `organic_chemical_formula_mask`, `text_mask`, `need_mask`, `abandon`, `unknown_mask` se **ignoran** al puntuar (quedan fuera del GT de bloques, ver `_odb_content_blocks`); **nunca** cuentan como `0.0` por no emitirlas, igual que `page_number`/`reference` en `layout`. Un motor que no las emite no se penaliza.

> La **asociación figura↔caption** (`asoc. fig↔caption`) exige que, además de detectar la figura, se localice su caption compañera: una página con las figuras detectadas pero **sin** sus captions baja esa columna aunque su `figuras recall` sea `1.0`, así que no puede puntuar igual que una completa.

| Motor (variante) | páginas medidas | páginas con GT de figuras | cobertura figuras |
| :--- | ---: | ---: | ---: |
| docling-default (pipeline) | 20 | 4 | 20% |
| indra (math) | 20 | 4 | 20% |
| pp_structurev3 (default) | 20 | 4 | 20% |

