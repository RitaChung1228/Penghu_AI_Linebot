def get_trip_carousel():
    return {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://images.unsplash.com/photo-1541414779316-956a5084c0d4?q=80&w=1000&auto=format&fit=crop",
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "絕美自然", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "適合愛拍照、看風景的人", "size": "sm", "color": "#666666", "margin": "md"}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#4EADAC",
                         "action": {"type": "message", "label": "查看自然行程", "text": "查看自然行程"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://images.unsplash.com/photo-1590059039931-815c32841477?q=80&w=1000&auto=format&fit=crop",
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "人文巡禮", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "適合想看古蹟、走老街的人", "size": "sm", "color": "#666666", "margin": "md"}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#4EADAC",
                         "action": {"type": "message", "label": "查看人文行程", "text": "查看人文行程"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000&auto=format&fit=crop",
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "舌尖澎湖", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "適合就是要吃好料的人 (推薦合作餐廳)", "size": "sm", "color": "#666666", "margin": "md", "wrap": True}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#4EADAC",
                         "action": {"type": "message", "label": "查看美食推薦", "text": "查看美食推薦"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://images.unsplash.com/photo-1530811755225-03d694fd9b6c?q=80&w=1000&auto=format&fit=crop",
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "海上冒險", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "適合熱血、愛玩水的人 (海上套裝行程)", "size": "sm", "color": "#666666", "margin": "md", "wrap": True}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#4EADAC",
                         "action": {"type": "message", "label": "查看玩水行程", "text": "查看玩水行程"}}
                    ]
                }
            }
        ]
    }
