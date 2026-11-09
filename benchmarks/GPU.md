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

`--features directml` **sí** registra DirectML (`onnxruntime` lo trae
estáticamente) y es un EP GPU válido. `--features cuda` compila y, con las DLL
del provider en el sitio correcto **y el parche de ORT 1.31** (§«Cómo ejecutar
con CUDA»), **registra y EJECUTA** CUDA en esta GPU Blackwell. Verificado con
salida real (2026-11-09):

```
$ maturin develop --features directml                              # EXIT=0
$ probe: available_providers() -> ['directml']
         device='auto'     -> provider_effective='directml'
         device='directml' -> provider_effective='directml'
         device='cuda'     -> PyOcrValueError (no registra)

$ maturin develop --features cuda   # provider DLL junto al .pyd + parche ort-sys→ORT 1.31
$ probe (DLL del provider copiadas junto a _pyocrust_core.pyd):
         available_providers() -> ['cuda']          # registra
         device='auto' -> provider_effective='cuda' # y ahora sí ejecuta:
$ .venv/Scripts/python.exe benchmarks/smoke_cuda.py
   CUDA pyocrust ok   ...   15 motores: 13 CUDA · 2 SKIP (modelo no descargado) · 0 FAIL
```

La causa histórica del fallo de **ejecución** —GPU Blackwell **sm_120** contra la
ORT 1.28 que enlazaba el crate— está resuelta en §«Cómo ejecutar con CUDA»: se
parcheó `ort-sys` para enlazar el binario **ORT 1.31** de pyke, que sí trae
kernels `sm_120`/`sm_120a`. CUDA **registra y ejecuta**; DirectML sigue siendo un
EP GPU válido para comparar, medido por separado.

### Campaña vigente: CUDA 13 (2026-11-09)

El EP medido en la campaña vigente es **CUDA** (`provider_effective='cuda'`),
con el build `--features cuda` (ORT 1.31 parcheado, §«Cómo ejecutar con CUDA»).
Campaña en serie, un banco a la vez y máquina libre:

| feature | run GPU | n |
| :--- | :--- | ---: |
| `text` | `2026-11-09_16-19-13` | 20 |
| `formula` | `2026-11-09_16-22-29` | 10 |
| `layout` | `2026-11-09_16-25-15` | 40 |
| `orientation` | `2026-11-09_16-29-18` | 20 |
| `rectification` | `2026-11-09_16-29-33` | 20 |
| `text_line` | `2026-11-09_16-29-48` | 20 |
| `seal` | `2026-11-09_16-29-57` | 20 |
| `table` | `2026-11-09_16-30-07` | 8 |
| `full_page` | `2026-11-09_16-30-33` | 6 |

**1858 filas GPU `ok`, 0 incoherencias de proveedor** (todas las `pyocrust*` en
`cuda`); `validez_medicion.py` → **9/9 VALIDA**. Números y tiempos en
[`reports/CPU_VS_GPU.md`](reports/CPU_VS_GPU.md).


## Comparativa CPU vs GPU (`text` y `formula`)

> **Histórico (pre-estratificado, n=5, 2026-11-02; GPU con
> `provider_effective=directml`).** Estos valores ya no son la referencia
> vigente. La comparativa CPU vs GPU con la muestra estratificada (2026-11-09,
> GPU en **CUDA**) está en [`reports/CPU_VS_GPU.md`](reports/CPU_VS_GPU.md) y las
> runs en §«Campaña vigente: CUDA 13».

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

### Honestidad de proveedor (comprobación sobre las filas; histórico, DirectML 2026-11-02)

Sobre las 4 runs (15 + 5 + 25 + 10 filas `ok`), **0 filas** tienen un
`provider_effective` incoherente con el `device_requested`; los backends
CPU-only bajo `--device gpu` quedan `skipped` con `provider_effective=n/a` y su
motivo. No hay ninguna fila `ok` con `provider_effective=cpu` bajo device GPU.

## Comparativa CPU vs GPU (resto de features: `layout`, `table`, `full_page`, `orientation`, `text_line`, `rectification`)

> **Histórico (pre-estratificado, 2026-11-02; GPU con
> `provider_effective=directml`).** La comparativa vigente con la muestra
> estratificada (2026-11-09, GPU en **CUDA**) está en
> [`reports/CPU_VS_GPU.md`](reports/CPU_VS_GPU.md) y las runs en §«Campaña
> vigente: CUDA 13».

Mismo método que arriba: valores **medidos** (`warmup=1`, `repeats=1`, un modelo a la
vez); el provider lo confirma `pyocrust` fila a fila. En estas runs históricas el
EP acelerador era **DirectML** (`provider_effective=directml`); el EP vigente es
**CUDA** (§«Campaña vigente: CUDA 13»).

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

