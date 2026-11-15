# Why `pyocrust` wins or loses, and why: model, engine and measurement

> Per-feature analysis (all **9** banks). For each one: **what is measured**,
> **who wins on quality**, **who wins on time**, and **the cause** of every
> difference — separating three things that are constantly conflated:
>
> 1. **model** — architecture, family and size. It drives **quality**.
> 2. **engine** — runtime and *execution provider*: ONNX Runtime through
>    `pyocrust`'s Rust wrapper vs. the official Python APIs (the PaddleOCR
>    pipeline, `transformers`/torch, docling, ultralytics). It drives **time**.
> 3. **measurement** — timer scope, GT granularity, a stale leg. It is neither
>    model nor engine, yet it moves the number.
>
> **Every figure carries its run and date.** The single source is the published
> runs (`results/<feature>/…`) and the reports `reports/<feature>/REPORT.md`; this
> document **adds no new measurement**. Whatever cannot be attributed with the
> available evidence is marked as open.

## Reference runs (one per feature and device)

| feature | CPU run | GPU run (CUDA) |
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

Per-engine numbers live in `reports/<feature>/REPORT.md` (comparison + CPU vs
GPU); validity state in `CRITERIO_MEDICION.md`. The current GPU leg is **CUDA**
(`provider_effective='cuda'`).

## What the timer includes (and what it does not)

- The ms is **inference + post-processing**: it **excludes** model load and
  download.
- `pyocrust`, `transformers` and docling time only *forward* + post-processing.
- `ultralytics` (the `layout` YOLOs) times its whole `model.predict(...)`, which
  **includes** its internal preprocessing: its `ms/image` is the most
  conservative and does **not** time the same span (`features/layout/README.md`,
  "Nota de equidad del tiempo").
- docling in a subprocess (`tableformer`) pays *spawn* + load on top of inference.

---

## text — FUNSD · `word_f1` (n=20)

| engine | word F1 | ms/img CPU | word F1 GPU | ms/img GPU |
| :--- | ---: | ---: | ---: | ---: |
| **pp_ocrv6 medium** (`pyocrust`) | **0.800** | 2 138 | 0.779 | 2 258 |
| PP-OCRv6 medium (PaddleOCR) | 0.796 | 19 811 | 0.796 | 487 |
| pp_ocrv6 small (`pyocrust`) | 0.784 | 823 | 0.767 | 1 012 |
| pp_ocrv6 tiny (`pyocrust`) | 0.717 | 318 | 0.684 | 419 |
| rapidocr | 0.585 | 4 807 | 0.585 | 4 498 |
| easyocr | 0.401 | 3 662 | 0.399 | 1 660 |

- **Quality**: `pyocrust` medium 0.800 vs PaddleOCR's `PP-OCRv6 medium` 0.796 is
  a technical tie (Δ 0.004 at n=20). There is no **model** difference between
  those two: it is **the same PP-OCRv6 medium**. `tiny` 0.717 vs medium 0.796 is
  **model size** (tiny → medium), not engine.
- **Time (CPU)**: `pyocrust` 2 138 ms vs PaddleOCR 19 811 ms → **≈9.3× faster**
  for the same model. Cause **engine**: ORT (Rust wrapper) vs Paddle's Python
  pipeline, plus `enable_mkldnn=False` forced on this host by the oneDNN/PIR clash
  of the installed paddle (`common/runner.py:2211-2227`).
- **Time (GPU)**: it flips. PaddleOCR's `PP-OCRv6 medium` drops to 487 ms while
  `pyocrust` medium rises to 2 258 ms → Paddle's pipeline is **≈4.6× faster on
  GPU**. The "pyocrust is faster" result is a **CPU** result: on tiny models the
  GPU does not amortize the fixed cost (copies + launch).
- **CPU vs GPU leg check**: both `pyocrust` presets **lose quality on GPU** (tiny
  0.717→0.684, small 0.784→0.767, medium 0.800→0.779) while `rapidocr`
  (0.585→0.585), `easyocr` (0.401→0.399) and the external PP-OCRv6 (0.796→0.796)
  **match**. With both legs from the **same day** (2026-11-15) and the **same
  dataset**, that divergence is **EP/numerics of the engine** (`pyocrust` under
  CUDA), not a stale leg (see "Corrections").

