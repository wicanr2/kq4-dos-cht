# 國王密使IV：羅賽拉的冒險 — CONTEXT

King's Quest IV: The Perils of Rosella（SCI 版）EGA ScummVM 繁體中文化。

## 引擎軌 / 關鍵事實（M0 盤點 2026-07-12）

| 項目 | 值 |
|---|---|
| 引擎 | **SCI0**（ScummVM `sci` 引擎），game id `sci:kq4sci` |
| 偵測全名 | King's Quest IV: The Perils of Rosella (SCI/DOS/English) |
| 文字資源 | **只有 `text.*`（139 個），無 `message.*`**（SCI0 特徵，同 qfg-1/qfg2 EGA 軌） |
| 資源規模 | 139 text / 155 script / 413 view / 150 pic / 4 font |
| 翻譯量 | text **1932 則** + script 內嵌 **189 則** = full_skeleton **2121 則**（~124k 英文字元） |
| 共通句複用 | 對 qfg2/qfg-1/larry 譯文預填僅命中 **73 則(3%)**（系統 UI/parser 回應）→ KQ4 劇情獨立，97% 需新譯 |
| 中文啟用 | config `language=tw` 或 CLI `--language=tw`（引擎判 `getLanguage()==ZH_TWN`） |
| 引擎讀取檔名（寫死） | `translation.tsv`、`qfg1_big5.fnt`、`qfg1_big5_hi.fnt`（沿用 qfg-1 檔名，放 game path） |

> 注意：此 zip 同時含 **AGI 版**（`KQ4/AGI/` 子夾，KQ4VOL/KQ4DIR/LOGIC）與 **SCI0 版**（`RESOURCE.*`）。
> CLAUDE.md 定調走 **SCI0 軌**，`game/` 只解 SCI 版資源（不含 AGI 子夾）。

## 範本複用（qfg2-ega-cht = 同軌 SCI0 EGA 最新範本）

`~/scummvm/qfg2-ega-cht/workplace` 與 `~/scummvm/qfg-1/workplace` 是 SCI0 EGA 成熟中文化範本。KQ4 SCI 同為 SCI0：

- **引擎 patch 不綁遊戲 → 直接複用**：`patches/0001-sci-cht-zh_twn.patch` + `fontchinese.{h,cpp}`（pinned upstream `3d408ec`）。含 ZH_TWN 啟用、Big5 繪字、hi-res 640×400 live 文字、kFormat 動態句 hook、GetLongest 日文 kinsoku 誤傷 Big5 修正、空白正規化 key。**預期一行引擎碼都不用改**即讓 KQ4 顯中文。
- **工具鏈全 game-agnostic 複用**：`extract_strings.py`（抽 text.*）、`extract_ega_scripts.py`（抽 script.* 內嵌）、`build_cht.py`（烘 16px Big5 字型 + runtime tsv）、`bake_hires_font.py`（烘 32×28 hi-res 字型）、`sci_view.py`/`sci0_view.py`（view/pic 編解碼，baked-art）、`merge_translations.py`。
- **現成 patched binary**：`~/scummvm/qfg-1/workplace/scummvm-src/scummvm`（含 SCI ZH_TWN + fontchinese，在 `qfg1-build` image 內編）→ M0/M1 dump/驗證直接借用，不必先自編。

## 環境

- docker image `qfg1-build:latest`（SCI-only build）；需再建 `kq4-capture`（+Xvfb/imagemagick/xdotool）做截圖。
- 字型烘焙：host `/usr/share/fonts/truetype/arphic/uming.ttc` face 2 (TW) + Pillow。
- dump 資源：`SCI_DUMP_RES=<dir>` env hook（**dump 完不自退，docker run 一律 `timeout` 包**）。
- 本機缺 `libjpeg.so.62`，binary 必須在 `qfg1-build` docker 內跑。

## 交付原則（硬）

- 中文化**僅放 ScummVM patch**：引擎 patch + `dist/`（translation.tsv + 字型）+ view/pic patch。原遊戲資源不入庫。
- 完整包（含遊戲 + MT-32 ROM）只在本機 `dist-all/`（gitignore）。
- MT-32 一律 enable（configure 不帶 `--disable-mt32emu`）。ROM 不入 GitHub。

## GitHub repo

https://github.com/wicanr2/kq4-dos-cht.git （patch-only）
