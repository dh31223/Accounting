#!/usr/bin/env python3
"""
生成 Accounting 应用图标 (app.ico)

用法:
    pip install Pillow   # 仅需运行一次
    python installer/generate_icon.py

产物: installer/app.ico (256x256, 48x48, 32x32, 16x16 多尺寸)
"""

import struct
import zlib
from pathlib import Path

INSTALLER_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = INSTALLER_DIR / "app.ico"

# ---- 颜色 ----
BG_COLOR = (129, 140, 248)     # #818cf8 — 应用强调色
TEXT_COLOR = (255, 255, 255)   # 白色

# ---- 32x32 图标像素绘制 ----
# 简约风格: 深色圆角正方形 + 白色 ¥ 符号

def _draw_icon(size: int) -> bytes:
    """绘制 size×size 的 RGBA 像素数据，返回 PNG 字节流。"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = max(2, size // 10)
    r = max(4, size // 5)

    # 圆角矩形背景
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=r,
        fill=BG_COLOR,
    )

    # ¥ 符号居中
    try:
        # 尝试系统自带字体
        font_size = int(size * 0.55)
        for font_name in [
            "segoeui.ttf", "segoeuib.ttf",
            "arial.ttf", "arialbd.ttf",
            "DejaVuSans-Bold.ttf", "DejaVuSans.ttf",
        ]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except (OSError, IOError):
                continue
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "¥", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), "¥", fill=TEXT_COLOR, font=font)

    # 输出 PNG 字节流
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _png_to_ico(png_sizes: dict[int, bytes]) -> bytes:
    """将多个尺寸的 PNG 打包为一个 .ico 文件。"""
    # ICO 头部: 6 bytes
    num_images = len(png_sizes)
    header = struct.pack("<HHH", 0, 1, num_images)

    # 计算图像目录 + 数据偏移
    dir_size = 6 + 16 * num_images  # 头部 + 目录
    entries = b""
    data_blocks = b""

    for size, png_data in png_sizes.items():
        offset = dir_size + len(data_blocks)
        # 目录项: 16 bytes
        # width, height (0 = 256), palette, reserved, planes, bpp, size, offset
        width = size if size < 256 else 0
        height = size if size < 256 else 0
        entry = struct.pack("<BBBBHHII",
            width, height,        # 宽高 (0 表示 256)
            0,                    # 调色板颜色数
            0,                    # 保留
            1,                    # 色彩平面
            32,                   # 位深
            len(png_data),        # 数据大小
            offset,               # 文件内偏移
        )
        entries += entry
        data_blocks += png_data

    return header + entries + data_blocks


def main():
    print("🎨 生成应用图标...")

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ 需要 Pillow 库: pip install Pillow")
        print()
        print("如果你没有 Pillow，也可以手动准备 app.ico 放在 installer/ 目录下")
        return False

    # 生成多个尺寸
    sizes = [256, 64, 48, 32, 16]
    png_map = {}

    for s in sizes:
        png_map[s] = _draw_icon(s)
        print(f"  ✓ {s}x{s} PNG 生成完成")

    # 打包为 .ico
    ico_data = _png_to_ico(png_map)
    OUTPUT_PATH.write_bytes(ico_data)
    print(f"✅ 图标已保存: {OUTPUT_PATH} ({len(ico_data)} bytes)")
    return True


if __name__ == "__main__":
    main()