## layout — OmniDocBench · `mAP@IoU 0.5` (n=40)

| engine | mAP CPU | ms/img CPU | mAP GPU | ms/img GPU |
| :--- | ---: | ---: | ---: | ---: |
| docling-layout-heron-101 | **0.818** | 999 | 0.818 | 71 |
| docling-layout-egret-xlarge | **0.818** | 688 | 0.817 | 77 |
| **pp-doclayoutv3 (130M)** (`pyocrust`) | 0.796 | 505 | 0.796 | 883 |
| **pp_structurev3** (`pyocrust`) | 0.751 | 2 926 | 0.751 | 3 201 |
| armaggheddon/y26-n (2.6M) (YOLO) | 0.572 | 62 | 0.572 | 33 |
| hantian/v8-x (YOLO) | 0.490 | 1 128 | 0.490 | 55 |
| omoured/v11-x (YOLO) | 0.331 | 940 | 0.331 | 65 |

- **Quality**: Heron/Egret (docling) tie for the lead at 0.818 and beat
  `pyocrust`'s `pp-doclayoutv3` (0.796). Cause **model**: they are **different
  layout models** (another family), not the same model via another route.
- The YOLOs (2.6–31.7 M, at 1024 px) are **detectors**, not layout models; their
  mAP sits at 0.33–0.57. Cause **model** (architecture + size), not engine.
- **Time**: the YOLOs are the fastest (61–1 128 ms CPU; 29–65 ms GPU), with
  `pp-doclayoutv3` at 505 ms CPU. **Measurement trap**: `ultralytics`'s ms
  includes its preprocessing while `pyocrust`/`transformers` do not (above), so
  their time advantage is **underestimated**, not inflated.
- **Measurement trap (GT)**: OmniDocBench's layout GT is per annotated block
  (`text_block`, `equation_isolated`, …) and **only classes with a declared
  equivalence score** (`features/layout/README.md:24-42`). An emitter whose block
  boundaries do not match that granularity loses mAP through a **vocabulary
  mismatch**, not because the model is worse.

## table — OmniDocBench · `TEDS` (n=8)

| engine | TEDS CPU | ms/table CPU | TEDS GPU | ms/table GPU |
| :--- | ---: | ---: | ---: | ---: |
| **slanext_wired (367M)** (`pyocrust`) | **0.914** | 577 | 0.914 | 202 |
| tableformer (docling) | 0.905 | 27 457 | 0.905 | 19 140 |
| SLANet_plus (paddleocr) | 0.889 | 247 | 0.889 | 99 |
| SLANeXt_wired (paddleocr) | 0.882 | 1 900 | N/A | N/A |
| **slanet_plus (7.8M)** (`pyocrust`) | 0.868 | 52 | 0.868 | 484 |
| table-transformer-structure-recognition | 0.790 | 718 | 0.790 | 47 |
| **pp_structurev3** (`pyocrust`) | 0.753 | 1 128 | 0.753 | 2 214 |

- **Quality**: `pyocrust` wins with **SLANeXt_wired (367M)** 0.914, followed by
  TableFormer 0.905. This is **model**: the `slanext_wired` / `slanet_plus` pair
  in `pyocrust` are two distinct networks (367,743,373 B vs 7,782,138 B →
  **≈47×** the weights), hence the TEDS jump (0.914 vs 0.868).
- **The SLANet anomaly, resolved (it was not performance).** What looked like "the
  same weights 15× slower" was a **different model**: `pyocrust_table` runs
  `slanext_wired.onnx` because `src/storage/registry.rs:203`
  (`const TASK_TABLE_STRUCTURE`) puts it first, "Wired by default", and the bank
  called it without `model_name`; the rival `paddleocr_slanet` runs **SLANet_plus**
  (7.8 M). The bank now measures both `pyocrust` models separately
  (`pyocrust_table` = SLANeXt_wired, `pyocrust_table_slanet` = SLANet_plus), so the
  legitimate `slanet_plus (7.8M)` row 0.868 **is** published. The crossed 2×2
  (engine × size) is: SLANeXt_wired 0.914 (pyocrust) / 0.882 (paddleocr);
  SLANet_plus 0.868 (pyocrust) / 0.889 (paddleocr).
