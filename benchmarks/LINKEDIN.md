# Borrador de post para LinkedIn

## Nota vigente B9 — no publicar como comparación (2026-10-31)

Prevalece esta nota sobre el post histórico inferior. Crítico R2:
**APROBADO acotado** al banco; regresiones comunicadas **21 pass, 17 deselected**,
no suite global ni reejecución documental. La run
`results/2026-10-31_23-37-34/summary.json` registra inferencia real **5/5 Tiny
(`text`), 5/5 Indra (`full_page`, `math`) y 5/5 RapidOCR (`text`)**, sin errores.
Artefactos recuperados tras timeout de la herramienta; exit code del runner
no observado, sin certificación de terminación correcta.
Estructura/fórmula **skipped**: seis artefactos PP-StructureV3 ausentes en offline.
FUNSD sin GT Markdown/bloques: **calidad Markdown N/A / no evaluada**, no calidad
matemática certificada. CPU solicitado, `provider_effective=unverified`,
`repeats=1`, `warmup=1`; `--device gpu` se rechaza con skip sin fallback CPU.
**Sin ganador general, claims de rendimiento GPU ni comparación publicable con
cinco muestras.** Contrato vigente: [README del banco](README.md), 22 columnas,
manifiesto con GT legítimo, fórmula desde `result.formulas` (no Markdown de página)
y legacy `cer_ord=None`.

## Histórico — borrador 2026-10-25, no listo para publicar

Las instrucciones de publicación, cifras y afirmaciones siguientes se conservan
solo como registro original; no son recomendaciones ni conclusiones vigentes.

> Listo para copiar y pegar. Los números salen **tal cual** de
> `benchmarks/output_examples/benchmark_summary.json` (run `2026-10-25_22-26-51`),
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
Hugging Face), las **mismas imágenes** para los tres motores, métricas de calidad
CER / WER / F1-palabra (Levenshtein implementado a mano) y velocidad en ms por
página. Todo en **CPU**, sin GPU y con el modelo **Tiny** de `pyocrust`. Aviso
honesto: **n = 30 imágenes por backend** — es una primera pasada, no un paper.

**Los números** (30 imágenes por backend, FUNSD, CPU):

| Motor | F1 palabra ↑ | WER ord. ↓ | CER ↓ | WER ↓ | ms/pág. ↓ | págs/s ↑ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **pyocrust** | **0,745** | **0,325** | 0,487 | 0,670 | **643** | **1,56** |
| **rapidocr** | 0,607 | 0,487 | **0,482** | 0,699 | 4534 | 0,22 |
| **easyocr** | 0,426 | 0,670 | 0,526 | 0,794 | 3247 | 0,31 |

**Lo que gana `pyocrust`:**

* **Velocidad**: 643 ms/página frente a 4534 de `rapidocr` (**≈7× más rápido**)
  y 3247 de `easyocr` (**≈5× más rápido**); 1,56 páginas/s frente a 0,22 y 0,31.
* Mejor **F1 de palabra** (0,745 vs. 0,607 de `rapidocr` y 0,426 de `easyocr`).
* Mejor **WER con orden neutralizado** (0,325, frente a 0,487 y 0,670): mide
  reconocimiento, no cómo se recorre la página.
* Mayor **confianza media** reportada por el motor (0,935 vs. 0,819 y 0,655),
  aunque cada motor usa su propia escala y no es directamente comparable.

**Lo que pierde, o donde empatan** (honestidad primero):

* En **CER crudo** gana `rapidocr` por muy poco: 0,482 frente a 0,487. Pero esa
  columna es la **única** que mide también el orden de lectura, y ahí el
  formulario multicolumna penaliza más a `pyocrust` que a `rapidocr` (0,162 de
  CER frente a 0,073). Por eso el ranking lo decide el **WER orden-neutralizado**,
  donde `pyocrust` gana por 0,162.
* `easyocr` queda por detrás en las tres métricas de calidad y es el más lento
  en la cola (p95 de **5,1 s por página**, con mucha dispersión entre imágenes).
* **Exact-match = 0** en los tres: ninguno reconstruye la página carácter a
  carácter.
* Y la letra pequeña importa: es un modelo **Tiny** contra los modelos por defecto
  de `rapidocr` y `easyocr`, en **CPU** y con **30 imágenes**. Son indicios, no un
  veredicto.

**Los gráficos:**

* `benchmark_quality_vs_speed.png` — calidad (F1) frente a velocidad: el que mejor
  cuenta la historia.
* `benchmark_quality.png` — CER y F1 de palabra por motor.
* `benchmark_speed.png` — ms por página y páginas por segundo.
* `benchmark_table.png` (y `.svg`) — la tabla anterior, renderizada.

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
  run `2026-10-25_22-26-51`, n = 30 por backend):

  | Dato | `pyocrust` | `rapidocr` | `easyocr` |
  | :--- | ---: | ---: | ---: |
  | `n` | 30 | 30 | 30 |
  | `cer` | 0.487 | 0.482 | 0.526 |
  | `wer` | 0.670 | 0.699 | 0.794 |
  | `cer_ord` | 0.325 | 0.487 | 0.670 |
  | `wer_ord` | 0.325 | 0.487 | 0.670 |
  | `word_f1` | 0.745 | 0.607 | 0.426 |
  | `exact_match` | 0.000 | 0.000 | 0.000 |
  | `mean_ms` | 643 | 4534 | 3247 |
  | `median_ms` | 641 | 4309 | 2517 |
  | `p95_ms` | 785 | 8134 | 5110 |
  | `pages_per_s` | 1.56 | 0.22 | 0.31 |
  | `mean_confidence` | 0.935 | 0.819 | 0.655 |

* **`≈7×`** = `rapidocr.mean_ms / pyocrust.mean_ms` = 4533,9 / 642,6 = **7,06×**.
* **`≈5×`** = `easyocr.mean_ms / pyocrust.mean_ms` = 3246,6 / 642,6 = **5,05×**.
* Los valores sin redondear están en `benchmarks/output_examples/benchmark_summary.json`;
  la métrica de tiempo completa (mediana y p95) también.
* **`B4` ya revisó la metodología** y sus hallazgos se aplicaron: el CER/WER crudos
  perdieron la marca de "mejor" (miden orden de lectura), se añadió `wer_ord` y el
  *warmup* ya no consume muestras. El post refleja esa corrección.
