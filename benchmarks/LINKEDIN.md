# Borrador de post para LinkedIn

## Nota vigente B9 — no publicar como comparación (2026-10-31)

Prevalece esta nota sobre el post histórico inferior. Crítico R2:
**APROBADO acotado** al banco; regresiones comunicadas **21 pass, 17 deselected**,
no suite global ni reejecución documental. La run
`results/2026-10-31_23-37-34/summary.json` registra inferencia real **5/5 Tiny
(`text`), 5/5 Indra (`full_page`, `math`) y 5/5 RapidOCR (`text`)**, sin errores.
Artefactos recuperados tras timeout de la herramienta; exit code del runner
no observado, sin certificación de terminación correcta.
Estructura/fórmula **skipped**: offline con seis artefactos PP-StructureV3 ausentes,
no generan filas. FUNSD sin GT Markdown/bloques: **calidad Markdown N/A / no evaluada**, no calidad
matemática certificada. CPU solicitado, `provider_effective=unverified`,
`repeats=1`, `warmup=1`; `--device gpu` se rechaza con skip sin fallback CPU.
**Sin ganador general, claims de rendimiento GPU ni comparación publicable con
cinco muestras.** Contrato vigente: [README del banco](README.md), 22 columnas,
manifiesto con GT legítimo, fórmula desde `result.formulas` (no Markdown de página)
y legacy `cer_ord=None`.

**Defectos abiertos (B8) que invalidan conclusiones publicadas:**
1. **CRÍTICO** — `markdown_f1`/`block_f1` vacíos en FUNSD: la tabla publicada
   encabeza con `F1 Markdown ↑` pero todas las filas muestran **N/A** porque
   FUNSD no trae GT Markdown/bloques (`run_benchmarks.py:227,525-526,542`).
2. **MAYOR** — `markdown_f1` mide LCS de tokens ordenados, no equivalencia de
   documento: reordenar secciones baja la puntuación de 1.0 a 0.6667
   (`run_benchmarks.py:203-218`).
3. **MAYOR** — `block_f1` compara etiquetas crudas sin normalizar; no comparable
   entre motores (`run_benchmarks.py:221-224,314`).
4. **MAYOR** — `model_variant` es nominal (`tiny`/`default`/`math`); `provider_effective="unverified"`
   no demuestra el provider ejecutado (`run_benchmarks.py:429,445`).
5. **MEDIO** — memoria entre imágenes no medida; CPU/RAM no en meta
   (`run_benchmarks.py:439,471,482,531-556`).
6. **PEQUEÑO** — sin versiones de datasets/HF/pesos; no reproducible exactamente
   entre máquinas (`run_benchmarks.py:531-556`).

## Histórico — borrador 2026-10-25, no listo para publicar

Las instrucciones de publicación, cifras y afirmaciones siguientes se conservan
solo como registro original; no son recomendaciones ni conclusiones vigentes.

> Listo para copiar y pegar. Los números salen **tal cual** de
> `benchmarks/results/2026-10-31_23-37-34/summary.json` (run `2026-10-31_23-37-34`),
> redondeados a la precisión que usa la tabla publicada. Los gráficos son los
> ficheros de `benchmarks/output_examples/`.

---

## Post

**¿Se puede escribir un OCR nativo en Rust y llamarlo desde Python sin perder lo
bueno de cada lado?** Llevo unos días con *pyocrust* y he medido lo que hay, sin
maquillar los resultados. 🦀🐍

**Qué es `pyocrust`.** Un wrapper nativo en Rust (PyO3 + Maturin) sobre el crate
`oar-ocr` que unifica OCR de texto (PP-OCRv6) y análisis de estructura documental
(PP-StructureV3) detrás de una sola API de Python.

**Cómo lo he medido.** Dataset real **FUNSD** (formularios escaneados, vía
Hugging Face), las **mismas imágenes** para los motores comparables, métricas de
calidad `word_f1` y `wer_ord` (neutralizan el orden de lectura) más `cer`/`wer`
crudos como referencia, y velocidad en ms por página. Todo en **CPU**, sin GPU
y con el modelo **Tiny** de `pyocrust` en `text`. Aviso honesto: **n = 5 imágenes
por backend** — es una primera pasada, no un paper.

**Los números** (5 imágenes por backend, FUNSD, CPU):

| Motor | task_type | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. ↓ | págs/s ↑ |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **pyocrust** (tiny) | `text` | **0.734** | **0.340** | 0.402 | 0.628 | **1290** | **0.78** |
| **rapidocr** (default) | `text` | 0.660 | 0.431 | 0.400 | 0.654 | 9355 | 0.11 |
| **pyocrust_indra** (math) | `full_page` | 0.457 | 0.648 | 1.552 | 0.815 | 644 | 1.55 |

