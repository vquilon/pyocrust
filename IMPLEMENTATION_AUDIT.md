# Auditoría de implementación — pyocrust frente a `oar-ocr`

> Evidencia de ejecución real (CPU, `PYOCRUST_OFFLINE=1`), no de exposición de símbolos.
> Fecha de la corrida: 2026-11-01. Imagen de prueba: fixture del repo + FUNSD.
> Comando: `PYOCRUST_OFFLINE=1 RAYON_NUM_THREADS=2 .venv/Scripts/python.exe` sobre los 11 `TaskPredictor` y los 5 presets.

## 1. Componentes del `oar-ocr` original

| Componente original | Implementación en pyocrust | Inferencia verificada | Tiempo |
| :--- | :--- | :---: | ---: |
| **Text Detection** — regiones de texto | `TaskPredictor("text_detection")` → `detections` | ✅ ok | 220 ms |
| **Text Recognition** — regiones → texto | `TaskPredictor("text_recognition")` | ✅ ok | 91 ms |
| **Layout Detection** — estructura (bloques, títulos, tablas, figuras) | `TaskPredictor("layout_detection")` | ✅ ok | 1233 ms |
| **Document Orientation** — rotación 0/90/180/270° | `TaskPredictor("document_orientation")` → `orientations` | ✅ ok | 173 ms |
| **Document Rectification** — corrección de perspectiva | `TaskPredictor("document_rectification")` → `image/width/height` | ✅ ok | 124 ms |
| **Text Line Classification** — orientación de línea | `TaskPredictor("text_line_orientation")` → `orientations` | ✅ ok | 98 ms |
| **Seal Text Detection** — texto en sellos circulares | `TaskPredictor("seal_text_detection")` → `detections` | ✅ ok | 977 ms |
| **Formula Recognition** — fórmulas matemáticas → LaTeX | `TaskPredictor("formula_recognition")` → `formula` | ✅ ok | 440 ms |

**Extra no listado en el original (cobertura ampliada):**

| Componente extra | Implementación | Inferencia verificada | Tiempo |
| :--- | :--- | :---: | ---: |
| Table Classification | `TaskPredictor("table_classification")` | ✅ ok | 178 ms |
| Table Structure Recognition | `TaskPredictor("table_structure_recognition")` | ✅ ok | 632 ms |
| Table Cell Detection | `TaskPredictor("table_cell_detection")` → `cells` | ✅ ok | 537 ms |

**Resultado: 11/11 componentes inferidos con modelo real en CPU. 8/8 componentes del original cubiertos.**

## 2. Features del original

| Feature original | Implementación en pyocrust | Estado |
| :--- | :--- | :--- |
| Complete OCR pipeline from image to text | `VeloceOCR("pp_ocrv6").recognize(...)` → `OcrResult` | ✅ verificado (224 ms, `OcrResult`) |
| High-level builder APIs | `VeloceOCR` (presets), `TaskPredictor` (tareas) | ✅ |
| Models load from file paths or in-memory bytes | `TaskPredictor(..., models="/ruta.onnx")`; `predict(bytes)` | ✅ |
| Model adapter system for easy model swapping | `src/engines/` (`oar_text`, `oar_structure`, `oar_indra`) | ✅ |
| Batch processing support | `TaskPredictor.predict_batch([...])` (conserva orden) | ✅ |
| ONNX Runtime integration for fast inference | vía `oar-ocr` (CPU; binarios `download-binaries` + `simd`) | ✅ CPU; GPU no verificada |

## 3. Módulos del original → módulos de pyocrust

| Módulo `oar-ocr` | Equivalente en `pyocrust_core` | Notas |
| :--- | :--- | :--- |
| `core` (traits, errores, batch) | `src/core/` (`error.rs`, `types.rs`) | `PyOcrError`/`ValueError`/`RuntimeError` |
| `domain` (tipos de orientación, modelos) | `src/core/types.rs` (parcial) | orientación expuesta, dominio reducido |
| `models` (adaptadores por tarea) | `src/storage/registry.rs`, `src/engines/` | registro de artefactos + motores |
| `oarocr` (builders de pipeline) | `src/engines/` + clase `VeloceOCR` | 5 presets |
| `processors` (procesado de imagen) | `src/core/image_processor.rs` | `TileStrategy`, pre/post-proceso |
| `utils` (imágenes y tensores) | delegado a `oar-ocr` | sin reimplementación |
| `predictors` (interfaces por tarea) | `src/tasks/mod.rs` (`TaskPredictor`) | 11 tareas |

## 4. Presets (pipelines de alto nivel)

| Preset | Familia | Salida | Inferencia verificada |
| :--- | :--- | :--- | :---: |
| `pp_ocrv6` (Tiny) | texto | `OcrResult` | ✅ ok (224 ms) |
| `pp_ocrv6_small` / `pp_ocrv6_medium` | texto | `OcrResult` | ⚠️ constructores OK; **modelos ausentes** offline |
| `pp_structurev3` | estructura | `StructureResult` | ✅ ok (2093 ms) |
| `indra` | estructura + math | `StructureResult` | ✅ ok (215 ms) |

## 5. Límites explícitos (lo que esta auditoría NO certifica)

- **GPU**: `pp_ocrv6` con `--features cuda` no se probó; la detección de hardware no prueba que el wheel CUDA funcione.
- **Calidad**: aquí se mide que cada componente **ejecuta**, no su precisión. La calidad de fórmulas, por ejemplo, es mixta (ver `benchmarks/FORMULA_REPORT.md`).
- **Variantes de modelo**: `pp_ocrv6_small`/`medium` y las variantes `plus`/`L` de PP-FormulaNet no están en caché; su estado es `skipped`, no "ok".
- **Suite global**: `pytest tests/` da 138 passed / 1 skip / 1 fallo por modelo PP-StructureV3 ausente (entorno).
