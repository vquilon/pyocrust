# Catálogo de alternativas SOTA por feature — qué falta para medirlas

> **Alcance.** Responde a *"queremos comparar con los SOTA de cada feature; qué
> necesitamos"*: qué motor alternativo es SOTA hoy por feature, con su licencia,
> su peso exacto, la dependencia que exige, si el adaptador existe o falta en
> `benchmarks/common/runner.py`, su coste (tamaño/RAM/CPU-vs-GPU) y un veredicto
> (`medible ya` / `medible con adaptador` / `no viable en este host`).
>
> **Método.** Inspección estática del repo (rutas `benchmarks/**` y `~/.oar`),
> `pip show`/`importlib` en el intérprete de `.venv` y consulta de las fichas de
> los pesos (URL citada en cada fila). **No se ejecutan modelos.** Ningún número
> de calidad propio se reproduce aquí: los medidos viven en `benchmarks/README.md`
> y `benchmarks/reports/`; las cifras externas van con su URL y se marcan
> `referencia` (no comparable 1:1).
>
> **Verificación de "instalado".** Medida en `.venv` de este host con
> `importlib.util.find_spec` + `importlib.metadata.version` (2026-11-08).
> Los pesos en caché se verificaron por tamaño de blob real, no por el nombre del
> directorio HF: **un `models--<repo>` puede existir con solo `refs/` y 0 bytes de
> payload** (p. ej. `Aryn--deformable-detr-DocLayNet`, `juliozhao--DocLayout-YOLO-*`).

## Resumen por feature

| Feature | SOTA candidato | Adaptador | Veredicto |
| :--- | :--- | :--- | :--- |
| `layout` | PP-DocLayoutV3 (ya es el motor propio) / docling-egret-xlarge | propio / `_hf_layout_backend` | `medible ya` (egret: añadir 1 línea) |
| `text` | Surya (datalab) | falta | `medible con adaptador` (fuera del default) |
| `formula` | UniMERNet (small/tiny) / TexTeller | falta (`unavailable_factory`) | `medible con adaptador` |
| `table` | TableFormer (docling) / TATR (ya medido) | falta / ya | `medible con adaptador` |
| `orientation` | PP-LCNet + **easyocr_rotation** (independiente) | ya | `medible ya` |
| `text_line` | PP-LCNet + **rapidocr_mobile_cls** (PP-OCRv2, RapidAI) | ya | `medible ya` |
| `rectification` | UVDoc + **opencv_perspective** (baseline clásico) | ya | `medible ya` |
| `full_page` | **MinerU 2.5** / docling / marker-pdf | **falta (0 reales)** | `medible con adaptador` |
| `seal` | **PaddleOCR PP-OCRv4_mobile_seal_det** | **falta (0 reales)** | `medible ya` vía `paddleocr` |

Leyenda de veredicto:
`medible ya` = adaptador presente y pesos/dependencia disponibles en este host;
`medible con adaptador` = falta escribir el adaptador (o instalar la dependencia),
pero el peso es viable aquí; `no viable en este host` = motivo explícito.

---

## 1. `layout`

