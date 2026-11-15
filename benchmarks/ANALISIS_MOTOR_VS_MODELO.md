# Qué gana `pyocrust` y por qué: modelo, motor y medida

> Análisis por feature (las **9** del banco). Para cada una: **qué se mide**,
> **quién gana en calidad**, **quién gana en tiempo** y **la causa** de cada
> diferencia, separando tres cosas que se confunden todo el tiempo:
>
> 1. **modelo** — arquitectura, familia y tamaño. Manda en **calidad**.
> 2. **motor** — runtime y *execution provider*: ONNX Runtime vía el envoltorio
>    Rust de `pyocrust` frente a las APIs oficiales de Python (el pipeline de
>    PaddleOCR, `transformers`/torch, docling, ultralytics). Manda en **tiempo**.
> 3. **medida** — alcance del cronómetro, granularidad del GT, pata vieja. No es
>    ni modelo ni motor, pero mueve el número.
>
> **Cada cifra lleva su run y su fecha.** La fuente única son las runs publicadas
> (`results/<feature>/…`) y los informes `reports/<feature>/REPORT.md`; este
> documento **no aporta ninguna medición nueva**. Lo que no se puede atribuir con
> la evidencia disponible se marca como abierto.

## Runs de referencia (una por feature y device)

| feature | run CPU | run GPU (CUDA) |
| :--- | :--- | :--- |
| text | `results/text/2026-11-15_20-11-47` | `results/_gpu/text/2026-11-15_21-26-21` |
| formula | `results/formula/2026-11-15_20-24-00` | `results/_gpu/formula/2026-11-15_21-31-15` |
| layout | `results/layout/2026-11-15_19-53-19` | `results/_gpu/layout/2026-11-15_21-34-04` |
| orientation | `results/orientation/2026-11-15_21-08-32` | `results/_gpu/orientation/2026-11-15_21-38-48` |
| rectification | `results/rectification/2026-11-15_21-24-42` | `results/_gpu/rectification/2026-11-15_21-39-04` |
| text_line | `results/text_line/2026-11-15_20-30-55` | `results/_gpu/text_line/2026-11-15_21-39-17` |
| seal | `results/seal/2026-11-08_15-28-48` | `results/_gpu/seal/2026-11-15_21-39-27` |
| table | `results/table/2026-11-15_20-06-20` | `results/_gpu/table/2026-11-15_21-39-38` |
| full_page | `results/full_page/2026-11-15_12-50-54` | `results/_gpu/full_page/2026-11-15_22-06-03` |

Los números por motor están en `reports/<feature>/REPORT.md` (comparativa + CPU vs
GPU); el estado de validez, en `CRITERIO_MEDICION.md`. La pata GPU vigente es
**CUDA** (`provider_effective='cuda'`).

## Qué entra en el cronómetro (y qué no)

- El ms es **inferencia + post-proceso**: **excluye** carga del modelo y descarga.
- `pyocrust`, `transformers` y docling cronometran solo *forward* + post-proceso.
- `ultralytics` (los YOLO de `layout`) cronometra su `model.predict(...)` **entero**,
  que **incluye** su preprocesado interno: su `ms/imagen` es el más conservador y
  **no** mide el mismo tramo (`features/layout/README.md`, «Nota de equidad del
  tiempo»).
- docling en subproceso (`tableformer`) paga *spawn* + carga además de la inferencia.

---

## text — FUNSD · `word_f1` (n=20)

| motor | F1 palabra | ms/img CPU | F1 palabra GPU | ms/img GPU |
| :--- | ---: | ---: | ---: | ---: |
| **pp_ocrv6 medium** (`pyocrust`) | **0.800** | 2 138 | 0.779 | 2 258 |
| PP-OCRv6 medium (PaddleOCR) | 0.796 | 19 811 | 0.796 | 487 |
| pp_ocrv6 small (`pyocrust`) | 0.784 | 823 | 0.767 | 1 012 |
| pp_ocrv6 tiny (`pyocrust`) | 0.717 | 318 | 0.684 | 419 |
| rapidocr | 0.585 | 4 807 | 0.585 | 4 498 |
| easyocr | 0.401 | 3 662 | 0.399 | 1 660 |