`structure`/`formula` **skipped** en esta run: offline con seis artefactos
PP-StructureV3 ausentes, no generan filas.

**Lo que gana `pyocrust` en `text`:**

* **Velocidad**: 1290 ms/página frente a 9355 de `rapidocr` (**≈7.3× más rápido**);
  0.78 páginas/s frente a 0.11.
* Mejor **F1 de palabra** (0.734 vs. 0.660 de `rapidocr`).
* Mejor **WER con orden neutralizado** (0.340, frente a 0.431): mide
  reconocimiento, no cómo se recorre la página.

**Lo que pierde, o donde empatan** (honestidad primero):

* En **CER crudo** gana `rapidocr` por muy poco: 0.400 frente a 0.402. Pero esa
  columna mide también el orden de lectura, y ahí el formulario multicolumna
  penaliza más a `pyocrust` que a `rapidocr`. Por eso el ranking lo decide el
  **WER orden-neutralizado**, donde `pyocrust` gana por 0.091.
* **Exact-match = 0** en los dos: ninguno reconstruye la página carácter a
  carácter.
* **F1 Markdown y F1 bloques = N/A** para todos los backends: FUNSD no trae
  GT Markdown/LaTeX/bloques, así que esas métricas titular no aportan información
  en esta run.
* Y la letra pequeña importa: es un modelo **Tiny** contra el modelo por defecto
  de `rapidocr`, en **CPU** y con **5 imágenes**. Son indicios, no un veredicto.
  Además `model_variant` es nominal y `provider_effective="unverified"` no
  demuestra el provider ejecutado.

**Qué mide de verdad y qué falta.** El banco de pruebas es reproducible (dataset
real, CSV por imagen, `warmup` común y metadatos de la run). Lo siguiente es una
comparación de igual a igual (mismo tamaño de modelo), GPU, una muestra mucho
mayor y un caso en **español**.

Si estás peleándote con OCR de documentos y quieres el detalle de la metodología,
te lo cuento en los comentarios. 🚀

#Rust #Python #OCR #PyO3 #ComputerVision #OpenSource #IA #MachineLearning

---

## Notas de publicación (no forman parte del post)

* **Gráficos a adjuntar:** `benchmark_quality_vs_speed.png` como imagen principal;
  `benchmark_quality.png`, `benchmark_speed.png` y `benchmark_table.png` en los
  comentarios.
* **Trazabilidad de los números** (todas las cifras del post provienen del JSON,
  run `2026-10-31_23-37-34`, n = 5 por backend):

  | Dato | `pyocrust` (tiny; text) | `rapidocr` (default; text) | `pyocrust_indra` (math; full_page) |
  | :--- | ---: | ---: | ---: |
  | `n` | 5 | 5 | 5 |
  | `cer` | 0.402 | 0.400 | 1.552 |
  | `wer` | 0.628 | 0.654 | 0.815 |
  | `wer_ord` | 0.340 | 0.431 | 0.648 |
  | `word_f1` | 0.734 | 0.660 | 0.457 |
  | `exact_match` | 0.000 | 0.000 | 0.000 |
  | `mean_ms` | 1290 | 9355 | 644 |
  | `median_ms` | 1270 | 6888 | 636 |
  | `p95_ms` | 1751 | 16607 | 733 |
  | `pages_per_s` | 0.78 | 0.11 | 1.55 |
  | `mean_confidence` | 0.951 | 0.816 | 0.000 |

* **`≈7.3×`** = `rapidocr.mean_ms / pyocrust.mean_ms` = 9354.8 / 1290.2 = **7.25×**.
* Los valores sin redondear están en `benchmarks/results/2026-10-31_23-37-34/summary.json`;
  la métrica de tiempo completa (mediana y p95) también.
* **Defectos abiertos (B8)** que inhabilitan publicar este post como comparación:
  (1) `markdown_f1`/`block_f1` vacíos en FUNSD (GT Markdown/bloques ausente);
  (2) `markdown_f1` es LCS de tokens ordenados, no equivalencia de documento;
  (3) `block_f1` compara etiquetas crudas sin normalizar;
  (4) `model_variant` nominal, `provider_effective="unverified"`;
  (5) memoria no medida, CPU/RAM no en meta;
  (6) sin versiones de datasets/HF/pesos.
* **`B4` ya revisó la metodología** y sus hallazgos se aplicaron: el CER/WER crudos
  perdieron la marca de "mejor" (miden orden de lectura), se añadió `wer_ord` y el
  *warmup* ya no consume muestras.
