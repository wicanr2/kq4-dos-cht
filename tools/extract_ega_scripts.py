#!/usr/bin/env python3
"""從 SCI_DUMP_RES dump 的 EGA `script.*` 抽「玩家可見顯示字串」(選單/死亡訊息/對白/講者名),
濾掉 SCI 內部符號名(egoBase/keyHandler)、CamelCase 類別名(BoxSelector)、bytecode 垃圾。
並對已抽的 `text.*` 字串去重,只輸出新增。

用法:extract_ega_scripts.py <ega_dump_dir> <out_json>  (輸出未跳脫的字串 list)
純 stdlib。含控制碼(` #)的選單列字串另外歸類(需保留控制碼,單獨處理)。
"""
import sys, glob, re, json, os

KNOWN = {'restore', 'restart', 'quit', 'save', 'cancel', 'start', 'continue', 'play',
         'pause', 'done', 'credits', 'arena', 'castle', 'cemetery', 'chase', 'challenge',
         'collect', 'cycle', 'controls', 'information', 'action'}
IDENT = re.compile(r'^[A-Za-z][a-zA-Z0-9]*$')

def text_strings(path):
    d = open(path, 'rb').read()
    body = d[2:] if d and d[0] in (0x83, 0x80) else d
    out = []
    for c in body.split(b'\x00'):
        try:
            s = c.decode('latin1')
        except Exception:
            continue
        pr = sum(1 for ch in s if 32 <= ord(ch) < 127 or ch == '\n')
        if s and pr / max(1, len(s)) >= 0.92 and len(s.strip()) >= 2 and re.search(r'[A-Za-z]{2,}', s):
            out.append(s)
    return out

def is_camel_ident(t):
    return IDENT.match(t) and t.lower() not in KNOWN and re.search(r'[a-z][A-Z]|[A-Z]{2}', t)

def is_display(s):
    t = s.strip()
    if len(t) < 2 or not re.search(r'[a-z]{2,}', t):
        return False
    if is_camel_ident(t):
        return False
    if ' ' in t or re.search(r'[.!?,:;"]', t):
        return True
    if t.lower() in KNOWN:
        return True
    if re.search(r'[a-z]{4,}', t) and not re.match(r'^[a-z][a-zA-Z0-9]*$', t):
        return True
    return False

def script_strings(path):
    d = open(path, 'rb').read()
    body = d[2:] if d and d[0] & 0x80 else d
    out = []
    for c in body.split(b'\x00'):
        try:
            s = c.decode('latin1')
        except Exception:
            continue
        if any(ord(ch) < 32 and ch not in '\n' for ch in s):
            continue  # 含控制碼 → 跳過(選單列另處理)
        pr = sum(1 for ch in s if 32 <= ord(ch) < 127)
        if pr / max(1, len(s)) >= 0.97 and is_display(s):
            out.append(s)
    return out

def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\n', ' ')).strip()

def main():
    dump_dir, out_json = sys.argv[1], sys.argv[2]
    txt = set()
    for f in glob.glob(os.path.join(dump_dir, 'text.*')):
        txt.update(text_strings(f))
    txtn = {norm(s) for s in txt}
    seen = set(); simple = []
    for f in sorted(glob.glob(os.path.join(dump_dir, 'script.*'))):
        for s in script_strings(f):
            if s in seen:
                continue
            seen.add(s)
            if norm(s) not in txtn and '`' not in s and '#' not in s:
                simple.append(s)
    json.dump(simple, open(out_json, 'w'))
    print(f"EGA script 新增顯示字串:{len(simple)} 則,{sum(len(s) for s in simple)} 字元 → {out_json}")

if __name__ == '__main__':
    main()
