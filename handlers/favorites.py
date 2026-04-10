"""
收藏清單 handler

功能：
    - handle()         : 處理「收藏清單」觸發詞，以 Flex carousel 顯示收藏列表
    - handle_postback(): 處理收藏、刪除、詳情三種 postback action
"""

import json
import os
from urllib.parse import parse_qs
from flex.trip_detail import get_trip_detail_carousel

FAVORITES_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "favorites")
_TRIPS_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "popular_trips.json")


# ── 工具函式 ───────────────────────────────────────────────

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


def _find_trip(trip_id):
    """從 popular_trips.json 以 id 查找行程 dict，查無回傳 None"""
    with open(_TRIPS_PATH, "r", encoding="utf-8") as f:
        all_trips = json.load(f)
    for trips in all_trips.values():
        for t in trips:
            if t["id"] == trip_id:
                return t
    return None


def _build_favorites_bubble(favorites):
    """將收藏 list 轉為單一 bubble，每筆行程一行（名稱 + 詳情 + 刪除）"""
    rows = [
        {
            "type": "text",
            "text": "⭐ 收藏清單",
            "weight": "bold",
            "size": "lg",
            "margin": "none"
        },
        {
            "type": "separator",
            "margin": "md"
        }
    ]

    for f in favorites:
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f["name"],
                    "flex": 3,
                    "size": "sm",
                    "wrap": True
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "flex": 2,
                    "action": {
                        "type": "postback",
                        "label": "詳情",
                        "data": f"action=trip_detail&id={f['id']}",
                        "displayText": f"查看「{f['name']}」詳情"
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#E05C5C",
                    "height": "sm",
                    "flex": 2,
                    "margin": "sm",
                    "action": {
                        "type": "postback",
                        "label": "刪除",
                        "data": f"action=unfavorite&id={f['id']}&name={f['name']}",
                        "displayText": f"刪除「{f['name']}」"
                    }
                }
            ]
        })

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "contents": rows
        }
    }


# ── 主要 handler ───────────────────────────────────────────

def handle(user_id, text, reply_token, user_states, reply_fn, push_fn, reply_flex_fn):
    """處理「收藏清單」觸發詞，以 Flex carousel 顯示收藏列表"""
    if text != "收藏清單":
        return False

    favorites = _get_favorites(user_id)

    if not favorites:
        reply_fn(reply_token, "你的收藏清單是空的！\n快去熱門行程找喜歡的行程收藏吧 ⭐")
        return True

    reply_flex_fn(reply_token, _build_favorites_bubble(favorites), "⭐ 收藏清單")
    return True


def handle_postback(user_id, data, reply_token, reply_fn, reply_flex_fn):
    """
    處理三種 postback action：
        favorite    → 收藏行程
        unfavorite  → 刪除收藏
        trip_detail → 顯示行程詳細卡片
    """
    params = parse_qs(data)
    action = params.get("action", [""])[0]

    # ── 收藏 ──
    if action == "favorite":
        trip_id   = params.get("id",   [""])[0]
        trip_name = params.get("name", [""])[0]
        favorites = _get_favorites(user_id)

        if any(f["id"] == trip_id for f in favorites):
            reply_fn(reply_token, f"「{trip_name}」已在收藏清單中 ⭐")
            return

        favorites.append({"id": trip_id, "name": trip_name})
        _save_favorites(user_id, favorites)
        reply_fn(reply_token, f"✅ 已收藏「{trip_name}」！\n可至「收藏清單」查看所有收藏。")

    # ── 刪除 ──
    elif action == "unfavorite":
        trip_id   = params.get("id",   [""])[0]
        trip_name = params.get("name", [""])[0]
        favorites = _get_favorites(user_id)
        new_list  = [f for f in favorites if f["id"] != trip_id]

        if len(new_list) == len(favorites):
            reply_fn(reply_token, "找不到該收藏項目。")
            return

        _save_favorites(user_id, new_list)
        reply_fn(reply_token, f"🗑 已刪除「{trip_name}」")

    # ── 詳情 ──
    elif action == "trip_detail":
        trip_id = params.get("id", [""])[0]
        trip    = _find_trip(trip_id)

        if not trip:
            reply_fn(reply_token, "找不到該行程資料。")
            return

        reply_flex_fn(reply_token, get_trip_detail_carousel([trip], unfavorite=True), trip["name"])
