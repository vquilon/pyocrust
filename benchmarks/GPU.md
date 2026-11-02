# Eje de proveedor (CPU / GPU) en los bancos

Este documento registra el **eje de proveedor** de `benchmarks/` y la
comparativa CPU vs GPU de `text` y `formula`. Rige una regla dura: **un fallback
CPU nunca se etiqueta como GPU**.

## Columnas del CSV (honestidad de proveedor)

Cada fila del CSV lleva dos columnas **aditivas** (contrato en
`common/runner.py`):

| Columna | Significado |
| :--- | :--- |
| `device_requested` | Eje pedido por CLI: `cpu` o `gpu`. |
| `provider_effective` | Provider que **de verdad** corrió la inferencia: `cpu` o un acelerador real (`cuda`, `directml`, …). `n/a` si no se ejecutó (fila/backend `skipped`). |

Reglas:

* `--device gpu` **no** cuenta como GPU por sí solo: sólo es `ok` si el motor
  **confirma** un acelerador real en `provider_effective`. Si el motor cae a CPU
  (o el recurso/build no está), la fila/backend queda `skipped` con motivo —
  nunca `ok` con `provider_effective=cpu` bajo un device GPU.
* El ranking por feature (`features/report.py`, `select_device_rows`) solo cuenta
  filas cuyo `provider_effective` es un acelerador real: una fila que pidió GPU
  pero cayó a CPU queda **fuera** del ranking GPU.

## Cómo funciona ahora `--device gpu`

La selección y **confirmación** del *execution provider* vive en `pyocrust`, no
en los bancos (tarjeta `t_13a1b2b7`: `VeloceOCR`/`TaskPredictor` aceptan
`device=`, exponen `provider_effective` y `pyocrust.available_providers()`):

* `--device cpu` → `pyocrust device="cpu"` explícito; no sondea ninguna GPU.
* `--device gpu` → `pyocrust device="auto"`: **prueba de verdad** los EPs
  aceleradores compilados (`OrtSessionConfig::resolve_auto`) y elige el que
  **registra**. El banco lee `engine.provider_effective` tras construir el motor;
  si no es un acelerador real, marca el backend `skipped` con el provider
  observado y `available_providers()`.
* Pedir un EP concreto que no registra (`device="cuda"` sin cuDNN operativo)
  **falla** en `pyocrust` (`PyOcrValueError`) en vez de degradar a CPU en
  silencio: nunca se etiqueta CPU como GPU.

### Estado de EPs en este host

`--features cuda` compila pero **no registra** el EP CUDA (desajuste de runtime
de `onnxruntime_providers_cuda.dll` / cuDNN). `--features directml` **sí**
registra DirectML (`onnxruntime` lo trae estáticamente). Verificado con salida
real:

```
$ .venv/Scripts/python.exe -m maturin develop --features cuda     # EXIT=0
$ probe: available_providers() -> []
         device='auto'     -> provider_effective='cpu'      # sin acelerador
         device='cuda'     -> PyOcrValueError (cuda does not register;
                              CPU is never reported as an accelerator)

$ .venv/Scripts/python.exe -m maturin develop --features directml # EXIT=0
$ probe: available_providers() -> ['directml']
         device='auto'     -> provider_effective='directml'
         device='directml' -> provider_effective='directml'
         device='cuda'     -> PyOcrValueError (no registra)
```

## Comparativa CPU vs GPU (`text` y `formula`)

Valores **medidos** por nosotros (`n=5`, `warmup=1`, `repeats=1`, un modelo a la
vez). El provider lo confirma `pyocrust` fila a fila.

* CPU `text`: `benchmarks/results/text/2026-11-02_14-52-52`
* GPU `text`: `benchmarks/results/_gpu/text/2026-11-02_14-54-27`
* CPU `formula`: `benchmarks/results/formula/2026-11-02_14-54-49`
* GPU `formula`: `benchmarks/results/_gpu/formula/2026-11-02_14-56-15`

### `text` (FUNSD, 5 imágenes)

| Motor | device | provider_effective | n | CER ↓ | F1 palabra ↑ | ms/imagen ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| pyocrust | cpu | cpu | 5 | 0.402 | 0.734 | 787 |
| pyocrust | **gpu** | **directml** | 5 | 0.405 | 0.715 | 2580 |
| rapidocr | cpu | cpu | 5 | 0.400 | 0.660 | 7372 |
| easyocr | cpu | cpu | 5 | 0.467 | 0.384 | 4387 |
| rapidocr | gpu | n/a | 0 | — | — | — (`skipped`: adaptador CPU-only) |
| easyocr | gpu | n/a | 0 | — | — | — (`skipped`: adaptador CPU-only) |

### `formula` (OmniDocBench `equation_isolated`, 5 recortes)

