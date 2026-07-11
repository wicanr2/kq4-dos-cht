#!/usr/bin/env python3
"""
烘 hi-res Big5 點陣字模(32px 寬 × H 列),供 640x400 upscale 時 GfxFontChinese 直接繪製。

格式(與 qfg1_big5.fnt 同族,只是寬 32):
  每字 = big-endian Big5 碼(>H) + H 列 × 4 bytes(32px 寬 1bpp,MSB 在左),最後 0xFFFF 終結。

用法:bake_hires_font.py <out.fnt> <tsv1> [tsv2 ...] [--size N] [--height H] [--width W] [--font PATH] [--face IDX]
  掃所有 tsv 的中文(Big5 雙位元組字),各烘一個 hi-res glyph。
"""
import sys, struct, argparse
from PIL import Image, ImageFont, ImageDraw

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("tsv", nargs="+")
    ap.add_argument("--width", type=int, default=32, help="字寬 px(須為 8 倍數)")
    ap.add_argument("--height", type=int, default=28, help="字高 px(glyph box)")
    ap.add_argument("--size", type=int, default=27, help="字型 pt(留描邊餘裕,略小於 height)")
    ap.add_argument("--font", default="/usr/share/fonts/truetype/arphic/uming.ttc")
    ap.add_argument("--face", type=int, default=2)
    a = ap.parse_args()
    W, H = a.width, a.height
    assert W % 8 == 0

    # 收集所有 tsv 中出現的 Big5 雙位元組字
    chars = set()
    for path in a.tsv:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if "\t" not in line:
                    continue
                zh = line.split("\t", 1)[1]
                for ch in zh:
                    try:
                        b5 = ch.encode("big5")
                    except UnicodeEncodeError:
                        continue
                    if len(b5) == 2:  # 雙位元組 = 中文/全形
                        chars.add(ch)

    font = ImageFont.truetype(a.font, a.size, index=a.face)
    glyphs = []
    for ch in sorted(chars):
        b5 = ch.encode("big5")
        code = (b5[0] << 8) | b5[1]
        img = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(img)
        try:
            bbox = d.textbbox((0, 0), ch, font=font)
        except Exception:
            bbox = (0, 0, W, H)
        gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ox = (W - gw) // 2 - bbox[0]
        oy = (H - gh) // 2 - bbox[1]
        d.text((ox, oy), ch, fill=255, font=font)
        px = img.load()
        rows = bytearray()
        for y in range(H):
            for byte_i in range(W // 8):  # 4 bytes / 列
                bits = 0
                for bit in range(8):
                    x = byte_i * 8 + bit
                    bits = (bits << 1) | (1 if px[x, y] >= 128 else 0)
                rows.append(bits)
        glyphs.append((code, bytes(rows)))

    with open(a.out, "wb") as out:
        for code, bmp in glyphs:
            out.write(struct.pack(">H", code))
            out.write(bmp)
        out.write(struct.pack(">H", 0xFFFF))
    print(f"hi-res 字型 {len(glyphs)} 字 (W={W}, H={H}, size={a.size}) → {a.out}")

if __name__ == "__main__":
    main()
