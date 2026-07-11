set -e
export HOME=/tmp XDG_RUNTIME_DIR=/tmp DISPLAY=:99
Xvfb :99 -screen 0 640x480x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /src
timeout 90 ./scummvm --path=/game --auto-detect --language=tw 2>/tmp/sv.log &
SV=$!
sleep 11
xdotool type --delay 100 "BOBALU"; sleep 1; xdotool key Return   # 過防拷
sleep 2
# 過標題/credits：狂送 Return + Esc 推進 intro，沿路截圖
for t in 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
  import -window root /out/shots/title_${t}.png 2>/dev/null || true
  xdotool key Return 2>/dev/null || true
  sleep 2
done
kill $SV 2>/dev/null || true
