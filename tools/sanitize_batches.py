#!/usr/bin/env python3
"""對每批 .done 強制 col1=source(防污染)、col2=譯文，並套全域收斂。輸出到 batch/。
用法：sanitize_batches.py"""
import glob,os,sys
conv=[]
if os.path.exists('translation/converge.tsv'):
    for l in open('translation/converge.tsv',encoding='utf-8'):
        if l.startswith('#') or '\t' not in l: continue
        a,b=l.rstrip('\n').split('\t',1); conv.append((a,b))
fixed=0;total=0
for done in sorted(glob.glob('translation/todo/batch-*.done')):
    n=os.path.basename(done)[:-5]  # batch-NN
    src=f'translation/todo/{n}.tsv'
    if not os.path.exists(src): continue
    S=[l.rstrip('\n').split('\t',1)[0] for l in open(src,encoding='utf-8') if '\t' in l]
    D=[l.rstrip('\n').split('\t') for l in open(done,encoding='utf-8') if '\t' in l]
    if len(S)!=len(D):
        print(f"✗ {n}: 行數 {len(S)}!={len(D)}, 跳過"); continue
    out=[]
    for i,en in enumerate(S):
        zh=D[i][1] if len(D[i])>=2 else en
        for a,b in conv: zh=zh.replace(a,b)
        if D[i][0]!=en: fixed+=1
        out.append(en+'\t'+zh)
    open(f'translation/batch/{n}.done','w',encoding='utf-8').write('\n'.join(out)+'\n')
    total+=len(out)
print(f"sanitize {total} 行, 修復 {fixed} 處 col1 污染 → translation/batch/")
