# Criterio de medición del banco — **férreo**

> Regla única: **para una misma feature y métrica, todos los motores se miden sobre
> el mismo dataset y las mismas filas — lo único que cambia es el motor** — y cada
> motor se mide en CPU y en GPU. Una diferencia de `n` entre filas de una misma
> tabla invalida la comparación entera.

## Reglas

1. **Un dir de run = un solo CSV = un solo `--limit`.** Nunca copiar el CSV de una
   corrida a la carpeta de otra: al publicar se sumaban las filas y un motor salía
   con `n=40+20=60`. *(Defecto detectado y corregido en `layout/2026-11-08_16-40-00`.)*
2. **Mismo `n` para todos los motores** de la run. Una fila con `n` distinto es
   incomparable, aunque venga de la misma corrida (1 muestra fallida ya la rompe).
3. **Mismo `n` en la run CPU y en la GPU** del mismo motor: la tabla consolidada
   toma la **calidad de CPU y el tiempo de GPU**; si no midieron las mismas páginas
   la comparación engaña. `load_gpu` descarta la fila GPU cuyo `n` no cuadre.
4. **Misma muestra heterogénea y reproducida** para todos los motores: dataset con
   la revisión HF fijada (`OMNIDOCBENCH_REVISION`) y el mismo muestreo
   estratificado (mismas filas, no "20 cualesquiera").
5. **Se publica UNA sola run de referencia por (feature, device)**: la de más
   muestras por motor y, en empate, la de más motores (`report.latest_run`). El CSV
   se resuelve con `report.run_csv` — exactamente uno y **sin adivinar**: si la
   carpeta tiene varios y ninguno casa, la run no se publica.
6. **En las tablas y gráficas de SOLO calidad, una fila por motor** (CPU manda, GPU
   solo si no hay CPU). Repetir el mismo modelo sobre el mismo dataset porque sea
   cpu o gpu no aporta nada. El device se publica solo donde hay tiempos
   (`CPU_VS_GPU.md`, `QUALITY_VS_TIME.md`).
7. **Un banco nunca comparte máquina** con otro banco ni con otro proceso pesado
   (otro banco, build, pytest con modelos): infla los ms y rompe CPU vs GPU.
8. **GPU sin proveedor** (`available_providers()` vacío) → fila `skipped` con
   motivo; **nunca** se etiqueta como CPU.
9. **Un solo EP acelerador por campaña.** Todas las features de una campaña miden la
   GPU con el **mismo** proveedor (directml **o** cuda, nunca mezcla): los tiempos de
   una tabla CPU vs GPU solo son comparables dentro del mismo EP. Cambiar de EP — o tocar
   el runner — obliga a re-medir **toda** la pata GPU, no una sola feature.

## Modo CUDA

`GPU.md` §«Cómo ejecutar con CUDA (CUDA 13)» tiene la receta (causa raíz verificada;
build + runtime pendientes de confirmar end-to-end): `--features cuda` compila pero **no
registra** hasta registrar el runtime CUDA 13 **antes de importar `pyocrust`** —
`os.add_dll_directory()` a `.venv/Lib/site-packages/torch/lib` y
`.venv/Lib/site-packages/nvidia/cu13/bin/x86_64` (desde Python 3.8 Windows ignora `PATH`).
Va en un helper del runner, no repetido por banco.

## Estado de cumplimiento

> Tabla **pre-campaña** (antes de la pata GPU en DirectML). Estado vigente al pie de la sección.
> Un motor CPU-only —el que `common.runner.device_outcome(..., "gpu")` marca con motivo— **no** cuenta como desemparejamiento: no puede tener fila GPU.

Comprobar con:

```bash
.venv/Scripts/python.exe benchmarks/validez_medicion.py
```

