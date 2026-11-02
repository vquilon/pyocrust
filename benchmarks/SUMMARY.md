# Resumen de benchmarks (métrica titular por feature)

> Generado por `features/summary.py` desde los `REPORT.md`. Todo `medido` (CPU).

## text — FUNSD (detección + reconocimiento)

| Motor | word F1 ↑ |
| :--- | ---: |
| **pyocrust (tiny)** | 0.734 |
| rapidocr (default) | 0.660 |
| easyocr (default) | 0.384 |

## formula — OmniDocBench (fórmula → LaTeX)

| Motor | LaTeX similarity ↑ |
| :--- | ---: |
| **pyocrust_formulanet (direct)** | 0.550 |
| pix2tex (default) | 0.533 |
| **pyocrust_formula (pp-formulanet-s)** | 0.419 |
| **pyocrust_indra (math)** | 0.184 |
| easyocr (default) | 0.152 |
| rapidocr (default) | 0.104 |