**Lectura honesta (resto de features; histórico, DirectML 2026-11-02).** La calidad vuelve a ser **idéntica** CPU vs
GPU (DirectML reproduce los mismos mAP/TEDS/Markdown/accuracy/SSIM dentro del
redondeo). En **tiempo**, DirectML es ~1.0–2.8× más lento en los modelos pequeños
(`full_page` 8955 → 24812 ms/página, el peor), y prácticamente empatado en `layout`
(1989 → 1973 ms/imagen) y `orientation`/`text_line`/`rectification` (~+5–8 %): el
coste de orquestación del EP pesa más que el cómputo en cargas pequeñas.

### Honestidad de proveedor (las 6 features restantes; histórico, DirectML 2026-11-02)

Sobre las 6 runs GPU (8 + 8 + 6 + 8 + 8 + 6 = **44 filas `ok`**), las 44 tienen
`device_requested=gpu` y `provider_effective=directml`; **0 filas `ok`** tienen
`provider_effective=cpu` bajo device GPU. Comprobado con
`benchmarks/results/_gpu/<feature>/<ts>/*.csv` (script de verificación:
`.venv/Scripts/python.exe` sobre el CSV — recuento e incoherencias por feature).

## Reproducir

```bash
# GPU vigente en este host: CUDA 13 (build --features cuda, ver §«Cómo ejecutar con CUDA»)
.venv/Scripts/python.exe -m maturin develop --release --features cuda

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

Con el build CUDA y las DLL del provider **no** colocadas junto al `.pyd`,
`available_providers()` sale `[]` y `--device gpu` sale **todo `skipped`** (el
banco se niega a etiquetar CPU como GPU). Con las DLL colocadas y el parche ORT
1.31, CUDA **registra y ejecuta**: las filas salen `ok` con
`provider_effective='cuda'` (§«Campaña vigente: CUDA 13»).

Es decir, **nunca** aparece una fila `ok` con `provider_effective=cpu` bajo un
device GPU; con el build CUDA, las filas `ok` salen con
`provider_effective='cuda'`.


## Cómo ejecutar con CUDA (CUDA 13)

> Estado (2026-11-09): build, **registro y ejecución** resueltos y verificados.
> La GPU es Blackwell **sm_120** y la ORT 1.28 que enlazaba el crate no traía
> kernels para esa arquitectura (`cudaErrorNoKernelImageForDevice`); se resolvió
> vendorizando `ort-sys` para enlazar el binario **ORT 1.31** de pyke (trae
> `sm_120`/`sm_120a`). Smoke real: **13/15 motores `CUDA ok`, 0 FAIL**.

El EP acelerador **medido** en la campaña vigente es **CUDA** (`--features cuda`;
§«Campaña vigente: CUDA 13»). DirectML (`--features directml`) va compilado dentro
de la ORT y registra sin pasos extra, pero queda como EP alternativo medido
históricamente. CUDA necesita un par de pasos extra. La causa del registro NO es
que falte la librería: es **dónde busca el provider**.


1. El `.pyd` enlaza **estáticamente** su ORT (crate Rust `ort` 2.0.0-rc.13 vía
   `oar-ocr`), que descarga **ORT 1.28.0** (`cdn.pyke.io/.../ms@1.28.0`) en
   `%LOCALAPPDATA%\ort.pyke.io`. Para `--features cuda` usa el set Windows
   `cuda13,tensorrt,nvrtx,directml`.
2. El provider CUDA vive en una DLL **aparte** (`onnxruntime_providers_cuda.dll`)
   que la ORT carga en runtime. Esa DLL importa **`cublas64_13.dll` +
   `cublasLt64_13.dll`** (CUDA 13). Esas DLL **están** en el venv pero en rutas que
   el proceso no mira:
   - `.venv/Lib/site-packages/nvidia/cu13/bin/x86_64/`
   - `.venv/Lib/site-packages/torch/lib/` (trae además cudnn9, cudart13, nvJitLink)
3. El provider CUDA no lo carga el proceso por `PATH`/`add_dll_directory`, sino
   que ORT lo busca en el **directorio del módulo** (el del `.pyd`). Por eso
   `add_dll_directory` **no** basta para que registre: hay que poner
   `onnxruntime_providers_cuda.dll` junto al `.pyd` (ver §Receta). DirectML no
   necesita DLL extra, por eso sí registra.

**Ojo:** desde Python 3.8, `LoadLibrary`/`ctypes` **ignoran `PATH`** (búsqueda
"segura") — hay que usar `os.add_dll_directory()`. Y la lib de
`D:\Environments\onnxruntime-win-x64-gpu_cuda13-1.24.4` es ORT **1.24** → **no
vale** (el crate usa 1.28; ABI distinto).

### Receta

```bash
cd D:/workspace/Plaiground/ac_documentalia/rust-bindings/pyocrust
export VIRTUAL_ENV="D:/workspace/Plaiground/ac_documentalia/rust-bindings/pyocrust/.venv"

