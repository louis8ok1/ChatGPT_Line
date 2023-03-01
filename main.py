
from flask import Flask,request,abort
#lask是一個使用Python編寫的輕量級Web應用框架。

from linebot import LineBotApi , WebhookHandler

from linebot.exceptions import InvalidSignatureError

from linebot.models import MessageEvent,TextMessage,TextSendMessage,ImageSendMessage
from dotenv import load_dotenv
"""
將一些重要的資料存在環境變數(environment variable)中，
是開發時常見的手段，不僅可以避免將重要的資料不小心 commit 進 codebase 之外，
也可以利用環境變數儲存系統或程式設定，
實務上也經常利用環境變數區隔開發環境(development)與生產環境(production)
"""
import os

from src.chatgpt import ChatGPT,DALLE
from src.models import OpenAIModel
from src.memory import Memory
from src.logger import logger

load_dotenv('.env')

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

models = OpenAIModel(api_key=os.getenv('OPENAI_API'), model_engine=os.getenv('OPENAI_MODEL_ENGINE'), max_tokens=int(os.getenv('OPENAI_MAX_TOKENS')))

memory = Memory()
chatgpt = ChatGPT(models, memory)
dalle = DALLE(models)#讓AI幫你生成圖片

@app.route("/callback",methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Error!!!!")
        abort(400)
    return 'OK'

"""
這一行程式碼，是提醒我們的 LINE 機器人，
當收到 LINE 的 MessageEvent (信息事件)，
而且信息是屬於 TextMessage (文字信息)的時候，就執行下列程式碼。
"""
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    logger.info(f'{user_id}: {text}')
    if text.startswith('/imagine'):
        response = dalle.generate(text[8:].strip())
        msg = ImageSendMessage(
            original_content_url=response,
            preview_image_url=response
        )
    else:
        response = chatgpt.get_response(user_id, text)
        msg = TextSendMessage(text=response)

    line_bot_api.reply_message(
        event.reply_token,
        msg
        )


@app.route("/", methods=['GET'])
def home():
    return 'Hello World'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)