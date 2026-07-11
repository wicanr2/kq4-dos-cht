set -e
export HOME=/tmp XDG_RUNTIME_DIR=/tmp DISPLAY=:99
Xvfb :99 -screen 0 640x480x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /out
timeout 60 /app/KQ4-CHT-full-x86_64.AppImage --appimage-extract-and-run 2>/tmp/app.log &
AP=$!
sleep 13
xdotool type --delay 100 "BOBALU"; sleep 1; xdotool key Return
sleep 3; xdotool key Return; sleep 3; xdotool key Return; sleep 2; xdotool key Return; sleep 3
import -window root /out/shots/appimage_verify.png 2>/dev/null || true
kill $AP 2>/dev/null || true
echo "=== app.log MT32 ==="; grep -iE "MT32|kq4sci|falling back" /tmp/app.log | head -3
