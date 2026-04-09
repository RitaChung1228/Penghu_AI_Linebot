# 澎湖旅遊 AI LINE Bot

澎湖在地旅遊助手，提供行程規劃、智慧查詢、航班查詢等旅遊服務。

---

## 系統功能

主選單提供五個功能入口：

| 功能 | 說明 |
|------|------|
| 熱門行程 | 推薦精選澎湖行程，以輪播卡片呈現 |
| 收藏清單 | 使用者個人收藏的行程或景點 |
| 智慧查詢 | 輸入需求，AI 結合 RAG 生成客製化澎湖行程建議 |
| 空房查詢 | 查詢澎湖飯店空房資訊 |
| 交通查詢 | 查詢往返澎湖的航班時刻與潮汐安全通行時間 |

---

## 技術架構

### 系統架構圖

```
LINE User
    │
    ▼
LINE Platform
    │  Webhook (HTTPS POST)
    ▼
┌─────────────────────────────────────────┐
│  app.py  ─  Flask Webhook 入口          │
│  user_states{}  ─  對話狀態機           │
└────────────────┬────────────────────────┘
                 │ 依 step 分派
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
  │ scenery_service  → 景點資料  │
  │ rag_service      → RAG引擎  │
  └─────────────────────────────┘
        │
        ▼
  rag/faiss_db/        data/
  FAISS 向量資料庫      靜態 JSON 資料
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
├── handlers/                   # 對話流程控制器（管理「對話在哪一步、說什麼」）
│   ├── popular_trip.py         # 熱門行程流程
│   ├── favorites.py            # 收藏清單流程
│   ├── smart_query.py          # 智慧查詢流程（呼叫 rag_service）
│   ├── room_query.py           # 空房查詢流程
│   └── transport_query.py      # 交通查詢流程（航班 + 潮汐）
│
├── services/                   # 資料服務層（純函式，只負責取資料）
│   ├── airline_service.py      # 華信航空航班爬蟲查詢
│   ├── weather_service.py      # 中央氣象署天氣 API
│   ├── tide_service.py         # 澎管處潮汐爬蟲
│   ├── scenery_service.py      # 景點資料讀取與查詢
│   └── rag_service.py          # RAG 智慧查詢核心（FAISS + Mistral pipeline）
│
├── rag/                        # RAG 相關資料（不含程式碼）
│   ├── faiss_db/               # FAISS 向量資料庫（由 source_docs 建立）
│   │   ├── index.faiss         # 向量索引
│   │   └── index.pkl           # 文件對照表
│   └── source_docs/            # 建立向量庫的原始文件
│       └── Panghu_schedule_database.md   # 澎湖行程活動資料庫
│
├── flex/                       # LINE Flex Message JSON 模板
│   ├── main_menu.py            # 五按鈕主選單
│   ├── trip_card.py            # 行程輪播卡片
│   └── hotel_card.py           # 飯店資訊卡片
│
├── data/                       # 靜態 JSON 資料檔（爬蟲產生或手動維護）
│   ├── scenery_data.json       # 澎湖景點完整資料（scenery_crawler 產生）
│   ├── popular_trips.json      # 熱門行程資料
│   └── hotels.json             # 飯店基本資訊
│
├── storage/                    # 使用者持久化資料
│   └── favorites/              # 每位使用者的收藏清單
│       └── {user_id}.json      # 以 LINE user_id 命名
│
├── crawlers/                   # 爬蟲腳本（手動執行以更新 data/）
│   └── scenery_crawler.py      # 澎湖景點爬蟲（更新 scenery_data.json）
│
└── picture/                    # 圖片資源
```

---

## 技術選型

| 類別 | 技術 |
|------|------|
| Web 框架 | Flask |
| LINE Bot SDK | line-bot-sdk v3 (Python) |
| 語言模型 | Mistral (`ministral-8b-latest`) via aisuite |
| 備援問答模型 | Google Gemini 2.0 Flash |
| Embedding 模型 | `google/embeddinggemma-300m`（HuggingFace） |
| 向量資料庫 | FAISS (Facebook AI Similarity Search) |
| RAG 框架 | LangChain Community |
| 天氣資料 | 中央氣象署開放資料平台 API |
| 航班資料 | 華信航空官網爬蟲（BeautifulSoup） |
| 景點資料 | 澎湖國家風景區管理處官網爬蟲 |
| 潮汐資料 | 澎管處潮汐頁面爬蟲 |
| 本機測試 | ngrok（HTTPS tunnel） |

---

## 環境設定

`.env` 需設定以下變數：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
GEMINI_API_KEY=your_gemini_key
MISTRAL_API_KEY=your_mistral_key
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

## 各模組分工說明

### app.py — 對話狀態機

`user_states` dict 儲存每位使用者目前的對話步驟（`step`），根據 step 呼叫對應的 handler：

```python
user_states = {
    "U1234": {"step": "smart_query"},
    "U5678": {"step": "transport_departure", "trip": "single"},
}
```

### handlers/ — 流程控制

負責「問什麼問題、等什麼輸入、何時呼叫 service」，不處理資料取得邏輯。

### services/ — 資料服務

純函式，輸入參數回傳結果。handler 呼叫 service，service 不知道對話存在。

### rag_service.py — RAG 核心

- **模組載入時**初始化 EmbeddingGemma + FAISS（只載入一次，避免重複耗時 2 分鐘）
- 提供 `rag_smart_reply(user_text: str) -> str` 單一入口
- 內部執行 4 步驟 pipeline（需求分析 → RAG檢索 → 行程規劃 → 審查修正）

---

## 待開發項目

- [ ] `services/rag_service.py` — 從 `Panghu_AI_Leader/main_core_code.py` 拆解整合
- [ ] `services/scenery_service.py` — 從 `information/scenery.py` 拆解服務層
- [ ] `crawlers/scenery_crawler.py` — 從 `information/scenery.py` 拆解爬蟲腳本
- [ ] `handlers/smart_query.py` — 智慧查詢對話流程
- [ ] `handlers/transport_query.py` — 航班 + 潮汐整合查詢流程
- [ ] `handlers/favorites.py` — 收藏清單 CRUD
- [ ] `handlers/popular_trip.py` — 熱門行程展示
- [ ] `handlers/room_query.py` — 空房查詢流程
- [ ] `flex/main_menu.py` — 主選單 Flex Message
- [ ] `flex/trip_card.py` — 行程輪播卡片
- [ ] `flex/hotel_card.py` — 飯店資訊卡片
- [ ] `data/popular_trips.json` — 熱門行程資料填入
- [ ] `data/hotels.json` — 飯店資訊填入