| feature | run CPU | n | motores | run GPU | n | motores | par CPU/GPU | estado |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| text | 2026-11-06_22-46-46 | 20 | 3 | 2026-11-07_14-52-35 | 20 | 1 | OK | REHACER: motor desemparejado (easyocr) |
| formula | 2026-11-08_16-01-52 | 20 | 6 | 2026-11-07_14-53-31 | 20 | 3 | OK | REHACER: motor desemparejado (paddle_latex_ocr) |
| layout | 2026-11-08_16-16-05 | 40 | 42 | 2026-11-08_11-15-40 | 40 | 39 | OK | REHACER: motor desemparejado (docling_heron_101) |
| orientation | 2026-11-08_19-54-17 | 20 | 3 | 2026-11-07_14-58-06 | 20 | 1 | OK | REHACER: motor desemparejado (easyocr_rotation) |
| rectification | 2026-11-08_19-53-54 | 20 | 3 | 2026-11-07_14-58-17 | 20 | 1 | OK | REHACER: motor desemparejado (opencv_perspective) |
| text_line | 2026-11-06_23-57-00 | 20 | 2 | 2026-11-07_14-58-28 | 20 | 1 | OK | REHACER: motor desemparejado (lcnet_textline_ori) |
| seal | 2026-11-08_15-28-48 | 20 | 2 | 2026-11-07_14-58-34 | 20 | 1 | OK | REHACER: motor desemparejado (onnx_seal_det) |
| table | 2026-11-08_18-43-55 | 20 | 4 | 2026-11-07_14-58-46 | 20 | 1 | OK | REHACER: motor desemparejado (docling_tableformer) |
| full_page | 2026-11-08_17-40-47 | 20 | 2 | 2026-11-07_14-59-12 | 19/20 | 2 | **NO** | REHACER: `n` distinto CPU/GPU |

### Histórico — tras la pata GPU en DirectML (2026-11-08, muestra n=20)

> **Ya no vigente.** La muestra estratificada de 2026-11-09 sustituyó a las runs
> n=20 de `formula`/`table`/`full_page`; el estado actual está al pie de esta sección.

| feature | run CPU | n | run GPU | n | estado |
| :--- | :--- | ---: | :--- | ---: | :--- |
| text | 2026-11-06_22-46-46 | 20 | 2026-11-08_22-36-55 | 20 | **VALIDA** |
| formula | 2026-11-08_16-01-52 | 20 | 2026-11-08_22-41-24 | 20 | **VALIDA** |
| layout | 2026-11-08_16-16-05 | 40 | 2026-11-08_22-47-01 | 40 | **VALIDA** |
| orientation | 2026-11-08_19-54-17 | 20 | 2026-11-08_23-01-31 | 20 | **VALIDA** |
| rectification | 2026-11-08_19-53-54 | 20 | 2026-11-08_23-02-26 | 20 | **VALIDA** |
| text_line | 2026-11-06_23-57-00 | 20 | 2026-11-08_23-02-51 | 20 | **VALIDA** |
| seal | 2026-11-08_15-28-48 | 20 | 2026-11-08_23-03-03 | 20 | **VALIDA** |
| table | 2026-11-08_18-43-55 | 20 | 2026-11-08_23-03-28 | 20 | REHACER: `pyocrust_structure` está en GPU y **no** en la run CPU |
| full_page | 2026-11-08_17-40-47 | 20 | 2026-11-08_23-06-10 | 20 | REHACER: `pyocrust_indra` está en GPU y **no** en la run CPU |

**7/9 cumplen.** Las 2 que faltan **no son un problema de GPU**: no existe ninguna run CPU que
mida **todos** los motores de `DEFAULT_BACKENDS` — las medidas están repartidas en runs
**parciales** (lanzadas con `--backends` explícito), y por el criterio **no se pueden coser** en
la run de referencia: eso es justo lo que producía el `n` mezclado. Medido:

* `table` — default `pyocrust_table, tatr, paddleocr_slanet, docling_tableformer, pyocrust_structure`.
  La referencia CPU tiene 4; `pyocrust_structure` solo vive en runs parciales de 3 motores.
