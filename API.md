# pyocrust — formas de interactuar con el wrapper de Python y objetos de salida

> **Alcance de este documento**: API disponible en el árbol actual. Las firmas de alto nivel se
> contrastan con `pyocrust/__init__.pyi`; el comportamiento descrito se basa en las rutas actuales
> de `pyocrust/entries.py`. No se presentan como disponibles contratos que sólo sean futuros.
>
> Convención: `1-indexado` siempre significa "como lo ve el usuario" (la página 1 es la primera).

---

## 1. Entradas públicas principales

| # | Quiero… | Entrada | Devuelve |
|---|---|---|---|
| 1 | texto / estructura de una imagen | `VeloceOCR(preset).recognize(image)` | `OcrResult` \| `StructureResult` |
| 2 | **sólo las cajas** de texto de una imagen | `VeloceOCR(preset).detect_regions(image, **det)` | `list[BoundingBox]` |
| 3 | OCR de **cajas que yo doy** | `VeloceOCR(preset).recognize_regions(image, boxes, **rec)` | `OcrResult` (1 por caja) |
| 4 | **una** tarea suelta (layout, tabla, fórmula…) | `TaskPredictor(task, **options).predict(image)` | `dict` (esquema por tarea, §4.6) |
| 5 | **varias** tareas/presets de una vez | `recognize(image, features=[...])` | salida suelta (1) o `{etiqueta: salida}` (N) |
| 6 | que **elija solo** (router) | `auto_recognize(image, declared=, probe=)` | `(salida, RouteDecision)` |
| 7 | **un PDF**: metadatos, text-layer y páginas raster | `parse_document(path, pages, dpi)` / `render_page(path, i, dpi)` | `list[PageInfo]` / `bytes` (PNG) |
| 8 | **una imagen** por la entrada nueva sin estado | `recognize_image(image, task=...)` | una salida: `OcrResult` \| `StructureResult` |
| 9 | **un documento** por la entrada nueva sin estado | `recognize_document(path, pages, task=...)` | `DocumentResult` con páginas `PageRun` |
| 10 | reutilizar motores entre llamadas | `with Session(...) as session` | `ImageOutput` o iterador de `PageRun` |

Y dos entradas que **no ejecutan nada** (sólo deciden): `resolve_pipeline(TaskSpec)` → `PipelineChoice`
y `route(declared, signals)` → `RouteDecision`.

---

## 2. Presets y tareas (la materia prima)

**5 presets** (pipeline completo, con par det+rec cableado):

| id | familia | salida | notas |
|---|---|---|---|
| `pp_ocrv6_tiny` \| `pp_ocrv6_small` \| `pp_ocrv6_medium` | texto | `OcrResult` | el tamaño manda precisión/velocidad |
| `pp_structurev3` | estructura | `StructureResult` | layout + tabla + fórmula + Markdown |
| `indra` | estructura | `StructureResult` | **licencia restrictiva** (ver §5) |

Nota: el constructor de `VeloceOCR` acepta además el nombre corto `"pp_ocrv6"`, que **es**
`pp_ocrv6_tiny` (es el valor por defecto). Los ids de la tabla son los que lista
`pipeline_profiles()`.

**11 tareas** (un modelo suelto cada una), tal como las lista `pipeline_profiles()`:
`text_detection`, `text_recognition`, `layout_detection`, `table_classification`,
`table_structure_recognition`, `table_cell_detection`, `document_orientation`,
`document_rectification`, `text_line_orientation`, `seal_text_detection`, `formula_recognition`.

**Alias** (`FEATURE_ALIASES`) para no escribir el id largo:
`text`→`text_recognition`, `layout`→`layout_detection`, `table`→`table_structure_recognition`,
`formula`→`formula_recognition`, `structure`/`full_page`→`pp_structurev3`.

---

## 3. Firma por firma

