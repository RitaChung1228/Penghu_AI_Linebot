# 澎湖旅遊 AI LINE Bot

澎湖在地旅遊助手，提供行程規劃、智慧查詢、航班查詢等旅遊服務。

---

## 系統功能

主選單提供五個功能入口：

| 功能 | 說明 |
|------|------|
| 熱門行程 | 四種行程類型輪播卡片，點入可瀏覽詳細行程並收藏 |
| 收藏清單 | 顯示個人收藏的行程，支援查看詳情與刪除 |
| 智慧查詢 | 輸入需求，AI 結合 RAG 生成客製化澎湖行程建議 |
| 空房查詢 | 查詢澎湖飯店空房資訊 |
| 交通查詢 | 查詢往返澎湖的航班時刻與島內交通資訊 |

---

## 技術架構

### 系統架構圖

```
LINE User
    │
    ▼
LINE Platform
    │  Webhook (HTTPS POST / Postback)
    ▼
┌─────────────────────────────────────────┐
│  app.py  ─  Flask Webhook 入口          │
│  user_states{}  ─  對話狀態機           │
└────────────────┬────────────────────────┘
                 │ 依 step / postback 分派
        ┌────────┴────────┐
        ▼                 ▼
  handlers/           flex/
  對話流程控制器       LINE Flex Message 模板
        │
        ▼
  services/
  資料服務層
  ┌─────────────────────────────┐
  │ airline_service  → 華信航空  │
  │ weather_service  → 氣象署API │
  │ tide_service     → 澎管處   │
  │ rag_service      → RAG引擎  │
  └─────────────────────────────┘
        │
        ▼
  rag/faiss_db/        data/
  FAISS 向量資料庫      靜態 JSON 資料
```

### 熱門行程 × 收藏流程

```
熱門行程
    │
    ▼
四種行程類型卡片（自然 / 人文 / 美食 / 海上）
    │  點選類型
    ▼
行程詳細 carousel（每張含圖片、天數、景點）
    │  點「⭐ 收藏行程」（postback）
    ▼
寫入 storage/favorites/{user_id}.json

收藏清單
    │
    ▼
單一 bubble 列出所有收藏（每筆一行，旁邊有「詳情」「刪除」按鈕）
    │  點「詳情」（postback）       點「刪除」（postback）
    ▼                               ▼
行程詳細卡片（含「取消收藏」按鈕）   從清單移除
```

### 智慧查詢 RAG 流程

```
使用者輸入需求
    │
    ▼
user_demand_analysis()       ← Mistral 分析需求
    │
    ▼
chat_with_schedule_rag()     ← FAISS 語意檢索 + Mistral 生成在地活動建議
    │  (EmbeddingGemma-300m 向量化，k=8 最相關文件)
    ▼
travel_planner()             ← Mistral 整合需求與RAG結果，生成行程
    │
    ▼
critical_reviewer()          ← Mistral 審查行程合理性
    │
    ▼
travel_replanner()           ← Mistral 依審查意見修正
    │
    ▼
push_message() → 回傳給使用者
```

> 因流程耗時約 30 秒，採用 `reply()` 先回「規劃中」，背景 thread 完成後再 `push()` 推送結果。

---

## 資料夾結構

```
Penghu_linebot/
│
├── app.py                      # Flask 主程式，LINE Webhook 入口，對話狀態機
├── .env                        # 環境變數（API Keys，不進版控）
├── requirements.txt            # Python 套件清單
│
├── handlers/                   # 對話流程控制器
│   ├── popular_trip.py         # 熱門行程：類型選單 → 行程詳細卡片
│   ├── favorites.py            # 收藏清單：顯示 / 刪除 / 詳情（postback）
│   ├── smart_query.py          # 智慧查詢流程（呼叫 rag_service）
│   ├── transport_query.py      # 交通查詢流程（航班 + 島內交通）
│   └── room_query.py           # 空房查詢流程（待開發）
│
├── services/                   # 資料服務層（純函式，只負責取資料）
│   ├── airline_service.py      # 華信航空航班爬蟲（Selenium）
│   ├── tide_service.py         # 澎管處潮汐爬蟲
│   ├── weather_service.py      # 中央氣象署天氣 API
│   └── rag_service.py          # RAG 智慧查詢核心（FAISS + Mistral pipeline）
│
├── rag/                        # RAG 相關資料
│   ├── faiss_db/               # FAISS 向量資料庫（已包含於版控）
│   │   ├── index.faiss         # 向量索引
│   │   └── index.pkl           # 文件對照表
│   ├── source_docs/            # 建立向量庫的原始文件
│   │   └── Panghu_schedule_database.md   # 澎湖行程活動資料庫
│   └── build_faiss.py          # 向量資料庫重建腳本
│
├── flex/                       # LINE Flex Message 模板
│   ├── trip_card.py            # 熱門行程類型輪播卡片
│   ├── trip_detail.py          # 行程詳細卡片（含收藏 / 取消收藏按鈕）
│   ├── transport_menu.py       # 交通查詢選單（島內 + 入島）
│   ├── main_menu.py            # 五按鈕主選單（待開發）
│   └── hotel_card.py           # 飯店資訊卡片（待開發）
│
├── data/                       # 靜態 JSON 資料檔
│   ├── popular_trips.json      # 熱門行程資料（4 類型 × 3 筆）
│   └── hotels.json             # 飯店基本資訊（待填入）
│
├── storage/                    # 使用者持久化資料（不進版控）
│   └── favorites/              # 每位使用者的收藏清單
│       └── {user_id}.json      # 以 LINE user_id 命名
│
└── crawlers/                   # 爬蟲腳本（手動執行以更新 data/）
    └── scenery_crawler.py      # 澎湖景點爬蟲（待開發）
```

