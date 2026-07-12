#!/usr/bin/env bash
# 把 mingw 交叉編譯出的 scummvm.exe + 遊戲資料(已合併中文化)+ MT-32 ROM 打包成 Windows x86_64 完整包。
# KQ4 只有一個版本(SCI0 EGA),不像 LSL1/QFG1 要分 ega/vga——用 --auto-detect 免指定 target。
# 完整包（含遊戲資料 + ROM）→ dist-all/,不上 GitHub。
# 前置：先跑 mingw build 產出 build/mingw-tree/scummvm.exe（見 BUILD.md 或 CI）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"          # /home/anr2/scummvm/kq4/workplace
REPO_ROOT="$(cd "$ROOT/.." && pwd)"                # /home/anr2/scummvm/kq4
source "$ROOT/tools/pkg_common.sh"                 # stage_mt32_rom

MINGW_IMG="${MINGW_IMG:-kq4-mingw}"
EXE="$ROOT/build/mingw-tree/scummvm.exe"
STAGE="$ROOT/build/win64-full"
DIST="$REPO_ROOT/dist-all"
OUT="$DIST/KQ4-CHT-win64.zip"

[ -f "$EXE" ] || { echo "!! 找不到 $EXE（先跑 mingw build：docker run ... kq4-mingw make）"; exit 1; }

mkdir -p "$DIST"
rm -rf "$STAGE"; mkdir -p "$STAGE/game"

echo ">> 複製 scummvm.exe + strip"
cp "$EXE" "$STAGE/scummvm.exe"
docker run --rm --name kq4-winpkg-strip -v "$STAGE:/s" "$MINGW_IMG" x86_64-w64-mingw32-strip /s/scummvm.exe

echo ">> 收集 mingw runtime DLL（objdump 確認只需 SDL2.dll + libwinpthread-1.dll，其餘皆系統內建）"
docker run --rm --name kq4-winpkg-sdl2dll "$MINGW_IMG" cat /usr/x86_64-w64-mingw32/bin/SDL2.dll > "$STAGE/SDL2.dll"
docker run --rm --name kq4-winpkg-pthreaddll "$MINGW_IMG" cat /usr/x86_64-w64-mingw32/lib/libwinpthread-1.dll > "$STAGE/libwinpthread-1.dll"

echo ">> 放入遊戲資料(已含 translation.tsv + Big5 字型,原樣複製)"
cp -r "$ROOT/game/." "$STAGE/game/"

# MT-32 ROM(完整包才附;有 ROM 才把音效驅動預設成 mt32,否則無 ROM 會彈阻擋框)
MT32ARGS=""
if stage_mt32_rom "$STAGE/game"; then
  MT32ARGS='--music-driver=mt32 --extrapath="%~dp0game"'
fi

# .bat 啟動器：auto-detect 直接啟動內嵌遊戲(game/ 內只有一款遊戲,免指定 target)
cat > "$STAGE/玩-國王密使4-繁中.bat" <<BAT
@echo off
chcp 950 >nul
cd /d "%~dp0"
scummvm.exe --path="%~dp0game" --language=tw --auto-detect $MT32ARGS
BAT

cat > "$STAGE/README.txt" <<'TXT'
國王密使 IV：羅賽拉的冒險（King's Quest IV: The Perils of Rosella）繁體中文化 — Windows x86_64 完整包

雙擊「玩-國王密使4-繁中.bat」即可開始遊戲。

內容物：
  scummvm.exe             patched ScummVM（含 Big5 中文繪字引擎改動 + MT-32 音源模擬）
  SDL2.dll / libwinpthread-1.dll   執行所需 runtime（其餘為 Windows 系統內建 DLL）
  game/                    遊戲資源 + 中文資料（translation.tsv、Big5 字型）+ MT-32 ROM（若隨附）

若要用 Roland MT-32 音源（推薦，音色遠優於 AdLib）：
  已內附 ROM 時 .bat 會自動帶 --music-driver=mt32；若想改用其他驅動，
  手動執行：scummvm.exe --path="game" --language=tw --auto-detect --music-driver=<driver>

repo（patch-only，不含遊戲資源/ROM）：https://github.com/wicanr2/kq4-dos-cht
TXT

OUT_TMP="$OUT"
rm -f "$OUT_TMP"
echo ">> zip 打包"
( cd "$STAGE" && zip -qr "$OUT_TMP" . )
echo ">> 完成: $OUT_TMP ($(du -h "$OUT_TMP" | cut -f1))"
