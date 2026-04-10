"""
交通查詢主選單 Flex Message 模板

包含：
    - 島內交通：租車服務、機車租借、自行車漫遊
    - 入島交通：飛機航班、船班資訊
"""


def get_transport_menu():
    """回傳交通查詢主選單的 Flex Message dict（bubble 格式）"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px",
            "contents": [
                # ── 島內交通 標題 ──
                {
                    "type": "text",
                    "text": "🏝 島內交通",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#333333"
                },
                # ── 租車服務 按鈕 ──
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": "#4EADAC",
                    "cornerRadius": "xl",
                    "paddingAll": "14px",
                    "margin": "md",
                    "alignItems": "center",
                    "action": {
                        "type": "message",
                        "label": "租車服務",
                        "text": "租車服務"
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "🚗",
                            "size": "xl",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "租車服務",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "align": "center",
                            "flex": 1
                        }
                    ]
                },
                # ── 機車租借 按鈕 ──
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": "#4EADAC",
                    "cornerRadius": "xl",
                    "paddingAll": "14px",
                    "margin": "md",
                    "alignItems": "center",
                    "action": {
                        "type": "message",
                        "label": "機車租借",
                        "text": "機車租借"
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "🛵",
                            "size": "xl",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "機車租借",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "align": "center",
                            "flex": 1
                        }
                    ]
                },
                # ── 自行車漫遊 按鈕 ──
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": "#4EADAC",
                    "cornerRadius": "xl",
                    "paddingAll": "14px",
                    "margin": "md",
                    "alignItems": "center",
                    "action": {
                        "type": "message",
                        "label": "自行車漫遊",
                        "text": "自行車漫遊"
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "🚲",
                            "size": "xl",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "自行車漫遊",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "align": "center",
                            "flex": 1
                        }
                    ]
                },
                # ── 分隔線 ──
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xl",
                    "contents": [
                        {
                            "type": "separator",
                            "color": "#DDDDDD"
                        }
                    ]
                },
                # ── 入島交通 標題 ──
                {
                    "type": "text",
                    "text": "✈️ 入島交通",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#333333",
                    "margin": "xl"
                },
                # ── 飛機航班 按鈕 ──
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": "#4EADAC",
                    "cornerRadius": "xl",
                    "paddingAll": "14px",
                    "margin": "md",
                    "alignItems": "center",
                    "action": {
                        "type": "message",
                        "label": "飛機航班",
                        "text": "飛機航班"
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "🛫",
                            "size": "xl",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "飛機航班",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "align": "center",
                            "flex": 1
                        }
                    ]
                },
                # ── 船班資訊 按鈕 ──
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": "#4EADAC",
                    "cornerRadius": "xl",
                    "paddingAll": "14px",
                    "margin": "md",
                    "alignItems": "center",
                    "action": {
                        "type": "message",
                        "label": "船班資訊",
                        "text": "船班資訊"
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "⛴",
                            "size": "xl",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "船班資訊",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "align": "center",
                            "flex": 1
                        }
                    ]
                }
            ]
        }
    }