- **Time**: `tableformer` 27 457 ms CPU is **docling in a subprocess** (spawn +
  load included) → **measurement**, not TableFormer being 50× slower.
- `slanet_plus (7.8M)` on GPU (52 → 484 ms) gets **worse**: a tiny model that does
  not amortize the EP's fixed cost.

## formula — OmniDocBench · LaTeX similarity (n=10)

| engine | LaTeX sim CPU | ms/formula CPU | LaTeX sim GPU | ms/formula GPU |
| :--- | ---: | ---: | ---: | ---: |
| paddle_latex_ocr | **0.653** | 11 331 | 0.653 | 3 322 |
| pix2tex | 0.555 | 4 659 | 0.566 | 1 182 |
| **pp-formulanet-s (direct)** (`pyocrust`) | 0.499 | 696 | 0.499 | 1 385 |
| **pp_structurev3 (pp-formulanet-s)** (`pyocrust`) | 0.497 | 1 052 | 0.497 | 2 031 |
| **pp_structurev3** (`pyocrust`) | 0.398 | 1 028 | 0.398 | 2 095 |
| **indra (math)** (`pyocrust`) | 0.326 | 82 | 0.326 | 708 |
| unimernet (tiny) | 0.260 | 14 927 | N/A | N/A |

- **Quality**: `paddle_latex_ocr` 0.653 and `pix2tex` 0.555 beat `pyocrust`'s
  `pp-formulanet-s` 0.499. Cause **model**: they are **different families**
  (LaTeX_OCR / pix2tex vs PP-FormulaNet), not the same model via another engine.
- **Time**: `indra` 82 ms CPU is the fastest but the worst on quality (0.326):
  speed ≠ quality. **Engine/EP**: `indra` goes from 82 ms CPU to 708 ms GPU
  (**8.6× worse**) and `pp_structurev3` from 1 028 to 2 095 ms (**2× worse**): on
  `formula` the GPU does **not** help `pyocrust`.

## full_page — OmniDocBench (EN) · `markdown_f1` (n=6)

| engine | Markdown F1 | ms/page CPU | Markdown F1 GPU | ms/page GPU |
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

- **Quality**: the **VLMs** (0.559–0.625) beat the **pipelines** (`indra` 0.556,
  `pp_structurev3` 0.530, docling 0.512). Cause **model/architecture**: they are
  **another class** — a *decoder* that generates the page markdown end to end —
  versus pipelines assembled from small models.
- **Time**: the price is brutal: the VLMs take 30.7–320.7 s/page versus 1.8 s for
  `indra` (**17×–34×** just across GLM-OCR…PaddleOCR-VL; LightOnOCR-3 0.8B reaches
  **≈179×**). The VLMs are **GPU-only** in the bank (impractical on CPU), so their
  CPU leg stays `N/A`.
- **Measurement**: `markdown_f1` is a token LCS in reading order that **blends
  content and format**; it is **not** comparable with the published olmOCR-bench or
  OmniDocBench numbers (different GT and metric definition).

## orientation / text_line / rectification / seal — synthetic (n=20)

Micro-models (4.8–31.7 M) with synthetic single-case GT. Here the question is not
"which family wins" but **engines on the same weights**.

| feature | metric | engine | value | ms CPU | ms GPU |
| :--- | :--- | :--- | ---: | ---: | ---: |
| orientation | accuracy | **pp-lcnet_x1_0_doc_ori (6.8M)** (`pyocrust`) | 1.000 | 60 | 298 |
| orientation | accuracy | pp-lcnet_x1_0_doc_ori (onnxruntime) | 1.000 | 4 | N/A |
| orientation | accuracy | craft_mlt_25k+latin_g2 (easyocr) | 0.350 | 43 311 | N/A |
| text_line | accuracy | **pp-lcnet_x1_0_textline_ori (6.8M)** (`pyocrust`) | 1.000 | 3 | 205 |
| text_line | accuracy | pp-lcnet_x1_0_textline_ori (onnxruntime) | 1.000 | 2 | N/A |
| text_line | accuracy | ch_ppocr_mobile_v2.0_cls (rapidocr) | 0.900 | 3 | N/A |
| rectification | SSIM | **uvdoc (31.7M)** (`pyocrust`) | 0.590 | 71 | 34 |
| rectification | SSIM | uvdoc (onnxruntime) | 0.595 | 74 | N/A |
| rectification | SSIM | perspective-4corner (OpenCV baseline) | 0.473 | 9 | N/A |
| seal | recall@IoU 0.5 | **pp-ocrv4_mobile_seal_det (4.8M)** (`pyocrust`) | 0.750 | 643 | 287 |
| seal | recall@IoU 0.5 | pp-ocrv4_mobile_seal_det (onnxruntime) | 0.750 | 217 | N/A |

