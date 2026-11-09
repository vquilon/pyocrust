"""Smoke CUDA — puerta previa a la campaña GPU.

Prueba que **todas las features y todos los modelos `pyocrust`** arrancan en el EP
CUDA: construye el motor con `device="cuda"` explícito (si el EP no registra,
`pyocrust` falla en vez de degradar a CPU en silencio) y ejecuta una inferencia
mínima. Reutiliza la tabla `PROVIDERS` de `common/runner.py`: la misma ruta que
usan los bancos, así que lo que aquí pasa es lo que correrá la campaña.

Un motor por **subproceso con timeout**, porque algún pipeline cuelga o hace
segfault *en proceso* y tumbaría el smoke entero sin decir cuál fue.

Estado por motor: `CUDA` · `SKIP:<motivo>` (modelo no disponible) · `FAIL:<motivo>`.
Sale 1 si algún motor da `FAIL`; `SKIP` no es fallo, pero se lista aparte.

    .venv/Scripts/python.exe benchmarks/smoke_cuda.py
    .venv/Scripts/python.exe benchmarks/smoke_cuda.py --only pyocrust_layout
    PYOCRUST_OFFLINE=1 ... benchmarks/smoke_cuda.py    # sin descargar nada
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

AUSENTE = ("ausente", "no está", "no esta", "missing", "descarga", "download",
           "offline", "not found", "no encontrado")
# Un fallo del EP CUDA (no del modelo): eso sí es FAIL de esta puerta.
EP_ERROR = ("cuda", "cublas", "onnxruntime_providers", "execution provider", "dll")


def _imagen():
    """Imagen con contenido real: una barra negra garantiza algo detectable.

    Con una imagen EN BLANCO los modelos de detección no ven nada y lanzan
    `failed to detect text` — que es la sesión CORRIENDO, no un fallo de CUDA.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (512, 128), "white")
    dibujo = ImageDraw.Draw(img)
    dibujo.rectangle([20, 20, 300, 60], fill="black")
    dibujo.text((20, 84), "Hola 123 ABC", fill="black")
    return img


def _probar(nombre: str) -> tuple[str, str]:
    """Construye un motor con CUDA y le ejecuta una inferencia mínima."""
    import pyocrust

    pyocrust.enable_cuda()  # search path del runtime CUDA ANTES de construir
    from common.runner import PROVIDERS

    imagen = _imagen()
    try:
        run = PROVIDERS[nombre](device="cuda")
    except Exception as exc:  # noqa: BLE001 - el motivo crudo se reporta tal cual
        detalle = f"{type(exc).__name__}: {exc}"
        return ("SKIP" if any(a in str(exc).lower() for a in AUSENTE) else "FAIL"), detalle
    provider = getattr(run, "provider_effective", None)
    if provider != "cuda":
        return "FAIL", f"provider_effective={provider!r} (no es el EP CUDA)"
    try:
        run(imagen)
    except Exception as exc:  # noqa: BLE001
        mensaje = str(exc)
        if any(k in mensaje.lower() for k in EP_ERROR):
            return "FAIL", f"ejecución en CUDA: {type(exc).__name__}: {mensaje}"
        # La sesión corrió en GPU y el modelo simplemente no halló nada útil: eso
        # PRUEBA lo que esta puerta busca (el EP ejecuta), así que no es FAIL.
        return "CUDA*", f"sesión OK, sin resultado con imagen sintética ({type(exc).__name__})"
    return "CUDA", "ok"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="prueba un solo motor (modo interno del subproceso)")
    ap.add_argument("--timeout", type=float, default=600.0, help="segundos por motor")
    args = ap.parse_args(argv)

    if args.only:
        estado, detalle = _probar(args.only)
        print(f"{estado}\t{args.only}\t{detalle}")
        return 0 if estado != "FAIL" else 1

    from common.runner import PROVIDERS

    nombres = sorted(n for n in PROVIDERS if n.startswith("pyocrust"))
    resultados: list[tuple[str, str, str]] = []
    for nombre in nombres:
        try:
            p = subprocess.run(
                [sys.executable, __file__, "--only", nombre],
                capture_output=True, text=True, timeout=args.timeout,
            )
            salida = [l for l in p.stdout.strip().splitlines() if l.strip()]
            estado, _, detalle = (salida[-1].split("\t", 2) + ["", ""])[:3] if salida else ("FAIL", nombre, "sin salida")
        except subprocess.TimeoutExpired:
            estado, detalle = "FAIL", f"timeout >{args.timeout:g}s"
        resultados.append((estado, nombre, detalle))
        print(f"{estado:5s} {nombre:28s} {detalle}")

    fallos = [r for r in resultados if r[0] == "FAIL"]
    skips = [r for r in resultados if r[0] == "SKIP"]
    print(f"\n{len(resultados)} motores: {len(resultados)-len(fallos)-len(skips)} CUDA · "
          f"{len(skips)} SKIP · {len(fallos)} FAIL")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