### 3.1 Imagen → texto o estructura
```python
VeloceOCR(
    preset="pp_ocrv6", custom_path=None, device="cpu",
    license_commercial_use=True, license_acknowledge=False,
    text_det_limit_side_len=None, text_det_limit_type=None, text_det_max_side_len=None,
    text_det_thresh=None, text_det_box_thresh=None,
    text_det_unclip_ratio=None, text_det_max_candidates=None,
    use_doc_orientation=True, use_doc_unwarping=True, use_textline_orientation=True,
    text_type="general",
)
    .recognize(image) -> OcrResult | StructureResult
```
- `image`: `str` (ruta), `bytes` (buffer) o `PathLike`.
- El tipo de retorno lo decide el **preset**: `OcrResult` en `pp_ocrv6*`, `StructureResult` en
  `pp_structurev3`/`indra`.
- `text_det_*`: **el mando de calidad** (§6). Sólo afectan a los presets `pp_ocrv6*`.
- `use_doc_orientation` / `use_doc_unwarping` / `use_textline_orientation`: enderezan página girada,
  rectifican curvada y giran recortes boca abajo. Los tres `True` por defecto (como PaddleOCR).
- `text_type`: `"general"` | `"table"` | `"seal"` (cambia preprocesado del detector y tipo de caja).
- Propiedades: `.provider_effective` (el EP que **de verdad** corre), `.models_dir`, `.license`.

### 3.2 Imagen → cajas (§11, `RDET`)
```python
VeloceOCR(preset).detect_regions(image, *, text_det_limit_side_len=None, text_det_limit_type=None,
                                 text_det_max_side_len=None, text_det_thresh=None,
                                 text_det_box_thresh=None, text_det_unclip_ratio=None,
                                 text_det_max_candidates=None) -> list[BoundingBox]
VeloceOCR(preset).recognize_regions(image, boxes, *, rec_score_threshold=None,
                                    region_batch_size=None) -> OcrResult
```
- `detect_regions` usa el modelo de detección **del preset** (no el `tiny` fijo de
  `TaskPredictor("text_detection")`) y hereda los `text_det_*` del constructor (los de aquí los pisan).
- La caja que devuelve es el **AABB** del cuadrilátero: se pierde la rotación de líneas inclinadas.
- `recognize_regions` recorta con `crop_imm` **sin reescalar** y devuelve **una `TextRegion` por caja
  de entrada, en el mismo orden**. `region_batch_size` por defecto 16 en `tiny` y 4 en el resto;
  nº de pasadas de rec = `ceil(N / region_batch_size)`.

### 3.3 Imagen → una tarea
```python
TaskPredictor(task, models=None, device="cpu",
              license_commercial_use=True, license_acknowledge=False, **options)
    .predict(image) -> dict          # esquema de la tarea (§4.6)
    .predict_batch(images) -> list[dict]   # uno por imagen, en orden; [] si vacío
```
- `models`: `None` (usa los artefactos registrados) | `str` (ruta de **fichero** de modelo, no de
  directorio) | `dict` con `model` y opcional `dict`/`tokenizer`.
- `**options`: whitelist por tarea y defaults en §4.6; una opción no soportada lanza
  `PyOcrValueError` **antes** de resolver modelos.
- Propiedades: `.provider_effective`, `.license`.

### 3.4 Imagen → varias features
```python
recognize(image, features, *, device="cpu", custom_path=None,
          parallel=False, max_workers=None,
          license_commercial_use=True, license_acknowledge=False)
    -> OcrResult | StructureResult | dict            # dict si features > 1
```
- `features`: secuencia de ids de `pipeline_profiles()` o alias de `FEATURE_ALIASES`.
- Con **una** feature devuelve exactamente lo de siempre, sin envolver; con **varias**,
  `{etiqueta_pedida: salida}`, conservando el esquema de cada feature (nunca aplanado).
- `str` suelto en vez de secuencia, o feature desconocida/duplicada/vacía → `PyOcrValueError`.
- Secuencial por defecto (ADR-008); `parallel=True` solapa las inferencias (liberan el GIL).