- **Quality = model.** Where `pyocrust` and `onnxruntime` load **the same `.onnx`**
  (`mismo_peso_otra_via`), quality **matches** (1.000/1.000, 0.750/0.750); the only
  tiebreak is the **numerics** of the route (rectification: uvdoc 0.590 vs 0.595 —
  same weights, another runtime). The large differences are **model**: easyocr's
  `craft_mlt_25k` (0.350) or rapidocr's classifier (0.900) are another network.
- **Here the GPU does not pay off.** `lcnet textline` 3 ms CPU → 205 ms GPU
  (**≈68× worse**); `lcnet doc_ori` 60 → 298 ms (**5× worse**). Crossing rule: the
  GPU pays **only when the per-image compute amortizes the fixed cost** (copies +
  launch + session). The `layout` YOLOs amortize it (v8-x 1 128 → 55 ms); a 6.8 M
  classifier does not. Honest exception: `seal` (643 → 287 ms) and `rectification`
  uvdoc (71 → 34 ms) **do** improve on GPU — it depends on the model.
- **Measurement**: the GTs are **synthetic and single-case** (one orientation, one
  line, one curvature), so these figures rank engines; they do not characterize
  real-document performance.

## General rule of the EP (ONNX Runtime + CUDA)

- With ORT's **CUDA** EP, operations **without a CUDA kernel** run on the CPU EP.
  On small models the per-image fixed cost (H↔D copy + launch + session) is **not
  amortized** and the GPU comes out **slower** — visible in `pyocrust` `text`
  tiny/small/medium, `formula` (`indra` 82 → 708 ms), `table` `slanet_plus`
  (52 → 484 ms) and the micro-models.
- The **same engine flips sign by size**: the `layout` YOLO detectors (v8-x
  1 128 → 55 ms) and docling's layout models (heron 999 → 71 ms) **do** amortize
  and win on GPU.
- In the bank, a CPU *fallback* **never** counts as GPU: it only scores if
  `provider_effective` confirms a real accelerator (`GPU.md`).

## Stale leg: when an old number explains a difference

- Operating rule: **always cite run + date next to every figure.** Two figures
  from legs of different dates are **not** comparable.
- In `text` the "stale leg" premise was **dismissed**: CPU
  (`2026-11-15_20-11-47`) and GPU (`2026-11-15_21-26-21`) are from the **same day**
  and the **same dataset** (FUNSD); the quality gap in the `pyocrust` presets
  persists while the rivals match → it is the **EP/numerics of the engine**.
- **One** genuinely stale leg remains: `seal` CPU is `2026-11-08_15-28-48`
  (earlier than its GPU `2026-11-15_21-39-27`). It is published with that date; its
  quality does not depend on the EP (same weights, Δ 0).

## Recorded corrections (honest reconciliation)

- **SLANet (`table`)**: the original reading — "same weights 15× slower" — is
  **superseded**. It was a **different model** (SLANeXt_wired vs SLANet_plus), not
  engine performance. See the `table` subsection.
- **`text` "stale leg"**: the original reading — "the GPU leg is from Nov 9" — is
  **superseded** by the 2026-11-15 re-measurement (both legs same day). The cause
  of the quality divergence is the EP, not a stale leg.
- **`layout` / `pp-doclayoutv3`**: its CPU ms moved from 2 219 ms
  (`2026-11-09_14-32-35`) to 505 ms (`2026-11-15_19-53-19`) with the same engine,
  the same dataset and the same device. **Cause not established** → probe it
  before using it in a time conclusion; the current value (505 ms) is published.
