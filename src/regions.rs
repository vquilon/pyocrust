//! SDK de regiones (`DESIGN.md` §11, bloque `RDET`): detección de cajas y OCR
//! por recorte, ambos sobre la imagen a resolución nativa.
//!
//! Reutiliza `TextDetectionPredictor`/`TextRecognitionPredictor` de `oar-ocr` y
//! el primitivo `image::imageops::crop_imm`; no introduce ningún tipo nuevo
//! (§11.3). Los predictores se construyen en la primera llamada y quedan
//! residentes: el detector solo se reconstruye cuando cambian los knobs de
//! detección efectivos, el reconocedor solo cuando cambia su umbral.

use std::path::Path;
use std::sync::{Arc, Mutex};

use image::RgbImage;
use pyo3::prelude::*;

use crate::core::error::{OcrError, PyOcrValueError};
use crate::core::{BoundingBox, ModelPaths, ModelSpec, OcrResult, OcrSize, TextRegion};
use crate::engines::TextDetectionOptions;
use oar_ocr::core::config::OrtSessionConfig;
use oar_ocr::core::ModelSource;
use oar_ocr::predictors::{TextDetectionPredictor, TextRecognitionPredictor};

/// Detección + reconocimiento por región de un preset.
///
/// No existe para los presets sin par det+rec propio (`indra`, VLM): el SDK de
/// regiones se define para los presets de texto (`pp_ocrv6*`) y
/// `pp_structurev3` (§11.2), y `RegionEngine::new` devuelve `None` en ellos.
pub struct RegionEngine {
    paths: ModelPaths,
    ort_session: OrtSessionConfig,
    /// Tamaño del preset: fija los defaults de umbral y el lote de rec (§11.5).
    size: OcrSize,
    /// Knobs del constructor; los kwargs de `detect_regions` los pisan.
    base_detection: TextDetectionOptions,
    detector: Mutex<Option<(TextDetectionOptions, Arc<TextDetectionPredictor>)>>,
    recognizer: Mutex<Option<(f32, Arc<TextRecognitionPredictor>)>>,
}

impl RegionEngine {
    /// `Some` solo para los presets con par det+rec propio.
    pub fn new(
        spec: &ModelSpec,
        paths: ModelPaths,
        ort_session: OrtSessionConfig,
        base_detection: TextDetectionOptions,
    ) -> Option<Self> {
        let size = match spec {
            ModelSpec::PpOcrV6(size) => *size,
            ModelSpec::PpStructureV3 => OcrSize::Tiny,
            ModelSpec::Indra | ModelSpec::Vlm(_) => return None,
        };
        Some(Self {
            paths,
            ort_session,
            size,
            base_detection,
            detector: Mutex::new(None),
            recognizer: Mutex::new(None),
        })
    }

    /// Recortes por pasada de rec cuando el llamante no lo fija (`§11.5`).
    pub fn default_batch(&self) -> usize {
        if self.size == OcrSize::Tiny { 16 } else { 4 }
    }

    /// Cajas AABB de las regiones detectadas, en coordenadas de la imagen.
    pub fn detect(
        &self,
        py: Python<'_>,
        page: RgbImage,
        overrides: &TextDetectionOptions,
    ) -> PyResult<Vec<BoundingBox>> {
        let options = self.base_detection.or(overrides);
        let detector = self.detector(&options)?;
        let result = py
            .detach(move || detector.predict(vec![page]))
            .map_err(|error| inference_error(error))?;
        Ok(result
            .detections
            .into_iter()
            .flatten()
            .map(|detection| {
                let (x1, y1, x2, y2) = detection.bbox.aabb();
                BoundingBox { x1, y1, x2, y2 }
            })
            .collect())
    }

    /// Una `TextRegion` por caja de entrada: la caja dada y el texto (o `""`) y
    /// score (`0.0`) del reconocimiento de su recorte nativo.
    pub fn recognize(
        &self,
        py: Python<'_>,
        page: &RgbImage,
        boxes: &[BoundingBox],
        score_threshold: f32,
        batch: usize,
    ) -> PyResult<OcrResult> {
        let recognizer = self.recognizer(score_threshold)?;
        let (width, height) = page.dimensions();
        let mut recognized: Vec<Option<(String, f32)>> = vec![None; boxes.len()];

        for window in (0..boxes.len()).collect::<Vec<_>>().chunks(batch) {
            let mut crops = Vec::new();
            let mut targets = Vec::new();
            for &index in window {
                if let Some(crop) = crop_region(page, &boxes[index], width, height) {
                    crops.push(crop);
                    targets.push(index);
                }
            }
            if crops.is_empty() {
                continue;
            }
            let recognizer = Arc::clone(&recognizer);
            let output = py
                .detach(move || recognizer.predict(crops))
                .map_err(|error| inference_error(error))?;
            for (offset, &index) in targets.iter().enumerate() {
                recognized[index] = Some((
                    output.texts.get(offset).cloned().unwrap_or_default(),
                    output.scores.get(offset).copied().unwrap_or(0.0),
                ));
            }
        }

        Ok(OcrResult {
            regions: boxes
                .iter()
                .zip(recognized)
                .map(|(box_, recognized)| {
                    let (text, confidence) = recognized.unwrap_or_default();
                    TextRegion {
                        text,
                        confidence,
                        box_: *box_,
                    }
                })
                .collect(),
        })
    }

