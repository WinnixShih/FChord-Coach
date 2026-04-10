# Design System — FChord Coach

## Product Context
- **What this is:** 吉他 F 和弦即時矯正教學 App，鏡頭分析手部姿勢，給出 AI 文字建議
- **Who it's for:** 初學者到中級吉他學習者（Android）
- **Space/industry:** 樂器學習 App（競品：Yousician、Fender Play、Simply Guitar）
- **Project type:** Android camera-native mobile app

## Aesthetic Direction
- **Direction:** Clinical Calm（臨床冷靜感）
- **Decoration level:** minimal — typography 和留白做主要工作
- **Mood:** 不是遊戲，不是玩具。像精準的矯正工具，讓使用者專注在姿勢上，而非被遊戲化 UI 分心。物理治療室的質感，不是街機。
- **Competitive insight:** 競品（Yousician、GuitarTuna、Fender Play）全部使用深色遊戲化設計。FChord Coach 是相機原生產品——使用者的手才是主角——應與競品的視覺語言刻意區隔。

## Typography
- **UI + 標題:** Plus Jakarta Sans — 現代、略圓潤但不幼稚，在 Android 上可讀性佳
- **信心指數數字:** Geist Mono（tabular-nums）— 讓數字讀起來像儀器讀數，不是遊戲分數
- **Loading:** Google Fonts CDN（Flutter 用 `google_fonts` package）
- **Scale:**
  - Display: 32sp / 700
  - Heading: 20sp / 600
  - Body: 14sp / 400
  - Caption / Label: 11sp / 400
  - Mono data: 16sp / 500

## Color
- **Approach:** restrained — 一個 accent + 中性色，顏色出現時有意義
- **Background:** `#F7F5F1` — 暖奶油白，不是冷白；練習時不刺眼，且競品中無人使用
- **Surface（卡片）:** `#FFFFFF`
- **Primary text:** `#1C1C1E`
- **Muted text:** `#6C6C70`
- **Accent / Correct:** `#2D6A4F`（深森林綠）— 成熟、琴弦感、鎮定；競品用螢光綠/電光紅/橘
- **Accent light（背景色）:** `#52B788` / `rgba(45,106,79,0.12)`
- **Warning / Error:** `#E07A2F`（琥珀橙）
- **Warning light（背景色）:** `rgba(224,122,47,0.12)`
- **Skeleton overlay:** `#52B788`（亮綠）搭配錯誤關節用 `#E07A2F` 高亮圈
- **Dark mode:** 降低飽和度 10–15%；`--bg: #0F0F0F`、`--surface: #1C1C1E`

## Spacing
- **Base unit:** 4dp
- **Density:** comfortable
- **Scale:** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64

## Layout
- **Approach:** grid-disciplined（規則對齊）
- **CameraPage（核心差異化）:**
  - 相機畫面佔 ~65% 螢幕高度
  - 底部 Bottom Sheet（半透明、backdrop blur）顯示即時偵測結果，不跳頁
  - 手永遠留在畫面裡，保持相機沈浸感
- **Border radius:** sm=8dp, md=14dp, lg=20dp, pill=100dp

## Motion
- **Approach:** minimal-functional — 只有幫助理解的動畫
- **Easing:** enter=easeOut, exit=easeIn, move=easeInOut
- **Duration:** micro=80ms, short=200ms, medium=300ms
- **Bottom Sheet:** slide-up 200ms easeOut；不做彈跳

## Hand Skeleton Overlay（BL-004 實作規範）
- 線條粗細：`strokeWidth = 1.5dp`
- 正常節點顏色：`#52B788`（Accent Light）
- 正常連線顏色：`#52B788`，`opacity = 0.85`
- 錯誤關節：額外畫一個 `#E07A2F` 圓圈（`radius = 5dp`，`strokeWidth = 1.5dp`）
- 掌心橫向連線：`stroke-dasharray`（虛線），`opacity = 0.5`
- 骨架不搶戲——使用者的手才是主角

## BL-009 實作範圍（Flutter）
BL-009 的 Flutter 實作包含以下工作，在 BL-003 / BL-004 開發期間同步進行：

| 工作項目 | 說明 |
|----------|------|
| `google_fonts` 依賴 | 加入 pubspec.yaml，設定 Plus Jakarta Sans + Geist Mono |
| `AppTheme` | 建立 `lib/shared/theme/app_theme.dart`，定義 ColorScheme、TextTheme |
| `AppColors` | 建立 `lib/shared/theme/app_colors.dart`，定義所有 token |
| `AppSpacing` | 建立 `lib/shared/theme/app_spacing.dart`，定義 spacing scale |
| CameraPage 底色 | 相機外框/狀態欄配合 dark overlay |
| Bottom Sheet 樣式 | 半透明 + backdrop blur，圓角 20dp |
| FeedbackPage 重構 | 套用 result card 樣式、chip 元件、conf bar |
| Chip widget | `CorrectChip` / `ErrorChip` 共用元件 |
| ConfidenceBar widget | accent/warn 雙色版本 |

## Decisions Log
| 日期 | 決策 | 理由 |
|------|------|------|
| 2026-04-10 | 美學方向：Clinical Calm | 與競品深色遊戲化設計刻意區隔；相機原生產品手才是主角 |
| 2026-04-10 | Accent：深森林綠 #2D6A4F | 成熟、鎮定、琴弦感；競品無人使用此色 |
| 2026-04-10 | 底色：暖奶油白 #F7F5F1 | 比冷白有質感，練習時不刺眼；競品無人使用 |
| 2026-04-10 | Bottom Sheet 回饋 | 相機永遠可見，不中斷使用者的姿勢調整流程 |
| 2026-04-10 | Geist Mono 數字 | 信心指數像儀器讀數，不是遊戲分數 |
| 2026-04-10 | 細線骨架 overlay | 手是主角；overlay 點到即止，不搶戲 |
