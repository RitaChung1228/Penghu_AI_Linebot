"""
熱門行程對話流程 handler

觸發詞：
    熱門行程         → 顯示四種行程類型輪播卡片
    查看自然行程     → 顯示自然行程詳細卡片（含收藏按鈕）
    查看人文行程     → 顯示人文行程詳細卡片
    查看美食推薦     → 顯示美食行程詳細卡片
    查看玩水行程     → 顯示海上行程詳細卡片
"""

import json
import os
from flex.trip_card import get_trip_carousel
from flex.trip_detail import get_trip_detail_carousel

# 載入行程資料
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "popular_trips.json")
with open(_DATA_PATH, "r", encoding="utf-8") as f:
    _TRIPS = json.load(f)

# 觸發詞 → 行程類型對照
_TRIGGER_MAP = {
    "查看自然行程": "nature",
    "查看人文行程": "culture",
    "查看美食推薦": "food",
    "查看玩水行程": "sea"
}

_TITLE_MAP = {
    "nature": "🌿 自然行程",
    "culture": "🏛 人文行程",
    "food":    "🍽 美食行程",
    "sea":     "🌊 海上行程"
}


def handle(user_id, text, reply_token, user_states, reply_fn, push_fn, reply_flex_fn):
    # 熱門行程入口
    if text == "熱門行程":
        reply_flex_fn(reply_token, get_trip_carousel(), "🏝 熱門行程")
        return True

    # 各行程類型詳細卡片
    if text in _TRIGGER_MAP:
        category = _TRIGGER_MAP[text]
        trips = _TRIPS.get(category, [])
        title = _TITLE_MAP[category]
        reply_flex_fn(reply_token, get_trip_detail_carousel(trips), title)
        return True

    return False