### 3.5 Imagen → automático (`RAUTO`, §12)
```python
auto_recognize(image, *, declared=None, probe=False, device="cpu", custom_path=None,
               parallel=False, max_workers=None,
               license_commercial_use=True, license_acknowledge=False)
    -> (salida, RouteDecision)
route(declared=None, signals=None) -> RouteDecision
resolve_pipeline(task: TaskSpec, hardware=None) -> PipelineChoice
```
- `auto_recognize` = `route()` + `recognize()`; la salida es **exactamente** la de `recognize`.
- `route` es **puro**: no mira la imagen ni carga modelos. Reglas en orden, gana la primera:
  R0 declarado → R1 geometría (`min(W,H) < GEOM_MIN_SIDE_PX=64`) → R2/R2' sonda
  (`n_regions >= ROUTE_MIN_REGIONS=24` o `ink_ratio >= ROUTE_MIN_DENSITY=0.12`) → R3 texto por defecto.
- **No** decide tabla/fórmula (eso lo gatea `OARStructure` aguas arriba) ni fija los flags de
  composición (son del constructor de `VeloceOCR`).

### 3.6 PDF → metadatos, text-layer y rasterizado
```python
parse_document(path, pages=None, dpi=200, *, text_min_chars=64) -> list[PageInfo]
render_page(path, index, dpi=200) -> bytes          # PNG
```
- `pages=None` → **todas**; si no, índices **1-indexados** (duplicados/fuera de rango/0-based → error).
- Regla de decisión: `has_text_layer = len(texto) >= text_min_chars` (por defecto 64). Si es `True`,
  la página trae su texto **exacto** con cajas (sin OCR); si `False`, `needs_ocr=True` y esa página se
  rasteriza con `render_page` y entra al OCR como cualquier imagen.
- `dpi` en `parse_document` sólo fija `width_px`/`height_px` (`round(pt * dpi / 72)`); las **cajas no
  cambian** con el `dpi`, así que re-renderizar a otro `dpi` no obliga a re-parsear.
- Requiere la librería nativa **PDFium**: se resuelve por `PYOCRUST_PDFIUM_LIB` (fichero o directorio)
  o desde el directorio del módulo nativo. Si no carga → `PyOcrRuntimeError` (nunca una lista vacía).

### 3.7 Decidir sin ejecutar
```python
TaskSpec(document_kind="digital", ocr_only=True, formulas="none", tables=False,
         quality="speed", output_format="text",
         license_commercial_use=True, license_acknowledge=False)
resolve_pipeline(task, hardware=None) -> PipelineChoice    # .id = pp_ocrv6_{size} | preset
```
Enums: `document_kind` `scanned|digital|mixed`; `formulas` `none|with_text|only`;
`quality` `speed|balanced|accuracy`; `output_format` `text|markdown|html|json`.
`resolve_pipeline` **no** carga ni descarga nada: sólo recomienda un preset y unas tareas.

### 3.8 Entradas nuevas sin estado: una imagen o un documento

```python
Resolution = Literal["default", "balanced", "native", "tiled"]
ImageOutput = OcrResult | StructureResult

def recognize_image(
    image: str | bytes | PathLike[str], *, task: TaskSpec | None = None,
    resolution: Resolution = "balanced", tile_size: int | None = None,
    tile_overlap: int | None = None, text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None, device: str = "cpu",
    custom_path: str | None = None, license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> ImageOutput: ...

def recognize_document(
    path: str | PathLike[str], pages: Sequence[int] | None = None, *,
    task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
    auto_route: bool = False, probe: bool = False, dpi: int = 600,
    text_min_chars: int = 64, resolution: Resolution = "balanced",
    tile_size: int | None = None, tile_overlap: int | None = None,
    text_det_limit_side_len: int | None = None,
    text_det_limit_type: Literal["min", "max"] | None = None,
    text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
    text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
    text_det_max_candidates: int | None = None, device: str = "cpu",
    custom_path: str | None = None, license_commercial_use: bool | None = None,
    license_acknowledge: bool | None = None,
) -> DocumentResult: ...

def available_features(*, license_commercial_use: bool = True,
                        license_acknowledge: bool = False) -> list[str]: ...
```

