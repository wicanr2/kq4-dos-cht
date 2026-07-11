#!/bin/bash
# 套用 KQ4 繁中化引擎改動到乾淨 ScummVM 原始碼樹。
# 用法：tools/apply_patches.sh <scummvm-src-dir>
set -e
SRC="${1:?用法: apply_patches.sh <scummvm-src-dir>}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
echo ">> 目標樹：$SRC"
echo ">> pinned upstream：$(cat "$HERE/patches/UPSTREAM_COMMIT.txt")"
# 1) 複製新檔（GfxFontChinese：Big5 繪字 + hi-res loader）
cp "$HERE/patches/fontchinese.cpp" "$SRC/engines/sci/graphics/fontchinese.cpp"
cp "$HERE/patches/fontchinese.h"   "$SRC/engines/sci/graphics/fontchinese.h"
# 2) 套用既有檔改動（ZH_TWN 啟用、Big5 繪字、hi-res 640x400、kFormat 模板 + %s 參數 hook、
#    GetLongest Big5 斷行、空白正規化 key、SCI_DUMP_RES）
patch -p1 -d "$SRC" < "$HERE/patches/0001-sci-cht-zh_twn.patch"
echo ">> 完成。configure（docker 內，MT-32 啟用）："
echo "   ./configure --disable-all-engines --enable-engine=sci --disable-detection-full && make -j\$(nproc)"
echo ">> 注意：啟用 mt32emu 首編若報 MT32EMU_VERSION_* 未宣告，"
echo "   從 pinned commit 補回 audio/softsynth/mt32/config.h（raw.githubusercontent.com）。"
