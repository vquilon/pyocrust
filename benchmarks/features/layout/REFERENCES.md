# Referencias externas — feature `layout`

> Valores **`referencia`**: publicados en papers / model cards, **no ejecutados aquí**.
> Métrica de detección de layout sobre **DocLayNet** (mAP). **No comparable 1:1** con
> nuestras cifras (dataset, preprocesado y GT distintos). Consultadas 2026-11-02.

| Modelo | Métrica | Valor | Fuente |
| :--- | :--- | ---: | :--- |
| YOLOv10-x (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
| YOLOv10-b (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
|| YOLOv10-l (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
|| YOLOv10-m (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
|| YOLOv10-s (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
|| YOLOv10-n (DocLayNet fine-tune) | mAP@0.5 | — | [ref: https://huggingface.co/omoured/YOLOv10-Document-Layout-Analysis] |
|| RT-DETR (Docling) | mAP@0.5 | — | [ref: https://arxiv.org/abs/2502.14949] (KITAB-Bench) |
|| Surya | mAP@0.5 | — | [ref: https://arxiv.org/abs/2502.14949] |
| Docling heron | mAP@0.5:0.95 | — | [ref: https://arxiv.org/abs/2509.11720] (COCO-tools) |
| Docling heron-101 | mAP@0.5:0.95 | — | [ref: https://arxiv.org/abs/2509.11720] (canonical DocLayNet) |

> **YOLO11 y YOLO26** (Ultralytics, fine-tune sobre DocLayNet / DocLayNet v1.2):
> sus model cards publican las curvas por clase, pero **no un mAP global en texto**
> ([ref: https://huggingface.co/Armaggheddon/yolo26-document-layout]). Se documentan
> aquí **sin cifra** para no inventar; añadir el valor cuando sea verificable.
