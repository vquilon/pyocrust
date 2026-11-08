# Reporte por feature: `formula`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/formula/bank.py --limit 20 --device cpu --output-dir benchmarks/results`
- **dataset**: `omnidocbench_formula` · **n** (por motor): `20` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **revision HF (fijada)**: `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` — misma revision en cualquier maquina; los bytes se verifican contra `benchmarks/datasets_manifest.json`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/formula/2026-11-08_16-01-52` · **fecha**: `2026-11-08_16-01-52`
- **runtime**: {'python': '3.12.11', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0', 'available_providers': []}

## Comparativa (media por motor)

| Motor (variante) | n | LaTeX exacto ↑ | Similitud ↑ | F1 tokens ↑ | Salidas con LaTeX ↑ | ms/fórmula ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| indra (math) | 20 | 0.000 | 0.211 | 0.437 | N/A | **147** |
| paddle_latex_ocr (default) | 20 | **0.050** | **0.715** | **0.829** | N/A | 7397 |
| pix2tex (default) | 20 | 0.000 | 0.585 | 0.759 | N/A | 11452 |
| pp-formulanet-s (direct) | 20 | 0.000 | 0.576 | 0.701 | N/A | 874 |
| pp_structurev3 (default) | 20 | 0.000 | 0.399 | 0.560 | N/A | 2336 |
| pp_structurev3 (pp-formulanet-s) | 20 | 0.000 | 0.607 | 0.746 | N/A | 2191 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `formula`. `N/A` = no evaluada (sin GT de esa columna **o** el motor no emite esa estructura), nunca un `0.0` inventado.

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
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. `pyocrust` confirma el EP real en `provider_effective`; si no hay acelerador, `--device gpu` queda `skipped` — un fallback CPU nunca se cuenta como GPU.

## CPU vs GPU (`device_requested` vs `provider_effective`)

> Mismo banco, mismo dataset y mismo GT en ambas columnas: la **calidad** debe coincidir; lo que cambia es el **tiempo**. La columna GPU solo lista motores que de verdad corrieron en un acelerador (`provider_effective` ∈ cuda/directml/…); un fallback CPU nunca se cuenta como GPU. `N/A` = ese motor **no** corre en GPU en este banco (queda `skipped` con motivo), no un valor de CPU repetido.

| Motor (variante) | LaTeX similarity ↑ (CPU) | LaTeX similarity ↑ (GPU) | ms CPU | ms GPU | provider GPU |
| :--- | ---: | ---: | ---: | ---: | :--- |
| indra (math) | 0.211 | 0.243 | 147 | 4182 | directml |
| paddle_latex_ocr (default) | 0.715 | 0.694 | 7397 | 1187 | cuda |
| pix2tex (default) | 0.585 | N/A | 11452 | N/A | n/a (no corre en GPU) |
| pp-formulanet-s (direct) | 0.576 | 0.497 | 874 | 2514 | directml |
| pp_structurev3 (default) | 0.399 | N/A | 2336 | N/A | n/a (no corre en GPU) |
| pp_structurev3 (pp-formulanet-s) | 0.607 | 0.196 | 2191 | 4470 | directml |

> El `provider GPU` sale del `provider_effective` real del `summary.json` GPU (`n/a` = el motor no expone ejecución GPU en este banco). No hay filas GPU inventadas: lo que no corrió en acelerador se ve como `N/A`.