- **Calidad**: empate técnico `pyocrust` medium 0.800 vs el `PP-OCRv6 medium` de
  PaddleOCR 0.796 (Δ 0,004 con n=20). No hay diferencia de **modelo** entre esos
  dos: es **el mismo PP-OCRv6 medium**. El `tiny` 0.717 frente al medium 0.796 es
  **tamaño de modelo** (tiny → medium), no motor.
- **Tiempo (CPU)**: `pyocrust` 2 138 ms vs PaddleOCR 19 811 ms → **≈9,3× más
  rápido** el mismo modelo. Causa **motor**: ORT (envoltorio Rust) frente al
  pipeline Python de Paddle, más `enable_mkldnn=False` forzado en este host por el
  choque oneDNN/PIR del paddle instalado (`common/runner.py:2211-2227`).
- **Tiempo (GPU)**: se invierte. El `PP-OCRv6 medium` de PaddleOCR baja a 487 ms
  y `pyocrust` medium sube a 2 258 ms → el pipeline de Paddle es **≈4,6× más
  rápido en GPU**. El "pyocrust es más rápido" es un resultado **de CPU**: en
  modelos diminutos la GPU no amortiza el coste fijo (copias + lanzamiento).
- **Verificación de la pata CPU vs GPU**: los dos presets de `pyocrust` **pierden
  calidad en GPU** (tiny 0.717→0.684, small 0.784→0.767, medium 0.800→0.779)
  mientras `rapidocr` (0.585→0.585), `easyocr` (0.401→0.399) y el PP-OCRv6 externo
  (0.796→0.796) **coinciden**. Con las dos patas del **mismo día** (2026-11-15) y
  el **mismo dataset**, esa divergencia es **EP/numérica del motor** (`pyocrust`
  bajo CUDA), no una pata vieja (ver «Correcciones»).

## layout — OmniDocBench · `mAP@IoU 0.5` (n=40)

| motor | mAP CPU | ms/img CPU | mAP GPU | ms/img GPU |
| :--- | ---: | ---: | ---: | ---: |
| docling-layout-heron-101 | **0.818** | 999 | 0.818 | 71 |
| docling-layout-egret-xlarge | **0.818** | 688 | 0.817 | 77 |
| **pp-doclayoutv3 (130M)** (`pyocrust`) | 0.796 | 505 | 0.796 | 883 |
| **pp_structurev3** (`pyocrust`) | 0.751 | 2 926 | 0.751 | 3 201 |
| armaggheddon/y26-n (2.6M) (YOLO) | 0.572 | 62 | 0.572 | 33 |
| hantian/v8-x (YOLO) | 0.490 | 1 128 | 0.490 | 55 |
| omoured/v11-x (YOLO) | 0.331 | 940 | 0.331 | 65 |

- **Calidad**: Heron/Egret (docling) empatan en cabeza con 0.818 y baten al
  `pp-doclayoutv3` de `pyocrust` (0.796). Causa **modelo**: son **layout models
  distintos** (otra familia), no el mismo modelo por otra vía.
- Los YOLO (2,6–31,7 M, a 1024 px) son **detectores**, no layout models; su mAP
  queda en 0,33–0,57. Causa **modelo** (arquitectura + tamaño), no motor.
- **Tiempo**: los YOLO son los más rápidos (61–1 128 ms CPU; 29–65 ms GPU), con
  `pp-doclayoutv3` en 505 ms CPU. **Trampa de medida**: el ms de `ultralytics`
  incluye su preprocesado y el de `pyocrust`/`transformers` no (arriba), así que
  su ventaja de tiempo está **subestimada**, no inflada.
- **Trampa de medida (GT)**: el GT de layout de OmniDocBench va por bloque anotado
  (`text_block`, `equation_isolated`, …) y **solo puntúan las clases con
  equivalencia declarada** (`features/layout/README.md:24-42`). Un emisor cuyos
  límites de bloque no casen con esa granularidad baja mAP por **desajuste de
  vocabulario**, no por ser peor modelo.

