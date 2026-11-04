"""Convert original.png into a full-page A0 CMYK print PDF."""

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject
from pypdf.generic import NameObject, NumberObject, TextStringObject
from reportlab import rl_config
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parent
PAGE_WIDTH, PAGE_HEIGHT = 841 * mm, 1189 * mm
PRINT_PPI = 152


def make_poster(profile):
    with Image.open(ROOT / "original.png") as original:
        # Center the whole artwork without stretching or cropping its edges.
        scale = min(PAGE_WIDTH / original.width, PAGE_HEIGHT / original.height)
        width, height = original.width * scale, original.height * scale
        size = (round(width * PRINT_PPI / 72), round(height * PRINT_PPI / 72))
        artwork = original.resize(size, Image.Resampling.LANCZOS)
    artwork = ImageCms.profileToProfile(
        artwork, ImageCms.createProfile("sRGB"), str(profile), outputMode="CMYK",
    )
    image = BytesIO()
    artwork.save(image, format="JPEG", quality=95, optimize=True)

    page = BytesIO()
    canvas = Canvas(page, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pdfVersion=(1, 4), invariant=True)
    canvas.setTitle("Re:Memory Cloud | 2045")
    canvas.setAuthor("E26-SW01-15")
    canvas.drawImage(ImageReader(image), (PAGE_WIDTH - width) / 2, (PAGE_HEIGHT - height) / 2,
                     width, height)
    canvas.save()

    page.seek(0)
    writer = PdfWriter(clone_from=page)
    icc = DecodedStreamObject()
    icc.set_data(profile.read_bytes())
    icc[NameObject("/N")] = NumberObject(4)
    intent = DictionaryObject({
        NameObject("/Type"): NameObject("/OutputIntent"),
        NameObject("/S"): NameObject("/GTS_PDFX"),
        NameObject("/OutputConditionIdentifier"): TextStringObject(
            ImageCms.getProfileDescription(str(profile)).strip()
        ),
        NameObject("/DestOutputProfile"): icc,
    })
    writer.root_object[NameObject("/OutputIntents")] = ArrayObject([intent.clone(writer)])
    writer.write(str(ROOT / "re-memory-cloud-a0.pdf"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=Path(
        "C:/Windows/System32/spool/drivers/color/RSWOP.icm"
    ))
    rl_config.useA85 = 0
    make_poster(parser.parse_args().profile)
