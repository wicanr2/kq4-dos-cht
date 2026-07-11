#!/usr/bin/env python3
"""驗證翻譯 .done 批次：col1 未改 + 行數一致 + 佔位符數量一致 + Big5 可編。
用法：validate_batch.py <原始 batch-NN.tsv> <譯後 .done> [--font]
回傳非 0 表示有問題。純 stdlib（Big5 檢查用 encode）。
"""
import sys, re

def specs(s):
    # 佔位符 %s %d %c %x %u 等（忽略 %% 轉義）
    return re.findall(r'%[-0-9.]*[sdcxuiXo]', s.replace('%%',''))

def main():
    src, done = sys.argv[1], sys.argv[2]
    S = [l.rstrip('\n').split('\t',1)[0] for l in open(src,encoding='utf-8') if '\t' in l]
    D = [l.rstrip('\n').split('\t') for l in open(done,encoding='utf-8') if '\t' in l]
    errs=[]
    if len(S)!=len(D):
        errs.append(f"行數不符：原 {len(S)} vs 譯 {len(D)}")
    n=min(len(S),len(D))
    nonbig5=set()
    for i in range(n):
        en=S[i]
        row=D[i]
        if len(row)<2:
            errs.append(f"行{i+1}：缺譯文欄"); continue
        k,zh=row[0],row[1]
        if k!=en:
            errs.append(f"行{i+1}：col1 被改 | 原={en[:40]!r} | 得={k[:40]!r}")
        se,sz=specs(en),specs(zh)
        if sorted(se)!=sorted(sz):
            errs.append(f"行{i+1}：佔位符不符 {se} vs {sz} | {en[:40]!r}")
        # Big5 可編檢查
        for ch in zh:
            if ord(ch)<128: continue
            try: ch.encode('big5')
            except: nonbig5.add(ch)
    if nonbig5:
        errs.append(f"非 Big5 字元({len(nonbig5)})：{''.join(sorted(nonbig5))}")
    if errs:
        print(f"✗ {done}：{len(errs)} 問題")
        for e in errs[:25]: print("  ",e)
        sys.exit(1)
    print(f"✓ {done}：{n} 行，col1 一致、佔位符一致、全 Big5 可編")

if __name__=='__main__': main()