**Estado en el repo.** 41 externos registrados en `PROVIDERS`
(`benchmarks/common/runner.py:1086-1127`): 39 YOLO DocLayNet (`YOLO_LAYOUT_MODELS`,
`runner.py:696-736`) + `docling_heron_101` + `deformable_detr` (`:1112-1113`). El motor
propio (`pyocrust_layout`) usa `pp-doclayoutv3.onnx`.

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **docling-layout-egret-xlarge** | `docling-project/docling-layout-egret-xlarge` — `model.safetensors` **251 101 540 B (≈240 MB)** en caché HF (`D:\Environments\cache\huggingface\hub`, blob verificado) | MIT (código docling y pesos `docling-ibm-models` [ref: https://github.com/docling-project/docling-ibm-models/blob/main/LICENSE]) | `transformers`+`torch` **instalados** (5.22.1 / 2.14.1+cu130); adaptador **existe** (`_hf_layout_backend`, `runner.py:628`), solo hay que añadir la línea en `LAYOUT_HF_MODELS` (`:610-613`) | GPU o CPU; RT-DETR xlarge, ~240 MB | `medible ya` (añadir 1 línea a `LAYOUT_HF_MODELS`) |
| **PP-DocLayoutV3** | `PaddlePaddle/PP-DocLayoutV3` — `inference.pdiparams` **131 MB** [ref: https://huggingface.co/PaddlePaddle/PP-DocLayoutV3/tree/main]; el `.onnx` local `~/.oar/pp-doclayoutv3.onnx` = **129 955 811 B (≈124 MB)** | Apache-2.0 | Es el motor **propio** de pyocrust, no alternativa | CPU/GPU; ~124 MB | `medible ya` (ya es `pyocrust_layout`) |
| **DocLayout-YOLO** (DocStructBench) | `juliozhao/DocLayout-YOLO-DocStructBench-imgsz1280-2501` — `.pt` (peso `imgsz1280`) [ref: https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench-imgsz1280-2501] | **AGPL-3.0** en el repo de pesos [ref: id.]; el paquete `doclayout_yolo` es AGPL-3.0 [ref: https://github.com/opendatalab/DocLayout-YOLO] | `ultralytics` **instalado** (8.4.198), pero el checkpoint es de `doclayout_yolo`, no de `ultralytics`; en este host el dir HF existe con **0 blobs** (no descargado) | ~40-80 MB `.pt`; CPU/GPU | `medible con adaptador` (adaptador YOLO propio + descargar `.pt`); **licencia AGPL: no comercial** |

**Trade-off rechazado.** Añadir `egret-xlarge` al banco de `layout` es la vía de
mayor relación calidad/esfuerzo: reutiliza el adaptador HF ya probado. Se descarta
por ahora subir a un detector más nuevo tipo OmniDocBench-VLM porque exigiría un
adaptador nuevo (VLM, salida texto) y un GT distinto al de cajas anotadas.

---

## 2. `text`

**Estado en el repo.** Reales: `rapidocr`, `easyocr`, `tesseract`
(`runner.py:1115-1117`). Declarados sin factoría: `surya`, `paddleocr`, `doctrl`
(`features/text/bank.py:54-59` `EXTRA_FACTORIES`, `unavailable_factory`).
> **Nota (`doctrl`).** El nombre hilado `doctrl` no corresponde a ningún paquete
> publicado: en el repo aparece **solo** en `features/text/bank.py` y
> `features/seal/bank.py`; no hay `pip install doctrl` documentado. Casi con
> seguridad es un typo de **`python-doctr`** (mindee/doctr, Apache-2.0). Conviene
> corregir el nombre antes de integrarlo.

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Surya** (`surya-ocr`) | pesos `datalab-to/*` (descarga en 1ª ejecución) [ref: https://github.com/datalab-to/surya] | Código **GPL-3.0-or-later**; pesos **AI Pubs Open RAIL-M (modificada, umbral $2M/$5M)** [ref: https://pypi.org/project/surya-ocr/] | `surya` **NO instalado**; `torch` sí. Adaptador **falta** | Modelo de línea ~1 GB; GPU recomendada, CPU lento | `medible con adaptador`; **licencia restrictiva (no comercial > $2M)** |
| **PaddleOCR** (`paddleocr`) | PP-OCRv4/v5 det+rec [ref: https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html] | Apache-2.0 | `paddleocr` 3.7.0 **instalado**; `paddlepaddle` instalado. Adaptador **falta** (hoy `unavailable_factory`) | Rec mobile ~10-15 MB; CPU/GPU | `medible con adaptador` (la más barata: paquete ya instalado) |
| **docTR** (`python-doctr`) | `mindee/doctr` pesos | Apache-2.0 | no instalado; adaptador **falta** | ~50 MB; CPU/GPU | `medible con adaptador` |

**Trade-off rechazado.** Surya es SOTA en OCR de línea pero su licencia de pesos
(RAIL-M con umbral de facturación) es incompatible con un uso comercial sin
licencia de Datalab — y el banco es contexto **no comercial** ya documentado
(`runner.py:277-281`). Para comparar contra SOTA *usable*, PaddleOCR resuelve con
la dependencia ya instalada; Surya se mide solo si se acepta la restricción.

---

## 3. `formula`

**Estado en el repo.** Reales: `pix2tex`, `paddle_latex_ocr`
(`runner.py:1114`, `:746`). Declarados sin factoría: `texify`, `nougat`,
`unimernet`, `pix2text`, `texteller`, `img2latex`
(`features/formula/bank.py:93-113`, `unavailable_factory`).

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UniMERNet** (small o tiny) | `wanderkid/unimernet_small` **773 MB**, `unimernet_tiny` **441 MB**, `unimernet_base` 1.3 GB [ref: https://github.com/opendatalab/unimernet] | **Apache-2.0** (código y pesos; `license: apache-2.0` en la ficha HF) [ref: https://huggingface.co/kitjesen/MinerU/blob/main/models/MFR/unimernet_small/unimernet_small.yaml] | `unimernet` **NO instalado**; `torch` sí. Adaptador **falta** (`unavailable_factory`) | 441 MB–1.3 GB; GPU recomendada (Donut/Swin), CPU viable | `medible con adaptador`; **mejor licencia comercial** de la tabla |
| **TexTeller** | `OleehyO/TexTeller` — **0.3B params** (ViT) [ref: https://huggingface.co/OleehyO/TexTeller]; pesos En/Ch (~1 GB) | **Apache-2.0** (código; pesos HF `license: mit`) [ref: https://github.com/OleehyO/TexTeller] | `texteller` **NO instalado**; `torch` sí. Adaptador **falta** | ~0.3B params; GPU recomendada | `medible con adaptador` |
| **Nougat** | `facebookresearch/nougat` (`0.1.0-small` / `0.1.0-base`) | Código **MIT**; **pesos CC-BY-NC** (no comercial) [ref: https://github.com/facebookresearch/nougat] | `nougat-ocr` **NO instalado**; `torch` sí. Adaptador **falta** | ~350M/1.4B; GPU recomendada | `medible con adaptador`; **no comercial (CC-BY-NC)** |

**Trade-off rechazado.** `pix2text` se probó y se dejó `skipped` **a propósito**
porque `pip install pix2text` degrada `transformers`/`huggingface_hub` y cambia
`opencv-python-headless`→`opencv-python` (`features/formula/bank.py:99-107`), lo
que rompería easyocr/rapidocr/datasets del mismo venv. UniMERNet en un venv
aparte evita ese conflicto y tiene licencia limpia.

---

## 4. `table`

**Estado en el repo.** Reales y **medidos**: `tatr` — `microsoft/table-transformer-structure-recognition`
(`runner.py:470`, `:1120`), `paddleocr_slanet` — SLANet de PaddleOCR
(`runner._paddleocr_slanet_backend`) y `docling_tableformer` — TableFormer de
docling (`runner._docling_tableformer_backend`). Declarados: `docling`,
`paddleocr` (`features/table/bank.py` `SPEC.alternatives`).

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TATR** (medido) | `microsoft/table-transformer-structure-recognition` — `model.safetensors` **115 434 268 B (≈110 MB)** en caché HF | **MIT** (comercial) [ref: https://github.com/microsoft/table-transformer/blob/main/LICENSE] | `transformers`+`torch` instalados; adaptador **existe** | ~110 MB; CPU | `medido` |
| **PaddleOCR SLANet** (medido) | `PaddlePaddle/SLANet_plus` en `~/.paddlex/official_models/SLANet_plus` | **Apache-2.0** | `paddleocr` 3.7.0 instalado; adaptador **existe** (`TableStructureRecognition`) | CPU; 71 ms/tabla | `medido` |
| **docling TableFormer** (medido) | `docling-project/docling-models` — `tableformer_accurate.safetensors` **212 758 388 B (≈203 MB)** en caché HF | **MIT** [ref: id.] | `docling` 2.149.0 en venv aislado; adaptador **existe** | 203 MB; CPU; 33 s/tabla | `medido` |
| **PP-Structure (SLANet)** | `pyocrust_table` ya usa `slanext_wired.onnx` (**367 743 373 B ≈351 MB**) en `~/.oar` | Apache-2.0 | motor propio | ~351 MB | `medido` (propio) |

**Resultado (n=20, CPU, run `2026-11-08_18-43-55`).** TEDS-S medio:
`paddleocr_slanet` **0.828** (71 ms) > `docling_tableformer` 0.807 (33 s, 14/20
evaluadas) > `pyocrust_table` 0.780 (796 ms) > `tatr` 0.698 (760 ms). El SLANet
oficial de PaddleOCR supera al propio; TATR va último con la rejilla simple.

**Trade-off rechazado.** TableFormer daría un TEDS de **árbol completo** (con
texto de celda) frente al TEDS-S del banco actual, que solo puntúa la gramática
`<tr>/<td>` (`features/table/bank.py` docstring; `runner._tatr_grid_html`,
`runner.py:507`). Igualar granularidad exige que el GT de OmniDocBench aporte cell text;
se deja fuera por ahora para no romper la comparabilidad con las filas ya medidas.

---

## 5. `orientation` y `text_line`

**Estado en el repo.** `pyocrust` corre estas tareas por el runtime Rust de `oar-ocr`
(PP-LCNet). Las alternativas `lcnet_doc_ori` / `lcnet_textline_ori` vía `onnxruntime`
son los **MISMOS** pesos de PaddleOCR (`runner.py:1597-1598`): el informe las declara
como **"mismo peso, distinta vía"**, no como un modelo distinto.

| Candidato | Peso | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PP-LCNet doc_ori** (`lcnet_doc_ori`) | `~/.oar/pp-lcnet_x1_0_doc_ori.onnx` **6.5 MB** | Apache-2.0 | `onnxruntime`; **mismo peso, otra vía** | 6.5 MB; CPU | `medible ya` |
| **PP-LCNet textline_ori** (`lcnet_textline_ori`) | `~/.oar/pp-lcnet_x1_0_textline_ori.onnx` **6.5 MB** | Apache-2.0 | idem | 6.5 MB; CPU | `medible ya` |
| **`easyocr_rotation`** (orientation) | `~/.EasyOCR/*.pth` **~100 MB** | Apache-2.0 | `easyocr` (torch) **instalado**; adaptador **existe** | CPU; ~60-100 s/página (4 pasadas OCR) | `medible ya` — **independiente** |
| **`rapidocr_mobile_cls`** (text_line) | `.venv/.../rapidocr/models/ch_ppocr_mobile_v2.0_cls_mobile.onnx` **585 KB** | Apache-2.0 | `rapidocr` **instalado**; adaptador **existe** | CPU; ~3 ms/línea | `medible ya` — **independiente** |

**Decisión.** Se añaden dos alternativas **realmente independientes** (no pesos
PaddleOCR): `easyocr_rotation` (el recognizer de EasyOCR elige la rotación de mayor
confianza — no un clasificador dedicado; el informe lo declara) y `rapidocr_mobile_cls`
(red mobile cls de PP-OCRv2 del proyecto RapidAI, arquitectura distinta del PP-LCNet).
Ya no se presenta el mismo peso por otro runtime como "modelo independiente".

---

## 6. `rectification`

**Estado en el repo.** `pyocrust` (`document_rectification`, UVDoc). La alternativa
`uvdoc` vía `onnxruntime` es el **MISMO** peso de PaddleOCR (`runner.py:1599`): el
informe la declara como **"mismo peso, distinta vía"**.

| Candidato | Peso | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UVDoc** (`uvdoc`) | `~/.oar/uvdoc.onnx` **30 MB** | Apache-2.0 | `onnxruntime`; **mismo peso, otra vía** | 30 MB; CPU | `medible ya` |
| **`opencv_perspective`** (baseline) | — (OpenCV, **sin pesos**) | Apache-2.0 | `cv2` instalado; adaptador **existe** | CPU; ~10 ms/página | `medible ya` — **independiente** (línea base clásica, no un SOTA) |
| **docling / DocTr++ / DocUNet** (SOTA) | — | MIT / varias | `docling` **no** tiene etapa de dewarping; DocTr++/DocUNet exigen descargar pesos | — | `no viable offline` (requiere descarga) |

**Decisión.** No hay un rectificador SOTA **no-PaddleOCR** disponible offline: docling
no incluye dewarping y DocTr++/DocUNet exigen pesos externos. Para que `rectification`
tenga una segunda entrada que **no** sean pesos PaddleOCR, se añade `opencv_perspective`:
una línea base geométrica clásica (Canny + homografía de 4 esquinas) **sin pesos**. El
informe la declara como **línea base clásica**, no como SOTA; sobre una homografía de
perspectiva severa recupera poco (es un suelo, no un techo).

---

## 7. `full_page` — **sin alternativa real hoy**

**Estado en el repo.** `EXTRA_FACTORIES` solo tiene `pdf_extract_kit` como
`unavailable_factory` (`features/full_page/bank.py:68-73`). `docling`,
`unstructured`, `marker-pdf`, `PP-StructureV3` están en `SPEC.alternatives`
(`:54-59`) **sin factoría**. Resultado: 0 alternativas externas medidas; el banco
solo corre el pipeline propio (`pyocrust_structure`, `pyocrust_indra`).
`unstructured` no está instalado ni tiene un peso de pipeline único citado → se
descarta como candidato medible (sería un framework, no un modelo).

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MinerU 2.5** (candidato #1) | `opendatalab/MinerU2.5-2509-1.2B` — VLM 1.2B [ref: https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B] | **AGPL-3.0** (repo y pesos; `license: agpl-3.0`) [ref: id.] | `mineru` **NO instalado**; `torch` sí. Paquete de pipeline: `mineru[docs]`. Adaptador **falta** | 1.2B VLM (~2.5 GB fp16); **GPU prácticamente obligatoria** en este host (API documentada "no GPU required" pero es el servicio) | `medible con adaptador`; **licencia AGPL: no comercial en producto** |
| **docling** (candidato #2) | `docling-project/docling`; usa los pesos ya en caché (layout heron + TableFormer) | **MIT** (comercial) [ref: https://github.com/docling-project/docling] | `docling` **NO instalado**; `transformers`/`torch` sí (sus pesos, en caché). Adaptador **falta** | reusa pesos cacheados; CPU viable | `medible con adaptador`; **licencia limpia** |
| **marker-pdf** (candidato #3) | `datalab-to/marker` (usa surya + texify) | Código **Apache-2.0** (≥2.1.0) / pesos **AI Pubs Open RAIL-M $5M** [ref: https://pypi.org/project/marker-pdf/] | `marker` **NO instalado**. Adaptador **falta** | surya+texify; GPU recomendada | `medible con adaptador`; **pesos restrictivos** |

### Plan de integración propuesto para `full_page` (≥1 candidato concreto)

Candidato elegido para integrar primero: **docling** (MIT, pesos ya en caché).
Alternativa de máxima calidad: **MinerU 2.5** (AGPL, GPU).

1. **Fichero**: `benchmarks/features/full_page/bank.py`. Sustituir la entrada de
   `EXTRA_FACTORIES` por adaptadores reales (o añadir una nueva clave), p. ej.
   `"docling": _docling_backend`. El adaptador devuelve `OcrOutput(texto_markdown)`
   con el Markdown de documento, que es lo que consume `markdown_f1`/`block_f1`
   (métrica ya calculada por el runner para `task_type != "text"`,
   `runner.py:1402-1403`).
2. **Dependencia**: `pip install docling` (extra en un **venv aparte** para no
   degradar `transformers`/`huggingface_hub` del venv del banco — mismo riesgo
   documentado para `pix2text`). Para MinerU: `pip install "mineru[docs]"`.
3. **GT**: ya existe y no hay que inventarlo — `omnidocbench_full_page`
   (`common/datasets.py:672`), con `gt_markdown` reconstruido de los bloques
   anotados en orden de lectura y `gt_blocks`. El GT es la misma referencia que el
   pipeline propio ⇒ comparación 1:1.
4. **Métrica**: sin cambios (`markdown_f1`/`block_f1`). Registrar el backend en
   `FEATURE_TYPES`/`TASK_TYPES` (`runner.py:1149-1222`) con `feature="full_page"`.
5. **Coste de medición**: `--limit` bajo (6-8 páginas) y `--device gpu` solo si el
   adaptador confirma proveedor acelerador (regla de honestidad de proveedor,
   `runner.py:1300-1314`).

**Nota `pdf_extract_kit`.** Sus pesos (`opendatalab/PDF-Extract-Kit-1.0`) están
en caché: solo un `yolo_v8_ft.pt` de **349 867 002 B (≈334 MB)** (blob verificado)
— es un detector de layout, **no** un pipeline full_page. El adaptador declarado
nunca se escribió; medirlo como "full_page" sería etiquetar un detector de layout
como pipeline de documento. Si se integra, corresponde al banco de `layout`.

---

## 8. `seal` — **sin alternativa real hoy**

**Estado en el repo.** `EXTRA_FACTORIES` solo tiene `paddleocr` y `doctrl` como
`unavailable_factory` (`features/seal/bank.py:61-64`). Resultado: 0 alternativas
externas; el banco solo corre `pyocrust_seal`. GT sintético determinista
(`synthetic_seal`, `common/datasets.py:938-965`).

| Candidato | Peso / enlace | Licencia | Dep. y estado | Coste | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PaddleOCR seal** (`PP-OCRv4_mobile_seal_det`) | `~/.oar/pp-ocrv4_mobile_seal_det.onnx` **4 826 518 B ≈4.6 MB** (local); ficha: **4.7 MB**, Hmean **96.36 %** [ref: https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html] | **Apache-2.0** (comercial) [ref: https://huggingface.co/PaddlePaddle/PP-OCRv4_mobile_seal_det] | `paddleocr` 3.7.0 **instalado** + peso **en `~/.oar`**. Adaptador `unavailable_factory` ⇒ **falta** (es ~10 líneas: `SealRecognition`/`TextDetection` de paddleocr sobre el mismo `.onnx`) | 4.7 MB; CPU | `medible ya` **una vez escrito el adaptador** |
| **docTR / paddleocr pipeline** (`doctrl`) | ver nota §2 (`doctrl` = typo de `python-doctr`) | Apache-2.0 | no instalado; adaptador falta | ~50 MB | `medible con adaptador` |

### Plan de integración propuesto para `seal`

1. **Fichero**: `benchmarks/features/seal/bank.py`. Reemplazar
   `unavailable_factory("paddleocr", ...)` por un adaptador real
   `_paddleocr_seal_backend` en `benchmarks/common/runner.py` (junto a
   `_paddle_latex_ocr_backend`, `:746`), que use
   `from paddleocr import TextDetection` (o `SealRecognition`) con el
   `.onnx` de `~/.oar/pp-ocrv4_mobile_seal_det.onnx` y emita
   `extra["boxes"]` como cajas de sello.
2. **Dependencia**: `paddleocr` + `paddlepaddle` — **ya instalados**; no añade nada.
3. **GT**: `synthetic_seal` ya existe (`common/datasets.py:938`); la métrica de
   cajas (`box_recall`/`box_iou_mean`) la calcula el runner sin `scorer` propio
   (`features/seal/bank.py:76-77`). No hay GT humano de sellos reales local
   (OmniDocBench v1.6 no anota `category_type=seal`), así que el veredicto es
   "medible ya" **sobre GT sintético**, declarado como tal.
4. **Ejecución**: `.venv/Scripts/python.exe benchmarks/features/seal/bank.py
   --limit 8 --backends pyocrust_seal,paddleocr`.

**Trade-off rechazado.** Usar `doctrl`/docTR en `seal` no aporta: docTR no tiene
modelo de detección de **sellos** específico (es OCR de texto); el peso canónico
de PaddleOCR (`PP-OCRv4_mobile_seal_det`) es el único detector de sellos maduro y
Apache-2.0.

---

## Qué falta, en una línea por feature

- `layout`: **nada** para egret-xlarge (1 línea en `LAYOUT_HF_MODELS`).
- `text`: instalar `surya` o `paddleocr` (este ya está) + adaptador. Los anunciados sin
  fabrica (`surya`/`paddleocr`/`doctrl`) quedan **fuera del default** hasta entonces.
- `formula`: venv aparte con `unimernet` (Apache) o `texteller` + adaptador.
- `table`: instalar `docling` + adaptador TableFormer.
- `orientation`: `easyocr_rotation` (independiente, ya medible); `lcnet_doc_ori` es el
  mismo peso por otra vía (declarado como tal).
- `text_line`: `rapidocr_mobile_cls` (PP-OCRv2 de RapidAI, independiente, ya medible);
  `lcnet_textline_ori` es el mismo peso por otra vía.
- `rectification`: `opencv_perspective` (baseline clásico sin pesos, independiente, ya
  medible); un SOTA no-PaddleOCR (DocTr++/DocUNet) sigue exigiendo descarga.
- `full_page`: escribir el adaptador (docling primero, MinerU si se acepta AGPL+GPU).
- `seal`: escribir el adaptador PaddleOCR (dep. y peso **ya en el host**).

## Fuentes externas citadas

- PaddleOCR PP-StructureV3 (tamaños seal, pipeline): https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html
- PP-OCRv4_mobile_seal_det (Apache-2.0): https://huggingface.co/PaddlePaddle/PP-OCRv4_mobile_seal_det
- PP-DocLayoutV3 (repo ~132 MB; `inference.pdiparams` 131 MB): https://huggingface.co/PaddlePaddle/PP-DocLayoutV3/tree/main
- DocLayout-YOLO (AGPL-3.0): https://github.com/opendatalab/DocLayout-YOLO · https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench-imgsz1280-2501
- docling (MIT, código): https://github.com/docling-project/docling
- docling-ibm-models (MIT, pesos): https://github.com/docling-project/docling-ibm-models/blob/main/LICENSE
- MinerU 2.5 (AGPL-3.0, 1.2B): https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B
- marker-pdf (Apache-2.0 en ≥2.1.0; pesos RAIL-M $5M): https://pypi.org/project/marker-pdf/
- surya-ocr (GPL-3.0 + pesos RAIL-M $2M): https://pypi.org/project/surya-ocr/
- UniMERNet (Apache-2.0; small 773 MB / tiny 441 MB): https://github.com/opendatalab/unimernet
- TexTeller (Apache-2.0; 0.3B): https://github.com/OleehyO/TexTeller · https://huggingface.co/OleehyO/TexTeller
- nougat (MIT código, CC-BY-NC pesos): https://github.com/facebookresearch/nougat
- Table Transformer (MIT): https://github.com/microsoft/table-transformer/blob/main/LICENSE
