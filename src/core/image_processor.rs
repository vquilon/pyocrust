//! Preprocesamiento puro de imagen: `ScaleDown` y `FullPageTiling`.
//!
//! **ADR-009:** estas funciones existen y se testean, pero el pipeline general
//! no las aplica. `ScaleDown` es la estrategia por defecto del pipeline, que
//! delega el escalado en `oar-ocr` (`preprocess.rs`, `limit_side_len`) porque
//! respeta la relación de aspecto que esperan los modelos de layout y tablas.
//! `FullPageTiling` queda como utilidad **opt-in**: trocear rompe la coherencia
//! geométrica de esos modelos, así que solo se aplica si alguien lo pide.
//!
//! Son funciones puras sobre `image::RgbImage`: sin I/O, sin red y sin
//! conocer `oar-ocr`. El adaptador PyO3 vive en [`pyapi`], separado para que
//! el nombre de la función pura no choque con el de la función expuesta.

use image::imageops::FilterType;
use image::RgbImage;

use super::error::ImageProcessError;

/// Mosaico por defecto de `FullPageTiling` (ADR-009, `DECISIONS.md` §5).
pub const DEFAULT_TILE_SIZE: u32 = 512;
/// Solapamiento por defecto de `FullPageTiling` (ADR-009, `DECISIONS.md` §5).
pub const DEFAULT_OVERLAP: u32 = 64;
/// Lado máximo que `oar-ocr` usa como límite en su preprocesamiento.
pub const DEFAULT_MAX_SIDE: u32 = 2048;

/// Mosaico recortado de una imagen, con su desplazamiento en la imagen origen.
///
/// El desplazamiento permite traducir las coordenadas de una caja detectada
/// dentro del mosaico de vuelta a la imagen completa.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Tile {
    /// Desplazamiento horizontal en la imagen origen.
    pub x: u32,
    /// Desplazamiento vertical en la imagen origen.
    pub y: u32,
    /// Ancho del mosaico, menor o igual que `tile_size` en los bordes.
    pub width: u32,
    /// Alto del mosaico, menor o igual que `tile_size` en los bordes.
    pub height: u32,
    /// Mosaico recortado. Nunca más grande que `tile_size`.
    pub image: RgbImage,
}

impl Tile {
    /// Traslada una coordenada horizontal del mosaico a la imagen origen.
    pub fn global_x(&self, local_x: u32) -> u32 {
        self.x + local_x
    }

    /// Traslada una coordenada vertical del mosaico a la imagen origen.
    pub fn global_y(&self, local_y: u32) -> u32 {
        self.y + local_y
    }
}

/// Parámetros de `ScaleDown`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScaleDownOptions {
    /// Lado máximo de salida. Por defecto `DEFAULT_MAX_SIDE`.
    pub max_side: u32,
    /// Filtro de remuestreo. Por defecto `FilterType::Triangle` (bilineal).
    pub filter: FilterType,
}

impl Default for ScaleDownOptions {
    fn default() -> Self {
        Self {
            max_side: DEFAULT_MAX_SIDE,
            filter: FilterType::Triangle,
        }
    }
}

/// Parámetros de `FullPageTiling`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FullPageTilingOptions {
    /// Lado del mosaico. Por defecto 512 (ADR-009).
    pub tile_size: u32,
    /// Solapamiento entre mosaicos adyacentes. Por defecto 64 (ADR-009).
    pub overlap: u32,
}

impl Default for FullPageTilingOptions {
    fn default() -> Self {
        Self {
            tile_size: DEFAULT_TILE_SIZE,
            overlap: DEFAULT_OVERLAP,
        }
    }
}

