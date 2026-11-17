# Fixtures minimas versionadas

Datasets **minimos** y commiteados para que un *checkout limpio* (o sin red)
pueda ejecutar las 9 features del banco sin depender de `benchmarks/data_cache/`
(545 MB, **gitignored**) ni de descargas de Hugging Face.

## Contenido

| Fixture | Sirve a | Esquema | Tamano |
|---|---|---|---|
| `omnidocbench_mini/` | `formula`, `layout`, `table`, `full_page`, `orientation`, `text_line`, `rectification` | `OmniDocBench.json` recortado + `images/<name>` (mismo esquema que la release HF) | ~10 MB |
| `funsd_mini/` | `text` | `manifest.json` (id/words/bboxes) + `images/<id>.jpg` | ~0.6 MB |
| `schematics_mini/` | dominio OCR de **esquematicos** (`dataset="schematics"`) | `manifest.json` (id/image/text + sha256) + `images/<id>.png` | ~1.3 MB |

`omnidocbench_mini` trae 10 paginas que cubren las categorias anotadas de las
que dependen los GT por feature (`text_block`, `title`, `equation_isolated`,
`table`, `figure`, ...). Las imagenes se reescalan a un lado mayor de 2400 px
(PNG) y los `poly`/`bbox` de la anotacion se reescalan en la misma proporcion
para que el GT siga siendo coherente con la imagen.

### `schematics_mini` — esquematicos (dominio OCR de diagramas)

Muestra **offline** de `bshada/open-schematics` (317 GB: NO cabe en un test):
10 paginas de esquematico con su PNG renderizado (`schematic_image`, la pagina
que ve el OCR) y el **texto visible esperado**. `load_schematics` (registrado
como `dataset="schematics"`) lee solo esta fixture; no hay camino "dataset
real", asi que su `provenance` es siempre `fixture`.

El GT de texto se extrae del fuente `.kicad_sch` (S-expr de KiCad 8) con
`build_schematics_fixture.py`: referencia/valor **no ocultos** de cada simbolo,
propiedades no ocultas de cada hoja, items `(text ...)`, etiquetas
(`label`/`global_label`/`hierarchical_label`) y el `title_block`. El marcado de
KiCad (`~{x}`, `_{x}`, `^{x}`, `{slash}`) se convierte al texto **renderizado**.
Los **pines** (nombres/numeros) NO se incluyen: viven en la definicion de
libreria con su propia visibilidad y no aportan al reconocimiento de rotulos.
El `manifest.json` guarda ademas el `sha256` de cada PNG (versionado verificable).

## Como funciona el fallback

`common/datasets.py` intenta primero la fuente real (cache local / HF) y, si
falla (sin red, cache vacio, dependencia ausente), sirve desde la fixture **en
silencio** y lo declara en el informe:

- `load_funsd` -> `fixtures/funsd_mini/manifest.json`
- `_load_omnidocbench_pages` / `_odb_image` -> `fixtures/omnidocbench_mini/`
- `_cached_page_images` / `_cached_page_annotation` (features sinteticas) -> paginas de la fixture

El origen del ultimo dataset cargado queda en `common.datasets.fixture_provenance()`
(`{"source": "dataset" | "fixture", "detail": ...}`) y el runner lo propaga al
`summary.json` (`dataset_source`). El informe por feature (`features/report.py`)
imprime un **AVISO** visible cuando `source == "fixture"`, para no mezclar
numeros de la fixture con los de la muestra completa.

`seal` no necesita fixture: su set es **sintetico** y determinista (tampon
pegado en documento blanco).

## Reconstruir las fixtures

Los scripts leen la cache existente de `benchmarks/data_cache` (una vez):

```bash
python benchmarks/build_fixture.py        # omnidocbench_mini
python benchmarks/build_funsd_fixture.py  # funsd_mini
python benchmarks/build_schematics_fixture.py  # schematics_mini (red: muestrea HF)
```

`build_schematics_fixture.py` no lee `data_cache`: muestrea `N_PAGES` filas de
`bshada/open-schematics` por el endpoint `/rows` del datasets-server de HF (con
la revision pinnada) y extrae el texto del `.kicad_sch`. `--self-check` valida el
extractor sin red.

## Verificar el criterio (sin red)

```bash
python benchmarks/verify_fixture_offline.py   # 9 features -> >=2 muestras desde la fixture
pytest benchmarks/tests/test_fixture_fallback.py -q      # 9 features offline
pytest benchmarks/tests/test_schematics_fixture.py -q    # esquematicos: N<=10, versionada, fallo claro
```

## Fetch reproducible (revision fijada + checksums)

La fuente real (HF) se baja **siempre** con `revision=` fijada
(`OMNIDOCBENCH_REVISION` en `common/datasets.py`): dos maquinas bajan la MISMA
revision. El sha256 de los ficheros que definen el GT va en
`benchmarks/datasets_manifest.json` (versionado) y se **verifica al cargar**: si no
cuadra, `DatasetUnavailable` con el hash esperado y el obtenido.

```bash
python benchmarks/prepare_datasets.py --fetch         # puebla data_cache una vez (~545 MB)
python benchmarks/prepare_datasets.py --fetch --update-manifest   # refresca el sha256
```

Sin red y con el cache vacio, `--fetch` (o `common.runner --fetch`) falla con **un
unico error claro** y la instruccion de como poblarlo — no deja N muestras en
`skipped`. La revision usada aparece en el `provenance` de cada `REPORT.md`.
