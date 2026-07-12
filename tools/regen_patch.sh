#!/bin/bash
# 從 pinned upstream 抓 pristine，對 scummvm-src 逐檔 diff → 重生 patches/0001-sci-cht-zh_twn.patch
set -e
cd /home/anr2/scummvm/kq4/workplace
COMMIT=$(cat patches/UPSTREAM_COMMIT.txt)
BASE="https://raw.githubusercontent.com/scummvm/scummvm/$COMMIT"
SRC=scummvm-src
PRIS=/tmp/kq4_pristine
FILES=(
  engines/sci/engine/kstring.cpp
  engines/sci/graphics/cache.cpp
  engines/sci/graphics/paint16.cpp
  engines/sci/graphics/paint16.h
  engines/sci/graphics/ports.cpp
  engines/sci/graphics/screen.cpp
  engines/sci/graphics/screen.h
  engines/sci/graphics/text16.cpp
  engines/sci/graphics/view.cpp
  engines/sci/graphics/view.h
  engines/sci/module.mk
  engines/sci/sci.cpp
  engines/sci/sci.h
)
rm -rf "$PRIS"; mkdir -p "$PRIS"
OUT=patches/0001-sci-cht-zh_twn.patch
: > "$OUT"
for f in "${FILES[@]}"; do
  mkdir -p "$PRIS/$(dirname "$f")"
  curl -sfL "$BASE/$f" -o "$PRIS/$f" || { echo "抓 pristine 失敗: $f"; exit 1; }
  # diff -u：label 用 a/ b/ 方便 patch -p1；若無差異 diff 回傳 1，忽略
  diff -u --label "a/$f" --label "b/$f" "$PRIS/$f" "$SRC/$f" >> "$OUT" || true
done
echo "=== 重生完成，驗證可套用到 pristine ==="
cp -r "$PRIS" /tmp/kq4_verify
( cd /tmp/kq4_verify && patch -p1 --dry-run < /home/anr2/scummvm/kq4/workplace/"$OUT" ) && echo "✅ patch -p1 dry-run 通過"
echo "受改檔數: ${#FILES[@]}；patch 行數: $(wc -l < "$OUT")"