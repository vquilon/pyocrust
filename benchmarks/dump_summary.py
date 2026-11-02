import json
d=json.load(open('results/2026-11-01_14-37-40/summary.json'))
print(json.dumps(d, indent=2)[:2000])
"