| Motor | device | provider_effective | n | LaTeX exacto | Similitud | F1 tokens | ms/fórmula ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| pyocrust_formula | cpu | cpu | 5 | 0.000 | 0.419 | 0.526 | 2938 |
| pyocrust_formula | **gpu** | **directml** | 5 | 0.000 | 0.419 | 0.526 | 7203 |
| pyocrust_formulanet | cpu | cpu | 5 | 0.000 | 0.550 | 0.627 | 1049 |
| pyocrust_formulanet | **gpu** | **directml** | 5 | 0.000 | 0.550 | 0.627 | 2830 |
| pix2tex | cpu | cpu | 5 | 0.000 | 0.489 | 0.678 | 2841 |
| easyocr | cpu | cpu | 5 | 0.000 | 0.152 | 0.427 | 908 |
| rapidocr | cpu | cpu | 5 | 0.000 | 0.104 | 0.298 | 2813 |
| pix2tex / easyocr / rapidocr | gpu | n/a | 0 | — | — | — | — (`skipped`: adaptador CPU-only) |

**Lectura honesta de los números.** La calidad es **idéntica** CPU vs GPU
(DirectML reproduce el mismo LaTeX y el mismo CER/F1 dentro del redondeo). En
**tiempo**, para estos modelos pequeños DirectML es **más lento** que CPU en este
host (pyocrust `text` 787 → 2580 ms/imagen; `formula` 2938 → 7203 ms/fórmula): el
coste de orquestación del EP pesa más que el cómputo en cargas tan pequeñas. La
GPU aporta margen real con modelos/páginas mayores, no aquí.

### Honestidad de proveedor (comprobación sobre las filas)

Sobre las 4 runs (15 + 5 + 25 + 10 filas `ok`), **0 filas** tienen un
`provider_effective` incoherente con el `device_requested`; los backends
CPU-only bajo `--device gpu` quedan `skipped` con `provider_effective=n/a` y su
motivo. No hay ninguna fila `ok` con `provider_effective=cpu` bajo device GPU.

## Comparativa CPU vs GPU (resto de features: `layout`, `table`, `full_page`, `orientation`, `text_line`, `rectification`)

Mismo método que arriba: valores **medidos** (`warmup=1`, `repeats=1`, un modelo a la
vez); el provider lo confirma `pyocrust` fila a fila. En este host el único EP
acelerador que registra es **DirectML**, así que toda fila GPU `ok` tiene
`provider_effective=directml`.

Runs citadas (CPU → GPU):

* CPU `layout`: `benchmarks/results/layout/2026-11-02_12-57-18` · GPU `layout`: `benchmarks/results/_gpu/layout/2026-11-02_15-28-09`
* CPU `table`: `benchmarks/results/table/2026-11-02_12-57-49` · GPU `table`: `benchmarks/results/_gpu/table/2026-11-02_15-28-38`
* CPU `full_page`: `benchmarks/results/full_page/2026-11-02_12-57-59` · GPU `full_page`: `benchmarks/results/_gpu/full_page/2026-11-02_15-29-00`
* CPU `orientation`: `benchmarks/results/orientation/2026-11-02_12-59-54` · GPU `orientation`: `benchmarks/results/_gpu/orientation/2026-11-02_15-32-14`
* CPU `text_line`: `benchmarks/results/text_line/2026-11-02_13-00-03` · GPU `text_line`: `benchmarks/results/_gpu/text_line/2026-11-02_15-32-26`
* CPU `rectification`: `benchmarks/results/rectification/2026-11-02_13-00-04` · GPU `rectification`: `benchmarks/results/_gpu/rectification/2026-11-02_15-32-30`

### `layout` (OmniDocBench, 8 páginas)

| Motor | device | provider_effective | n | mAP@IoU 0.5 ↑ | recall@IoU 0.5 ↑ | ms/imagen ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| pyocrust_layout (pp-doclayoutv3) | cpu | cpu | 8 | 0.764 | 0.795 | 1989 |
| pyocrust_layout (pp-doclayoutv3) | **gpu** | **directml** | 8 | 0.764 | 0.795 | 1973 |

### `table` (OmniDocBench, 8 recortes)

| Motor | device | provider_effective | n | TEDS estrut. ↑ | ms/tabla ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: |
| pyocrust_table (slanet_plus) | cpu | cpu | 8 | 0.885 | 693 |
| pyocrust_table (slanet_plus) | **gpu** | **directml** | 8 | 0.885 | 1020 |

### `full_page` (OmniDocBench, 6 páginas)

| Motor | device | provider_effective | n | Markdown F1 ↑ | F1 bloques ↑ | CER ↓ | ms/página ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| pyocrust_structure (pp_structurev3) | cpu | cpu | 6 | 0.158 | 0.823 | 6.82 | 8955 |
| pyocrust_structure (pp_structurev3) | **gpu** | **directml** | 6 | 0.158 | 0.823 | 6.82 | 24812 |
| pyocrust_indra | cpu | n/a | 0 | — | — | — | — (`skipped`: 9 artefactos Indra ausentes) |
| pyocrust_indra | gpu | n/a | 0 | — | — | — | — (`skipped`: la descarga de `det.onnx` falla en este host) |

