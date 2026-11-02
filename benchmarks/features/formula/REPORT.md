# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 5 --warmup 1 --device cpu --dump-outputs`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `5` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-02_12-39-32` · **fecha**: `2026-11-02_12-39-32`
- **runtime**: {'python': '3.14.9', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0'}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 5 | 0.000 | 0.152 | 0.427 | 0% | 562 |
| pix2tex (default) | 5 | 0.000 | 0.533 | **0.729** | **100%** | 5794 |
| pyocrust_formula (pp-formulanet-s) | 5 | 0.000 | 0.419 | 0.526 | 80% | 3063 |
| pyocrust_formulanet (direct) | 5 | 0.000 | **0.550** | 0.627 | 80% | 1107 |
| pyocrust_indra (math) | 5 | 0.000 | 0.184 | 0.432 | 40% | **196** |
| rapidocr (default) | 5 | 0.000 | 0.104 | 0.298 | 0% | 3372 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `img2latex` — pip install img2latex
- `nougat` — pip install nougat-ocr
- `pix2text` — pip install pix2text (no forzado: degrada transformers/huggingface_hub y cambia opencv-python-headless→opencv-python)
- `texify` — pip install texify
- `texteller` — pip install texteller
- `unimernet` — pip install unimernet (github.com/opendatalab/UniMERNet)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. Mientras `pyocrust` no exponga la selección de device (tarjeta `t_8a0f369f`), `--device gpu` queda `skipped` y un fallback CPU nunca se cuenta como GPU.

## Referencias externas (calidad)

> Métricas publicadas de motores que no ejecutamos en este repo. **No son comparables 1:1** con los valores `medido` de la tabla anterior: se miden sobre el dataset completo y con otro preprocesado.

### 1. Texify (repo público)

Tabla publicada en el README del repo de texify, muestreo sobre arxiv + im2latex [ref: https://github.com/VikParuchuri/texify] (consultado 2026-11-02):

| Model | BLEU ↑ | METEOR ↑ | Edit Distance ↓ |
| :--- | ---: | ---: | ---: |
| pix2tex | 0.382659 | 0.543363 | 0.352533 |
| nougat | 0.697667 | 0.668331 | 0.288159 |
| texify | **0.842349** | **0.885731** | **0.0651534** |

### 2. UniMERNet (paper arXiv)

Tabla 5 de UniMERNet paper (arXiv 2404.15254), evaluación sobre UniMER-Test [ref: https://arxiv.org/abs/2404.15254] (consultado 2026-11-02):

| Method | SPE BLEU ↑ | SPE EditDis ↓ | CPE BLEU ↑ | CPE EditDis ↓ | SCE BLEU ↑ | SCE EditDis ↓ | HWE BLEU ↑ | HWE EditDis ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pix2tex | 0.873 | 0.088 | 0.655 | 0.408 | 0.092 | 0.817 | 0.012 | 0.920 |
| Texify | 0.906 | 0.061 | 0.690 | 0.230 | 0.420 | 0.390 | 0.341 | 0.522 |
| UniMERNet | 0.917 | 0.058 | 0.916 | 0.060 | 0.616 | 0.229 | 0.921 | 0.055 |
