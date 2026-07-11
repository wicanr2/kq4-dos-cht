#!/usr/bin/env bash
# 把 patched ScummVM + 遊戲資料(已合併中文化)+ MT-32 ROM 打包成雙擊即玩的完整 AppImage。
# KQ4 只有一個版本(SCI0 EGA),不像 LSL1/QFG1 要分 ega/vga——用 --auto-detect 免指定 target。
# 完整包（含遊戲資料 + ROM）→ dist-all/,不上 GitHub。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"          # /home/anr2/scummvm/kq4/workplace
REPO_ROOT="$(cd "$ROOT/.." && pwd)"                # /home/anr2/scummvm/kq4
source "$ROOT/tools/pkg_common.sh"                 # stage_mt32_rom

STAGE="$ROOT/build/appimg-full"
DIST="$REPO_ROOT/dist-all"
APPDIR="$STAGE/AppDir"
OUT="$DIST/KQ4-CHT-full-x86_64.AppImage"

mkdir -p "$DIST"
rm -rf "$APPDIR"; mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/game"

echo ">> 複製 scummvm + strip"
cp "$ROOT/scummvm-src/scummvm" "$APPDIR/usr/bin/scummvm"
docker run --rm --name kq4-pkg-strip -v "$APPDIR/usr/bin:/b" qfg1-build:latest strip /b/scummvm 2>/dev/null || true

echo ">> 收集共享庫(qfg1-build 內 ldd,排除 glibc 核心)"
docker run --rm --name kq4-pkg-libs \
  -v "$APPDIR/usr/bin/scummvm:/collect/bin:ro" \
  -v "$APPDIR/usr/lib:/collect/out" \
  -v "$ROOT/tools/pkg_collect_libs.py:/collect/collect.py:ro" \
  -w /collect qfg1-build:latest python3 collect.py bin out
echo "   $(ls "$APPDIR/usr/lib" | wc -l) 個 .so"

echo ">> 放入遊戲資料(已含 translation.tsv + Big5 字型,原樣複製)"
cp -r "$ROOT/game/." "$APPDIR/usr/share/game/"

# MT-32 ROM(完整包才附;有 ROM 才把音效驅動預設成 mt32,否則無 ROM 會彈阻擋框)
MT32ARGS=""
if stage_mt32_rom "$APPDIR/usr/share/game"; then
  MT32ARGS='--music-driver=mt32 --extrapath="$GAME"'
fi

# AppRun:auto-detect 直接啟動內嵌遊戲(usr/share/game 內只有一款遊戲,免指定 target)
cat > "$APPDIR/AppRun" <<APPRUN
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\$0")")"
export LD_LIBRARY_PATH="\$HERE/usr/lib:\${LD_LIBRARY_PATH:-}"
GAME="\$HERE/usr/share/game"
exec "\$HERE/usr/bin/scummvm" --path="\$GAME" --language=tw --auto-detect $MT32ARGS "\$@"
APPRUN
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/kq4-cht.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=國王密使IV 羅賽拉的冒險（繁體中文版）
Comment=King's Quest IV: The Perils of Rosella 繁體中文化 — ScummVM patch
Exec=AppRun
Icon=kq4-cht
Categories=Game;
Terminal=false
DESK
cp "$ROOT/tools/assets/kq4-cht.png" "$APPDIR/kq4-cht.png"
ln -sf kq4-cht.png "$APPDIR/.DirIcon"

rm -f "$OUT"
echo ">> appimagetool 打包(--appimage-extract-and-run 免 FUSE)"
docker run --rm --name kq4-pkg-appimagetool -v "$STAGE:/stage" -v "$ROOT/tools/.cache:/cache:ro" -e ARCH=x86_64 -w /stage \
  qfg1-build:latest bash -c "apt-get update -qq >/dev/null && apt-get install -y -qq file >/dev/null && \
    /cache/appimagetool-x86_64.AppImage --appimage-extract-and-run 'AppDir' '/stage/$(basename "$OUT")'"
mv "$STAGE/$(basename "$OUT")" "$OUT"
chmod +x "$OUT"
echo ">> 完成: $OUT ($(du -h "$OUT" | cut -f1))"