- `recognize_image` valida los bytes como imagen y devuelve **una sola salida**: el preset
  seleccionado da `OcrResult` (`pp_ocrv6*`) o `StructureResult` (`pp_structurev3`). No devuelve una
  lista ni un contenedor de páginas. `task=None` usa `TaskSpec()`.
- `recognize_document` devuelve `DocumentResult`; `pages=None` selecciona todas las páginas y una
  secuencia explícita usa índices **1-indexados**. Las páginas se devuelven en el orden seleccionado;
  `page_tasks` asocia `TaskSpec` por índice y sólo admite páginas seleccionadas. `auto_route=True`
  no se combina con `task` ni `page_tasks`; `probe` sólo activa la sonda de esa ruta.
- La selección del contenido no depende del sufijo: la ruta de imagen rechaza `%PDF` si aparece en
  los primeros 1024 bytes y luego valida los bytes con el decodificador; la ruta PDF exige `%PDF` en
  ese prefijo y procesa el archivo con PDFium. Por tanto, un marcador `%PDF` dentro de metadatos de
  una imagen también puede provocar `IncompatibleImageError`; el sufijo no corrige esa clasificación
  (`pyocrust/entries.py:84-97,256-267`; decoder: `src/lib.rs:481-489`).
- Los siete `text_det_*` son escapes explícitos sobre la resolución seleccionada. No se afirma una
  tasa de reconocimiento ni que una página sin text-layer vaya a producir texto útil.

Las firmas públicas están declaradas en `pyocrust/__init__.pyi:474-543`; la exportación de las
funciones está en `pyocrust/__init__.py:51-54`. La selección de páginas, detección de contenido,
preflight y construcción de resultados se implementan en `pyocrust/entries.py:218-366`.

### 3.9 `Session`: motores reutilizables dentro de un bloque

```python
class Session:
    def __init__(
        self, *, device: str = "cpu", custom_path: str | None = None,
        resolution: Resolution = "balanced", tile_size: int | None = None,
        tile_overlap: int | None = None, text_det_limit_side_len: int | None = None,
        text_det_limit_type: Literal["min", "max"] | None = None,
        text_det_max_side_len: int | None = None, text_det_thresh: float | None = None,
        text_det_box_thresh: float | None = None, text_det_unclip_ratio: float | None = None,
        text_det_max_candidates: int | None = None,
        license_commercial_use: bool = True, license_acknowledge: bool = False,
    ) -> None: ...
    def __enter__(self) -> Session: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...
    def recognize_image(self, image: str | bytes | PathLike[str], *,
                        task: TaskSpec | None = None) -> ImageOutput: ...
    def iter_document_pages(
        self, path: str | PathLike[str], pages: Sequence[int] | None = None, *,
        task: TaskSpec | None = None, page_tasks: Mapping[int, TaskSpec] | None = None,
        auto_route: bool = False, probe: bool = False, dpi: int = 600,
        text_min_chars: int = 64,
    ) -> Iterator[PageRun]: ...
    def purge(self) -> None: ...
```

`Session` carga los motores de forma perezosa y conserva los runners entre llamadas mientras el
bloque `with` está activo. `purge()` los libera sin cerrar la sesión; al salir del bloque la caché se
limpia y la instancia queda cerrada. Sus métodos fuera del bloque activo lanzan
`PyOcrRuntimeError`; la instancia cerrada no se puede reactivar. La caché sólo retiene runners,
no documentos, rasteres ni resultados. `iter_document_pages` produce las páginas sincrónicamente.

Los flags de licencia del constructor de `Session` fijan su política. Un `TaskSpec` pasado a sus
métodos debe tener ambos flags iguales a esa política o se rechaza con `PyOcrValueError`. En las
funciones sin estado, los flags explícitos `None` heredan los valores de `task` (o de `TaskSpec()`);
un booleano explícito los sustituye. `available_features` devuelve IDs ordenados permitidos por los
flags declarados, sin cargar modelos. Fuentes: `pyocrust/entries.py:37-81,409-461,464-551` y
`pyocrust/__init__.pyi:487-512`.