/// Redimensiona una imagen manteniendo la relación de aspecto (ADR-009).
///
/// Si la imagen ya cabe en `max_side`, se devuelve una copia con las mismas
/// dimensiones en lugar de una ampliación, porque subir de resolución no
/// aporta información al modelo y sí cuesta memoria.
pub fn scale_down(image: &RgbImage, options: &ScaleDownOptions) -> Result<RgbImage, ImageProcessError> {
    let (width, height) = image.dimensions();
    if width == 0 || height == 0 {
        return Err(ImageProcessError::EmptyImage);
    }
    if options.max_side == 0 {
        return Err(ImageProcessError::ZeroMaxSide);
    }

    let longest = width.max(height);
    if longest <= options.max_side {
        return Ok(image.clone());
    }

    // Ambos lados se derivan del mismo factor para que el redondeo acumulado
    // no deforme la imagen y el lado largo nunca supere `max_side`.
    let scale = options.max_side as f64 / longest as f64;
    let new_width = ((width as f64 * scale).floor() as u32).max(1);
    let new_height = ((height as f64 * scale).floor() as u32).max(1);

    Ok(image::imageops::resize(
        image,
        new_width,
        new_height,
        options.filter,
    ))
}

/// Trocea una imagen en mosaicos con solapamiento (ADR-009).
///
/// Reglas del troceado:
///
/// * El avance entre mosaicos es `tile_size - overlap`.
/// * El **último** mosaico de cada lado se realinea con el borde de la imagen
///   (`side - tile_size`), de modo que lo que se ahorra de avance se gana en
///   solapamiento: entre dos mosaicos adyacentes siempre hay **al menos**
///   `overlap` píxeles, nunca menos, y ninguna franja queda sin cubrir.
/// * Los mosaicos son de `tile_size` salvo en el borde, donde se recorta el
///   resto de imagen.
/// * Una imagen más pequeña que un mosaico produce **un único mosaico**, que es
///   la imagen completa.
/// * `overlap >= tile_size` se rechaza con error: el avance sería cero o
///   negativo y el bucle nunca terminaría (ADR-009 lo exige explícitamente).
///
/// # Ejemplo
///
/// Una imagen de 1200x900 con `tile_size = 512` y `overlap = 64` produce 6
/// mosaicos: offsets horizontales `0, 448, 688` (el último realineado con
/// `1200 - 512`) y offsets verticales `0, 388` (`900 - 512`). Los solapamientos
/// resultantes son 64px y 272px en horizontal y 124px en vertical.
/// Calcula la geometría `(x, y, ancho, alto)` de cada mosaico a partir de las
/// dimensiones `(width, height)` y las opciones de troceado, sin recortar ni clonar
/// búferes de imagen.
pub fn full_page_tiling_boxes(
    width: u32,
    height: u32,
    options: &FullPageTilingOptions,
) -> Result<Vec<(u32, u32, u32, u32)>, ImageProcessError> {
    if options.tile_size == 0 {
        return Err(ImageProcessError::ZeroTileSize);
    }
    if options.overlap >= options.tile_size {
        return Err(ImageProcessError::OverlapTooLarge {
            overlap: options.overlap,
            tile_size: options.tile_size,
        });
    }

    if width == 0 || height == 0 {
        return Err(ImageProcessError::EmptyImage);
    }

    let step = options.tile_size - options.overlap;
    let xs = offsets(width, options.tile_size, step);
    let ys = offsets(height, options.tile_size, step);

    let mut boxes = Vec::with_capacity(xs.len() * ys.len());
    for &y in &ys {
        for &x in &xs {
            let tile_width = options.tile_size.min(width - x);
            let tile_height = options.tile_size.min(height - y);
            boxes.push((x, y, tile_width, tile_height));
        }
    }
    Ok(boxes)
}

pub fn full_page_tiling(
    image: &RgbImage,
    options: &FullPageTilingOptions,
) -> Result<Vec<Tile>, ImageProcessError> {
    let (width, height) = image.dimensions();
    let boxes = full_page_tiling_boxes(width, height, options)?;
    let tiles = boxes
        .into_iter()
        .map(|(x, y, tile_width, tile_height)| Tile {
            x,
            y,
            width: tile_width,
            height: tile_height,
            image: image::imageops::crop_imm(image, x, y, tile_width, tile_height).to_image(),
        })
        .collect();
    Ok(tiles)
}

