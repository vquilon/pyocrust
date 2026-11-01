# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 8 --backends pyocrust_formulanet,pyocrust_formula,pyocrust_indra,pix2tex,texify,unimernet,pix2text,texteller,img2latex,easyocr,rapidocr --dump-outputs`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `8` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-01_22-13-00` · **fecha**: `2026-11-01_22-13-00`
- **runtime**: {'python': '3.14.9', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0'}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| easyocr (default) | 8 | 0.000 | 0.160 | 0.417 | 0% | 818 |
| pyocrust_formula (pp-formulanet-s) | 8 | 0.000 | 0.305 | 0.395 | 62% | 2257 |
| pyocrust_formulanet (direct) | 8 | 0.000 | **0.615** | **0.695** | **88%** | 1080 |
| pyocrust_indra (math) | 8 | 0.000 | 0.201 | 0.412 | 50% | **140** |
| rapidocr (default) | 8 | 0.000 | 0.104 | 0.277 | 0% | 3239 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `img2latex` — pip install img2latex
- `pix2tex` — pip install pix2tex
- `pix2text` — pip install pix2text
- `texify` — pip install texify
- `texteller` — pip install texteller
- `unimernet` — pip install unimernet (github.com/opendatalab/UniMERNet)

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).

