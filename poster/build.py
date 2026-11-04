"""Build the A0 CMYK poster and the GitHub preview from the team artwork."""

import argparse
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageCms
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject
from pypdf.generic import NameObject, NumberObject, TextStringObject
from reportlab.lib.colors import CMYKColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 841, 1189
NAVY = CMYKColor(0.96, 0.75, 0.35, 0.36)
BLUE = CMYKColor(0.93, 0.51, 0, 0.09)
MUTED = CMYKColor(0.69, 0.51, 0.31, 0.21)
PALE = CMYKColor(0.07, 0.025, 0, 0)
LINE = CMYKColor(0.15, 0.06, 0, 0.02)
WHITE = CMYKColor(0, 0, 0, 0)


def make_poster(font_dir, profile):
    pdfmetrics.registerFont(TTFont("Body", str(font_dir / "malgun.ttf")))
    pdfmetrics.registerFont(TTFont("Bold", str(font_dir / "malgunbd.ttf")))
    page = BytesIO()
    canvas = Canvas(
        page, pagesize=(WIDTH * mm, HEIGHT * mm), pdfVersion=(1, 4),
        initialFontName="Body", invariant=True,
    )
    canvas.setTitle("Re:Memory Cloud | 2045")
    canvas.setAuthor("E26-SW01-15")
    canvas.setCreator("Re:Memory poster source")

    def rect(x, top, width, height, color):
        canvas.setFillColor(color)
        canvas.rect(x * mm, (HEIGHT - top - height) * mm, width * mm, height * mm,
                    fill=1, stroke=0)

    def label(x, baseline, value, size, color=NAVY, bold=False, limit=None):
        font = "Bold" if bold else "Body"
        available = WIDTH - 42 - x if limit is None else limit
        if pdfmetrics.stringWidth(value, font, size) > available * mm:
            raise ValueError(f"Text exceeds its column: {value}")
        canvas.setFillColor(color)
        canvas.setFont(font, size)
        canvas.drawString(x * mm, (HEIGHT - baseline) * mm, value)

    def lines(x, baseline, values, limit, size=32, leading=16, color=NAVY):
        for index, value in enumerate(values):
            label(x, baseline + index * leading, value, size, color, limit=limit)

    # Header and the focal scene, cropped from the team's supplied poster.
    rect(42, 38, 12, 4, BLUE)
    label(62, 44, "2045 미래 서비스  /  국민대학교 유레카 프로젝트", 34, BLUE, True)
    label(42, 108, "Re:Memory Cloud", 166, NAVY, True)
    label(44, 153, "기억을 잃어도, 삶은 잃지 않도록", 77, NAVY, True)
    label(44, 185, "초기 알츠하이머를 겪는 시니어를 위한 클라우드 회상 보조", 41, MUTED)
    label(44, 207, "Re:Memory 팀  ·  정현구  /  고지민  /  세짐", 30, BLUE, True)

    hero_width, hero_height = 757, 325
    pixels = tuple(round(value * 152 / 25.4) for value in (hero_width, hero_height))
    with Image.open(ROOT / "original.png") as original:
        scene = original.crop((0, 191, 866, 562)).resize(pixels, Image.Resampling.LANCZOS)
    scene = ImageCms.profileToProfile(
        scene, ImageCms.createProfile("sRGB"), str(profile), outputMode="CMYK",
    )
    jpeg = BytesIO()
    scene.save(jpeg, format="JPEG", quality=92)
    canvas.drawImage(ImageReader(jpeg), 42 * mm, (HEIGHT - 226 - hero_height) * mm,
                     hero_width * mm, hero_height * mm)

    rect(42, 551, 757, 96, NAVY)
    label(59, 578, "2045년의 어느 오후  /  할아버지의 거실", 32, WHITE, True)
    label(59, 613, "“우리 지우 왔구나. 공원에서 아이스크림 먹었지?”", 55, WHITE, True)
    label(59, 635, "이름이 떠오르지 않던 순간, 함께 보낸 날의 단서가 돌아옵니다.", 31, WHITE)

    label(42, 678, "01  우리가 풀고 싶은 문제", 42, BLUE, True)
    lines(42, 703, [
        "초기 알츠하이머를 겪는 할아버지에게",
        "사진을 찾아도 그날의 맥락이 떠오르지",
        "않을 수 있습니다.",
    ], 365)
    label(435, 701, "지금  /  사진첩에서 단서를 직접 찾는다", 33, MUTED, True)
    label(435, 725, "2045  /  동의한 기록에서 회상 단서를 찾는다", 33, NAVY, True)
    label(435, 750, "가족과 추억을 이야기할 기회를 되찾습니다.", 32)

    rect(42, 769, 757, 0.7, LINE)
    label(42, 799, "02  기억을 다시 잇는 세 단계", 42, BLUE, True)
    for x, name, detail in (
        (42, "1  기록", ["동의한 순간의 시각·감정", "신호를 신경 칩으로 읽습니다."]),
        (299, "2  저장·검색", ["기록은 암호화해 저장하고", "AI가 사람·시간별로 분류합니다."]),
        (556, "3  회상 보조", ["사용자가 요청하면 관련 단서를", "찾아 신경 인터페이스로 전달합니다."]),
    ):
        rect(x, 815, 243, 92, PALE)
        label(x + 12, 842, name, 41, NAVY, True, 219)
        lines(x + 12, 869, detail, 219, size=29, leading=17)

    label(42, 945, "03  연구에서 서비스까지", 42, BLUE, True)
    label(435, 945, "04  기억을 맡길 수 있으려면", 42, BLUE, True)
    lines(42, 973, [
        "현재 | 해마 자극을 통한 기억 과제 연구,",
        "fMRI 신호를 이용한 시각 자극 재구성",
        "과제 | 장기 이식 안전성, 개인별 신호 해석,",
        "실제 회상에 도움이 되는 단서의 전달",
    ], 370, size=30, leading=17)
    lines(435, 973, [
        "왜곡 | 확신이 낮으면 단서를 보내지 않기",
        "유출 | 암호화와 접근 기록으로 열람 통제",
        "잊을 권리 | 기록 거부와 개별 삭제 보장",
        "접근성 | 이식 없이 쓸 수 있는 보조 수단",
    ], 365, size=30, leading=17)

    rect(42, 1046, 757, 58, PALE)
    label(56, 1071, "미래의 우리  /  기억을 다루는 SW·AI 개발자", 35, NAVY, True)
    label(56, 1092, "정확도와 함께, 어떤 기억을 남기고 지울지 스스로 결정할 수 있게 설계합니다.", 31)
    label(42, 1129, "연구  /  Hampson 외 (2018), J Neural Eng  ·  Takagi & Nishimoto (2023), CVPR", 25, MUTED)
    label(42, 1147, "AI 활용  /  팀 포스터의 2045년 가족·신경 칩·기억 장면 이미지 및 포스터 문안 편집", 25, MUTED)
    canvas.save()
    return page


def write_outputs(page, profile):
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
    pdf_path = ROOT / "re-memory-cloud-a0.pdf"
    writer.write(str(pdf_path))

    with fitz.open(pdf_path) as doc:
        zoom = 1800 / doc[0].rect.width
        preview = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        Image.frombytes("RGB", (preview.width, preview.height), preview.samples).save(
            ROOT.parent / "poster.jpg", quality=94, optimize=True
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, default=Path("C:/Windows/Fonts"))
    parser.add_argument("--profile", type=Path, default=Path(
        "C:/Windows/System32/spool/drivers/color/RSWOP.icm"
    ))
    args = parser.parse_args()
    write_outputs(make_poster(args.font_dir, args.profile), args.profile)