/// Offsets de arranque de cada mosaico a lo largo de un lado de la imagen.
///
/// `step` siempre es positivo porque el llamador garantiza `overlap < tile_size`.
/// Cada avance es `min(step, side - tile_size)`, así que el último offset nunca
/// deja sin cubrir el final de la imagen y ningún avance supera `step` (que es
/// lo que garantiza el solapamiento mínimo).
fn offsets(side: u32, tile_size: u32, step: u32) -> Vec<u32> {
    let mut result = Vec::new();
    let mut offset: u32 = 0;
    loop {
        result.push(offset);
        if offset.saturating_add(tile_size) >= side {
            return result;
        }
        offset = (offset + step).min(side - tile_size);
    }
}

/// Adaptador PyO3 del troceado (ADR-009, utilidad opt-in).
///
/// Viven aquí para que `tests/test_tiling.py` (`V1`) pueda ejercitar el
/// solapamiento desde Python; el pipeline general no llama a esta función.
pub mod pyapi {
    use pyo3::prelude::*;
    use pyo3::types::PyModule;

    use super::FullPageTilingOptions;
    use crate::core::error::OcrError;

    /// Registra la utilidad de troceado en el módulo nativo.
    pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(full_page_tiling, m)?)?;
        Ok(())
    }

    /// Trocea una imagen codificada (PNG, JPEG, BMP, WebP...) y devuelve la
    /// geometría de cada mosaico como `(x, y, ancho, alto)`.
    ///
    /// `tile_size` por defecto es 512 y `overlap` por defecto 64 (ADR-009).
    /// Un `overlap` mayor o igual que `tile_size` lanza `PyOcrValueError`.
    #[pyfunction]
    #[pyo3(signature = (image, tile_size=None, overlap=None))]
    pub fn full_page_tiling(
        image: &[u8],
        tile_size: Option<u32>,
        overlap: Option<u32>,
    ) -> PyResult<Vec<(u32, u32, u32, u32)>> {
        let mut options = FullPageTilingOptions::default();
        if let Some(tile_size) = tile_size {
            options.tile_size = tile_size;
        }
        if let Some(overlap) = overlap {
            options.overlap = overlap;
        }
        let (width, height) = match image::ImageReader::new(std::io::Cursor::new(image))
            .with_guessed_format()
        {
            Ok(reader) => match reader.into_dimensions() {
                Ok(dims) => dims,
                Err(_) => {
                    let decoded = image::load_from_memory(image).map_err(OcrError::from)?;
                    (decoded.width(), decoded.height())
                }
            },
            Err(_) => {
                let decoded = image::load_from_memory(image).map_err(OcrError::from)?;
                (decoded.width(), decoded.height())
            }
        };
        let boxes =
            super::full_page_tiling_boxes(width, height, &options).map_err(OcrError::from)?;
        Ok(boxes)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Imagen sintética determinista: el valor de cada píxel depende de su
    /// posición, así que un mosaico mal recortado se detecta al comparar.
    fn synthetic(width: u32, height: u32) -> RgbImage {
        let mut image = RgbImage::new(width, height);
        for (x, y, pixel) in image.enumerate_pixels_mut() {
            *pixel = image::Rgb([(x % 256) as u8, (y % 256) as u8, (x.wrapping_add(y) % 256) as u8]);
        }
        image
    }

    /// Criterio de aceptación de la tarjeta `I2`: una imagen sintética de
    /// 1200x900 con mosaico 512 y solapamiento 64 produce **exactamente** los
    /// mosaicos y offsets esperados.
    #[test]
    fn tiling_1200x900_512_64_produces_the_expected_tiles() {
        let image = synthetic(1200, 900);
        let options = FullPageTilingOptions {
            tile_size: 512,
            overlap: 64,
        };
        let tiles = full_page_tiling(&image, &options).expect("el troceado debe succeed");

        // Avance = 512 - 64 = 448. En 1200: 0, 448 y el último realineado con
        // el borde (1200 - 512 = 688). En 900: 0 y 900 - 512 = 388.
        let expected: Vec<(u32, u32, u32, u32)> = vec![
            (0, 0, 512, 512),
            (448, 0, 512, 512),
            (688, 0, 512, 512),
            (0, 388, 512, 512),
            (448, 388, 512, 512),
            (688, 388, 512, 512),
        ];
        let actual: Vec<(u32, u32, u32, u32)> = tiles
            .iter()
            .map(|tile| (tile.x, tile.y, tile.width, tile.height))
            .collect();
        assert_eq!(
            actual, expected,
            "los mosaicos y offsets deben coincidir exactamente"
        );
        assert_eq!(tiles.len(), 6);
    }

    /// Ningún mosaico se solapa por debajo de 64px en los bordes de corte, y
    /// la unión de los mosaicos cubre la imagen entera (sin huecos).
    #[test]
    fn tiling_overlap_is_never_below_the_requested_value() {
        let image = synthetic(1200, 900);
        let options = FullPageTilingOptions {
            tile_size: 512,
            overlap: 64,
        };
        let tiles = full_page_tiling(&image, &options).unwrap();

        for tile in &tiles {
            assert!(tile.width > 0 && tile.height > 0, "mosaico vacío");
            assert!(tile.width <= options.tile_size && tile.height <= options.tile_size);
        }

        // Solapamiento entre offsets consecutivos de cada lado.
        let xs = offsets(1200, options.tile_size, options.tile_size - options.overlap);
        let ys = offsets(900, options.tile_size, options.tile_size - options.overlap);
        for window in xs.windows(2) {
            let overlap = options.tile_size - (window[1] - window[0]);
            assert!(
                overlap >= options.overlap,
                "solape horizontal de {overlap}px < {}px entre {window:?}",
                options.overlap
            );
        }
        for window in ys.windows(2) {
            let overlap = options.tile_size - (window[1] - window[0]);
            assert!(
                overlap >= options.overlap,
                "solape vertical de {overlap}px < {}px entre {window:?}",
                options.overlap
            );
        }

        // Recubrimiento fila a fila: sin huecos y llegando al borde derecho.
        let mut rows: Vec<u32> = tiles.iter().map(|tile| tile.y).collect();
        rows.sort_unstable();
        rows.dedup();
        for row in rows {
            let mut spans: Vec<(u32, u32)> = tiles
                .iter()
                .filter(|tile| tile.y == row)
                .map(|tile| (tile.x, tile.width))
                .collect();
            spans.sort_unstable();
            let mut cursor = 0;
            for (x, width) in spans {
                assert!(x <= cursor, "hueco entre {cursor} y {x} en la fila y={row}");
                cursor = x + width;
            }
            assert_eq!(cursor, 1200, "la fila y={row} no llega al borde derecho");
        }

        // Lo mismo por columnas.
        let mut columns: Vec<u32> = tiles.iter().map(|tile| tile.x).collect();
        columns.sort_unstable();
        columns.dedup();
        for column in columns {
            let mut spans: Vec<(u32, u32)> = tiles
                .iter()
                .filter(|tile| tile.x == column)
                .map(|tile| (tile.y, tile.height))
                .collect();
            spans.sort_unstable();
            let mut cursor = 0;
            for (y, height) in spans {
                assert!(y <= cursor, "hueco entre {cursor} y {y} en la columna x={column}");
                cursor = y + height;
            }
            assert_eq!(cursor, 900, "la columna x={column} no llega al borde inferior");
        }
    }

    /// El mismo contrato con otros solapamientos, comprobado sobre la geometría
    /// (`offsets`) en lugar de materializar mosaicos: con `overlap` 511 un
    /// barrido sobre 1200x900 reservaría cientos de GB de mosaicos.
    #[test]
    fn overlap_holds_for_every_configured_value() {
        let (width, height) = (1200u32, 900u32);
        let tile_size = 512u32;
        for overlap in [1u32, 16, 64, 128, 511] {
            let step = tile_size - overlap;
            for (side, offsets) in [
                (width, offsets(width, tile_size, step)),
                (height, offsets(height, tile_size, step)),
            ] {
                assert_eq!(offsets.first(), Some(&0), "overlap {overlap}: no empieza en 0");
                assert_eq!(
                    offsets.last().expect("siempre hay un offset") + tile_size,
                    side,
                    "overlap {overlap}: el ultimo mosaico no toca el borde de {side}px"
                );
                for window in offsets.windows(2) {
                    let actual = tile_size - (window[1] - window[0]);
                    assert!(
                        actual >= overlap,
                        "overlap {overlap}: solape de {actual}px entre {window:?}"
                    );
                    assert!(window[1] <= window[0] + tile_size, "hueco entre {window:?}");
                }
            }
        }
    }

    /// Una imagen más pequeña que un mosaico produce un único mosaico.
    #[test]
    fn image_smaller_than_a_tile_produces_a_single_tile() {
        let image = synthetic(300, 200);
        let tiles = full_page_tiling(&image, &FullPageTilingOptions::default()).unwrap();
        assert_eq!(tiles.len(), 1);
        assert_eq!((tiles[0].x, tiles[0].y), (0, 0));
        assert_eq!(tiles[0].width, 300);
        assert_eq!(tiles[0].height, 200);
    }

    /// Caso degenerado: `overlap >= tile_size` se rechaza con error en lugar de
    /// producir un bucle infinito (lo verifica también `C1`).
    #[test]
    fn degenerate_overlap_is_rejected() {
        let image = synthetic(1200, 900);
        for overlap in [512, 600, 1024] {
            let result = full_page_tiling(
                &image,
                &FullPageTilingOptions {
                    tile_size: 512,
                    overlap,
                },
            );
            assert!(
                matches!(result, Err(ImageProcessError::OverlapTooLarge { .. })),
                "overlap {overlap} debe rechazarse, llegó {result:?}"
            );
        }
    }

    #[test]
    fn zero_tile_size_is_rejected() {
        let image = synthetic(100, 100);
        let result = full_page_tiling(
            &image,
            &FullPageTilingOptions {
                tile_size: 0,
                overlap: 0,
            },
        );
        assert!(matches!(result, Err(ImageProcessError::ZeroTileSize)));
    }

    /// Cada mosaico contiene los píxeles exactos de la imagen en su offset.
    #[test]
    fn tiles_preserve_the_original_pixels() {
        let image = synthetic(1200, 900);
        let tiles = full_page_tiling(
            &image,
            &FullPageTilingOptions {
                tile_size: 512,
                overlap: 64,
            },
        )
        .unwrap();
        for tile in &tiles {
            assert_eq!(tile.image.get_pixel(0, 0), image.get_pixel(tile.x, tile.y));
            assert_eq!(
                tile.image.get_pixel(tile.width - 1, tile.height - 1),
                image.get_pixel(tile.x + tile.width - 1, tile.y + tile.height - 1)
            );
        }
    }

    #[test]
    fn scale_down_preserves_aspect_ratio() {
        let image = synthetic(4000, 2000);
        let scaled = scale_down(&image, &ScaleDownOptions::default()).unwrap();
        assert_eq!(scaled.width(), DEFAULT_MAX_SIDE);
        assert_eq!(scaled.height(), DEFAULT_MAX_SIDE / 2);
        // Una imagen que ya cabe no se amplía.
        let small = synthetic(800, 600);
        let unchanged = scale_down(&small, &ScaleDownOptions::default()).unwrap();
        assert_eq!(unchanged.dimensions(), small.dimensions());
        // Un `max_side` de cero es un error, no un no-op silencioso.
        let result = scale_down(
            &image,
            &ScaleDownOptions {
                max_side: 0,
                filter: FilterType::Triangle,
            },
        );
        assert!(matches!(result, Err(ImageProcessError::ZeroMaxSide)));
    }

    #[test]
    fn tiling_boxes_matches_full_page_tiling_geometry() {
        let image = synthetic(1200, 900);
        let options = FullPageTilingOptions {
            tile_size: 512,
            overlap: 64,
        };
        let tiles = full_page_tiling(&image, &options).unwrap();
        let boxes = full_page_tiling_boxes(1200, 900, &options).unwrap();
        assert_eq!(tiles.len(), boxes.len());
        for (tile, b) in tiles.iter().zip(boxes.iter()) {
            assert_eq!((tile.x, tile.y, tile.width, tile.height), *b);
        }
    }

    #[test]
    fn high_overlap_calculates_boxes_without_materializing_buffers() {
        let options = FullPageTilingOptions {
            tile_size: 512,
            overlap: 511,
        };
        let boxes = full_page_tiling_boxes(600, 600, &options).unwrap();
        assert_eq!(boxes.len(), 7921);
    }
}
