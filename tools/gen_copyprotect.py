#!/usr/bin/env python3
"""產生 KQ4 防拷問題句的中文譯文 + 附真答案（來自官方 Answer Key）。
- PAGE / OVERVIEW / verb-list：附高信心真答案。
- TIPS：僅翻中文，答案靠提示模板的 BOBALU 萬用碼兜底（key 的 tip#/段欄 JPEG 難可靠判讀）。
輸出 batch_cp.tsv（英文原問題 <TAB> 中文問題[（答案：WORD）]）；未在 skeleton 者另補進 skeleton。
"""
import json, re, sys

ORD = {'first':1,'second':2,'third':3,'fourth':4,'fifth':5,'sixth':6,
       'seventh':7,'eighth':8,'ninth':9,'tenth':10}
ORD_ZH = {1:'第一',2:'第二',3:'第三',4:'第四',5:'第五',6:'第六',
          7:'第七',8:'第八',9:'第九',10:'第十','last':'最後一'}

# ── 官方 Answer Key（自 517x800 preview 高倍灰階 crop 精讀）──
# PAGE: (page, paragraph, word) -> WORD ；word 為 int 或 'last'
PAGE = {
 (2,2,8):'LIVED',(2,2,4):'KINGDOM',(2,1,4):'LEGEND',(2,2,6):'DAVENTRY',
 (3,1,4):'BRAVEST',(3,3,4):'VENTURED',(3,3,'last'):'CROWN',(3,1,6):'MOST',
 (3,2,3):'RETURN',(3,1,10):'KNIGHTS',(3,3,8):'DARED',
 (4,1,3):'RULED',(4,2,2):'WOULD',(4,1,6):'LAND',(4,3,'last'):'VELVET',
 (4,1,7):'WITH',(4,3,3):'MIST',(4,3,4):'CLEARED',(4,3,8):'IMAGE',
 (5,2,5):'SUDDENLY',(5,3,8):'VOWED',(5,5,7):'GRAHAM',(5,2,3):'HEART',
 (5,3,2):'MIRROR',(5,1,4):'TEARS',(5,4,8):'VOICE',(5,5,9):'INDEED',
 (6,1,9):'RESCUED',(6,2,4):'WITHIN',(6,2,'last'):'TERROR',(6,2,8):'RUMBLINGS',
 (6,2,6):'FORESTS',(6,1,3):'MARRIED',
 (7,1,10):'WIZARD',(7,3,2):'WOULD',(7,3,9):'FEAR',(7,1,1):'MEANWHILE',
 (7,2,5):'POWERFUL',(7,2,3):'SOLITUDE',
 (8,3,2):'ENTIRE',(8,1,1):'TIME',(8,1,5):'CHANGES',(8,3,6):'RESCUE',(8,3,9):'DOWNFALL',
 (9,1,3):'LEGEND',(9,1,4):'SHORTLY',(9,1,7):'RESCUE',(9,2,7):'NOBLEST',
}
# OVERVIEW: (paragraph, word) -> WORD
OVERVIEW = {(1,2):'SIERRA',(1,6):'GAME',(2,1):'EACH',(2,3):'ANIMATED'}

def gen():
    qs = json.load(open('/tmp/all_q.json'))
    out = []           # (en, zh)
    matched = 0
    for q in qs:
        zh = None; ans = None
        # PAGE: On page N, what is the ORD word (in|of) the ORD paragraph|sentence?
        m = re.match(r"^On page (\d+), what is the (\w+) word (?:in|of) the (\w+) (paragraph|sentence)\??$", q)
        if m:
            pg=int(m.group(1)); w=ORD.get(m.group(2),'last' if m.group(2)=='last' else None)
            para=ORD.get(m.group(3),1)   # 'first sentence' 視為第一段
            wkey = 'last' if m.group(2)=='last' else w
            zh=f"在第 {pg} 頁，{ORD_ZH[para]}段的{ORD_ZH.get(wkey,wkey)}個字是什麼？"
            ans=PAGE.get((pg,para,wkey))
        # OVERVIEW
        elif 'OVERVIEW' in q:
            m2=re.match(r"^What is the (\w+) word of the (\w+) paragraph in the OVERVIEW\?$",q)
            if m2:
                w=ORD.get(m2.group(1)); para=ORD.get(m2.group(2))
                zh=f"OVERVIEW（概覽）中，{ORD_ZH[para]}段的{ORD_ZH[w]}個字是什麼？"
                ans=OVERVIEW.get((para,w))
        # verb list
        elif 'verb list' in q:
            zh='動詞表中，以「b」開頭的最後一個字是什麼？'; ans='BRIDLE'
        # TIPS：翻中文，不硬貼答案（靠 BOBALU）
        elif q.startswith('In the section'):
            mt=re.search(r"tip #(\d+) \(([^)]+)\)", q)
            mw=re.search(r"the (\w+) word", q)
            mp=re.search(r"the (\w+) paragraph", q)
            tip=mt.group(1) if mt else '?'
            wtxt=mw.group(1) if mw else ''
            wz=ORD_ZH.get(ORD.get(wtxt,'last' if wtxt=='last' else wtxt), wtxt)
            seg=f"{ORD_ZH.get(ORD.get(mp.group(1)),'')}段的" if mp else ''
            zh=f"「新手冒險者提示」第 {tip} 則中，{seg}{wz}個字是什麼？"
            ans=None
        if zh is None:
            zh=q  # 保底：未解析就留原文
        # 答案暫掠過（下週補權威答案）：只翻中文問題，靠提示模板的 BOBALU 萬用碼兜底。
        _ = ans
        out.append((q, zh))
    with open('translation/batch_cp.tsv','w',encoding='utf-8') as f:
        for en,zh in out:
            f.write(f"{en}\t{zh}\n")
    # 補未在 skeleton 的問題句進 full_skeleton
    have=set(l.split('\t',1)[0] for l in open('translation/full_skeleton.tsv',encoding='utf-8') if '\t' in l)
    add=[q for q,_ in out if q not in have]
    if add:
        with open('translation/full_skeleton.tsv','a',encoding='utf-8') as f:
            for q in add:
                f.write(f"{q}\t{q}\n")
    print(f"問題 {len(out)} 條，附真答案 {matched} 條，補進 skeleton {len(add)} 條")

if __name__=='__main__':
    gen()
