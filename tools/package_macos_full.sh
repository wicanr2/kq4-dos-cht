#!/bin/bash
# 把 GitHub Actions CI 建好的 macOS ScummVM.app（engine-only）在本機注入
# 遊戲資源 + 中文資料 + 中文標題疊圖 + MT-32 ROM + 啟動包裝，做成「完整包」。
# 產物含遊戲/ROM → 只放本機 dist-all/（gitignore），不散布公開。
#
# 前提：先從 CI artifact 下載 engine-only tar.gz（gh run download ... --name kq4-cht-macos）。
# 用法：package_macos_full.sh <ci-tar.gz> [game-dir] [mt32-rom-dir]
#
# ⚠ 改動已簽名的 .app 會使簽章失效 → 附「修復-macOS.command」，玩家於 Mac 上先跑一次
#   (xattr 去隔離 + codesign --force --deep --sign - 重簽)，Linux 端無法代簽/實測。
set -e
CI_TAR="${1:?用法: package_macos_full.sh <ci-tar.gz> [game-dir] [rom-dir]}"
GAME_SRC="${2:-/home/anr2/scummvm/kq4/workplace/game}"
ROM_SRC="${3:-/home/anr2/cht/mt32}"
OUT="/home/anr2/scummvm/kq4/dist-all/macos"
WORK="$(mktemp -d)"; APP="$WORK/ScummVM.app"

tar xzf "$CI_TAR" -C "$WORK"
[ -d "$APP" ] || { echo "!! CI tar 內找不到 ScummVM.app" >&2; exit 1; }

# 1) 統一 game 夾：遊戲資源 + cht 對白/字型/ovl（game_src 已含）
GAME="$APP/Contents/Resources/game"; mkdir -p "$GAME"
cp "$GAME_SRC"/RESOURCE.* "$GAME/"
cp "$GAME_SRC"/translation.tsv "$GAME_SRC"/qfg1_big5.fnt "$GAME_SRC"/qfg1_big5_hi.fnt "$GAME_SRC"/kq4_title.ovl "$GAME/"
# 2) MT-32 ROM（正名）
cp "$ROM_SRC"/MT32_CONTROL.1987-10-07.v1.07.ROM "$GAME/MT32_CONTROL.ROM"
cp "$ROM_SRC"/MT32_PCM.ROM "$GAME/MT32_PCM.ROM"
# 3) 啟動包裝：binary 改名 + wrapper 帶 KQ4 中文 + MT-32 參數
mv "$APP/Contents/MacOS/scummvm" "$APP/Contents/MacOS/scummvm.bin"
cat > "$APP/Contents/MacOS/scummvm" <<'WRAP'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"; GAME="$DIR/../Resources/game"
exec "$DIR/scummvm.bin" --path="$GAME" --auto-detect --language=tw --music-driver=mt32 --extrapath="$GAME" "$@"
WRAP
chmod +x "$APP/Contents/MacOS/scummvm" "$APP/Contents/MacOS/scummvm.bin"
# 4) 移除失效簽章（改「未簽」，配 fix 腳本）
rm -rf "$APP/Contents/_CodeSignature"
# 5) 修復腳本 + README
cat > "$WORK/修復-macOS.command" <<'FIX'
#!/bin/bash
cd "$(dirname "$0")"; echo "處理中…"
xattr -cr ScummVM.app 2>/dev/null
codesign --force --deep --sign - ScummVM.app 2>/dev/null && echo "已重簽。" || echo "（codesign 略過）"
echo "完成！雙擊 ScummVM.app 開始《國王密使 IV：羅塞拉的冒險》。"
read -n1 -p "按任意鍵關閉…"
FIX
chmod +x "$WORK/修復-macOS.command"
cat > "$APP/Contents/Resources/README-cht.txt" <<'RM'
國王密使 IV：羅塞拉的冒險 — 繁體中文化（macOS 完整包，開箱即玩）
內含遊戲資源 + 中文對白/字型 + 中文標題 + MT-32 ROM。
【首次使用】雙擊「修復-macOS.command」(去隔離 + ad-hoc 重簽) → 再雙擊 ScummVM.app。
【防拷】開場輸入通關碼 BOBALU 按 Enter 通過。
RM
# 6) 打包
mkdir -p "$OUT"
( cd "$WORK" && tar czf "$OUT/KQ4-CHT-macos-universal-full.tar.gz" "ScummVM.app" "修復-macOS.command" )
echo "完成 → $OUT/KQ4-CHT-macos-universal-full.tar.gz ($(du -h "$OUT/KQ4-CHT-macos-universal-full.tar.gz" | cut -f1))"
rm -rf "$WORK"
