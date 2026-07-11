#!/usr/bin/env bash
# 共用函式:MT-32 ROM staging(僅完整包 dist-all;[HARD] 絕不入 GitHub release/patch 包)。
# 精簡自 larry_suit_leisure_suit/workplace/tools/pkg_common.sh——KQ4 的 game/ 已合併好中文資料,
# 不需要 stage_cht_data()/gen_readme(),只借用 stage_mt32_rom() 這一段。
#
# 用法:source tools/pkg_common.sh

# 把 Roland MT-32 ROM 改名成 ScummVM Munt 認的檔名放進 $1;有放成功回 0、無回 1(呼叫端據此決定要不要設 music_driver=mt32)。
# 來源 MT32_ROM_SRC 預設本機 /home/anr2/cht/mt32(ROM 有版權,不散布、不入版控)。優先 1987 v1.07 老 MT-32(合 KQ4 年代)。
MT32_ROM_SRC="${MT32_ROM_SRC:-/home/anr2/cht/mt32}"
stage_mt32_rom() {
  local out="$1" ctrl
  ctrl=$(ls "$MT32_ROM_SRC"/MT32_CONTROL.1987*.ROM "$MT32_ROM_SRC"/MT32_CONTROL*.ROM "$MT32_ROM_SRC"/MT32_CONTROL.ROM 2>/dev/null | head -1)
  if [ -z "$ctrl" ] || [ ! -f "$MT32_ROM_SRC/MT32_PCM.ROM" ]; then
    echo ">>    (無 MT-32 ROM @ $MT32_ROM_SRC → 略過,完整包退回預設音效驅動)" >&2
    return 1
  fi
  cp "$ctrl" "$out/MT32_CONTROL.ROM"
  cp "$MT32_ROM_SRC/MT32_PCM.ROM" "$out/MT32_PCM.ROM"
  echo ">>    MT-32 ROM 已放入 $out（完整包專用，$(basename "$ctrl")→MT32_CONTROL.ROM）" >&2
  return 0
}
