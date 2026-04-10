"""
收藏清單 handler

功能：
    - handle_postback(): 處理收藏按鈕的 postback 事件，寫入收藏
    - handle(): 處理「收藏清單」觸發詞，顯示用戶的收藏列表
"""

import json
import os
from urllib.parse import parse_qs

FAVORITES_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "favorites")


def _get_favorites(user_id):
    """讀取用戶收藏清單，不存在則回傳空 list"""
    os.makedirs(FAVORITES_DIR, exist_ok=True)
    path = os.path.join(FAVORITES_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_favorites(user_id, favorites):
    """儲存用戶收藏清單"""
    os.makedirs(FAVORITES_DIR, exist_ok=True)
    path = os.path.join(FAVORITES_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def handle_postback(user_id, data, reply_token, reply_fn):
    """
    處理收藏 postback。

    data 格式：action=favorite&id=nature_1&name=西嶼秘境一日遊
    """
    params = parse_qs(data)
    action = params.get("action", [""])[0]

    if action != "favorite":
        return

    trip_id = params.get("id", [""])[0]
    trip_name = params.get("name", [""])[0]

    favorites = _get_favorites(user_id)

    # 檢查是否已收藏
    if any(f["id"] == trip_id for f in favorites):
        reply_fn(reply_token, f"「{trip_name}」已在收藏清單中 ⭐")
        return

    favorites.append({"id": trip_id, "name": trip_name})
    _save_favorites(user_id, favorites)
    reply_fn(reply_token, f"✅ 已收藏「{trip_name}」！\n可至「收藏清單」查看所有收藏。")


def handle(user_id, text, reply_token, user_states, reply_fn, push_fn, reply_flex_fn):
    """
    處理「收藏清單」觸發詞，顯示用戶的所有收藏。
    """
    if text != "收藏清單":
        return False

    favorites = _get_favorites(user_id)

    if not favorites:
        reply_fn(reply_token, "你的收藏清單是空的！\n快去熱門行程找喜歡的行程收藏吧 ⭐")
        return True

    lines = ["⭐ 你的收藏清單\n"]
    for i, f in enumerate(favorites, 1):
        lines.append(f"{i}. {f['name']}")
    reply_fn(reply_token, "\n".join(lines))
    return True