# 1) Build con CUDA. El parche de Cargo.toml ([patch.crates-io] ort-sys) hace que
#    ort-sys enlace ORT 1.31 (kernels sm_120) automáticamente. Si el .pyd está
#    bloqueado por otro proceso, maturin puede fallar al copiar; entonces:
#    cp -f target/debug/pyocrust_core.dll pyocrust/_pyocrust_core.pyd
.venv/Scripts/maturin.exe develop --features cuda

# 2) Las DLL del provider deben quedar JUNTO al .pyd (ORT no las busca por PATH):
cp -f target/debug/onnxruntime_providers_cuda.dll target/debug/onnxruntime_providers_shared.dll pyocrust/
```

```python
# 3) Registrar el runtime CUDA 13 (Windows Py3.8+ ignora PATH → add_dll_directory).
#    Helper del paquete (una sola versión, no un bloque por banco):
import pyocrust
print(pyocrust.available_providers())
```

Paso 2 (las dependencias del provider) es barato y se hace con
`pyocrust.enable_cuda()` (`pyocrust/gpu.py`, idempotente).

**El paso que de verdad decide el registro** es distinto: ORT carga
`onnxruntime_providers_cuda.dll` con búsqueda restringida al **directorio del
módulo** (el del `.pyd`), y ese directorio NO incluye lo que se añada por
`os.add_dll_directory`. Medido: con los directorios del runtime añadidos por
`add_dll_directory` y sin las DLL del provider junto al `.pyd`,
`available_providers()` sale `[]`; copiando `onnxruntime_providers_cuda.dll` y
`onnxruntime_providers_shared.dll` **a `pyocrust/`** (los mismos que `ort-sys`
deja en `target/<perfil>/`) sale `['cuda']`. `maturin develop` solo instala el
`.pyd`, así que en un empaquetado real esas DLL tienen que viajar con él.

Con `available_providers()==['cuda']` el motor se construye con
`provider_effective='cuda'` y **la inferencia ejecuta** (smoke real: 13/15
motores `CUDA ok`, 2 SKIP por modelo no descargado, 0 FAIL).

### Por qué fallaba y cómo se cerró (ORT con kernels sm_120)

La GPU es **RTX PRO 4000 Blackwell, compute capability 12.0 (sm_120)**: las
kernels precompiladas de la **ORT 1.28** que enlazaba el crate (`oar-ocr` 0.10.x
fija `ort = "=2.0.0-rc.13"` → ORT 1.28) no cubren sm_120 →
`cudaErrorNoKernelImageForDevice`. Prueba independiente: el `onnxruntime` 1.31.1
del venv corría el MISMO `.onnx` en CUDA sin error (driver, GPU y runtime CUDA 13
funcionan; lo que faltaban eran kernels de la versión de ORT). Medido con
`grep -ao` sobre los providers: ORT 1.28 trae `sm_120` **1 vez** (residual) y
`sm_120a` **0**; ORT 1.31 trae `sm_120` 24 y `sm_120a` 29.

No hay versión publicada de `oar-ocr` que enlace ORT ≥1.31 (0.10.2 sigue fijando
rc.13). Se resolvió **sin tocar el código Rust**: `ort-sys` es el crate que
gestiona la lib nativa, así que se vendoriza (`vendor/ort-sys/`, misma versión
2.0.0-rc.13) y se edita **una línea** de `build/download/dist.tsv`, apuntando el
dist Windows `cuda13,tensorrt,nvrtx,directml` al binario oficial **`ms@1.31.0`**
de pyke (ORT 1.31, ya trae sm_120). `Cargo.toml` lo activa con
`[patch.crates-io] ort-sys = { path = "vendor/ort-sys" }`. La API C de ORT es
append-only, así que los bindings de rc.13 (api-27) enlazan contra la lib 1.31
sin recompilar el crate `ort` ni `oar-ocr`.

**Conclusión de este host:** CUDA **registra y ejecuta** en sm_120 con este
parche. DirectML sigue siendo un EP GPU válido para comparar; cada campaña mide
un solo EP (cambiar de EP obliga a re-medir toda la pata GPU).

## Hallazgo abierto (fuera de criterio de la campaña)

Bajo CUDA, `pyocrust_formula` y `pyocrust_formulanet` emiten **LaTeX aislado
vacío** en las 10 muestras de la run `2026-11-09_16-22-29` (`latex_sim` y
`latex_exact` vacíos en el CSV) → su calidad de fórmula en GPU sale `N/A`.
**No** rompe `n` ni el EP: las filas siguen `ok` con
`provider_effective='cuda'`. CPU y DirectML sí traen calidad de fórmula.
Investigación en `t_e1630cbe`.

