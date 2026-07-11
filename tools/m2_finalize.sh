#!/bin/bash
# M2 收尾一條龍：逐批 validate → 合併 → 收斂 → 烘字型 → 放 game/
set -e
cd /home/anr2/scummvm/kq4/workplace

echo "===== 1) 逐批 validate（col1/佔位符/Big5）====="
bad=0
for i in $(seq -w 1 16); do
  d=translation/done/batch-$i.done
  [ -f "$d" ] || { echo "缺 $d"; bad=1; continue; }
  python3 tools/validate_batch.py translation/batch/batch-$i.tsv "$d" || bad=1
done
[ $bad -eq 0 ] || { echo "!! 有批次未過驗證，停"; exit 1; }

echo "===== 2) 合併全部（reuse + m1 + cp + 16 批 done）====="
python3 tools/merge_translations.py translation/full_skeleton.tsv translation/translation.tsv \
  /home/anr2/scummvm/qfg2-ega-cht/workplace/translation/translation_utf8.tsv \
  /home/anr2/scummvm/qfg-1/workplace/translation/translation.tsv \
  translation/batch_m1.tsv translation/batch_cp.tsv \
  translation/done/batch-*.done 2>/dev/null | head -1

echo "===== 3) 全域收斂（converge.tsv）====="
if [ -f translation/converge.tsv ]; then
  python3 - <<'PY'
conv=[]
for l in open('translation/converge.tsv',encoding='utf-8'):
    if l.startswith('#') or '\t' not in l: continue
    a,b=l.rstrip('\n').split('\t',1); conv.append((a,b))
rows=[]
for l in open('translation/translation.tsv',encoding='utf-8'):
    if '\t' not in l: rows.append(l.rstrip('\n')); continue
    en,zh=l.rstrip('\n').split('\t',1)
    for a,b in conv: zh=zh.replace(a,b)
    rows.append(en+'\t'+zh)
open('translation/translation.tsv','w',encoding='utf-8').write('\n'.join(rows)+'\n')
print(f"套用 {len(conv)} 條收斂規則")
PY
fi

echo "===== 4) 烘字型 + 放 game/ ====="
python3 tools/build_cht.py translation/translation.tsv dist --face 2 2>&1 | tail -2
python3 tools/bake_hires_font.py dist/qfg1_big5_hi.fnt translation/translation.tsv --face 2 2>&1 | tail -1
cp dist/translation.tsv dist/qfg1_big5.fnt dist/qfg1_big5_hi.fnt game/
echo "===== 完成 ====="
python3 -c "
n=t=0
for l in open('translation/translation.tsv',encoding='utf-8'):
    if '\t' not in l: continue
    en,zh=l.rstrip('\n').split('\t',1); n+=1
    if any('一'<=c<='鿿' for c in zh): t+=1
print(f'覆蓋率：{t}/{n} ({100*t//n}%)')
"