* `full_page` — default `pyocrust_structure, pyocrust_indra, pp_structurev3_api, docling, pdf_extract_kit`.
  La referencia CPU tiene 2; `pyocrust_indra` vive en runs de 2 motores, y `pp_structurev3_api`
  y `pdf_extract_kit` **no están medidos en CPU**.

### Estado vigente (2026-11-09, muestra estratificada)

> Fuente: salida real de `benchmarks/validez_medicion.py` (2026-11-09). Las runs
> n=20 de `formula`/`table`/`full_page` se relocalizaron a
> `results/_superseded_pre_stratified/`; la muestra vigente es `formula` n=10,
> `table` n=8, `full_page` n=6, `layout` n=40.

| feature | run CPU | n | motores | run GPU | n | motores | par CPU/GPU | estado |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| text | 2026-11-06_22-46-46 | 20 | 3 | 2026-11-08_22-36-55 | 20 | 3 | OK | VALIDA |
| formula | 2026-11-09_14-13-57 | 10 | 7 | 2026-11-09_15-10-51 | 9/10 | 5 | NO | REHACER: n distinto CPU/GPU |
| layout | 2026-11-09_14-32-35 | 40 | 42 | 2026-11-09_15-17-40 | 40 | 41 | OK | VALIDA |
| orientation | 2026-11-08_19-54-17 | 20 | 3 | 2026-11-08_23-01-31 | 20 | 1 | OK | VALIDA |
| rectification | 2026-11-08_19-53-54 | 20 | 3 | 2026-11-08_23-02-26 | 20 | 1 | OK | VALIDA |
| text_line | 2026-11-06_23-57-00 | 20 | 2 | 2026-11-08_23-02-51 | 20 | 1 | OK | VALIDA |
| seal | 2026-11-08_15-28-48 | 20 | 2 | 2026-11-08_23-03-03 | 20 | 1 | OK | VALIDA |
| table | 2026-11-09_14-22-58 | 8 | 5 | 2026-11-09_15-14-53 | 8 | 2 | OK | VALIDA |
| full_page | 2026-11-09_14-28-38 | 6 | 3 | 2026-11-09_15-16-00 | 6 | 2 | OK | VALIDA |

**8/9 VALIDA.** `formula` queda **REHACER**: la run GPU `2026-11-09_15-10-51` no es
uniforme (`pyocrust_indra` 9 `ok` + 1 error bajo DirectML), así que su `n` (9/10)
no casa con la run CPU (10). Seguimiento: `t_c7188477`.

**Pendiente:** (1) re-medir la pata GPU de `formula` con una run uniforme (mismo `n`
que la CPU) y (2) una run CPU y otra GPU COMPLETAS por feature — todos los motores de
`DEFAULT_BACKENDS` ( `ok` o `skipped` con motivo ) — con la pata GPU **priorizando CUDA**
(tarjeta *[bench][gpu] Campaña GPU en modo CUDA 13*), que por la regla 9 obliga de todos modos a
re-medir **toda** la pata GPU. Cierre: `validez_medicion.py` → **9/9 VALIDA** con
`provider_effective` acelerador en todas las filas `ok`.

## Campaña definitiva (en serie, máquina libre)

Por cada feature, y **una cada vez**:

```bash
.venv/Scripts/python.exe benchmarks/features/<feature>/bank.py --limit <N> --device cpu
.venv/Scripts/python.exe benchmarks/features/<feature>/bank.py --limit <N> --device gpu
```

`<N>` = el de la muestra estratificada vigente (`formula` 10, `table` 8,
`full_page` 6, `layout` 40; resto 20) y **el mismo en CPU y GPU**.
Al terminar cada par: regenerar la cadena en este orden y volver a comprobar.

```bash
.venv/Scripts/python.exe benchmarks/features/report.py --all
.venv/Scripts/python.exe benchmarks/tools_regen_derived.py   # SUMMARY/SCOREBOARD/QUALITY_VS_TIME/overview
.venv/Scripts/python.exe -m pytest benchmarks/tests -q
```
