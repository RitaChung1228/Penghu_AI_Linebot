"""
行程詳細卡片 Flex Message 模板

每張卡片顯示：圖片、行程名稱、天數、景點列表、收藏按鈕（postback）
"""

import json


def get_trip_detail_carousel(trips, unfavorite=False):
    """
    將行程 list 轉為 carousel Flex Message dict。

    參數：
        trips      : list[dict]，每筆含 id、name、days、spots、image
        unfavorite : True 時 footer 顯示「取消收藏」，False 顯示「收藏行程」
    """
    return {
        "type": "carousel",
        "contents": [_build_bubble(t, unfavorite) for t in trips]
    }


def _build_bubble(trip, unfavorite=False):
    spots_text = "　".join(f"📍{s}" for s in trip["spots"])

    if unfavorite:
        footer_button = {
            "type": "button",
            "style": "primary",
            "color": "#E05C5C",
            "action": {
                "type": "postback",
                "label": "取消收藏",
                "data": f"action=unfavorite&id={trip['id']}&name={trip['name']}",
                "displayText": f"已取消收藏「{trip['name']}」"
            }
        }
    else:
        footer_button = {
            "type": "button",
            "style": "primary",
            "color": "#4EADAC",
            "action": {
                "type": "postback",
                "label": "⭐ 收藏行程",
                "data": f"action=favorite&id={trip['id']}&name={trip['name']}",
                "displayText": f"已收藏「{trip['name']}」"
            }
        }

    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": trip["image"],
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": trip["name"],
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": f"🗓 {trip['days']} 天",
                    "size": "sm",
                    "color": "#888888"
                },
                {
                    "type": "text",
                    "text": spots_text,
                    "size": "sm",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "sm"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [footer_button]
        }
    }
