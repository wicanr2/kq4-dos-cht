# 國王密使IV 羅賽拉的冒險 繁中化 — WORKLIST（起於 2026-07-12）

repo：`github.com/wicanr2/kq4-dos-cht`（patch-only）。工作目錄 `~/scummvm/kq4/workplace`。

## 里程碑

| 里程碑 | 狀態 |
|---|---|
| **M0 環境盤點 + 可行性** | ✅ SCI0 EGA、`sci:kq4sci`、139 text/155 script、翻譯量 2121 則、qfg-1/qfg2 patch 可零改複用（2026-07-12） |
| **M1 端到端打通** | ✅ 引擎 patch 零修改複用；防拷框實機顯中文（hi-res 銳利）、kFormat 模板 hook 正常；驗證 **BOBALU 萬用通關碼**可過防拷（2026-07-12） |
| **M2 全文字翻譯** | ✅ 16 批 fan-out sonnet 全譯，worklist **100%(2144/2144)**、覆蓋 99%，逐批 validate+收斂，字型烘 2023 字；**開場敘述實機驗證中文 hi-res 銳利**（亞歷山大/羅塞拉/卡拉漢國王）（2026-07-12） |
| **M3 中文標題疊圖** | ✅ 引擎新增 SCI `.ovl` 疊圖 hook（drawPicture pic96 時 blit 中文副標到 640×400 display buffer）；`build_title_overlay.py` 烘「羅塞拉的冒險」金字黑底板 → `kq4_title.ovl`；實機驗證標題顯中文副標（2026-07-12）。Yes/No 按鈕為 baked-art view 仍英文（次要，另記）。 |
| **M4 交付** | ✅ 全部完成：patch（含 %s + 疊圖 hook）、dist-cht 中文資料、README/手冊/BUILD、**push 到 kq4-dos-cht**、**三平台包**（Linux AppImage / Windows zip / macOS universal dmg+tar.gz，皆含中文標題 + MT-32），macOS CI 首跑成功 |

## 三平台包（dist-all/，gitignore，本機）

| 平台 | 檔案 | 大小 | 驗證 |
|---|---|---|---|
| Linux | `KQ4-CHT-full-x86_64.AppImage` | 15MB | 實跑顯中文敘述 + 標題 + MT-32 |
| Windows | `KQ4-CHT-win64.zip` | 14MB | exe 含疊圖 hook + ovl + DLL + ROM + .bat |
| macOS | `macos/KQ4-CHT-macos-universal.{dmg,tar.gz}` | 34.5MB | GitHub Actions macos-14 CI 首跑成功（自編 SDL2 universal + mt32emu） |

## 次要後補（非核心）

- **Yes/No 等 baked-art 按鈕 view 仍英文**：這些是 view cel 內烘死的英文字，要 sci0_view.py 解碼重繪成 是/否。低優先，另議。
- **防拷逐題真答案**：BOBALU 兜底中；可用手冊 PDF 精確導出（下週）。
- **狀態列分數列**：font.0 限制保留英文。

## M4 交付內容（2026-07-12）

- **引擎 patch**：`tools/regen_patch.sh` 從 pinned upstream 逐檔 diff 重生 `0001-sci-cht-zh_twn.patch`（11 檔，含新增 %s hook），`patch -p1 --dry-run` 驗證可乾淨套用。`apply_patches.sh` 一鍵套用。
- **中文資料**：`dist-cht/`（translation.tsv + qfg1_big5.fnt + qfg1_big5_hi.fnt）。
- **文件**：README（圖文並茂 + 引言 + 手冊要點索引 + 安裝）、`docs/manual-cht.md`（故事轉寫 + 操作 + 守則）、BUILD.md（三平台 + MT-32 config.h 雷）。
- **repo**：`git init` + 本機 commit（47 檔，無遊戲資源/ROM/大檔漏網）。**git push 待使用者確認**（代理邊界）。
- **打包**：Linux AppImage（`dist-all/`，gitignore）。Windows/macOS 待後續。
- **狀態列**：還原乾淨英文（font.0 無法顯 Big5），最終建置實機驗證通過。

