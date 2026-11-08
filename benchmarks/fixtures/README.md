# Fixtures minimas versionadas

Datasets **minimos** y commiteados para que un *checkout limpio* (o sin red)
pueda ejecutar las 9 features del banco sin depender de `benchmarks/data_cache/`
(545 MB, **gitignored**) ni de descargas de Hugging Face.

## Contenido

| Fixture | Sirve a | Esquema | Tamano |
|---|---|---|---|
| `omnidocbench_mini/` | `formula`, `layout`, `table`, `full_page`, `orientation`, `text_line`, `rectification` | `OmniDocBench.json` recortado + `images/<name>` (mismo esquema que la release HF) | ~10 MB |
| `funsd_mini/` | `text` | `manifest.json` (id/words/bboxes) + `images/<id>.jpg` | ~0.6 MB |

`omnidocbench_mini` trae 10 paginas que cubren las categorias anotadas de las
que dependen los GT por feature (`text_block`, `title`, `equation_isolated`,
`table`, `figure`, ...). Las imagenes se reescalan a un lado mayor de 2400 px
(PNG) y los `poly`/`bbox` de la anotacion se reescalan en la misma proporcion
para que el GT siga siendo coherente con la imagen.

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
```

## Verificar el criterio (sin red)

```bash
python benchmarks/verify_fixture_offline.py   # 9 features -> >=2 muestras desde la fixture
pytest benchmarks/tests/test_fixture_fallback.py -q
```