    /// Detector residente para estos knobs (uno por configuración efectiva).
    fn detector(&self, options: &TextDetectionOptions) -> PyResult<Arc<TextDetectionPredictor>> {
        let mut slot = self.detector.lock().unwrap_or_else(|poison| poison.into_inner());
        if let Some((current, predictor)) = slot.as_ref() {
            if current == options {
                return Ok(Arc::clone(predictor));
            }
        }
        let model = self.paths.detection_model.clone();
        let predictor = TextDetectionPredictor::builder()
            .with_config(options.to_config(self.size))
            .with_ort_config(self.ort_session.clone())
            .build(ModelSource::from(model.clone()))
            .map_err(|error| model_error(&model, error))?;
        let predictor = Arc::new(predictor);
        *slot = Some((options.clone(), Arc::clone(&predictor)));
        Ok(predictor)
    }

    /// Reconocedor residente para este umbral.
    fn recognizer(&self, score_threshold: f32) -> PyResult<Arc<TextRecognitionPredictor>> {
        let mut slot = self.recognizer.lock().unwrap_or_else(|poison| poison.into_inner());
        if let Some((current, predictor)) = slot.as_ref() {
            if *current == score_threshold {
                return Ok(Arc::clone(predictor));
            }
        }
        let model = self.paths.recognition_model.clone().ok_or_else(|| {
            PyOcrValueError::new_err("this preset has no recognition model for the region SDK")
        })?;
        let dictionary = self.paths.character_dict.clone().ok_or_else(|| {
            PyOcrValueError::new_err("this preset has no character dictionary for the region SDK")
        })?;
        let predictor = TextRecognitionPredictor::builder()
            .score_threshold(score_threshold)
            .dict_path(dictionary)
            .with_ort_config(self.ort_session.clone())
            .build(ModelSource::from(model.clone()))
            .map_err(|error| model_error(&model, error))?;
        let predictor = Arc::new(predictor);
        *slot = Some((score_threshold, Arc::clone(&predictor)));
        Ok(predictor)
    }
}

/// Recorte nativo de una caja, o `None` si la caja no tiene área dentro de la
/// página (no hay nada que reconocer).
///
/// `crop_imm` ya recorta fuera de límites; el `clamp` previo evita además el
/// `x2 - x1` negativo de una caja invertida.
fn crop_region(page: &RgbImage, box_: &BoundingBox, width: u32, height: u32) -> Option<RgbImage> {
    let clamp = |value: f32, limit: u32| value.max(0.0).min(limit as f32) as u32;
    let x1 = clamp(box_.x1, width);
    let y1 = clamp(box_.y1, height);
    let x2 = clamp(box_.x2, width);
    let y2 = clamp(box_.y2, height);
    if x2 <= x1 || y2 <= y1 {
        return None;
    }
    Some(image::imageops::crop_imm(page, x1, y1, x2 - x1, y2 - y1).to_image())
}

fn inference_error(error: impl std::fmt::Display) -> PyErr {
    OcrError::Inference {
        message: error.to_string(),
        source: None,
    }
    .into()
}

fn model_error(path: &Path, error: impl std::fmt::Display) -> PyErr {
    OcrError::ModelLoad {
        model_path: path.display().to_string(),
        reason: error.to_string(),
    }
    .into()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::VlmModel;

    fn paths(spec: &ModelSpec) -> ModelPaths {
        ModelPaths::new(Path::new("/nonexistent"), spec)
    }

    #[test]
    fn regions_exist_only_for_presets_with_det_and_rec() {
        let session = OrtSessionConfig::new();
        for spec in [ModelSpec::PpOcrV6(OcrSize::Tiny), ModelSpec::PpStructureV3] {
            assert!(
                RegionEngine::new(&spec, paths(&spec), session.clone(), TextDetectionOptions::default())
                    .is_some(),
                "{spec:?} must support the region SDK"
            );
        }
        for spec in [ModelSpec::Indra, ModelSpec::Vlm(VlmModel::GlmOcr)] {
            assert!(
                RegionEngine::new(&spec, paths(&spec), session.clone(), TextDetectionOptions::default())
                    .is_none(),
                "{spec:?} has no det+rec pair"
            );
        }
    }

    #[test]
    fn default_batch_is_16_for_tiny_and_4_otherwise() {
        let session = OrtSessionConfig::new();
        let tiny = RegionEngine::new(
            &ModelSpec::PpOcrV6(OcrSize::Tiny),
            paths(&ModelSpec::PpOcrV6(OcrSize::Tiny)),
            session.clone(),
            TextDetectionOptions::default(),
        )
        .expect("tiny supports regions");
        let medium = RegionEngine::new(
            &ModelSpec::PpOcrV6(OcrSize::Medium),
            paths(&ModelSpec::PpOcrV6(OcrSize::Medium)),
            session,
            TextDetectionOptions::default(),
        )
        .expect("medium supports regions");
        assert_eq!(tiny.default_batch(), 16);
        assert_eq!(medium.default_batch(), 4);
    }

    #[test]
    fn crop_region_clamps_boxes_to_the_page() {
        let page = RgbImage::new(100, 50);
        // Caja entera fuera de la página: no hay recorte.
        let outside = BoundingBox { x1: 200.0, y1: 10.0, x2: 300.0, y2: 20.0 };
        assert!(crop_region(&page, &outside, 100, 50).is_none());
        // Caja invertida (x2 < x1): sin área.
        let inverted = BoundingBox { x1: 30.0, y1: 10.0, x2: 10.0, y2: 20.0 };
        assert!(crop_region(&page, &inverted, 100, 50).is_none());
        // Caja que rebasa el borde: se recorta a la parte visible.
        let clipped = BoundingBox { x1: 90.0, y1: 40.0, x2: 500.0, y2: 500.0 };
        let crop = crop_region(&page, &clipped, 100, 50).expect("la parte visible se recorta");
        assert_eq!(crop.dimensions(), (10, 10));
    }
}
