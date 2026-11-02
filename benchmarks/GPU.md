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

* `provider_effective=cpu` es el valor por defecto y honesto: `pyocrust` no fija
  ningún *execution provider* de ONNX Runtime, así que sus sesiones corren en el
  EP de CPU del runtime.
* Pedir `--device gpu` **no** cuenta como GPU. Mientras no se pueda **confirmar**
  el provider, la fila/backend queda `skipped` con motivo — nunca `ok`.
* El ranking por feature (`features/report.py`, `select_device_rows`) solo cuenta
  filas cuyo `provider_effective` coincide con el device pedido: una fila que
  pidió GPU pero cayó a CPU queda **fuera** del ranking GPU.

## Por qué `--device gpu` está `skipped` hoy

Pedir GPU exige que alguien **seleccione** el *execution provider* en la sesión
ONNX y lo **confirme** después. Eso vive en `pyocrust`, no en los bancos:

* `pyocrust` construye los pipelines sin *session config*
  (`src/engines/oar_text.rs`, `src/engines/oar_structure.rs`): `ort_session_config
  = None`.
* En `oar-ocr-core 0.10.1` (`ort_infer_builders.rs`), sin `common.ort_session`
  **no se aplica ningún EP** → ONNX Runtime usa su EP por defecto = **CPU**.
* Por tanto, compilar con `--features cuda` (o instalar el wheel `pyocrust-gpu`)
  **no** basta: sin `OrtSessionConfig` sigue ejecutando en CPU.

La pieza que falta es la **tarjeta `t_8a0f369f`** (exponer `device` en
`VeloceOCR`/`TaskPredictor`, mapear a `OrtSessionConfig` y publicar el provider
efectivo). Cuando aterrice, este banco consumirá ese provider real y rellenará
`provider_effective=cuda` en las filas que de verdad corran en GPU.

Mientras tanto, el banco **se niega** a etiquetar CPU como GPU:

```
[run] pyocrust ...
  skipped: GPU pedida pero no se puede confirmar el execution provider real:
  pyocrust no expone seleccion de device ni el provider efectivo (tarjeta
  t_8a0f369f). Su API Python no acepta `device` y el pipeline no pasa
  `OrtSessionConfig`, asi que un build --features cuda sigue ejecutando en CPU;
  se niega a etiquetar CPU como GPU.
```

## Comparativa CPU vs GPU (`text` y `formula`)

Valores **medidos** por nosotros (`n=5`, `warmup=1`, `repeats=1`). CPU: run
`benchmarks/results/<feature>/2026-11-02_12-45-01` (text) y
`…/formula/2026-11-02_12-47-15`. GPU: run local del 2026-11-02_12-50 (todas las
filas `skipped`, 0 filas `ok`).

### `text` (FUNSD, 5 imágenes)

| Motor | device | provider_effective | n | CER ↓ | F1 palabra ↑ | ms/imagen ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| pyocrust | cpu | cpu | 5 | 0.402 | 0.734 | 705 |
| rapidocr | cpu | cpu | 5 | 0.400 | 0.660 | 10864 |
| easyocr | cpu | cpu | 5 | 0.467 | 0.384 | 6569 |
| pyocrust | **gpu** | **n/a** | **0** | — | — | — |

### `formula` (OmniDocBench `equation_isolated`, 5 recortes)

| Motor | device | provider_effective | n | LaTeX exacto | Similitud | F1 tokens | ms/imagen ↓ |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| pyocrust_formula | cpu | cpu | 5 | 0.000 | 0.419 | 0.526 | 2656 |
| pix2tex | cpu | cpu | 5 | 0.000 | 0.416 | 0.615 | 7588 |
| easyocr | cpu | cpu | 5 | 0.000 | 0.152 | 0.427 | 512 |
| rapidocr | cpu | cpu | 5 | 0.000 | 0.104 | 0.298 | 3216 |
| pyocrust_formula | **gpu** | **n/a** | **0** | — | — | — | — |

Relanzar (una vez `t_8a0f369f` esté):

```bash
.venv/Scripts/python.exe benchmarks/features/text/bank.py    --limit 5 --device gpu
.venv/Scripts/python.exe benchmarks/features/formula/bank.py --limit 5 --device gpu
```

Si el provider no se puede confirmar, esas runs volverán a salir `skipped` con
motivo: **no** aparecerá ninguna fila `ok` con `provider_effective=cpu` bajo un
device GPU.
