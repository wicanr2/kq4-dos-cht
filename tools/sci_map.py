#!/usr/bin/env python3
"""最小 SCI1 / SCI1.1 RESOURCE.MAP 解析器。
格式照 ScummVM engines/sci/resource/resource.cpp readResourceMapSCI1 逐位元組對齊。
用途:列舉 font(type7)/ message(type15)/ text(type3) 資源 id,供中文化引擎 hook 與抽字。
純 stdlib。"""
import sys, struct

# raw type index -> 名稱 (s_resTypeMapSci0)
TYPES = ["view","pic","script","text","sound","memory","vocab","font",
         "cursor","patch","bitmap","palette","cdaudio","audio","sync","message",
         "map","heap","audio36","sync36","translation","rave"]

def parse(map_path):
    data = open(map_path, "rb").read()
    n = len(data)
    # --- 讀 type 目錄:{byte type&0x1F, u16 offset},直到 type==0x1F ---
    dir_entries = []  # (rawtype, woffset)
    p = 0
    while True:
        t = data[p] & 0x1F
        woff = struct.unpack_from("<H", data, p+1)[0]
        dir_entries.append((t, woff))
        p += 3
        if t == 0x1F:
            break
    # 建 type -> (offset, next_offset)。prevtype 邏輯照 ScummVM:size 屬於「前一個 type」
    # 依序:每筆的 woffset 是本 type 起點;前一 type 的 size=(本起點-前起點)/entrysize
    # 先蒐集 (type, woffset) 序列(去掉 0x1F 終結,但保留其 offset 當最後 size 界)
    seq = dir_entries  # 含終結 0x1F(其 woffset = 檔長界)
    # 偵測 entry size:對每個相鄰 pair 的 offset 差,需能被 entrysize 整除
    def fits(esize):
        for i in range(len(seq)-1):
            diff = seq[i+1][1] - seq[i][1]
            if diff < 0 or diff % esize != 0:
                return False
        return True
    esize = None
    for cand in (5, 6):
        if fits(cand):
            esize = cand
            break
    if esize is None:
        # 放寬:取多數整除者
        esize = 5 if sum((seq[i+1][1]-seq[i][1])%5==0 for i in range(len(seq)-1)) >= \
                     sum((seq[i+1][1]-seq[i][1])%6==0 for i in range(len(seq)-1)) else 6
    sci11 = (esize == 5)

    result = {}  # typename -> list of (id, fileoffset, volume)
    for i in range(len(seq)-1):
        rawtype, woff = seq[i]
        if rawtype == 0x1F:
            continue
        nextoff = seq[i+1][1]
        size = (nextoff - woff) // esize
        tname = TYPES[rawtype] if rawtype < len(TYPES) else f"type{rawtype}"
        lst = result.setdefault(tname, [])
        q = woff
        for _ in range(size):
            number = struct.unpack_from("<H", data, q)[0]
            if sci11:
                foff = struct.unpack_from("<H", data, q+2)[0]
                foff |= data[q+4] << 16
                foff <<= 1
                vol = 0
            else:
                val = struct.unpack_from("<I", data, q+2)[0]
                vol = val >> 28
                foff = val & 0x0FFFFFFF
            lst.append((number, foff, vol))
            q += esize
    return esize, sci11, result

if __name__ == "__main__":
    mp = sys.argv[1]
    esize, sci11, res = parse(mp)
    print(f"# map={mp} entry_size={esize} sci_version={'SCI1.1' if sci11 else 'SCI1'}")
    for t in ("font","text","message","view","pic","script"):
        if t in res:
            ids = sorted(x[0] for x in res[t])
            print(f"{t:8s} count={len(ids):4d}  ids={ids}")
    # font/message 詳列 offset
    for t in ("font","message"):
        if t in res:
            print(f"\n## {t} 詳細 (id, RESOURCE.000 offset, vol):")
            for number, foff, vol in sorted(res[t]):
                print(f"  {t} {number:5d}  @0x{foff:07x}  vol{vol}")
