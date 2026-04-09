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
    TextMessage as TextMsg
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv
import handlers.smart_query as smart_query_handler

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


def handle_message(user_id, text, reply_token):
    """
    訊息分派中心。
    依序呼叫各 handler，由 handler 回傳 True/False 決定是否繼續往下判斷。
    """
    text = text.strip()

    # ── 智慧查詢 ──────────────────────────────────────────
    # handle() 回傳 True 表示此訊息已處理，不需再往下判斷
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


if __name__ == "__main__":
     app.run(port=5000, debug=True, use_reloader=False)