---

## 4. Objetos de salida

### 4.1 `OcrResult` — salida de texto
| campo | tipo | significado |
|---|---|---|
| `regions` | `list[TextRegion]` | regiones en el orden que devolvió el backend |
| `text` | `str` | texto de todas las regiones, unidas por `\n` |
| `confidence` | `float` | confianza **media** de las regiones (0.0 si no hay ninguna) |
`len(result)` = nº de regiones.

### 4.2 `TextRegion` — una región
| campo | tipo | significado |
|---|---|---|
| `text` | `str` | texto reconocido; `""` = falló o se filtró por confianza |
| `confidence` | `float` | `[0, 1]` |
| `box` | `BoundingBox` | caja envolvente |

### 4.3 `BoundingBox` — caja (AABB)
`x1, y1, x2, y2` (`float`), más `.width` y `.height` (nunca negativos).
**Marco de coordenadas**: píxeles de la imagen de entrada en el OCR; en `parse_document`, **puntos
PDF con origen arriba-izquierda** (el `y` se voltea para que comparar cajas de text-layer y de OCR sea
directo).

### 4.4 `StructureResult` — salida de estructura
| campo | tipo | significado |
|---|---|---|
| `elements` | `list[LayoutRegion]` | elementos de layout en orden de lectura |
| `regions` | `list[TextRegion]` | regiones de texto OCR del documento |
| `formulas` | `list[str]` | fórmulas LaTeX detectadas (vacío si el preset no las separa) |
| `.to_markdown()` | `str` | Markdown ya renderizado (títulos, tablas en HTML, LaTeX) |
`len(result)` = nº de `elements`.

### 4.5 `LayoutRegion` — un elemento de layout
`kind: str` (`doc_title`, `text`, `table`, `formula`, `figure_title`…), `text: str` (en `formula`,
su **LaTeX**), `confidence: float`, `box: BoundingBox`.

### 4.6 `TaskPredictor.predict` — diccionario por tarea
| tarea | claves |
|---|---|
| `text_detection`, `seal_text_detection` | `{detections: [{bbox: [[x,y]×4], score}]}` |
| `text_recognition` | `{text: str, score: float}` |
| `layout_detection` | `{elements: [{bbox, element_type, score}], is_reading_order_sorted: bool}` |
| `table_classification` | `{classifications: [{class_id, label, score}]}` |
| `table_structure_recognition` | `{structures: [str], bboxes: [[…]]}` |
| `table_cell_detection` | `{cells: [{bbox, label, score}]}` |
| `document_orientation`, `text_line_orientation` | `{orientations: [{class_id, label, score}]}` |
| `document_rectification` | `{image: bytes (PNG), width: int, height: int}` |
| `formula_recognition` | `{formula: str, score: float \| None}` |

**Whitelist y defaults de `**options`** (exactos):
`text_detection` → `score_threshold=0.3, box_threshold=0.6, unclip_ratio=1.5, max_candidates=1000`;
`text_recognition` → `score_threshold=0.0, dict_path`;
`layout_detection` → `score_threshold=0.5, model_name='pp_doclayoutv3'`;
`table_classification` → `score_threshold=0.5, topk=2, input_shape=(224,224)`;
`table_structure_recognition` → `dict_path, model_name, input_shape`;
`table_cell_detection` → `score_threshold=0.3, model_name` (detectado de la ruta, fallback
`rt-detr-l_wired_table_cell_det`);
`document_orientation` → `score_threshold=0.5, topk=4`;
`text_line_orientation` → `score_threshold=0.5, topk=2, input_shape=(80,160)`;
`seal_text_detection` → `score_threshold=0.5`;
`document_rectification` / `formula_recognition` → sin opciones.
`input_shape` es `(H, W)`, enteros positivos. Ojo: este detector suelto usa el modelo **tiny** con
umbrales genéricos (0.3/0.6/1.5/1000); para cajas de calidad usa `VeloceOCR.detect_regions` (§3.2).

