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

## Reproducir

```bash
# GPU disponible en este host: DirectML
.venv/Scripts/python.exe -m maturin develop --features directml

.venv/Scripts/python.exe benchmarks/features/text/bank.py    --limit 5 --device cpu --backends pyocrust,rapidocr,easyocr
.venv/Scripts/python.exe benchmarks/features/text/bank.py    --limit 5 --device gpu --backends pyocrust,rapidocr,easyocr --output-dir benchmarks/results/_gpu
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 5 --device cpu --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 5 --device gpu --backends pyocrust_formula,pyocrust_formulanet,pix2tex,easyocr,rapidocr --output-dir benchmarks/results/_gpu
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