---

## 技術選型

| 類別 | 技術 |
|------|------|
| Web 框架 | Flask |
| LINE Bot SDK | line-bot-sdk v3 (Python) |
| 語言模型 | Mistral (`ministral-8b-latest`) via aisuite |
| Embedding 模型 | `google/embeddinggemma-300m`（HuggingFace，需申請存取權） |
| 向量資料庫 | FAISS (Facebook AI Similarity Search) |
| RAG 框架 | LangChain Community |
| 天氣資料 | 中央氣象署開放資料平台 API |
| 航班資料 | 華信航空官網爬蟲（Selenium + headless Chrome） |
| 潮汐資料 | 澎管處潮汐頁面爬蟲（requests + BeautifulSoup） |
| 本機測試 | ngrok（HTTPS tunnel） |

---

## 環境設定

`.env` 需設定以下變數：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
MISTRAL_API_KEY=your_mistral_key
HUGGINGFACE_HUB_TOKEN=your_hf_token
OPENDATA_CWA_API_KEY=your_cwa_key
```

---

## 本機啟動

```bash
# 安裝套件
pip install -r requirements.txt

# 啟動 Flask
python app.py

# 另開終端，啟動 ngrok
./ngrok http 5000
```

將 ngrok 產生的 HTTPS URL 填入 LINE Developers Console 的 Webhook URL：
```
https://xxxx.ngrok-free.app/callback
```

---

## 向量資料庫更新

`rag/faiss_db/` 已包含在版控中，一般情況下不需要重建。

**僅在 `rag/source_docs/Panghu_schedule_database.md` 有更新時**，才需要重新執行：

### 前置條件

1. 登入 HuggingFace 並取得 `google/embeddinggemma-300m` 存取權限
   - 申請：`https://huggingface.co/google/embeddinggemma-300m`
2. 登入 HuggingFace CLI
   ```bash
   python -c "from huggingface_hub import login; login(token='你的token')"
   ```

### 重建向量庫

```bash
python rag/build_faiss.py
```

執行時間約 10–20 分鐘（含模型下載），完成後將 `rag/faiss_db/` 重新 commit 進版控。

---

## 各模組分工說明

### app.py — 對話狀態機 + Postback 路由

- `user_states` dict 儲存每位使用者目前的對話步驟
- `MessageEvent` → `handle_message()` 依序呼叫各 handler
- `PostbackEvent` → `favorites_handler.handle_postback()` 處理收藏/刪除/詳情

### handlers/ — 流程控制

負責「問什麼問題、等什麼輸入、何時呼叫 service / flex」，不處理資料取得邏輯。

### favorites.py — 收藏清單

- 收藏清單以單一 bubble 呈現，每筆行程一行，旁邊有「詳情」「刪除」兩個按鈕
- 點「詳情」→ 顯示行程卡片，footer 改為「取消收藏」（紅色）
- 收藏資料儲存於 `storage/favorites/{user_id}.json`

### services/ — 資料服務

純函式，輸入參數回傳結果。handler 呼叫 service，service 不知道對話存在。

### rag_service.py — RAG 核心

- **模組載入時**初始化 EmbeddingGemma + FAISS（只載入一次，避免重複耗時 2 分鐘）
- 提供 `rag_smart_reply(user_text: str) -> str` 單一入口
- 內部執行 4 步驟 pipeline（需求分析 → RAG檢索 → 行程規劃 → 審查修正）

### airline_service.py — 航班爬蟲

- 使用 Selenium headless Chrome 操作華信航空官網
- 對外提供 `search_flights(dep_code, arr_code, date_str)` 與 `format_result()` 兩個函式

---

## 待開發項目

- [x] `services/rag_service.py` — RAG 智慧查詢核心
- [x] `handlers/smart_query.py` — 智慧查詢對話流程
- [x] `rag/build_faiss.py` — 向量資料庫建立腳本
- [x] `handlers/transport_query.py` — 航班 + 島內交通查詢流程
- [x] `flex/transport_menu.py` — 交通查詢 Flex Message 選單
- [x] `handlers/popular_trip.py` — 熱門行程展示
- [x] `flex/trip_card.py` — 行程類型輪播卡片
- [x] `flex/trip_detail.py` — 行程詳細卡片（含收藏/取消收藏）
- [x] `handlers/favorites.py` — 收藏清單 CRUD
- [x] `data/popular_trips.json` — 熱門行程資料（暫用測試資料）
- [ ] `handlers/room_query.py` — 空房查詢流程
- [ ] `flex/main_menu.py` — 主選單 Flex Message
- [ ] `flex/hotel_card.py` — 飯店資訊卡片
- [ ] `data/hotels.json` — 飯店資訊填入
- [ ] `data/popular_trips.json` — 替換為正式行程資料
