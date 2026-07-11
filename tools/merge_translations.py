#!/usr/bin/env python3
"""把「批次譯文」併入完整 worklist,產出 exact-key 的 translation.tsv。

- skeleton.tsv:抽字產生的完整 worklist(精確英文 key `\t` 英文,未翻)。
- batch/*.tsv:譯者手寫的譯文(英文(可省略尾隨空白)`\t` 中文)。以 strip() 後英文比對,
  比對到就把該 worklist 行的 col2 換成中文,**保留原本精確 key**(含尾隨空白)。
- 輸出 translation.tsv:全 worklist,已翻者 col2=中文,未翻者 col2=英文。

用法:merge_translations.py <skeleton.tsv> <out.tsv> <batch1.tsv> [batch2.tsv ...]
純 stdlib。
"""
import sys

def load_batch(paths):
    m = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or "\t" not in line or line.lstrip().startswith("#"):
                    continue
                en, zh = line.split("\t", 1)
                if zh.strip():
                    m[en.strip()] = zh
    return m

def main():
    skeleton, out = sys.argv[1], sys.argv[2]
    batch = load_batch(sys.argv[3:])
    n_total = n_tr = 0
    with open(skeleton, encoding="utf-8") as f, open(out, "w", encoding="utf-8") as o:
        for line in f:
            line = line.rstrip("\n")
            if not line or "\t" not in line:
                continue
            en, _ = line.split("\t", 1)
            n_total += 1
            zh = batch.get(en.strip())
            if zh:
                o.write(f"{en}\t{zh}\n")
                n_tr += 1
            else:
                o.write(f"{en}\t{en}\n")
    print(f"worklist {n_total} 則,已翻 {n_tr} 則 ({100*n_tr//max(1,n_total)}%) → {out}")
    # 回報 batch 中未命中的(可能 key 有出入)
    used = set()
    with open(skeleton, encoding="utf-8") as f:
        for line in f:
            if "\t" in line:
                used.add(line.split("\t", 1)[0].strip())
    miss = [k for k in batch if k not in used]
    if miss:
        print(f"⚠ batch 有 {len(miss)} 則未在 worklist 命中(前 5):")
        for k in miss[:5]:
            print("   ", repr(k[:60]))

if __name__ == "__main__":
    main()
