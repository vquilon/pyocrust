# Feature `full_page` — banco de benchmark (implementado)

> Origen de los números: **`medido`** — ver `REPORT.md` (comando + dataset + n + device + fecha).

## Qué mide

El pipeline completo de página → Markdown/bloques (texto + tablas + fórmulas
juntos).

## Tarea `pyocrust`

`pp_structurev3` (`VeloceOCR`) e Indra (pipeline completo de página).

## Métrica

**markdown_f1 / block_f1**: equivalencia de documento (tokens LCS sensibles al
orden y conservando el LaTeX) y multiconjunto de tipos de bloque, además del
CER/WER de texto que ya mide el runner.

**Desgranado estructura/posición** (misma pasada): `layout mAP@0.5`, `TEDS tabla`
y similitud `LaTeX`; detección + texto + secuencia de **títulos** y **orden de
lectura** (Kendall τ); y, como métrica **propia**, **figuras e imágenes**:
`figure_recall`/`figure_precision` (detección de las cajas `figure`, IoU@0.5 como
`layout`), `figure_caption_recall`/`figure_caption_precision` (detección de las
captions) y **`figure_caption_pair_f1`** (asociación figura↔caption: exige que,
detectada la figura, se localice su caption compañera; una página con las figuras
detectadas pero **sin** sus captions puntúa bajo aquí aunque su `figure_recall`
sea `1.0`). Sin GT de figuras, quedan `N/A` (nunca `0.0`). Las **máscaras**
(`*_mask`), no emitibles por el pipeline, se **ignoran** al puntuar.

## Dataset / ground truth

`omnidocbench_full_page`: la release de `OmniDocBench` **no** publica un Markdown
de página renderizado, pero **sí** anota el contenido de cada bloque
(`text`/`latex`/`html`) y su `order` de lectura. El Markdown de referencia se
**reconstruye** concatenando esos contenidos en ese orden (las máscaras `*_mask` y
los bloques `ignore`/`abandon` no son contenido), y los tipos de bloque se
traducen al vocabulario que emite el pipeline (`kind`, vía
`common.datasets.ODB_CATEGORY_TO_KIND`) para que `block_f1` compare la misma
taxonomía en ambos lados. No se inventa contenido: solo se serializa lo anotado.

## Alternativas Python reales (a comparar)

| Alternativa | Módulo / `pip install` |
| :--- | :--- |
| docling | `docling` |
| unstructured | `unstructured` |
| paddleocr PP-StructureV3 | `paddleocr paddlepaddle` |
| marker-pdf | `marker-pdf` |
| LightOnOCR-2-1B (Apache-2.0) | `transformers>=5` (en `.venv_docling`) |
| GLM-OCR (MIT) | `transformers>=5` (en `.venv_docling`) |
| PaddleOCR-VL (Apache-2.0) | `transformers>=5` (en `.venv_docling`) |
| MinerU2.5 (AGPL-3.0) | **documentado, no medido** — licencia no comercial |

**Medidas hoy**: `docling` (MIT). PaddleOCR `pp_structurev3_api` (Apache-2.0)
**ya corre en subproceso con timeout** (mismo patrón que `docling`/`unimernet`):
su pipeline en proceso **cuelga o segfaultea** (exit 139) en páginas reales
(medido 2026-11-09, imagen grande 11112x7925, tras cargar 16 submodelos y en 4/5
páginas), así que se aisló: un segfault o un cuelgue mata solo al hijo y la fila
sale `error`/`skipped` con motivo, **sin abortar el banco**.

**Smoke real 2026-11-09** (`--limit 3 --warmup 0 --backends pp_structurev3_api`,
`.scratch/smoke`): **rc=0, 3/3 `ok`**, 0 `error`, Markdown **no vacío** (616 chars
en la primera página) y 154 s/imagen. Por eso `pp_structurev3_api` **entra en el
`DEFAULT_BACKENDS`**. Es **CPU-only** (`device_outcome` lo salta en las runs GPU).
`unstructured`, `marker-pdf` y `pdf_extract_kit` siguen `skipped` (adaptador
pendiente / solo publican un detector de layout, no un pipeline de documento);
`pdf_extract_kit` queda fuera del default por eso mismo.

