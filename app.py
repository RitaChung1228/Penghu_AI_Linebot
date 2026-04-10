"""
澎湖旅遊 AI LINE Bot 主程式

職責：
    - 接收 LINE Webhook 事件
    - 將訊息分派給對應的 handler 處理
"""

import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage as TextMsg,
    FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent
from dotenv import load_dotenv
import handlers.smart_query as smart_query_handler
import handlers.transport_query as transport_query_handler
import handlers.popular_trip as popular_trip_handler
import handlers.favorites as favorites_handler

load_dotenv()

app = Flask(__name__)
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 記錄每位使用者目前的對話步驟
# 格式：{ user_id: {"step": "smart_query_input"} }
user_states = {}


def reply(reply_token, text):
    """即時回覆使用者（reply token 有時效，只能用一次）"""
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMsg(type="text", text=text)]
            )
        )

def push(user_id, text):
    """主動推送訊息給使用者（無時效限制，適合背景作業完成後使用）"""
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMsg(type="text", text=text)]
            )
        )

def reply_flex(reply_token, flex_dict, alt_text="選單"):
    """即時回覆 Flex Message（bubble 或 carousel）"""
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    FlexMessage(
                        alt_text=alt_text,
                        contents=FlexContainer.from_dict(flex_dict)
                    )
                ]
            )
        )


def handle_message(user_id, text, reply_token):
    """
    訊息分派中心。
    依序呼叫各 handler，由 handler 回傳 True/False 決定是否繼續往下判斷。
    """
    text = text.strip()

    # ── 熱門行程 ──────────────────────────────────────────
    if popular_trip_handler.handle(user_id, text, reply_token, user_states, reply, push, reply_flex):
        return

    # ── 收藏清單 ──────────────────────────────────────────
    if favorites_handler.handle(user_id, text, reply_token, user_states, reply, push, reply_flex):
        return

    # ── 交通查詢 ──────────────────────────────────────────
    if transport_query_handler.handle(user_id, text, reply_token, user_states, reply, push, reply_flex):
        return

    # ── 智慧查詢 ──────────────────────────────────────────
    if smart_query_handler.handle(user_id, text, reply_token, user_states, reply, push):
        return


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook 入口，驗證簽名後交給 handler 處理"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    """接收文字訊息事件，取出 user_id、文字、reply_token 後傳入分派中心"""
    handle_message(event.source.user_id, event.message.text, event.reply_token)


@handler.add(PostbackEvent)
def handle_postback(event):
    """接收 postback 事件（如收藏、刪除、詳情按鈕），交給 favorites handler 處理"""
    favorites_handler.handle_postback(
        event.source.user_id,
        event.postback.data,
        event.reply_token,
        reply,
        reply_flex
    )


if __name__ == "__main__":
     app.run(port=5000, debug=True, use_reloader=False)
