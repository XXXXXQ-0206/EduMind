import sys
from pathlib import Path

from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from agents.slides_agent import SlidesAgent, normalize_page_count  # noqa: E402


def test_supported_slide_page_counts_are_five_and_ten():
    assert normalize_page_count(5) == 5
    assert normalize_page_count(10) == 10
    assert normalize_page_count(15) == 10


def test_fallback_illustration_creates_a_valid_image(tmp_path):
    image_path = SlidesAgent._create_fallback_illustration(tmp_path, 5)

    assert image_path.is_file()
    with Image.open(image_path) as image:
        assert image.format == "PNG"
        assert image.size == (1280, 720)
