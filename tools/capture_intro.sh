set -e
export HOME=/tmp XDG_RUNTIME_DIR=/tmp DISPLAY=:99
Xvfb :99 -screen 0 640x480x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /src
timeout 150 ./scummvm --path=/game --auto-detect --language=tw 2>/tmp/sv.log &
SV=$!
sleep 11
xdotool type --delay 100 "BOBALU"; sleep 1; xdotool key Return   # 過防拷
sleep 3
xdotool key Return; sleep 3      # 過標題
xdotool key Return; sleep 3      # 過 credits
# "Is this your first time?" → 選 No（避免教學），點右鈕
xdotool key Return; sleep 2
# 進入 intro 動畫敘述：連續截圖 + Return 推進文字框
for t in $(seq -w 1 24); do
  import -window root /out/shots/intro_${t}.png 2>/dev/null || true
  xdotool key Return 2>/dev/null || true
  sleep 3
done
kill $SV 2>/dev/null || true
