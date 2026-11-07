# Referencias externas — feature `rectification`

Resultados **publicados**, no ejecutados aquí. Las cifras de rectificación no se comparan directamente con nuestro SSIM en GT sintético: datasets, GT, OCR y protocolos son distintos.

## Datasets

| Dataset | Tamaño | `seal` / rectificación / orientación | URL | Licencia declarada | Descargable | GT | Métrica de referencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DocUNet benchmark** | 130 fotos reales (bench de evaluación); la publicación también describe ~100k imágenes sintéticas para entrenamiento | Rectificación: sí; seal/orientación: no | [Página oficial](https://www3.cs.stonybrook.edu/~cvl/docunet.html)[11] | No especificada en la página del dataset | Sí; originales, recortes centrados y scans GT (enlaces ZIP oficiales) | Sí; fotos deformadas y scans flatbed de referencia | MS-SSIM ↑, Local Distortion (LD) ↓; trabajos posteriores añaden AD y OCR ED/CER |
| **DIR300** | 300 fotos reales, 300 documentos | Rectificación: sí; seal/orientación: no | [DocGeoNet (oficial)](https://github.com/fh2019ustc/DocGeoNet) · [paper](https://arxiv.org/html/2210.08161)[13][14] | No atribuir licencia abierta a las imágenes; repo indica contacto para uso comercial | Sí; el repo publica el test set DIR300 | Sí; referencias de documentos rectangulares/alineados y datos geométricos descritos en el paper | MS-SSIM ↑, LD/AD ↓, OCR ED/CER ↓ |
| **UVDoc benchmark** | 50 imágenes de benchmark, sintéticas/pseudo-fotorrealistas | Rectificación: sí; seal/orientación: no | [Dataset](https://github.com/tanguymagne/UVDoc-Dataset) · [implementación/resultados corregidos](https://github.com/tanguymagne/UVDoc)[15][16] | Repo de código/dataset declara MIT; verificar por separado derechos de las texturas/documentos de origen | Sí; `UVDoc_benchmark.zip` | Sí; geometría/mapas y referencia para imágenes generadas | MS-SSIM ↑ y AD ↓ (valores corregidos por los autores para las 50 imágenes) |
| **ArbDoc** | 188 fotos reales con cuatro condiciones de borde | Rectificación: benchmark de dewarping; sólo OCR GT citado, no se confirma par GT pixel-perfect para evaluación visual. No seal/orientación | [Paper MataDoc](https://arxiv.org/html/2307.12571)[12] | No encontrada en el paper consultado | No hay enlace de descarga pública citado en el paper | Sí para OCR; GT geométrico/render de referencia no confirmado en la fuente consultada | ED/CER OCR por tipo de borde; usar con cautela como métrica indirecta de rectificación |

**OmniDocBench** (1.651 páginas) y **ParseBench** (2.078 páginas únicas) no son benchmarks de rectificación: ninguno proporciona transformaciones/imagen rectificada de referencia. OmniDocBench evalúa parsing y ParseBench evalúa reglas de fidelidad/estructura. [1][2][3]

El benchmark clásico DocUNet aporta GT de scan y código de evaluación MS-SSIM/LD. DIR300 es mayor y más desafiante en fondos/iluminación; su paper afirma ground truth capturado/alineado antes de deformar. UVDoc es sintético pero de referencia abierta y con corrección pública de métricas para el conjunto completo; no confundirlo con prueba de generalización completamente real. [11][12][13][14][15][16][17]

## Modelos y resultados publicados

| Modelo | Benchmark | Resultado publicado | Fuente |
| :--- | :--- | :--- | :--- |
| **MataDoc** | DocUNet (130 imágenes; métricas de imagen; OCR en subconjunto) | MS-SSIM 0,5029 ↑; LD 7,4263 ↓; AD 0,3154 ↓; CER 0,1692/0,1505 ↓ (dos configuraciones OCR indicadas por el paper) | [Paper, tabla 4](https://arxiv.org/html/2307.12571)[12] |
| **MataDoc** | DIR300 (300 imágenes; OCR reportado por el paper) | MS-SSIM 0,6389 ↑; LD 5,7593 ↓; AD 0,1785 ↓; ED 482,90 ↓; CER 0,1785 ↓ | [Paper, tabla 5](https://arxiv.org/html/2307.12571)[12] |
| **UVDoc (método propuesto)** | UVDoc benchmark completo (50 imágenes; valores corregidos por los autores) | MS-SSIM 0,785 ↑; AD 0,119 ↓ | [Repositorio oficial, tabla corregida](https://github.com/tanguymagne/UVDoc)[16] |
| **DocGeoNet** | UVDoc benchmark completo (50 imágenes; valores corregidos) | MS-SSIM 0,706 ↑; AD 0,168 ↓ | [Repositorio oficial UVDoc, tabla corregida](https://github.com/tanguymagne/UVDoc) |

Los valores de UVDoc en el repositorio reemplazan explícitamente los números originales calculados con sólo la mitad del benchmark; conservar los corregidos para cualquier comparación. Los resultados MataDoc sobre DocUNet/DIR300 dependen de la versión del set y del protocolo OCR del paper. [12][14][16]

## Recomendación para este benchmark

- Priorizar DocUNet como evaluación pública real con GT raster y métricas de imagen; DIR300 como segundo set real de mayor tamaño.
- UVDoc es útil para reproducibilidad y métricas visuales, pero identificarlo claramente como datos sintéticos.
- ArbDoc puede informar impacto OCR en casos de borde incompleto, no sustituir una métrica pixel-level hasta confirmar acceso/GT geométrico.
- No presentar métricas de OCR (`CER`, `ED`) como equivalentes a SSIM/LD: evalúan resultados diferentes.

## Sources

[1] https://huggingface.co/datasets/opendatalab/OmniDocBench/raw/main/README.md
[2] https://github.com/run-llama/ParseBench/blob/main/README.md
[3] https://huggingface.co/datasets/llamaindex/ParseBench
[11] https://www3.cs.stonybrook.edu/~cvl/docunet.html
[12] https://arxiv.org/html/2307.12571
[13] https://github.com/fh2019ustc/DocGeoNet
[14] https://arxiv.org/html/2210.08161
[15] https://github.com/tanguymagne/UVDoc-Dataset
[16] https://github.com/tanguymagne/UVDoc
[17] https://arxiv.org/html/2302.02887
