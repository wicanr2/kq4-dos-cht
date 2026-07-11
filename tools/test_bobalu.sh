set -e
export HOME=/tmp XDG_RUNTIME_DIR=/tmp DISPLAY=:99
Xvfb :99 -screen 0 640x480x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /src
timeout 60 ./scummvm --path=/game --auto-detect --language=tw 2>/tmp/sv.log &
SV=$!
sleep 12                      # 等到防拷框
import -window root /out/shots/bob_before.png 2>/dev/null || true
xdotool type --delay 120 "${ANS:-BOBALU}"
sleep 1
import -window root /out/shots/bob_typed.png 2>/dev/null || true
xdotool key Return
sleep 4
import -window root /out/shots/bob_after1.png 2>/dev/null || true
sleep 5
import -window root /out/shots/bob_after2.png 2>/dev/null || true
kill $SV 2>/dev/null || true
