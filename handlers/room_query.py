"""
空房查詢對話流程 handler

觸發詞：
    空房查詢         → 顯示空房查詢主選單
    立即查詢住宿日期  → 引導輸入入住／退房日期（待串接飯店 API）
    價格與優惠       → 顯示價格說明（待填入）
    房間照片         → 顯示房間照片（待填入）
    常見問題         → 顯示常見問題（待填入）
"""

from flex.room_menu import get_room_menu


def handle(user_id, text, reply_token, user_states, reply_fn, push_fn, reply_flex_fn):
    state = user_states.get(user_id, {})
    step = state.get("step", "start")

    # ── 入口 ──────────────────────────────────────────────
    if text == "空房查詢":
        user_states[user_id] = {"step": "start"}
        reply_flex_fn(reply_token, get_room_menu(), "🏨 空房查詢")
        return True

    # ── 立即查詢住宿日期 ───────────────────────────────────
    if text == "立即查詢住宿日期":
        user_states[user_id] = {"step": "room_checkin"}
        reply_fn(reply_token, "📅 請輸入入住日期：\n格式：2026/07/01")
        return True

    if step == "room_checkin":
        date = _parse_date(text)
        if not date:
            reply_fn(reply_token, "❌ 日期格式錯誤，請使用 2026/07/01 格式")
            return True
        user_states[user_id] = {"step": "room_checkout", "checkin": date}
        reply_fn(reply_token, f"📅 入住：{date}\n\n請輸入退房日期：")
        return True

    if step == "room_checkout":
        date = _parse_date(text)
        if not date:
            reply_fn(reply_token, "❌ 日期格式錯誤，請使用 2026/07/01 格式")
            return True
        checkin = state.get("checkin")
        user_states[user_id] = {"step": "start"}
        # TODO: 串接飯店空房 API
        reply_fn(reply_token,
            f"🔍 查詢中...\n\n"
            f"📅 入住：{checkin}\n"
            f"📅 退房：{date}\n\n"
            f"（空房查詢功能開發中，敬請期待）"
        )
        return True

    # ── 靜態資訊回覆（待填入正式內容） ───────────────────────
    if text == "價格與優惠":
        reply_fn(reply_token, "💰 價格與優惠\n\n（內容待填入）")
        user_states[user_id] = {"step": "start"}
        return True

    if text == "房間照片":
        reply_fn(reply_token, "📷 房間照片\n\n（內容待填入）")
        user_states[user_id] = {"step": "start"}
        return True

    if text == "常見問題":
        reply_fn(reply_token, "❓ 常見問題\n\n（內容待填入）")
        user_states[user_id] = {"step": "start"}
        return True

    return False


def _parse_date(text):
    """解析日期，支援 2026/07/01 或 2026-07-01，回傳標準格式或 None"""
    import re
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text.strip())
    if m:
        return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
    return None
