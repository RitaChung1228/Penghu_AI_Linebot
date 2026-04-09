"""
智慧查詢對話流程處理器

觸發條件：使用者點選主選單「智慧查詢」按鈕
流程：
    1. 使用者點「智慧查詢」→ 回覆引導訊息，等待輸入需求
    2. 使用者輸入需求      → 先回覆「規劃中」，背景執行 RAG pipeline
    3. RAG 完成            → push 行程結果給使用者
"""

import threading
from services.rag_service import rag_smart_reply


def handle(user_id, text, reply_token, user_states, reply_fn, push_fn):
    """
    智慧查詢的訊息處理入口。

    參數：
        user_id     : LINE 使用者 ID
        text        : 使用者傳入的文字
        reply_token : LINE reply token（只能用一次，且有時效）
        user_states : 全域對話狀態 dict，記錄每位使用者目前的步驟
        reply_fn    : reply(reply_token, text) — 即時回覆（有時效限制）
        push_fn     : push(user_id, text)     — 主動推送（無時效限制）

    回傳：
        True  — 此訊息已被智慧查詢處理，app.py 不需再往下判斷
        False — 此訊息與智慧查詢無關，交還給 app.py 繼續處理
    """
    state = user_states.get(user_id, {})
    step = state.get("step", "start")

    # ── Step 1：使用者點選「智慧查詢」────────────────────
    # 設定狀態，等待使用者輸入需求
    if text == "智慧查詢":
        user_states[user_id] = {"step": "smart_query_input"}
        reply_fn(reply_token, "🤖 請輸入你的需求，例如：\n「喜歡吃海鮮、玩水，規劃三天兩夜」")
        return True

    # ── Step 2：使用者輸入需求────────────────────────────
    # RAG pipeline 耗時約 30 秒，用 reply 先回覆「規劃中」避免逾時
    # 實際運算放到背景 thread，完成後透過 push 推送結果
    if step == "smart_query_input":
        reply_fn(reply_token, "⏳ 正在幫你規劃澎湖行程，約需 30 秒，請稍候...")

        # 重置狀態，避免使用者重複觸發
        user_states[user_id] = {"step": "start"}

        # 背景執行 RAG pipeline
        def _run():
            result = rag_smart_reply(text)
            push_fn(user_id, result)

        threading.Thread(target=_run, daemon=True).start()
        return True

    # 非智慧查詢的訊息，交還給 app.py
    return False
