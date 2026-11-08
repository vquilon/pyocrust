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

## Estado de cumplimiento

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

**Ningún feature cumple aún el par CPU/GPU completo** → los 9 se re-miden en la
campaña definitiva. Las runs CPU actuales son internamente uniformes (`n` igual en
todos sus motores); lo que falta es la pata **GPU** con los mismos motores/`n`
(y, en `full_page`, cerrar la muestra que falla).

## Campaña definitiva (en serie, máquina libre)

Por cada feature, y **una cada vez**:

```bash
.venv/Scripts/python.exe benchmarks/features/<feature>/bank.py --limit <N> --device cpu
.venv/Scripts/python.exe benchmarks/features/<feature>/bank.py --limit <N> --device gpu
```

`<N>` = el mismo de la tabla (`20`; `40` en `layout`) y **el mismo en CPU y GPU**.
Al terminar cada par: regenerar la cadena en este orden y volver a comprobar.

```bash
.venv/Scripts/python.exe benchmarks/features/report.py --all
.venv/Scripts/python.exe benchmarks/tools_regen_derived.py   # SUMMARY/SCOREBOARD/QUALITY_VS_TIME/overview
.venv/Scripts/python.exe -m pytest benchmarks/tests -q
```