### 4.7 `PageInfo` — una página de PDF
| campo | tipo | significado |
|---|---|---|
| `index` | `int` | 1-indexado |
| `has_text_layer` | `bool` | la capa de texto superó `text_min_chars` |
| `needs_ocr` | `bool` | `== not has_text_layer` → rasterizar y pasar al OCR |
| `width_px`, `height_px` | `int` | `round(puntos * dpi / 72)` |
| `text_regions` | `list[TextRegion]` | segmentos del text-layer, o `[]` si `needs_ocr` |

### 4.8 `RouteDecision` — por qué se eligió (fuera de la salida OCR)
`preset: str | None`, `size: str | None`, `features: tuple[str, ...]`, `reason: str`
(`declared`/`geometry`/`probe`/`default-text`), `artifacts: tuple[str, ...]`.
Un consumidor ve el mismo `OcrResult`/`StructureResult` con router o sin él: la explicabilidad viaja
aquí, no dentro del resultado.

### 4.9 `PipelineChoice` — la recomendación
`preset: str`, `size: str | None`, `tasks: tuple[str, ...]`, `models_dir: str`, `offline: bool`,
y `.id` = `pp_ocrv6_{size}` o el preset.

### 4.10 `PageRun` y `DocumentResult` — salidas paginadas

| campo | tipo | significado |
|---|---|---|
| `PageRun.index` | `int` | índice 1-indexado de la página |
| `PageRun.source` | `"text_layer"` \| `"ocr"` | origen de la salida de esa página |
| `PageRun.output` | `OcrResult` \| `StructureResult` | salida de esa página, sin aplanar |
| `PageRun.route_decision` | `RouteDecision` \| `None` | decisión de esa página si se usó `auto_route`; si no, `None` |
| `PageRun.warnings` | `tuple[str, ...]` | avisos de resolución de esa página |
| `DocumentResult.pages` | `tuple[PageRun, ...]` | páginas seleccionadas en su orden |

Una página con text-layer suficiente se devuelve como `source="text_layer"`, con las regiones
extraídas en `OcrResult`; en ese caso no se ejecuta OCR y el `TaskSpec` no cambia esa salida. Sin
text-layer suficiente, `source="ocr"` lleva el resultado del preset resuelto. Esto no garantiza
que el modelo reconozca texto en cada página. En `Session`, el mismo contrato se entrega como un
iterador de `PageRun` en lugar de materializar `DocumentResult` (`pyocrust/entries.py:338-366,519-551`; tipos: `pyocrust/entries.py:23-34`; orden de selección: `src/documents.rs:176-239`).

---

## 5. Errores

```
Exception
└── PyOcrError
    ├── PyOcrValueError     # entrada del llamante (opciones, índices, rangos, licencia)
    │   ├── IncompatibleImageError
    │   └── IncompatiblePdfError
    └── PyOcrRuntimeError   # fallo de entorno (p.ej. lectura/PDFium/modelo)
        └── ResolutionError # exportada; no se ha verificado una ruta que la emita
```
Regla general: **nunca un fallback silencioso**. Un valor inválido o una opción no soportada lanza
`PyOcrValueError` **antes** de cargar modelos; una librería nativa que falta es `PyOcrRuntimeError`.

