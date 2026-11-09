# Parche local de `ort-sys` 2.0.0-rc.13 → ORT 1.31 (kernels sm_120)

Copia vendoreada de `ort-sys` 2.0.0-rc.13 con **una sola línea** cambiada:
`build/download/dist.tsv`, fila `x86_64-pc-windows-msvc` + `cuda13,tensorrt,nvrtx,directml`.

- **Antes:** `.../ms@1.28.0/x86_64-pc-windows-msvc+cuda13,tensorrt,nvrtx,directml.tar.lzma2`
  (hash `efb686cb…`) → ORT 1.28, sin kernels sm_120.
- **Ahora:** `.../ms@1.31.0/x86_64-pc-windows-msvc+cuda13,tensorrt,nvrtx,directml.tar.lzma2`
  (hash `3a009500…`) → ORT 1.31, con `sm_120`/`sm_120a`.

**Por qué:** `oar-ocr` 0.10.x fija `ort = "=2.0.0-rc.13"` (→ ORT 1.28). En la GPU
de este host (RTX PRO 4000 Blackwell, sm_120) la ORT 1.28 falla toda inferencia
CUDA con `cudaErrorNoKernelImageForDevice`. `ort-sys` es quien elige y enlaza la
lib nativa, así que se le apunta al binario oficial de pyke para ORT 1.31 (ya
trae sm_120) **sin recompilar** el crate `ort` ni `oar-ocr`: la API C de ORT es
append-only, los bindings de rc.13 (api-27) enlazan contra la lib 1.31.

**Reconstruir el vendor** (solo si se sube de versión `ort-sys`): copiar
`ort-sys-<ver>` de `~/.cargo/registry/src/…`, editar la fila y el hash real del
dist `ms@<ver>/…` (el hash es el SHA-256 que pyke publica en su `dist.tsv`).

**Verificar** que ejecuta de verdad (no solo registra):

```bash
.venv/Scripts/python.exe benchmarks/smoke_cuda.py     # 0 FAIL
```
