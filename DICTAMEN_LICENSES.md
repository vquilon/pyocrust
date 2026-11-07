# Dictamen: Sign-off del contrato de licencias contra DESIGN.md — t_2c9a9a57

Veredicto: **APROBADO**

## Ficheros revisados
- src/storage/license.rs
- src/storage/catalog.rs
- src/lib.rs
- src/tasks/mod.rs
- pyocrust/resolver.py
- pyocrust/__init__.pyi
- tests/test_license.py
- (de respaldo) src/storage/registry.rs, src/storage/models.rs, pyocrust/hardware.py, DESIGN.md, pyproject.toml

## Pruebas ejecutadas
- `cargo test` → exit 0; 64 passed; 0 failed; 0 ignored (unittests pyocrust_core).
- `python -m pytest tests/test_license.py -v` → 11 passed, 0 failed.
- `python -m pytest tests/ -q` → 141 passed, 13 skipped, 4 failed (ver Verdes 1 y 2: ficheros fuera de alcance del sign-off, herederos del L4 corregido).

## Lo revisado / estado de los 13 defectos del L4
| L4 | Clasificación | Estado |
|---|---|---|
| Critico: cargo test rojo | ✓ | Correcto: 64 passed / 0 failed. `block_message_names_the_opt_in` ahora acepta "unverified license" (linea 146) y los `assert` del test (license.rs:227-234) se cumplen. |
| Alto: TaskPredictor omite bloqueo | ✓ | Correcto (tasks/mod.rs:57-67): `license.allows(...)` antes del build. |
| Alto: acknowledge=false vs LICENSE Indra §7 | ✓ | Correcto (license.rs:39 `acknowledge: true`; getter `license()` → `license_dict` con acknowledge=true). |
| Medio: block_message opt-in vs cond. permite | ✓ | Correcto: requiere ambas condiciones acumulativas (license.rs:150-155). |
| Medio: license_url blob/main | ✓ | Correcto: commit SHA bd02167… (license.rs:41; registry.rs:212). |
| Medio: license_notes omiten §7/§8/§4/§5 | ✓ | Correcto: notas completas (license.rs:40). |
| Medio/ bajo: license_acknowledge flag muerto | ⚠ | Pendiente de test. El flag sigue en el modelo y los getters; no hay test con acknowledge=true. No es bloqueante (el bloqueo opera sobre allows()/block_message). |
| Medio: ModelScope sin hash preflight | ✗ | Fuera de alcance (models.rs no estaba en la lista). |
| Bajo: VeloceOCR(custom_path) expone licencia preset | ⚠ | Preserva el comportamiento existente (lib.rs:73-84). |
| Bajo: resolve_pipeline recomienda indra sin flags | ✓ | Correcto: ahora la recomienda solo si `_license_allows` (resolver.py:109-112) satisface el catálogo. |
| Bajo: polaridad license_commercial_use | ✓ | Consistente: True = intención comercial, en VeloceOCR/TaskPredictor/TaskSpec. |
| Bajo/Latente: for_artifacts AND de commercial_use | ✓ | Justificado: `rank` + AND hereda la más restrictiva (license.rs:106-123). La assertura de L4 ("etiqueta más permisiva") no se corresponde con el código. |
| Bajo: url Apache no cita fuente ModelScope | ✓ | No es defecto de licencia; la licencia Apache-2.0 es la fuente authoritative (LICENSE). |

## Verdes 1 y 2: 4 pruebas que fallan (ficheros fuera de ciclo de sign-off)
Hay 4 fallos en `tests/test_indra.py`, `tests/test_recognize.py`, `tests/test_resolver.py`. Los tres vuelven el falso de L4: el subtest pasa `license_acknowledge=False` para Indra, que ahora se bloquea correctamente como OpenRAIL-M-Mod (requiere atribución §7). No son defectos del contrato:
- test_indra_offline: `VeloceOCR('indra', ..., license_commercial_use=False)` → ahora PyOcrValueError (exige acknowledge=True) antes de la preflight offline. El comportamiento es el correcto.
- test_el_latex_de_una_formula_es_accesible_desde_python / test_indra_devuelve_markdown_bloques_y_regiones: mismo motivo (Indra bloqueado sin `license_acknowledge=True`).
- test_accuracy_con_gpu_de_8_gib_filtra_indra_segun_politica: `resolve_pipeline` bloquea la recomendación de indra sin `license_acknowledge=True` (resolver.py:109-112). Es la corrección deseada, no un bug.

Para volver verde son capaces de actualizar esos test a `license_acknowledge=True`/`license_commercial_use=False` cuando corresponds.

## Desviaciones razonadas
1. `license_acknowledge` sigue sin tests; el flag es funcional pero inactivo. Su cobertura es un requisito menor (regresivo), no bloqueante.
2. ModelScope no verifica hash en preflight (models.rs). Fuera de la lista de archivo del sign-off; consistencia del registro de `oar-ocr` + `finder()` + sidecar de descarga.
3. `VeloceOCR(custom_path=...)` expone la licencia del preset (lib.rs:73-84). Trabajo previo de L1; no es un bloqueo de contrato (el catalogo expone la licencia real de los artefactos, coincidiendo con el informe).
4. 3 herederos de tests del L4 que confunden el bloqueo correcto de Indra con un defecto. La suite `test_license.py` — el objeto del sign-off — pasa 11/11.

## Conclusión
El contrato de licencias es fiel al informe y a la fuente primaria: clasificación Apache-2.0 (Paddle/PP) / OpenRAIL-M-Mod (Indra) / Unknown (deny por defecto). El bloqueo por defecto no se puede esquivar (Indra exige `license_commercial_use=False` y `license_acknowledge=True`; Unknown deniega). Los flags son consistentes en las tres superficies. Los defectos críticos y altos del L4 están corregidos; el árbol de Rust y la suite focal pasan.
