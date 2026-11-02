# Reporte por feature: `full_page`

> **Origen: `medido`** — ejecutado por nosotros en este repo. No hay filas de `referencia` (externas) en esta tabla.

## Provenance

- **comando**: `D:\workspace\Plaiground\ac_documentalia\rust-bindings\pyocrust\.venv\Scripts\python.exe benchmarks/features/full_page/bank.py --limit 6 --device cpu`
- **dataset**: `omnidocbench_full_page` · **n** (por motor): `6` · **warmup**: `1` · **repeats**: `1` · **device**: `cpu`
- **seed**: no aplica (banco determinista, sin aleatoriedad)
- **run**: `benchmarks/results/full_page/2026-11-02_12-57-59` · **fecha**: `2026-11-02_12-57-59`
- **runtime**: {'python': '3.14.9', 'platform': 'Windows-11-10.0.26200-SP0', 'machine': 'AMD64', 'processor': 'Intel64 Family 6 Model 198 Stepping 2, GenuineIntel', 'pyocrust': '0.1.0'}

## Comparativa (media por motor)

| Motor (variante) | n | Markdown F1 ↑ | F1 bloques ↑ | CER ↓ | ms/página ↓ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| pyocrust_structure (default) | 6 | 0.158 | 0.823 | 6.820 | 8955 |

> En negrita, el mejor de cada métrica entre los motores **medidos** de `full_page`. `N/A` = no evaluada (sin GT de esa columna), nunca un `0.0` inventado.

## Saltados (`skipped`) — no cuentan como ejecutados

- `pyocrust_indra` — PyOcrRuntimeError: offline mode is active (PYOCRUST_OFFLINE) and 9 model artifact(s) for preset 'indra' are missing: det.onnx, rec.onnx, order.onnx, meta.json, mathcls.onnx, math_enc.onnx, math_dec_init.onnx, math_dec_step.onnx, math_meta.json. No network request was made. Download them with: download det.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/det.onnx; download rec.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/rec.onnx; download order.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/order.onnx; download meta.json from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/meta.json; download mathcls.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/mathcls.onnx; download math_enc.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/math_enc.onnx; download math_dec_init.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/math_dec_init.onnx; download math_dec_step.onnx from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/math_dec_step.onnx; download math_meta.json from https://huggingface.co/datalab-to/indra-ocr/resolve/bd02167fdf2005a19962cc15188f8496a2c87d3b/math_meta.json; unset PYOCRUST_OFFLINE; python -c "import pyocrust; pyocrust.VeloceOCR('indra')"

## Nota de honestidad

- Ningún motor ausente se registra como `ok`: queda `skipped` con su `pip install`.
- Las columnas sin GT no se rellenan con ceros: aparecen como `N/A` (no evaluada).
- Honestidad de proveedor: el ranking sólo cuenta filas que de verdad corrieron en `device=cpu`. Mientras `pyocrust` no exponga la selección de device (tarjeta `t_8a0f369f`), `--device gpu` queda `skipped` y un fallback CPU nunca se cuenta como GPU.

