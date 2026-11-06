# Mapa de features, módulos y modelos (pyocrust ↔ `oar-ocr`)

> Documento **consolidado**: qué features del crate base se usan y para qué, qué
> módulo de `oar-ocr` cubre cada pieza, y qué modelo sirve a cada tarea/preset.
> Fuentes: `DESIGN.md` §1.1/§1.2/§3.1.2/§3.1.3/ADR-010, `IMPLEMENTATION_AUDIT.md`,
> `Cargo.toml` y `src/**` de este repo. Verificado 2026-11-02.

## 1. Features del crate base (`oar-ocr` 0.10.1)

| Feature | Categoría | Para qué sirve | Estado en pyocrust | Dónde |
| :--- | :--- | :--- | :--- | :--- |
| `default` | conjunto | No es capacidad: activa `download-binaries` + `simd` | — | — |
| `simd` | optimización CPU | Acelera la normalización CHW (pre) y el argmax CTC (post). **No** cambia el provider | **Usada** | `Cargo.toml` (`oar-ocr/features`); `src/core/image_processor.rs` |
| `download-binaries` | build | Descarga un binario de ONNX Runtime compatible al compilar. Es el runtime de inferencia | **Usada** (implícita, vía `default`) | build/maturin; `Cargo.toml` |
| `auto-download` | gestión de modelos | Descarga los `.onnx` registrados desde ModelScope a `$OAR_HOME` en el primer uso | **Usada** | `Cargo.toml`; `src/storage/models.rs`, `registry.rs` |
| `cuda` | execution provider | Provider CUDA de ONNX Runtime (NVIDIA) | **Declarada** (opcional, no en el build por defecto) | `Cargo.toml [features]`; workflows `ci-cd-gpu*.yml` |
| `directml` | execution provider | Provider DirectML (Windows, DirectX 12) | **Declarada** (opcional) | `Cargo.toml [features]` |
| `tensorrt` | execution provider | Provider TensorRT (NVIDIA; requiere TensorRT instalado) | **Pendiente** (passthrough por añadir) | — / `t_8a0f369f` |
| `coreml` | execution provider | Provider Core ML (macOS/iOS) | **Pendiente** | — / `t_8a0f369f` |
| `webgpu` | execution provider | Provider WebGPU (targets soportados; experimental) | **Pendiente** | — / `t_8a0f369f` |
| `openvino` | execution provider | Provider Intel OpenVINO (Intel CPU/GPU) | **Pendiente** | — / `t_8a0f369f` |

Notas:
- Los providers son **compile-time**: un wheel liga los que se activaron al construir; la **selección es en runtime** (`OrtSessionConfig`). Pedir un provider sin su feature → error de configuración.
- `oar-ocr-vl` (versión con **Candle**, no ONNX Runtime) queda **fuera de v1** (ADR-001): sus features `cuda`/`metal` **no aplican** a pyocrust.

## 2. Módulos del crate base → equivalente en pyocrust

| Módulo `oar-ocr` | Cubre | Equivalente en `pyocrust_core` |
| :--- | :--- | :--- |
| `core` | traits, errores, batch | `src/core/` (`error.rs`, `types.rs`) |
| `domain` | tipos de dominio (orientación, modelos de predicción) | `src/core/types.rs` (parcial) |
| `models` | adaptadores por tarea | `src/storage/registry.rs`, `src/engines/` |
| `oarocr` | builders de pipeline de alto nivel | `src/engines/` + clase `VeloceOCR` |
| `processors` | utilidades de procesado de imagen | `src/core/image_processor.rs` |
| `utils` | utilidades de imágenes/tensores | delegado a `oar-ocr` (sin reimplementar) |
| `predictors` | interfaces por tarea | `src/tasks/mod.rs` (`TaskPredictor`) |

Superficie Python (paquete `pyocrust/`): `__init__.py` (fachada), `hardware.py` (`detect_hardware`), `resolver.py` (`resolve_pipeline`).

## 3. Modelos por tarea (`TaskPredictor`)

| Tarea | Artefactos gestionados (registro real) |
| :--- | :--- |
| `text_detection` | `pp-ocrv6_tiny_det.onnx` |
| `text_recognition` | `pp-ocrv6_tiny_rec.onnx`, `ppocrv6_tiny_dict.txt` |
| `layout_detection` | `pp-doclayoutv3.onnx` |
| `table_classification` | `pp-lcnet_x1_0_table_cls.onnx` |
| `table_structure_recognition` | `slanext_wired.onnx`, `table_structure_dict_ch.txt` |
| `table_cell_detection` | `rt-detr-l_wired_table_cell_det.onnx` |
| `document_orientation` | `pp-lcnet_x1_0_doc_ori.onnx` |
| `document_rectification` | `uvdoc.onnx` |
| `text_line_orientation` | `pp-lcnet_x1_0_textline_ori.onnx` |
| `seal_text_detection` | `pp-ocrv4_mobile_seal_det.onnx` |
| `formula_recognition` | `pp-formulanet-s.onnx`, `pp-formulanet-tokenizer.json` |

## 4. Modelos por preset (`VeloceOCR`)

| Preset | Familia | Artefactos | Salida |
| :--- | :--- | :--- | :--- |
| `pp_ocrv6` / `_tiny` / `_small` / `_medium` | texto | 3 (det + rec + dict) | `OcrResult` |
| `pp_structurev3` | estructura | 11 (layout, tablas, fórmulas, orientación…) | `StructureResult` |
| `indra` | estructura + math | 9 (Hugging Face `datalab-to/indra-ocr`) | `StructureResult` |

Catálogo y tamaños exactos en runtime: `model_catalog()` y `pipeline_profiles()` (`DESIGN.md` §3.1.3).

## 5. Fuera de alcance de v1

| Fuera de v1 | Motivo |
| :--- | :--- |
| **Candle** y `oar-ocr-vl` (VLMs ~0.9B) | ADR-001: v1 solo ONNX Runtime |
| PP-OCRv4 / PP-OCRv5 (presets de texto alternativos) | `DESIGN.md` §1.1 |
| `tensorrt`, `openvino`, `coreml`, `webgpu` en el **wheel por defecto** | Requieren runtimes del sistema / son por plataforma; quedan como features documentadas |