## table — OmniDocBench · `TEDS` (n=8)

| motor | TEDS CPU | ms/tabla CPU | TEDS GPU | ms/tabla GPU |
| :--- | ---: | ---: | ---: | ---: |
| **slanext_wired (367M)** (`pyocrust`) | **0.914** | 577 | 0.914 | 202 |
| tableformer (docling) | 0.905 | 27 457 | 0.905 | 19 140 |
| SLANet_plus (paddleocr) | 0.889 | 247 | 0.889 | 99 |
| SLANeXt_wired (paddleocr) | 0.882 | 1 900 | N/A | N/A |
| **slanet_plus (7,8M)** (`pyocrust`) | 0.868 | 52 | 0.868 | 484 |
| table-transformer-structure-recognition | 0.790 | 718 | 0.790 | 47 |
| **pp_structurev3** (`pyocrust`) | 0.753 | 1 128 | 0.753 | 2 214 |

- **Calidad**: gana `pyocrust` con **SLANeXt_wired (367M)** 0.914, seguido de
  TableFormer 0.905. Es **modelo**: la pareja `slanext_wired` / `slanet_plus` de
  `pyocrust` son dos redes distintas (367 743 373 B vs 7 782 138 B → **≈47×** de
  pesos) y de ahí su salto de TEDS (0.914 vs 0.868).
- **La anomalía del SLANet, resuelta (no era rendimiento).** Lo que parecía "el
  mismo peso 15× más lento" era **modelo distinto**: `pyocrust_table` corre
  `slanext_wired.onnx` porque `src/storage/registry.rs:203`
  (`const TASK_TABLE_STRUCTURE`) lo pone primero, "Wired by default", y el banco
  lo llamaba sin `model_name`; el rival `paddleocr_slanet` corre **SLANet_plus**
  (7,8 M). El banco ya mide los dos modelos de `pyocrust` por separado
  (`pyocrust_table` = SLANeXt_wired, `pyocrust_table_slanet` = SLANet_plus), así
  que la fila legítima `slanet_plus (7,8M)` 0.868 **sí** se publica. El 2×2
  cruzado (motor × tamaño) es: SLANeXt_wired 0.914 (pyocrust) / 0.882 (paddleocr);
  SLANet_plus 0.868 (pyocrust) / 0.889 (paddleocr).
- **Tiempo**: `tableformer` 27 457 ms CPU es **docling en subproceso** (spawn +
  carga incluidos) → **medida**, no que TableFormer sea 50× más lento.
- `slanet_plus (7,8M)` en GPU (52 → 484 ms) **empeora**: modelo diminuto que no
  amortiza el coste fijo del EP.

## formula — OmniDocBench · similitud LaTeX (n=10)

| motor | LaTeX sim CPU | ms/fórmula CPU | LaTeX sim GPU | ms/fórmula GPU |
| :--- | ---: | ---: | ---: | ---: |
| paddle_latex_ocr | **0.653** | 11 331 | 0.653 | 3 322 |
| pix2tex | 0.555 | 4 659 | 0.566 | 1 182 |
| **pp-formulanet-s (direct)** (`pyocrust`) | 0.499 | 696 | 0.499 | 1 385 |
| **pp_structurev3 (pp-formulanet-s)** (`pyocrust`) | 0.497 | 1 052 | 0.497 | 2 031 |
| **pp_structurev3** (`pyocrust`) | 0.398 | 1 028 | 0.398 | 2 095 |
| **indra (math)** (`pyocrust`) | 0.326 | 82 | 0.326 | 708 |
| unimernet (tiny) | 0.260 | 14 927 | N/A | N/A |

- **Calidad**: `paddle_latex_ocr` 0.653 y `pix2tex` 0.555 baten al
  `pp-formulanet-s` de `pyocrust` 0.499. Causa **modelo**: son **familias
  distintas** (LaTeX_OCR / pix2tex frente a PP-FormulaNet), no el mismo modelo por
  otro motor.
