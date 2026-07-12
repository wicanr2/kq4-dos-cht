#!/usr/bin/env python3
"""烘 KQ4 中文標題副標疊圖 kq4_title.ovl（引擎 drawPicture pic96 時 blit 到 640x400 display）。
渲染「羅塞拉的冒險」金色點陣（配合 King's Quest logo 金色調）→ 量化到 EGA 16 色調色盤 →
輸出 .ovl：u16LE width,height,x,y（display 640x400 座標）+ width*height bytes EGA index(0-15)，
0xFF=透明。純輸出，字型用 Pillow。

用法：build_title_overlay.py <out.ovl> [--text 羅塞拉的冒險] [--font PATH] [--face IDX]
"""
import sys, struct, argparse
from PIL import Image, ImageFont, ImageDraw

# 標準 EGA 16 色（index -> RGB）
EGA = [
 (0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
 (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def nearest_ega(r,g,b):
    best,bi=1<<30,0
    for i,(er,eg,eb) in enumerate(EGA):
        d=(r-er)**2+(g-eg)**2+(b-eb)**2
        if d<best: best,bi=d,i
    return bi

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--text",default="羅塞拉的冒險")
    ap.add_argument("--font",default="/usr/share/fonts/truetype/arphic/uming.ttc")
    ap.add_argument("--face",type=int,default=2)
    ap.add_argument("--size",type=int,default=44)
    ap.add_argument("--disp-w",type=int,default=640)
    ap.add_argument("--disp-h",type=int,default=400)
    ap.add_argument("--y",type=int,default=316)   # 底部（IV 盾下方）
    a=ap.parse_args()

    font=ImageFont.truetype(a.font,a.size,index=a.face)
    # 量測
    tmp=Image.new("RGB",(10,10)); d=ImageDraw.Draw(tmp)
    bbox=d.textbbox((0,0),a.text,font=font)
    tw,th=bbox[2]-bbox[0],bbox[3]-bbox[1]
    pad=4
    W,H=tw+2*pad, th+2*pad
    pad=12
    W,H=tw+2*pad, th+2*pad
    img=Image.new("RGB",(W,H),(0,0,0))
    mask=Image.new("L",(W,H),0)       # 非透明遮罩（含黑暈，讓字在任何背景可讀）
    dd=ImageDraw.Draw(img); dm=ImageDraw.Draw(mask)
    ox,oy=pad-bbox[0],pad-bbox[1]
    # 0) 黑色圓角底板 plaque（整條黑底，金字才在盾的黃色上也乾淨可讀）
    dd.rounded_rectangle([0,0,W-1,H-1],radius=10,fill=(0,0,0))
    dm.rounded_rectangle([0,0,W-1,H-1],radius=10,fill=255)
    # 2) 深棕描邊（logo 陰影感）
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2):
            if dx or dy:
                dd.text((ox+dx,oy+dy),a.text,font=font,fill=(170,85,0))
    # 3) 金黃字身
    dd.text((ox,oy),a.text,font=font,fill=(255,255,85))
    # 上緣白高光（往上偏 2px 疊白，僅字身內）
    hi=Image.new("L",(W,H),0); dh_=ImageDraw.Draw(hi)
    dh_.text((ox,oy-2),a.text,font=font,fill=255)

    x=(a.disp_w-W)//2
    px=img.load(); pm=mask.load(); ph=hi.load()
    data=bytearray()
    for yy in range(H):
        for xx in range(W):
            if pm[xx,yy]==0:
                data.append(0xFF); continue        # 透明
            r,g,b=px[xx,yy]
            if ph[xx,yy]>0 and (r,g,b)==(255,255,85):
                data.append(15)                     # 高光白
            else:
                data.append(nearest_ega(r,g,b))
    with open(a.out,"wb") as f:
        f.write(struct.pack("<HHHH",W,H,x,a.y))
        f.write(bytes(data))
    # 統計非透明色
    used=set(b for b in data if b!=0xFF)
    print(f"標題疊圖 {W}x{H} @({x},{a.y}) → {a.out}（EGA 色 {sorted(used)}，{len(data)} px）")

if __name__=="__main__":
    main()
