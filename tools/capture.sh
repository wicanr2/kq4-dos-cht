set -e
export HOME=/tmp XDG_RUNTIME_DIR=/tmp DISPLAY=:99
Xvfb :99 -screen 0 640x480x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /src
PREFIX="${PREFIX:-kq4}"
EXTRA="${EXTRA:-}"
timeout 45 ./scummvm --path=/game --auto-detect $EXTRA 2>/tmp/sv.log &
SV=$!
for t in 04 08 12 16 20 26 32 38; do
  sleep 4
  import -window root /out/shots/${PREFIX}_${t}s.png 2>/dev/null || true
done
kill $SV 2>/dev/null || true
echo "=== stderr tail ==="; tail -20 /tmp/sv.log
