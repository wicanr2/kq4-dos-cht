#!/usr/bin/env python3
"""從 SCI_DUMP_RES dump 出的(未壓縮)message.* / text.* patch 檔抽「精確」可翻譯字串,
產生 translation.tsv 骨架(英文原文 <TAB> 英文原文,待翻)。

- message.*(SCI message V3:headerSize=8, recordSize=10):照 ScummVM MessageReaderV3
  逐 record 取 stringOffset 指向的 null 結尾文字欄位(避免把 record header bytes 黏進 key)。
- text.*(SCI text 資源:單純 null 結尾字串表):直接 null 切。

key = GfxText16 收到的原文,故 runtime 內容替換能精確命中。
dump 檔開頭 2 bytes 為 patch header(type, skip);resource data 從 offset 2 起。

用法:extract_strings.py <dump_dir> <out_tsv>
純 stdlib。
"""
import sys, os, re, struct, glob, argparse

PATCH_HEADER = 2  # dump 檔前 2 bytes:resource type + headerSkip

def is_translatable(s):
    s2 = s.strip()
    if len(s2) < 2:
        return False
    if not re.search(r"[A-Za-z]{2,}", re.sub(r"%[-0-9.]*[a-zA-Z]", "", s2)):
        return False
    return True

def clean(s):
    return s.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

def parse_message_v3(path):
    """回傳該 message 資源所有 record 的文字(依原順序)。"""
    raw = open(path, "rb").read()
    d = raw[PATCH_HEADER:]  # resource data
    if len(d) < 8:
        return []
    version = struct.unpack_from("<I", d, 0)[0] // 1000
    if version != 3:
        # 非 V3 就退回 null 切(保守)
        return null_split(raw)
    header_size, record_size = 8, 10
    count = struct.unpack_from("<H", d, header_size - 2)[0]
    out = []
    for i in range(count):
        rec = header_size + i * record_size
        if rec + record_size > len(d):
            break
        string_off = struct.unpack_from("<H", d, rec + 5)[0]
        if string_off >= len(d):
            continue
        end = d.find(b"\x00", string_off)
        if end < 0:
            end = len(d)
        try:
            s = d[string_off:end].decode("latin1")
        except Exception:
            continue
        out.append(s)
    return out

def null_split(raw):
    out = []
    for chunk in raw.split(b"\x00"):
        try:
            s = chunk.decode("latin1")
        except Exception:
            continue
        printable = sum(1 for c in s if 32 <= ord(c) < 127 or c in "\r\n\t")
        if not s or printable / max(1, len(s)) < 0.95:
            continue
        out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir")
    ap.add_argument("out_tsv")
    a = ap.parse_args()

    seen = set()
    rows = []

    def add(src, s):
        s = clean(s)
        if not is_translatable(s) or s in seen:
            return
        seen.add(s)
        rows.append((src, s))

    for f in sorted(glob.glob(os.path.join(a.dump_dir, "message.*"))):
        for s in parse_message_v3(f):
            add(os.path.basename(f), s)
    for f in sorted(glob.glob(os.path.join(a.dump_dir, "text.*"))):
        for s in null_split(open(f, "rb").read()):
            add(os.path.basename(f), s)

    with open(a.out_tsv, "w", encoding="utf-8") as out:
        for src, key in rows:
            out.write(f"{key}\t{key}\n")

    total = sum(len(k) for _, k in rows)
    print(f"抽出 {len(rows)} 則(精確 key),共 {total} 英文字元 → {a.out_tsv}")

if __name__ == "__main__":
    main()