- **Tiempo**: `indra` 82 ms CPU es el más rápido pero el peor en calidad
  (0.326): velocidad ≠ calidad. **Motor/EP**: `indra` pasa de 82 ms CPU a 708 ms
  GPU (**8,6× peor**) y `pp_structurev3` de 1 028 a 2 095 ms (**2× peor**): en
  `formula` la GPU **no** ayuda a `pyocrust`.

## full_page — OmniDocBench (EN) · `markdown_f1` (n=6)

| motor | Markdown F1 | ms/página CPU | Markdown F1 GPU | ms/página GPU |
| :--- | ---: | ---: | ---: | ---: |
| LightOnOCR-3 (0.8B) (VLM) | N/A | N/A | **0.625** | 320 707 |
| PaddleOCR-VL (0.9B) (VLM) | N/A | N/A | 0.597 | 60 907 |
| LightOnOCR-3 (4B) (VLM) | N/A | N/A | 0.590 | 72 249 |
| LightOnOCR-2-1B (1B) (VLM) | N/A | N/A | 0.588 | 44 737 |
| GLM-OCR (0.9B) (VLM) | N/A | N/A | 0.559 | 30 716 |
| **indra (math)** (`pyocrust`) | 0.556 | 1 251 | 0.556 | 1 793 |
| **pp_structurev3** (`pyocrust`) | 0.530 | 3 652 | 0.528 | 4 350 |
| docling-default (pipeline) | 0.512 | 26 739 | 0.512 | 22 740 |
| PP-StructureV3 (paddleocr) | 0.427 | 180 058 | 0.496 | 68 269 |

- **Calidad**: ganan los **VLM** (0.559–0.625) a los **pipelines** (`indra` 0.556,
  `pp_structurev3` 0.530, docling 0.512). Causa **modelo/arquitectura**: son **otra
  clase** — un *decoder* que genera el markdown de la página de punta a punta —
  frente a pipelines ensamblados de modelos pequeños.
- **Tiempo**: el precio es brutal: los VLM tardan 30,7–320,7 s/página frente a
  1,8 s de `indra` (**17×–34×** solo en el tramo GLM-OCR…PaddleOCR-VL; LightOnOCR-3
  0.8B llega a **≈179×**). Los VLM son **GPU-only** en el banco (en CPU son
  impracticables), así que su pata CPU queda `N/A`.
- **Medida**: `markdown_f1` es un LCS de tokens en orden de lectura que **mezcla
  contenido y formato**; **no** es comparable con los números de olmOCR-bench ni
  de OmniDocBench publicados (otro GT y otra definición de la métrica).

## orientation / text_line / rectification / seal — sintético (n=20)

Micro-modelos (4,8–31,7 M) con GT sintético de un solo caso. Aquí la pregunta no
es "quién gana" entre familias, sino **motores del mismo peso**.

| feature | métrica | motor | valor | ms CPU | ms GPU |
| :--- | :--- | :--- | ---: | ---: | ---: |
| orientation | accuracy | **pp-lcnet_x1_0_doc_ori (6.8M)** (`pyocrust`) | 1.000 | 60 | 298 |
| orientation | accuracy | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 4 | N/A |
| orientation | accuracy | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 43 311 | N/A |
| text_line | accuracy | **pp-lcnet_x1_0_textline_ori (6.8M)** (`pyocrust`) | 1.000 | 3 | 205 |
| text_line | accuracy | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 2 | N/A |
| text_line | accuracy | ch_ppocr_mobile_v2.0_cls (rapidocr) | 0.900 | 3 | N/A |
| rectification | SSIM | **uvdoc (31.7M)** (`pyocrust`) | 0.590 | 71 | 34 |
| rectification | SSIM | uvdoc (onnxruntime) | 0.595 | 74 | N/A |
| rectification | SSIM | perspective-4corner (baseline OpenCV) | 0.473 | 9 | N/A |
| seal | recall@IoU 0.5 | **pp-ocrv4_mobile_seal_det (4.8M)** (`pyocrust`) | 0.750 | 643 | 287 |
| seal | recall@IoU 0.5 | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A |

