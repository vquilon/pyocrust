# Referencias externas — feature `layout`

> Valores **`referencia`**: publicados en papers / model cards, **no ejecutados aquí**.
> Métrica de detección de layout sobre **DocLayNet** (mAP). **No comparable 1:1** con
> nuestras cifras (dataset, preprocesado y GT distintos). Consultadas 2026-11-02.

| Modelo | Métrica | Valor | Fuente |
| :--- | :--- | ---: | :--- |
| YOLOv10-x (DocLayNet fine-tune) | mAP@0.5 | 0.924 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-b (DocLayNet fine-tune) | mAP@0.5 | 0.922 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-l (DocLayNet fine-tune) | mAP@0.5 | 0.921 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-m (DocLayNet fine-tune) | mAP@0.5 | 0.917 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-s (DocLayNet fine-tune) | mAP@0.5 | 0.905 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-n (DocLayNet fine-tune) | mAP@0.5 | 0.892 | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| DocLayout-YOLO | mAP (DocLayNet) | 0.797 | [ref: https://arxiv.org/abs/2410.12628] |
| RT-DETR (Docling) | mAP@0.5 | 0.758 | [ref: https://arxiv.org/abs/2502.14949] (KITAB-Bench) |
| YOLO-doclaynet (MinerU) | mAP@0.5 | 0.675 | [ref: https://arxiv.org/abs/2502.14949] |
| Surya | mAP@0.5 | 0.404 | [ref: https://arxiv.org/abs/2502.14949] |
| Docling heron | mAP@0.5:0.95 | 0.699 | [ref: https://arxiv.org/abs/2509.11720] (COCO-tools) |
| Docling heron-101 | mAP@0.5:0.95 | 0.780 | [ref: https://arxiv.org/abs/2509.11720] (canonical DocLayNet) |

> **YOLO11 y YOLO26** (Ultralytics, fine-tune sobre DocLayNet / DocLayNet v1.2):
> sus model cards publican las curvas por clase, pero **no un mAP global en texto**
> ([ref: https://huggingface.co/Armaggheddon/yolo26-document-layout]). Se documentan
> aquí **sin cifra** para no inventar; añadir el valor cuando sea verificable.
