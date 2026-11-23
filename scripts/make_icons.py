"""Генерирует иконки приложения (оригинальный рисунок: секундомер).

    python scripts/make_icons.py

Результат: src/activity_tracker/assets/{app.ico, app.png, tray.png}
Хочешь другой стиль, подмени эти три файла или поправь цвета ниже.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "src" / "activity_tracker" / "assets"
SS = 1024  # рисуем крупно и уменьшаем: получается гладкий край

BLUE_TOP, BLUE_BOTTOM = (59, 130, 246), (29, 78, 216)
WHITE = (255, 255, 255, 255)
ACCENT = (253, 224, 71, 255)  # жёлтая секундная стрелка


def gradient(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        color = tuple(round(BLUE_TOP[i] + (BLUE_BOTTOM[i] - BLUE_TOP[i]) * t) for i in range(3)) + (255,)
        for x in range(size):
            px[x, y] = color
    return img


def stopwatch(draw: ImageDraw.ImageDraw, size: int) -> None:
    c = size / 2
    cy = c + size * 0.04
    r = size * 0.30
    ring = size * 0.065

    # кнопка сверху
    draw.rounded_rectangle(
        (c - size * 0.06, cy - r - size * 0.115, c + size * 0.06, cy - r - size * 0.03),
        radius=size * 0.02, fill=WHITE,
    )
    # корпус
    draw.ellipse((c - r, cy - r, c + r, cy + r), outline=WHITE, width=round(ring))
    # деления на 12, 3, 6, 9
    for k in range(4):
        a = math.radians(k * 90)
        x1, y1 = c + math.sin(a) * (r - ring * 1.7), cy - math.cos(a) * (r - ring * 1.7)
        x2, y2 = c + math.sin(a) * (r - ring * 0.9), cy - math.cos(a) * (r - ring * 0.9)
        draw.line((x1, y1, x2, y2), fill=WHITE, width=round(size * 0.035))
    # стрелки
    w = round(size * 0.05)
    draw.line((c, cy, c, cy - r * 0.62), fill=WHITE, width=w)
    draw.line((c, cy, c + r * 0.45, cy + r * 0.25), fill=ACCENT, width=w)
    dot = size * 0.045
    draw.ellipse((c - dot, cy - dot, c + dot, cy + dot), fill=WHITE)


def app_icon() -> Image.Image:
    bg = gradient(SS)
    mask = Image.new("L", (SS, SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SS - 1, SS - 1), radius=int(SS * 0.22), fill=255)
    icon = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    icon.paste(bg, mask=mask)
    stopwatch(ImageDraw.Draw(icon), SS)
    return icon


def tray_icon() -> Image.Image:
    """Круглая версия: читается и на тёмной, и на светлой панели задач."""
    bg = gradient(SS)
    mask = Image.new("L", (SS, SS), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, SS - 1, SS - 1), fill=255)
    icon = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    icon.paste(bg, mask=mask)
    stopwatch(ImageDraw.Draw(icon), SS)
    return icon


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = app_icon()
    app.resize((256, 256), Image.LANCZOS).save(OUT / "app.png")
    app.resize((256, 256), Image.LANCZOS).save(
        OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    tray_icon().resize((64, 64), Image.LANCZOS).save(OUT / "tray.png")
    print("Иконки записаны в", OUT)


if __name__ == "__main__":
    main()