### docling — versión y entorno (reproducible)

`docling` **no** se instala en el venv del banco: su `[standard]` arrastra
torch/torchvision y degradaría los backends de `layout`/`table`. Vive en un venv
aislado `benchmarks/.venv_docling` y se invoca por **subproceso**, un modelo a la
vez (ver `common/runner.py::_docling_backend`).

| Paquete | Versión medida |
| :--- | :--- |
| `docling` | **2.149.0** |
| `transformers` | 5.22.2 |
| `huggingface_hub` | 2.4.0 (requiere `>=2` por `ResolvedRevision` que importa transformers 5.x) |
| `tokenizers` | 0.23.3 (`transformers` 5.22 exige `>=0.23.1,<0.24`) |
| `torch` | 2.15.0 (CPU) |

Creación del venv (si no existe) y pins que hubo que corregir:

```bash
uv venv benchmarks/.venv_docling
uv pip install --python benchmarks/.venv_docling/Scripts/python.exe docling
# pins obligatorios: sin ellos docling no arranca con transformers 5.x
uv pip install --python benchmarks/.venv_docling/Scripts/python.exe \
    "huggingface_hub>=2" "tokenizers>=0.23.1,<0.24.0"
```

## Estado

**Implementado**: ejecuta `pyocrust_structure` (PP-StructureV3) y `pyocrust_indra`
sobre las páginas anotadas y publica `markdown_f1`/`block_f1`. Si Indra no tiene
sus 9 artefactos en disco, queda **`skipped` con su motivo** (no se mide a medias).

### VLMs documentales SOTA (`lightonocr`, `glm_ocr`, `paddleocr_vl`)

Los SOTA de conversión página→Markdown de 2025-2026 son **VLMs end-to-end** (una
pasada imagen→Markdown), no pipelines. Se miden como **una fila más** del banco
(mismo GT y misma métrica), por su ruta **`transformers`** en el **mismo venv
aislado de docling** (`transformers` 5.x + `torch` CUDA), por **subproceso con
timeout**, **un modelo a la vez** (ver `common/runner.py::_hf_vlm_backend`).

