# Referencias externas — feature `full_page`

> Valores **`referencia`**: leaderboard de **OmniDocBench** (v1.6, *overall score*),
> publicados por los autores, **no ejecutados aquí**. **No comparable 1:1** con
> nuestras cifras (nuestro banco aún no mide `full_page` con GT de página).

| Modelo | Tipo | Overall ↑ | Fuente |
| :--- | :--- | ---: | :--- |
| MinerU2.5-Pro | VLM especializado (1.2B) | — | [ref: https://github.com/OpenDataLab/OmniDocBench] (consultado 2026-11-02) |
| MinerU-2.5 | VLM especializado (1.2B) | — | [ref: https://github.com/OpenDataLab/OmniDocBench] (consultado 2026-11-02) |
| MinerU-Pipeline | Pipeline tools | — | [ref: https://github.com/OpenDataLab/OmniDocBench] (consultado 2026-11-02) |
| PaddleOCR (OCR-based) | OCR | — | [ref: https://arxiv.org/html/2412.07626v2] (OmniDocBench paper, consultado 2026-11-02) |

## MinerU2.5 — **documentado, NO medido (licencia AGPL-3.0)**

`opendatalab/MinerU2.5-2509-1.2B`
([ref: https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B]) es un VLM de parse
de 1.2B con **licencia AGPL-3.0** (repo y pesos). Por eso **no se mide** en esta
comparativa: la AGPL lo limita a un **contexto de benchmark no comercial** y
**jamás** es preset de producto del envoltorio (`model-license-governance`). Los
tres VLMs que **sí** se miden (`lightonocr` Apache-2.0, `glm_ocr` MIT,
`paddleocr_vl` Apache-2.0) son de licencia permisiva y sí son enviables.

> Si en el futuro se mide MinerU2.5, su fila debe declarar la licencia AGPL y el
> contexto no comercial, y **nunca** entrar en `DEFAULT_BACKENDS` ni en un preset.
