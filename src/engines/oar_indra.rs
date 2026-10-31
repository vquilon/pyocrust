//! Indra page reader over the existing model registry and output types.

use crate::core::{
    BoundingBox, LayoutRegion, ModelPaths, ModelSpec, OcrEngineBackend, OcrError,
    OcrOutput, StructureResult, TextRegion,
};

#[derive(Debug, Default)]
pub struct OarIndraEngine {
    pipeline: Option<oar_ocr::indra::IndraOcr>,
}

impl OcrEngineBackend for OarIndraEngine {
    fn load_model(&mut self, paths: &ModelPaths) -> Result<(), OcrError> {
        if paths.spec != ModelSpec::Indra {
            return Err(OcrError::InvalidInput {
                message: "OarIndraEngine requires the indra preset".into(),
            });
        }
        let root = paths.detection_model.parent().ok_or_else(|| OcrError::Config {
            message: "indra model directory is missing".into(),
        })?;
        self.pipeline = Some(oar_ocr::indra::IndraOcrBuilder::new(root)
            .math(true)
            .build()
            .map_err(|error| OcrError::ModelLoad {
                model_path: root.display().to_string(),
                reason: error.to_string(),
            })?);
        Ok(())
    }

    fn recognize(&self, image_bytes: &[u8]) -> Result<OcrOutput, OcrError> {
        let pipeline = self.pipeline.as_ref().ok_or_else(|| OcrError::InvalidInput {
            message: "model not loaded".into(),
        })?;
        let image = image::load_from_memory(image_bytes)
            .map_err(OcrError::from)?.into_rgb8();
        let page = pipeline.predict(vec![image])
            .map_err(|error| OcrError::Inference {
                message: error.to_string(),
                source: Some(Box::new(error)),
            })?
            .into_iter().next().ok_or_else(|| OcrError::Inference {
                message: "indra returned no page for one input image".into(),
                source: None,
            })?;
        let regions = page.lines.into_iter().map(|line| TextRegion {
            text: line.text,
            confidence: line.confidence,
            box_: bbox(line.bbox, page.rotation, page.width, page.height),
        }).collect();
        let elements = page.blocks.into_iter().map(|block| LayoutRegion {
            kind: block.label,
            text: block.text,
            // Indra has no block confidence; do not invent a model score.
            confidence: 0.0,
            box_: bbox(block.bbox, page.rotation, page.width, page.height),
        }).collect();
        Ok(OcrOutput::Structure(StructureResult {
            markdown: page.markdown,
            regions,
            elements,
            // Inline math is preserved in markdown/regions. Indra does not
            // expose separate formula records, so this list stays empty.
            formulas: Vec::new(),
        }))
    }
}

// Indra rotates the input clockwise before OCR. Undo only that rotation:
// the crate already maps boxes back across deskew and vertical reading.
fn bbox([x1, y1, x2, y2]: [f32; 4], rotation: u32, width: u32, height: u32) -> BoundingBox {
    let (w, h) = (width as f32, height as f32);
    let [x1, y1, x2, y2] = match rotation {
        90 => [y1, w - x2, y2, w - x1],
        180 => [w - x2, h - y2, w - x1, h - y1],
        270 => [h - y2, x1, h - y1, x2],
        _ => [x1, y1, x2, y2],
    };
    BoundingBox { x1, y1, x2, y2 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bbox_recovers_original_after_clockwise_quarter_turns() {
        let original = BoundingBox {
            x1: 13.0,
            y1: 27.0,
            x2: 79.0,
            y2: 61.0,
        };
        // Original page: 200 x 120. Independently rotate its four box corners
        // clockwise via (x, y) -> (height - y, x), then take their min/max.
        // Quarter turns swap page dimensions; these are the oriented sizes.
        let cases = [
            (0, 200, 120, [13.0, 27.0, 79.0, 61.0]),
            (90, 120, 200, [59.0, 13.0, 93.0, 79.0]),
            (180, 200, 120, [121.0, 59.0, 187.0, 93.0]),
            (270, 120, 200, [27.0, 121.0, 61.0, 187.0]),
        ];
        for (rotation, width, height, rotated) in cases {
            assert_eq!(
                bbox(rotated, rotation, width, height),
                original,
                "rotation {rotation}"
            );
        }
    }
}
