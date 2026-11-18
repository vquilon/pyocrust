import sys
sys.path.insert(0, '.')
import pyocrust
print('PYOCRUST:', pyocrust.__file__)
print('constants:', 'GEOM_MIN_SIDE_PX', pyocrust.GEOM_MIN_SIDE_PX,
      'ROUTE_MIN_REGIONS', pyocrust.ROUTE_MIN_REGIONS,
      'ROUTE_MIN_DENSITY', pyocrust.ROUTE_MIN_DENSITY)
print('pipeline_profiles:', sorted(pyocrust.pipeline_profiles().keys()))
