"""Small offline safety checks; real-image visual inspection is still required."""
import io
import unittest
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw

from crop_dataset import detect, jpeg_bytes, quality, reading_order


class CropTests(unittest.TestCase):
    def test_partial_border_is_rejected(self):
        im = Image.new('RGB', (1000, 800), 'white')
        draw = ImageDraw.Draw(im)
        draw.ellipse((-100, 200, 170, 500), fill=(70, 140, 50))
        draw.ellipse((500, 200, 740, 500), fill=(70, 140, 50))
        boxes = detect(im, SimpleNamespace(
            min_subject_score=.05, review_subject_score=.06, min_visible_fraction=.70))
        self.assertEqual(len(boxes), 2)
        self.assertIn('estimated_visible_below_threshold', boxes[0][4])
        self.assertNotIn('estimated_visible_below_threshold', boxes[1][4])

    def test_reading_order(self):
        boxes = [(200, 10, 300, 110), (10, 20, 110, 120), (10, 200, 110, 300)]
        self.assertEqual(reading_order(boxes), [boxes[1], boxes[0], boxes[2]])

    def test_jpeg_budget_and_metadata(self):
        rng = np.random.default_rng(10)
        im = Image.fromarray(rng.integers(0, 256, (2000, 2500, 3), dtype=np.uint8))
        im.info['exif'] = b'sensitive-metadata'
        data, size = jpeg_bytes(im)
        self.assertLess(len(data), 2_000_000)
        self.assertEqual(max(size), 1600)
        decoded = Image.open(io.BytesIO(data))
        self.assertEqual(decoded.format, 'JPEG')
        self.assertFalse(decoded.getexif())

    def test_blank_and_small_flagged(self):
        reasons, _ = quality(Image.new('RGB', (100, 100), 'white'), 300, 35)
        self.assertIn('too_small', reasons)
        self.assertIn('possibly_blurred', reasons)
        self.assertIn('extreme_exposure', reasons)


if __name__ == '__main__':
    unittest.main()
