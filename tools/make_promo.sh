#!/usr/bin/env bash
set -eu
# ===== 設計 token（KQ4 童話：鎏金 + 深藍紫）=====
BGD='#0b1030'; BGD2='#1a1848'; GOLD='#d8b24a'; GOLDSH='#7a5c14'; BLOOD='#a3231a'; CREAM='#f2ead2'
FB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
FR='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
W=1280; H=720; FPS=25; SHOT=/shots; MUS=/music; OUT=/out; TMP=/tmp/c; mkdir -p "$TMP" "$OUT"

card(){ # $1 out $2 中標 $3 英標 $4 副標
  convert -size ${W}x${H} "radial-gradient:${BGD2}-${BGD}" -font "$FB" -gravity center \
    -fill "$GOLDSH" -pointsize 96 -annotate +4+4 "$3" -fill "$GOLD" -pointsize 96 -annotate +0+0 "$3" \
    -fill "$CREAM" -pointsize 60 -annotate +0+96 "$2" \
    -fill "$BLOOD" -font "$FR" -pointsize 30 -annotate +0+178 "$4" "$1"; }
slide(){ # $1 out $2 screenshot $3 字幕
  convert -size ${W}x${H} "gradient:${BGD2}-${BGD}" "$TMP/bg.png"
  convert "$SHOT/$2" -resize x574 -bordercolor "$GOLD" -border 3 "$TMP/sc.png"
  convert "$TMP/bg.png" \( "$TMP/sc.png" \) -gravity north -geometry +0+22 -composite \
    -fill "#000000aa" -draw "rectangle 0,642 ${W},720" \
    -font "$FR" -fill "$CREAM" -gravity south -pointsize 34 -annotate +0+28 "$3" "$1"; }
compare(){ # $1 out $2 en.png $3 cht.png $4 字幕 —— 左英右中對照
  convert "$SHOT/$2" -resize 512x384 -bordercolor '#888' -border 2 "$TMP/l.png"
  convert "$SHOT/$3" -resize 512x384 -bordercolor "$GOLD" -border 2 "$TMP/r.png"
  # 小標
  convert "$TMP/l.png" -gravity north -background '#00000000' -splice 0x34 -font "$FR" -fill '#cfcfcf' -pointsize 26 -annotate +0+4 '英文原版' "$TMP/l2.png"
  convert "$TMP/r.png" -gravity north -background '#00000000' -splice 0x34 -font "$FR" -fill "$GOLD" -pointsize 26 -annotate +0+4 '繁體中文化' "$TMP/r2.png"
  convert "$TMP/l2.png" "$TMP/r2.png" +append "$TMP/lr.png"
  convert -size ${W}x${H} "gradient:${BGD2}-${BGD}" \( "$TMP/lr.png" \) -gravity center -geometry +0-28 -composite \
    -font "$FR" -fill "$CREAM" -gravity south -pointsize 36 -annotate +0+40 "$4" "$1"; }
kb(){ # $1 png $2 mp4 $3 秒 —— 靜態 + fade（不用 zoompan）
  local FO; FO=$(awk "BEGIN{print $3-0.6}")
  ffmpeg -y -loglevel error -loop 1 -i "$1" -t "$3" -r $FPS \
    -vf "fade=t=in:st=0:d=0.6,fade=t=out:st=$FO:d=0.6,format=yuv420p" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$2"; }

# ===== 分鏡 =====
card    "$TMP/00.png" '國王密使 IV：羅塞拉的冒險' "King's Quest IV" 'Sierra 1988 · SCI0 EGA · 繁體中文化'
slide   "$TMP/01.png" title_cht.png     '經典紅金 logo 下，並存中文標題「羅塞拉的冒險」'
compare "$TMP/02.png" narr_en.png narr_cht.png '開場敘述 —— 全程實機中文，hi-res 銳利'
slide   "$TMP/03.png" narr_cht.png      '亞歷山大歸來、羅塞拉獲救 —— 童話奇幻，自然口語'
slide   "$TMP/04.png" copyprot_cht.png  '開場防拷中文化 · 附萬用通關碼 BOBALU'
slide   "$TMP/05.png" beach.png         '羅塞拉漂流至塔米亞，一日冒險就此展開'
card    "$TMP/99.png" '全文字繁中化 · 2144 則' 'The Perils of Rosella' 'github.com/wicanr2/kq4-dos-cht · 致敬 Roberta Williams'

# ===== concat =====
LIST="$TMP/list.txt"; : > "$LIST"
declare -A SEC=( [00]=5 [01]=6 [02]=8 [03]=6 [04]=6 [05]=6 [99]=7 )
for f in 00 01 02 03 04 05 99; do kb "$TMP/$f.png" "$TMP/s_$f.mp4" "${SEC[$f]}"; echo "file '$TMP/s_$f.mp4'" >> "$LIST"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$TMP/silent.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/silent.mp4"); FO=$(awk "BEGIN{print $DUR-3}")
# ===== 鋪原版 MT-32 配樂（aloop 循環，不用 -shortest）=====
ffmpeg -y -loglevel error -i "$TMP/silent.mp4" -i "$MUS/kq4_bgm.wav" \
  -filter_complex "[1:a]aloop=loop=-1:size=2000000000,atrim=0:$DUR,afade=t=in:st=0:d=2,afade=t=out:st=$FO:d=3[a]" \
  -map 0:v -map "[a]" -threads 2 -c:v libx264 -preset veryfast -c:a aac -b:a 192k -movflags +faststart \
  "$OUT/kq4_cht_promo.mp4"
echo "=== 完成 ==="; ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/kq4_cht_promo.mp4"
ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$OUT/kq4_cht_promo.mp4"