| Entrada | Condición | Resultado |
|---|---|---|
| Imagen | tipo de entrada no admitido; `%PDF` en el prefijo; bytes que el decoder no puede abrir; ruta ilegible; `task`/flags de tipo incorrecto | `PyOcrValueError` por tipo de entrada; `TypeError` por `task`/flags; `PyOcrRuntimeError` por lectura; `IncompatibleImageError` por contenido PDF o imagen no decodificable (`pyocrust/entries.py:37-45,84-97,230-235`; `src/lib.rs:481-489`) |
| Documento | tipo de ruta incorrecto, `pages`/índices/dpi/umbral inválidos, `page_tasks` inválido o combinación `auto_route` con `task`/`page_tasks` | `PyOcrValueError`; argumentos booleanos de tipo incorrecto pueden dar `TypeError` (`pyocrust/entries.py:256-297`; `src/documents.rs:153-218`) |
| Documento | ruta ilegible | `PyOcrRuntimeError`; un prefijo sin `%PDF` da `IncompatiblePdfError` (`pyocrust/entries.py:256-267`) |
| Imagen/documento/sesión | controles `resolution`, mosaico o `text_det_*` fuera de rango; `tiled` con un perfil que no sea de texto | `PyOcrValueError` (`pyocrust/entries.py:110-145,245-253,308-325`) |
| Sesión | método usado fuera del `with`, instancia ya cerrada o política de licencia distinta en `TaskSpec` | `PyOcrRuntimeError` para el ciclo de vida; `PyOcrValueError` para política distinta (`pyocrust/entries.py:409-435`) |

**Licencia**: `license_commercial_use` y `license_acknowledge` son declaraciones **del usuario**
(intención comercial / aceptación de atribución), no los términos del modelo. Un preset restrictivo
(hoy sólo `indra`, `OpenRAIL-M-Mod`) exige ambas; si no, `PyOcrValueError` en el constructor. En
`recognize(features=[...])` los flags se pasan **a cada** motor. En las nuevas entradas, una
feature con licencia `Unknown`, sin permiso comercial bajo una política comercial, o con atribución
obligatoria no aceptada se rechaza con `PyOcrValueError`. `recognize_image` hace ese preflight tras
leer/validar la imagen y antes de construir el predictor; `recognize_document` lo hace antes de
parsear/rasterizar/crear motores, pero actualmente incluye `task` por defecto y todos los valores de
`page_tasks`, incluso si alguna página no los necesita. Con `auto_route=True` valida los candidatos
`pp_ocrv6_tiny` y, si `probe=True`, también `pp_structurev3` y `text_detection`, antes de saber qué
ruta se elegirá. `Session.iter_document_pages` primero obtiene las páginas seleccionadas y omite
text-layer al calcular los perfiles OCR; después valida licencias antes del primer raster/sonda/motor.
En modo automático sólo añade esos candidatos si alguna página requiere OCR. Por ello, un perfil no
permitido que `recognize_document` haya incluido preventivamente puede no ser necesario en esa
corrida. `available_features` es un filtro informativo y no sustituye al preflight
(`pyocrust/entries.py:48-81,230-253,311-326,328-365,490-517`).

**Resolución en las entradas nuevas** (`recognize_image`, `recognize_document` y `Session`):

| `resolution` | comportamiento actual |
|---|---|
| `"default"` | detector `960/Max/4000` (compatibilidad histórica) |
| `"balanced"` | `64/Min` y límite máximo igual al lado mayor de la entrada, salvo overrides; si los knobs efectivos reducen, emite `RuntimeWarning` |
| `"native"` | parte del mismo límite calculado que `balanced`, pero rechaza con `PyOcrValueError` si los overrides reducen la entrada; una entrada grande puede emitir aviso de coste |
| `"tiled"` | sólo preset de texto `pp_ocrv6*`; `tile_size=2048` y `tile_overlap=256` por defecto; los parámetros de mosaico sólo se aceptan en este modo |

Los knobs y modos inválidos, los mosaicos para salida de estructura, y cualquier reducción en modo
`native` producen `PyOcrValueError`. Una reducción efectiva en otros modos añade `RuntimeWarning`;
en `recognize_document` y `Session.iter_document_pages` el mismo texto se guarda en
`PageRun.warnings`. El aviso actual nombra la dimensión de entrada y el knob limitante, pero no
promete dimensiones resultantes. Aunque `ResolutionError` se exporta como subtipo de
`PyOcrRuntimeError`, en el árbol inspeccionado sólo aparece su declaración/exportación; no se
documenta como resultado garantizado de un fallo de reserva. Fuentes: `pyocrust/entries.py:110-210,245-253,359-365,540-551`; ejecución tiled: `pyocrust/multifeature.py:110-124`; firma tiled: `pyocrust/__init__.pyi:459-472`; exportación de error: `pyocrust/__init__.pyi:176-181,545-589`.

