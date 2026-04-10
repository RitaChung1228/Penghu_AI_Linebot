"""
交通查詢對話流程 handler

功能：
    - 交通查詢 → 顯示交通選單 Flex Message
    - 飛機航班 → 引導輸入出發城市、抵達城市、日期，查詢華信航空航班
    - 船班資訊 → 顯示台華輪訂票連結
    - 租車服務 / 機車租借 / 自行車漫遊 → 顯示提示文字

對話步驟（user_states 的 step 欄位）：
    transport_flight_departure  ─ 等待輸入出發城市
    transport_flight_arrival    ─ 等待輸入抵達城市
    transport_flight_date       ─ 等待輸入出發日期
"""

from flex.transport_menu import get_transport_menu
from services.airline_service import search_flights, format_result
from services.tide_service import get_today_tide, format_tide_entry
from datetime import datetime

# 城市名稱 → 航班代碼對照表（華信航空）
CITY_CODES = {
    "台北": "TSA",
    "台中": "RMQ",
    "嘉義": "CYI",
    "高雄": "KHH",
    "澎湖": "MZG"
}

CITY_OPTIONS = "、".join(CITY_CODES.keys())  # 台北、台中、嘉義、高雄、澎湖


def handle(user_id, text, reply_token, user_states, reply_fn, push_fn, reply_flex_fn):
    """
    交通查詢主入口。

    參數：
        user_id      : LINE 使用者 ID
        text         : 使用者輸入文字
        reply_token  : LINE reply token（即時回覆用）
        user_states  : 全域對話狀態 dict
        reply_fn     : reply(reply_token, text) 函式
        push_fn      : push(user_id, text) 函式
        reply_flex_fn: reply_flex(reply_token, flex_dict, alt_text) 函式

    回傳：
        True  → 此訊息已由本 handler 處理
        False → 非本 handler 負責，交由下一個 handler 判斷
    """
    state = user_states.get(user_id, {})
    step = state.get("step", "start")

    # ── 入口：使用者點選「交通查詢」選單按鈕 ──────────────
    if text == "交通查詢":
        user_states[user_id] = {"step": "transport_menu"}
        reply_flex_fn(reply_token, get_transport_menu(), "🚌 交通查詢")
        return True

    # ── 島內交通：靜態資訊回覆 ─────────────────────────────
    if text == "租車服務":
        reply_fn(reply_token,
            "🚗 澎湖租車服務\n\n"
            "澎湖島內有多家租車業者，建議提前預約：\n"
            "• 馬公市區及機場附近均有租車點\n"
            "• 可租 4~7 人座轎車或休旅車\n"
            "• 費用約 NT$1,500–2,500 / 天\n\n"
            "建議搜尋「澎湖租車」選擇有口碑的業者，出發前電話確認。"
        )
        user_states[user_id] = {"step": "start"}
        return True

    if text == "機車租借":
        reply_fn(reply_token,
            "🛵 澎湖機車租借\n\n"
            "機車是澎湖最方便的島內交通工具：\n"
            "• 機場、馬公市區、各大飯店附近均有租借點\n"
            "• 需持有效機車駕照（含國際駕照）\n"
            "• 費用約 NT$300–500 / 天（機車）\n"
            "• 電動機車也可租借，更環保省錢\n\n"
            "⚠️ 澎湖多風，騎車請注意安全，戴好安全帽！"
        )
        user_states[user_id] = {"step": "start"}
        return True

    if text == "自行車漫遊":
        reply_fn(reply_token,
            "🚲 澎湖自行車漫遊\n\n"
            "享受慢遊澎湖的愜意時光：\n"
            "• 馬公市區及觀音亭周邊有自行車道\n"
            "• 租借費用約 NT$100–200 / 小時\n"
            "• 適合短程景點遊覽，不適合跨島\n\n"
            "推薦路線：觀音亭海濱公園 → 馬公老街 → 天后宮"
        )
        user_states[user_id] = {"step": "start"}
        return True

    # ── 入島交通：船班資訊（靜態） ────────────────────────
    if text == "船班資訊":
        reply_fn(reply_token,
            "⛴ 澎湖船班資訊\n\n"
            "【台華輪】高雄 ↔ 馬公\n"
            "• 航程約 4–6 小時\n"
            "• 每日一至數班（依季節調整）\n"
            "• 訂票：台灣航業官網或電話\n"
            "  📞 07-561-3866（高雄）\n\n"
            "【台馬輪】基隆/台中 ↔ 馬公\n"
            "• 航程約 8–10 小時（含離島航線）\n\n"
            "⚠️ 船班受天候影響，出發前請確認最新動態。\n"
            "🔗 建議至台灣航業官網查詢即時班次。"
        )
        user_states[user_id] = {"step": "start"}
        return True

    # ── 入島交通：飛機航班查詢（多步驟對話） ────────────────
    if text == "飛機航班":
        user_states[user_id] = {"step": "transport_flight_departure"}
        reply_fn(reply_token,
            f"🛫 飛機航班查詢\n\n請輸入出發城市：\n{CITY_OPTIONS}"
        )
        return True

    if step == "transport_flight_departure":
        code = CITY_CODES.get(text)
        if not code:
            reply_fn(reply_token, f"❌ 無法識別城市，請輸入：{CITY_OPTIONS}")
            return True
        user_states[user_id] = {"step": "transport_flight_arrival", "departure": code, "dep_name": text}
        reply_fn(reply_token, f"📍 出發：{text}\n\n請輸入抵達城市：\n{CITY_OPTIONS}")
        return True

    if step == "transport_flight_arrival":
        code = CITY_CODES.get(text)
        if not code:
            reply_fn(reply_token, f"❌ 無法識別城市，請輸入：{CITY_OPTIONS}")
            return True
        user_states[user_id] = {
            **state,
            "step": "transport_flight_date",
            "arrival": code,
            "arr_name": text
        }
        dep_name = state.get("dep_name", "")
        reply_fn(reply_token,
            f"📍 {dep_name} → {text}\n\n請輸入出發日期：\n格式：2026/05/16"
        )
        return True

    if step == "transport_flight_date":
        date = _parse_date(text)
        if not date:
            reply_fn(reply_token, "❌ 日期格式錯誤，請使用 2026/05/16 格式")
            return True

        departure = state.get("departure")
        arrival = state.get("arrival")
        dep_name = state.get("dep_name", departure)
        arr_name = state.get("arr_name", arrival)

        reply_fn(reply_token, f"🔍 查詢中：{dep_name} → {arr_name}  {date}，請稍候...")
        user_states[user_id] = {"step": "start"}

        # 在背景執行航班查詢（網路請求可能較慢）
        import threading
        def _search():
            try:
                flights = search_flights(departure, arrival, date)
                result = format_result(dep_name, arr_name, date, flights, 1)
            except Exception as e:
                result = f"⚠️ 查詢失敗，請稍後再試。\n（{e}）"
            push_fn(user_id, result)

        threading.Thread(target=_search, daemon=True).start()
        return True

    return False


def _parse_date(text):
    """
    解析日期輸入，支援 2026/05/16 或 2026-05-16 格式。
    回傳 'YYYY/MM/DD' 字串，格式錯誤回傳 None。
    """
    import re
    text = text.strip()
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if m:
        return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
    return None