- **Calidad = modelo.** Donde `pyocrust` y `onnxruntime` cargan **el mismo `.onnx`**
  (`mismo_peso_otra_via`), la calidad **coincide** (1.000/1.000, 0.750/0.750); el
  único desempate es la **numérica** de la vía (rectification: uvdoc 0.590 vs
  0.595 — mismo peso, otro runtime). Las diferencias grandes son de **modelo**: el
  `craft_mlt_25k` de easyocr (0.350) o el clasificador de rapidocr (0.900) son
  otra red.
- **Aquí la GPU no compensa.** `lcnet textline` 3 ms CPU → 205 ms GPU (**≈68×
  peor**); `lcnet doc_ori` 60 → 298 ms (**5× peor**). Regla del cruce: la GPU paga
  **solo cuando el cómputo por imagen amortiza el coste fijo** (copias +
  lanzamiento + sesión). Los YOLO de `layout` lo amortizan (v8-x 1 128 → 55 ms);
  un clasificador de 6,8 M no. Excepción honesta: `seal` (643 → 287 ms) y
  `rectification` uvdoc (71 → 34 ms) **sí** mejoran en GPU — depende del modelo.
- **Medida**: los GT son **sintéticos y de un solo caso** (una orientación, una
  línea, una curvatura), así que estas cifras ordenan motores, no caracterizan el
  rendimiento en documentación real.

## Regla general del EP (ONNX Runtime + CUDA)

- Con el EP **CUDA** de ORT, las operaciones **sin kernel CUDA** las ejecuta el EP
  de CPU. En modelos pequeños, el coste fijo por imagen (copia H↔D + lanzamiento +
  sesión) **no se amortiza** y la GPU sale **más lenta** — se ve en `pyocrust`
  `text` tiny/small/medium, `formula` (`indra` 82 → 708 ms), `table`
  `slanet_plus` (52 → 484 ms) y los micro-modelos.
- El **mismo motor cambia de signo según el tamaño**: los detectores YOLO de
  `layout` (v8-x 1 128 → 55 ms) y los layout models de docling (heron 999 → 71 ms)
  **sí** amortizan y ganan en GPU.
- En el banco, un *fallback* CPU **nunca** se cuenta como GPU: solo puntúa si
  `provider_effective` confirma un acelerador real (`GPU.md`).

## Pata obsoleta: cuándo un número viejo explica una diferencia

- Regla operativa: **citar siempre run + fecha junto a cada cifra.** Dos cifras de
  patas de fechas distintas **no** son comparables.
- En `text` la premisa de "pata vieja" quedó **descartada**: CPU
  (`2026-11-15_20-11-47`) y GPU (`2026-11-15_21-26-21`) son del **mismo día** y el
  **mismo dataset** (FUNSD); la diferencia de calidad en los presets de `pyocrust`
  persiste mientras los rivales coinciden → es **EP/numérica del motor**.
- Queda **una** pata genuinamente vieja: `seal` CPU es
  `2026-11-08_15-28-48` (anterior a su GPU `2026-11-15_21-39-27`). Se publica con
  esa fecha; su calidad no depende del EP (mismo peso, Δ 0).

## Correcciones registradas (reconciliación honesta)

- **SLANet (`table`)**: la lectura original — "mismo peso 15× más lento" — está
  **superada**. Era **modelo distinto** (SLANeXt_wired vs SLANet_plus), no
  rendimiento del motor. Ver la subsección de `table`.
- **`text` "pata obsoleta"**: la lectura original — "la pata GPU es del 9-nov" —
  está **superada** por la re-medida del 2026-11-15 (ambas patas del mismo día).
  La causa de la divergencia de calidad es el EP, no una pata vieja.
- **`layout` / `pp-doclayoutv3`**: su ms CPU pasó de 2 219 ms
  (`2026-11-09_14-32-35`) a 505 ms (`2026-11-15_19-53-19`) con el mismo motor, el
  mismo dataset y el mismo device. **Causa no establecida** → seccionar antes de
  usarlo en una conclusión de tiempo; se publica el valor vigente (505 ms).