| Backend | Modelo (HF) | Licencia | Tamaño | `emits` |
| :--- | :--- | :--- | :--- | :--- |
| `lightonocr` | [`lightonai/LightOnOCR-2-1B`](https://huggingface.co/lightonai/LightOnOCR-2-1B) | Apache-2.0 | 1B | `frozenset()` |
| `glm_ocr` | [`zai-org/GLM-OCR`](https://huggingface.co/zai-org/GLM-OCR) | MIT | 0.9B | `frozenset()` |
| `paddleocr_vl` | [`PaddlePaddle/PaddleOCR-VL`](https://huggingface.co/PaddlePaddle/PaddleOCR-VL) | Apache-2.0 | 0.9B | `frozenset()` |

- **Solo Markdown ⇒ sin filas `0.0` falsas.** Los tres declaran `emits=frozenset()`
  (como `docling`): sus columnas de estructura (`block_f1`, `layout mAP`, `TEDS`,
  `LaTeX sim`, títulos, orden de lectura, figuras) salen **`N/A`**, nunca `0.000`.
  Sólo compiten en `markdown_f1`/`CER`/`WER`.
- **No entran en `DEFAULT_BACKENDS`** (peso ~2 GiB y segundos/página): se piden
  explícitamente con `--backends lightonocr,glm_ocr,paddleocr_vl`. Sin los pesos en
  caché queda **`skipped` con el comando exacto de descarga** (no bajan solos).
- **GPU**: la fila sólo se etiqueta `cuda` si el venv de docling **ve la GPU**
  (sonda `torch.cuda.is_available`); si no, `skipped` con motivo. Nunca una fila
  CPU disfrazada de CUDA.
- **Métrica honesta**: `markdown_f1` es LCS de tokens sobre un GT **reconstruido**
  por nosotros; los SOTA reportan en **olmOCR-bench** (unit tests) u
  **OmniDocBench** (edit-distance/CDM/TEDS). Nuestro número vale como
  **motor-vs-motor medido por nosotros**, nunca como un ranking del leaderboard.
- **PaddleOCR-VL por `transformers` es reconocimiento por elemento**: su parsing
  de página completa es la pipeline oficial (PP-DocLayout + post-proceso), fuera de
  este venv. Aquí se le pasa la página entera con el prompt nativo `OCR:` como a
  los demás; es la ruta que documenta su ficha para `transformers`.
- **MinerU2.5** (1.2B) queda **documentado como AGPL-3.0, no medido**: su licencia lo
  limita al contexto de benchmark no comercial y **nunca** es preset de producto
  (ver `REFERENCES.md`).


**Alternativas externas medidas** (muestra **no china** `--dataset omnidocbench_full_page_en`,
n=6 CPU, run `results/full_page/2026-11-14_18-38-10`; misma muestra que la pata GPU
`results/_gpu/full_page/2026-11-14_18-09-59`):

| Motor | `markdown_f1` | CER | ms/página |
| :--- | ---: | ---: | ---: |
| `pp_structurev3` (pyocrust) | 0.530 | 1.344 | 3 527 |
| `indra` (pyocrust) | 0.556 | 0.784 | 1 253 |
| `docling` (MIT) | 0.512 | **0.509** | 26 023 |
| `PP-StructureV3` (paddleocr, Apache-2.0) | 0.427 | 1.443 | 176 264 |
| `LightOnOCR-2-1B` (Apache-2.0) | 0.590 | 1.241 | 151 454 |
| `GLM-OCR` (MIT) | 0.559 | 0.850 | 151 850 |
| `PaddleOCR-VL` (Apache-2.0) | 0.669 | 0.514 | 430 548 |

> Los tres VLMs entran con `emits=frozenset()`: sus columnas de estructura salen
> **`N/A`** (no emiten cajas/tabla/fórmula aparte), nunca `0.0`; solo compiten en
> `markdown_f1`/`CER`. **Caveat honesto**: `PaddleOCR-VL` en **CPU** completó
> **4/6** páginas (2 `TimeoutExpired` a 1200 s en páginas densas: es el VLM más
> lento en CPU con NaViT a resolución dinámica) — su fila CPU es `n=4`, y por eso
> `validez_medicion.py` marca `full_page` como `REHACER: n distinto CPU/GPU`. En
> **GPU** los tres VLMs van 6/6. Re-medir la pata CPU con timeout ampliado es una
> tarjeta de seguimiento.


> El `markdown_f1` se mide sobre la muestra **no china** (`omnidocbench_full_page_en`):
> una página china anota un párrafo entero como **un solo token** y la LCS de
> tokens sale ruidosa, por eso la comparativa de parse usa el subconjunto `english`.
> `PP-StructureV3` **sí** emite tablas HTML (`TEDS` 1.000 en la muestra `_en`); su
> `ms` incluye *spawn* + carga de los 16 submodelos + inferencia (patrón
> `docling`/`unimernet`), no solo la inferencia. Corre en **CPU y GPU**.


> **Límite honesto de docling en este banco**: el adaptador devuelve **solo el
> Markdown** (`export_to_markdown`), sin cajas ni tipos de bloque. Por eso sus
> columnas de estructura (`block_f1`, `layout mAP`, `title_recall`,
> `figure_recall`) salen **`N/A`** —el motor no emite esa modalidad y el informe
> no la evalúa—, nunca un `0.000`. La comparación justa con `pyocrust_structure`
> es la columna `markdown_f1`/`CER`; desgranar layout/tabla/fórmula de docling
> exigiría un adaptador sobre `export_to_dict` (fuera del alcance de esta tarjeta).

## Provenance

Cada cifra de `REPORT.md` va etiquetada **`medido`**: comando reproducible,
dataset, `n`, `warmup`, `repeats`, `device` y fecha, guardados en el
`summary.json` de la run. No hay valores `referencia` en esta tabla.