## M2 完成內容（2026-07-12）

- 譯名採當年智冠/軟體世界中文說明書權威定名（羅塞拉、卡拉漢、吉妮絲、樂樂蒂、塔米亞…），寫進 `INSTRUCTIONS.md`。
- 1991 未翻則切 16 批 → sonnet subagent 平行 fan-out（童話奇幻・自然口語）。
- 逐批 `validate_batch.py`（col1/佔位符/Big5）→ 攔下 3 問題（2 批非 Big5 `～`、1 批 col1 掉 `\x04`），修復後全過。
- 合併 + `converge.tsv` 收斂（ogress→女食人魔）→ 烘 16px + hi-res 字型。
- **狀態列（分數列）走 font.0 無法顯 Big5 → 保留英文**（QFG1 precedent，避免亂碼）。
- 實機：開場王座廳敘述、防拷框、in-game 敘述全中文 hi-res。

## M0 完成內容（2026-07-12）

1. 解 KQ4 zip 的 **SCI 版**（排除 `AGI/` 子夾）→ `game/`（41 檔）。ScummVM 偵測 = `sci:kq4sci`。
2. `SCI_DUMP_RES` dump 139 text/155 script/413 view/150 pic/4 font → `extract/dump/`。無 message.*。
3. `extract_strings.py` 抽 1932 text、`extract_ega_scripts.py` 抽 189 script 內嵌 → `translation/full_skeleton.tsv`（2121 則）。
4. 複製 qfg2 引擎 patch + 工具鏈 + docker。
5. 多來源（qfg2/qfg-1/larry）預填共通句 → `translation/translation.tsv`，命中 73 則(3%)。

## M2 執行計畫（待 M1 打通後啟動）

1. 建 KQ4 專屬 scummvm-src：clone pinned `3d408ec` → 套 0001 + fontchinese → docker 編譯自家 binary（脫離 qfg-1 依賴）。
2. 批次翻譯 ~2048 未命中 text + script 內嵌，分批 fan-out sonnet subagent（kb `workflows/batch-subagent-localization.md`），台式在地化。KQ4 文風：童話奇幻、羅賽拉第一人稱冒險。
3. kFormat 動態句（`%s/%d` 模板）翻中文模板（子序列對應 + 參數重映射）。
4. 烘完整字型：`build_cht.py`（16px）+ `bake_hires_font.py`（32×28 hi-res）。
5. 覆蓋驗證：混雜態證明渲染路徑；實機截多畫面。

## 防拷（copy protection）

- KQ4 開場有防拷驗證（翻手冊回答問題）。`script.701` 內含 **`BOBALU`** = 萬用通關碼（實機驗證：任何問題輸入 BOBALU 即過）。
- 中文版做法：提示模板已改為「…或直接輸入通關碼 BOBALU 通過」（`translation/batch_m1.tsv`），玩家不需手冊。
- 官方 Answer Key 圖存 `~/scummvm/kq4/copy_protection/`（頁碼/段落/字序→答案詞），如需逐題顯示真答案可據此對應。
- 問題句已中文化（新增 kFormat `%s` 參數翻譯 hook，見下）。**逐題真答案暫掠過**（answer-key 圖判讀有誤、手冊文字檔待確認）——維持 BOBALU 萬用碼，答案下週用手冊 PDF（`king__s_quest_4_-_guide.pdf` 含 Page N 標記的故事正文）精確導出再補。
- **引擎增補**：`kstring.cpp` kFormat case 's' 在模板已翻時對插入的 `%s` 字串也查表翻譯（查無原樣通過）→ 防拷問題句、動態插入道具/地名顯中文。這是 qfg-1/qfg2 patch 沒有的增補，回填 patch 0001 要含。

## 已知雷 / 注意

- KQ4 是 Sierra 首款 SCI 遊戲（1988），SCI0 早期版；hi-res live 文字路徑沿用 qfg-1。
- 選單列字串帶 padding 空格（`   Quit   `），逐字保留精確 key。
- 內容含硬換行 `\r\n` 的句子須空白正規化（`sciChtNormKey`，引擎 patch 已含）。
