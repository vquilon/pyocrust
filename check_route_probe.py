"""Sonda propia (probador) sobre RAUTO (DESIGN.md §12).

No entra en tests/ ni modifica la suite: comprueba con efecto medido
1) que route() es pura (nunca construye modelos/tareas), 2) los disparos de
frontera de GEOM_MIN_SIDE_PX, ROUTE_MIN_REGIONS, ROUTE_MIN_DENSITY y su
dirección exacta, 3) que auto_recognize(probe=False) no construye ninguna
sesión de estructura (VeloceOCR/TaskPredictor que revienten si se llaman con
pp_structurev3 / text_detection).
"""
import sys
sys.path.insert(0, '.')

from unittest.mock import patch

import pyocrust
from pyocrust import route, TaskSpec

results = []

def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    print(('PASS' if cond else 'FAIL'), '-', name, ('| ' + str(detail) if detail else ''))

# --- 1) Los tres umbrales son exactamente los de §12.3 (reflexión, no hardcode) ---
check('GEOM_MIN_SIDE_PX == 64', pyocrust.GEOM_MIN_SIDE_PX == 64, pyocrust.GEOM_MIN_SIDE_PX)
check('ROUTE_MIN_REGIONS == 24', pyocrust.ROUTE_MIN_REGIONS == 24, pyocrust.ROUTE_MIN_REGIONS)
check('ROUTE_MIN_DENSITY == 0.12', pyocrust.ROUTE_MIN_DENSITY == 0.12, pyocrust.ROUTE_MIN_DENSITY)

# --- 2) Frontieras de GEOM_MIN_SIDE_PX (precondición estricta: min(W,H) < 64) ---
check('frontera geom: W=63 -> geometry', route(None, {'W': 63, 'H': 1000}).reason == 'geometry')
check('frontera geom: W=64 -> DEFAULT-TEXT (64 no dispara)',
      route(None, {'W': 64, 'H': 1000}).reason == 'default-text')
check('frontera geom: W=64,H=64 -> DEFAULT-TEXT',
      route(None, {'W': 64, 'H': 64}).reason == 'default-text')

# --- 3) Frontieras de ROUTE_MIN_REGIONS / DENSITY ---
check('frontera sondas: regions=23 (<24) -> texto',
      route(None, {'n_regions': 23, 'ink_ratio': 0.0}).features == ('pp_ocrv6_tiny',))
check('frontera sondas: regions=24 (>=24) -> estructura',
      route(None, {'n_regions': 24, 'ink_ratio': 0.0}).features == ('pp_structurev3',))
check('frontera densidad: 0.12 (>=0.12) -> estructura',
      route(None, {'n_regions': 0, 'ink_ratio': 0.12}).features == ('pp_structurev3',))
check('frontera densidad: 0.1199 (<0.12) -> texto',
      route(None, {'n_regions': 0, 'ink_ratio': 0.1199}).features == ('pp_ocrv6_tiny',))
check('frontera densidad: 0.1201 (>=0.12) -> estructura',
      route(None, {'n_regions': 0, 'ink_ratio': 0.1201}).features == ('pp_structurev3',))

# --- 4) Geometria gana sobre la sonda ---
check('geom gana: 40x40 con 99 regiones -> geometry',
      route(None, {'W': 40, 'H': 40, 'n_regions': 99, 'ink_ratio': 0.99}).reason == 'geometry')

# --- 5) signals con solo una dimensiï¿½n no dispara geometrï¿½a ---
check('señal sin par (W solo) no dispara geometría',
      route(None, {'W': 40}).reason == 'default-text')

# --- 6) route() PURA: con mocks que revienten si construyen modelos ---
class _ExplodeModels:
    """Record no se usa; la presencia del constructor ya es fallo."""
    def __init__(self, *args, **kwargs):
        raise AssertionError('route() construyó algo: %r %r' % (args, kwargs))

with patch.object(pyocrust.multifeature, 'TaskPredictor', _ExplodeModels), \
     patch.object(pyocrust.multifeature, 'VeloceOCR', _ExplodeModels):
    route(TaskSpec(tables=True), None)
    route(['layout', 'table'], None)
    route(None, {'n_regions': 31, 'ink_ratio': 0.9})
    route(None, None)
    route(None, {'W': 40, 'H': 40})
check('route() no construye modelos en los 5 path', True)

# --- 7) auto_recognize(probe=False) no construye ninguna sesión de estructura ---
class _ExplodeVeloceOCR:
    calls = []
    def __init__(self, preset, custom_path=None, device='cpu', **opts):
        if preset == 'pp_structurev3':
            raise AssertionError('auto_recognize(probe=False) cargó estructura: %r' % preset)
        self.preset = preset
        type(self).calls.append(preset)
    def recognize(self, image):
        return {'preset': self.preset}

class _ExplodeTaskTask:
    calls = []
    def __init__(self, task, models=None, device='cpu', **opts):
        if task == 'text_detection':
            raise AssertionError('auto_recognize(probe=False) llamó text_detection: %r' % task)
        self.task = task

with patch.object(pyocrust.multifeature, 'VeloceOCR', _ExplodeVeloceOCR), \
     patch.object(pyocrust.multifeature, 'TaskPredictor', _ExplodeTaskTask):
    salida, decision = pyocrust.auto_recognize('pagina.png', probe=False)
check('auto_recognize(probe=False) decision: features=pp_ocrv6_tiny',
      decision.features == ('pp_ocrv6_tiny',), decision.features)
check('auto_recognize(probe=False) decision: preset=pp_ocrv6 size=tiny',
      (decision.preset, decision.size) == ('pp_ocrv6', 'tiny'), (decision.preset, decision.size))
check('auto_recognize(probe=False) decision: reason=default-text',
      decision.reason == 'default-text', decision.reason)
check('auto_recognize(probe=False) solo pp_ocrv6_tiny (0 estructura, 0 sonda)',
      _ExplodeVeloceOCR.calls == ['pp_ocrv6_tiny'], repr(_ExplodeVeloceOCR.calls))
check('auto_recognize(probe=False) TaskPredictor nunca llamado (0 tareas)',
      _ExplodeTaskTask.calls == [], repr(_ExplodeTaskTask.calls))
check('auto_recognize(probe=False) salida es el resultado del preset texto',
      salida == {'preset': 'pp_ocrv6_tiny'}, salida)

# --- 8) Control positivo: con probe=True SI se dispara estructura (demo del probe) ---
class _LightVeloceOCR:
    calls = []
    def __init__(self, preset, custom_path=None, device='cpu', **opts):
        _LightVeloceOCR.calls.append(preset)
        self.preset = preset
    def recognize(self, image):
        return {'preset': self.preset}

class _ProbingTask:
    def __init__(self, task, models=None, device='cpu', **opts):
        self.task = task
    def predict(self, image):
        # 1 caja 200x50 en 200x100 -> ink_ratio 0.25 >= 0.12 -> estructura
        return {'detections': [{'bbox': [[0, 0], [200, 0], [200, 50], [0, 50]], 'score': 1.0}]}

with patch.object(pyocrust.multifeature, 'VeloceOCR', _LightVeloceOCR), \
     patch.object(pyocrust.multifeature, 'TaskPredictor', _ProbingTask):
    _, dec = pyocrust.auto_recognize('im.png', probe=True)
    check('control positivo probe=True -> estructura (pp_structurev3)',
          dec.features == ('pp_structurev3',) and dec.reason == 'probe',
          (dec.features, dec.reason))

failures = [r for r in results if not r[1]]
print()
print('TOTAL: %d checks, %d FAIL' % (len(results), len(failures)))
sys.exit(1 if failures else 0)
