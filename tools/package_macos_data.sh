#!/usr/bin/env bash
# 把 macOS CI(.github/workflows/build-macos.yml)產出的「空引擎」ScummVM.app,
# 注入國王密使 IV 繁中資料(dist-cht/ 的 translation.tsv + qfg1_big5.fnt + qfg1_big5_hi.fnt)+ README,
# 重新打包成可交付檔。在 CI runner 內跑(bash 內建即可,不需 docker/python)。
#
# KQ4 只有單一 SCI0 EGA 版本(不像 QFG1/LSL1 要分 vga/ega),故不帶 edition 參數。
#
# 用法:tools/package_macos_data.sh <engine.tar.gz 或 .app 路徑> <輸出目錄>
#
# 交付原則(硬):.app 本身只含 patched 引擎;中文資料放進
# .app/Contents/Resources/cht-data/,原遊戲資源與 MT-32 ROM 絕不塞入。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:?用法: package_macos_data.sh <engine.tar.gz|.app> <輸出目錄>}"
OUT="${2:?需指定輸出目錄}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 接受 .tar.gz 或已展開的 .app 兩種輸入
if [ -d "$SRC" ] && [[ "$SRC" == *.app ]]; then
  cp -R "$SRC" "$WORK/ScummVM.app"
else
  tar xzf "$SRC" -C "$WORK"
fi
APP="$(find "$WORK" -maxdepth 2 -iname '*.app' -type d | head -1)"
[ -n "$APP" ] || { echo "!! 在 $SRC 裡找不到 .app" >&2; exit 1; }

CHT_DIR="$APP/Contents/Resources/cht-data"
echo ">> 注入中文資料 → $CHT_DIR"
rm -rf "$CHT_DIR"; mkdir -p "$CHT_DIR"
[ -f "$ROOT/dist-cht/translation.tsv" ] || { echo "!! 找不到 $ROOT/dist-cht/translation.tsv" >&2; exit 1; }
cp "$ROOT/dist-cht/translation.tsv" "$CHT_DIR/"
cp "$ROOT"/dist-cht/*.fnt "$CHT_DIR/"
[ -f "$ROOT/dist-cht/kq4_title.ovl" ] && cp "$ROOT/dist-cht/kq4_title.ovl" "$CHT_DIR/"   # 中文標題疊圖
echo ">>    staged $(ls "$CHT_DIR" | wc -l) 個中文資料檔 → $CHT_DIR"

README="$APP/Contents/Resources/README-cht.txt"
cat > "$README" <<'EOF'
國王密使 IV：羅賽拉的冒險（King's Quest IV: The Perils of Rosella）繁體中文化 — macOS 版

本包內容
--------
- patched ScummVM 執行檔（含 Big5 繪字、ZH_TWN 語言支援、hi-res 640x400 對白文字的引擎改動）
- cht-data/：中文資料（translation.tsv 對白/訊息、qfg1_big5.fnt 低解析字型、qfg1_big5_hi.fnt hi-res 字型、kq4_title.ovl 中文標題疊圖）
- 本說明檔

本包【不含】原遊戲資源，也不含 Roland MT-32 ROM（版權因素不隨包分發）。
請自備合法取得的國王密使 IV（SCI/DOS 版）遊戲檔。

安裝步驟
--------
1. 準備好你自己的遊戲資料夾（內含 RESOURCE.* 等 SCI 資料）。
2. 把 cht-data/ 資料夾內的所有檔案，複製進上述遊戲資料夾（與 RESOURCE.* 同一層）。
3. 把 ScummVM.app 拖進「應用程式」，第一次執行前先解除 Gatekeeper 隔離（未簽署 app）：
     xattr -dr com.apple.quarantine /Applications/ScummVM.app
4. 開啟 ScummVM.app，在啟動器按「Add Game...」，選剛才那個遊戲資料夾加入。
5. 加入後在 Game Options 把 Language 設為 Chinese (Taiwan)（或啟動時帶 --language=tw），
   即可看到繁體中文。

也可終端機直接啟動：
  ScummVM.app/Contents/MacOS/scummvm --language=tw --path="你的遊戲資料夾路徑" --auto-detect

MT-32 音效
--------
本 build 已啟用 MT-32 模擬（Munt）能力，但因 ROM 有版權不隨包分發，預設仍使用 AdLib。
若你自備合法的 MT32_CONTROL.ROM + MT32_PCM.ROM，放進遊戲資料夾後於音效選項選
Roland MT-32 即可啟用（老 Sierra 遊戲原生支援 MT-32，音色遠勝 AdLib）。

交付原則
--------
中文化僅以 ScummVM patch 形式交付（引擎改動 + 中文資料），原遊戲資源與 ROM 不入包、不散布。
repo：https://github.com/wicanr2/kq4-dos-cht.git
EOF

# 重簽:Resources 內容變動後,原本 build 期的 ad-hoc 簽章需要重蓋(--deep 涵蓋巢狀 dylib)
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP" 2>/dev/null || echo "!! codesign 失敗(非 macOS host 執行屬預期,CI runner 上應成功)"
fi

mkdir -p "$OUT"
LABEL="KQ4-CHT-macos-universal"
tar czf "$OUT/${LABEL}.tar.gz" -C "$(dirname "$APP")" "$(basename "$APP")"
echo ">> -> $OUT/${LABEL}.tar.gz"

if command -v hdiutil >/dev/null 2>&1; then
  hdiutil create -volname "$LABEL" -srcfolder "$APP" -ov -format UDZO "$OUT/${LABEL}.dmg"
  echo ">> -> $OUT/${LABEL}.dmg"
else
  echo ">> (非 macOS host,略過 .dmg——hdiutil 只在 macOS 存在;CI runner 上會產出)"
fi

ls -la "$OUT"