---

## 6. El mando que decide la calidad en `VeloceOCR` (reescalado)

Esta sección describe el API existente de `VeloceOCR` y `render_page`; no sustituye las opciones
`Resolution` de las nuevas entradas (§3.8–§3.9).

Sólo hay **dos** sitios donde se pierde resolución, y los dos son explícitos:

1. **Render del PDF a `dpi`** (`render_page`). Por defecto 200.
2. **El detector** (`text_det_*`). Sin knobs hereda `limit_side_len=960, limit_type="max"`,
   tope `max_side_len=4000` → una página 7000×5000 se ve a ~960 px y **se pierde texto fino**.

El recorte de `recognize_regions` y el reconocimiento de un recorte **no reescalan** (`crop_imm`).

Para **no reducir** una imagen grande hacen falta los **tres** knobs (el tope del lado largo recorta
**incondicionalmente**, así que `min`/64 solo no basta):

```python
RECETA = dict(text_det_limit_type="min", text_det_limit_side_len=64, text_det_max_side_len=7000)
engine = VeloceOCR("pp_ocrv6_medium", **RECETA)
boxes = engine.detect_regions(png, **RECETA)
result = engine.recognize_regions(png, boxes)
```
Medición de referencia (página sintética 7000×5000, texto fino, `pp_ocrv6_medium`, CPU):
default **0–2** regiones vs receta **77–112**.

---

## 7. Catálogo y entorno

| función | devuelve |
|---|---|
| `pipeline_profiles()` | `dict[id, fila]` — 5 presets + 11 tareas. Fila: `id, family, quality, output_format, description, artifacts, disk_bytes, ram_bytes, license, license_commercial_use, license_acknowledge, license_restricted, license_notes, license_url` |
| `model_catalog()` | `dict[nombre_artefacto, fila]` (115 filas) — sin escaneo de disco, sin red, sin inferencia |
| `models_status(custom_path=None)` | `dict` con `models_dir, offline, presets{preset: [{name, present, size, required}]}, indra` |
| `resolve_models_dir(custom_path=None)` | `str` — la raíz resuelta (native `OAR_HOME` → `OCR_MODELS_CACHE_DIR` → `~/.oar`) |
| `available_providers()` | `list[str]` — EPs que **registran de verdad** (`[]` si ninguno) |
| `enable_cuda()` | exporta las rutas del runtime CUDA y devuelve `available_providers()`; llamar **antes** de construir el motor |
| `detect_hardware()` | `HardwareProfile(cpu_count, ram_bytes, gpu: GpuInfo(name, vram_bytes))` — inventario físico, no capacidad del wheel |
| `full_page_tiling(image, tile_size=512, overlap=64)` | `list[(x, y, ancho, alto)]` — **sólo geometría** (ADR-009: opt-in, no lo aplica el pipeline) |

Constantes del router: `GEOM_MIN_SIDE_PX=64`, `ROUTE_MIN_REGIONS=24`, `ROUTE_MIN_DENSITY=0.12`.

---

## 8. Estado de las entradas

`recognize_image`, `recognize_document`, `Session` y `available_features` están exportadas en el
paquete y declaradas en el stub (`pyocrust/__init__.py:51-54,67-113`;
`pyocrust/__init__.pyi:474-543,587-589`). Estas entradas forman parte del contrato disponible que
se documenta aquí.
`DESIGN.md` §15 conserva texto marcado como diseño propuesto; en particular, sus promesas de
`ResolutionError` ante fallos de reserva y sus reglas de preflight no deben leerse como descripción
literal del comportamiento actual. Esta página documenta ese comportamiento desde
`pyocrust/entries.py` y deja explícitas las diferencias observadas.