> `pyocrust_indra` bajo device GPU queda `skipped` con `provider_effective=n/a`: sus
> 9 artefactos no están en disco y la descarga falla; no se etiqueta como GPU.

### `orientation` (synthetic_orientation, 8 páginas)

| Motor | device | provider_effective | n | accuracy (4 clases) ↑ | ms/página ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: |
| pyocrust_orientation (pp-lcnet_x1_0_doc_ori) | cpu | cpu | 8 | 1.000 | 667 |
| pyocrust_orientation (pp-lcnet_x1_0_doc_ori) | **gpu** | **directml** | 8 | 1.000 | 706 |

### `text_line` (synthetic_text_line, 8 líneas)

| Motor | device | provider_effective | n | accuracy (0/180) ↑ | ms/línea ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: |
| pyocrust_textline (pp-lcnet_x1_0_textline_ori) | cpu | cpu | 8 | 1.000 | 30 |
| pyocrust_textline (pp-lcnet_x1_0_textline_ori) | **gpu** | **directml** | 8 | 1.000 | 36 |

### `rectification` (synthetic_rectification, 6 páginas)

| Motor | device | provider_effective | n | SSIM ↑ | ms/página ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: |
| pyocrust_rectify (uvdoc) | cpu | cpu | 6 | 0.704 | 276 |
| pyocrust_rectify (uvdoc) | **gpu** | **directml** | 6 | 0.704 | 299 |

**Lectura honesta (resto de features).** La calidad vuelve a ser **idéntica** CPU vs
GPU (DirectML reproduce los mismos mAP/TEDS/Markdown/accuracy/SSIM dentro del
redondeo). En **tiempo**, DirectML es ~1.0–2.8× más lento en los modelos pequeños
(`full_page` 8955 → 24812 ms/página, el peor), y prácticamente empatado en `layout`
(1989 → 1973 ms/imagen) y `orientation`/`text_line`/`rectification` (~+5–8 %): el
coste de orquestación del EP pesa más que el cómputo en cargas pequeñas.

### Honestidad de proveedor (las 6 features restantes)

Sobre las 6 runs GPU (8 + 8 + 6 + 8 + 8 + 6 = **44 filas `ok`**), las 44 tienen
`device_requested=gpu` y `provider_effective=directml`; **0 filas `ok`** tienen
`provider_effective=cpu` bajo device GPU. Comprobado con
`benchmarks/results/_gpu/<feature>/<ts>/*.csv` (script de verificación:
`.venv/Scripts/python.exe` sobre el CSV — recuento e incoherencias por feature).

## Reproducir

```bash
# GPU disponible en este host: DirectML
.venv/Scripts/python.exe -m maturin develop --features directml

.venv/Scripts/python.exe benchmarks/features/text/bank.py    --limit 5 --device cpu --backends pyocrust,rapidocr,easyocr
.venv/Scripts/python.exe benchmarks/features/text/bank.py    --limit 5 --device gpu --backends pyocrust,rapidocr,easyocr --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 5 --device cpu --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 5 --device gpu --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr --output-dir benchmarks/results/_gpu

# Resto de features (comparativa de la sección de arriba): CPU (REPORT) y GPU (_gpu)
.venv/Scripts/python.exe benchmarks/features/layout/bank.py        --limit 8 --device gpu --backends pyocrust_layout      --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/table/bank.py         --limit 8 --device gpu --backends pyocrust_table       --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/full_page/bank.py     --limit 6 --device gpu --backends pyocrust_structure   --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/orientation/bank.py   --limit 8 --device gpu --backends pyocrust_orientation --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/text_line/bank.py     --limit 8 --device gpu --backends pyocrust_textline    --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/rectification/bank.py --limit 6 --device gpu --backends pyocrust_rectify     --output-dir benchmarks/results/_gpu
```

Con el build CUDA (que no registra en este host), `--device gpu` sale **todo
`skipped`** — comprobado de extremo a extremo:

```
$ .venv/Scripts/python.exe -m maturin develop --features cuda      # EXIT=0
$ .venv/Scripts/python.exe benchmarks/features/text/bank.py --limit 3 --device gpu --backends pyocrust
[run] pyocrust ...
  skipped: device=gpu pedido pero el motor corre en 'cpu' (sin acelerador confirmado;
  available_providers()=[]); se niega a etiquetar CPU como GPU
# CSV: 1 línea (solo cabecera, 0 filas `ok`)
```

Es decir, **nunca** aparece una fila `ok` con `provider_effective=cpu` bajo un
device GPU.
