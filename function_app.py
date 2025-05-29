import logging
import json
import os
import re
from typing import Optional, Tuple
import azure.functions as func
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

# LINE Bot設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
parser = WebhookParser(os.getenv('LINE_CHANNEL_SECRET'))

# OpenAI設定（最新のクライアント初期化方式）
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Azure Functions v2 アプリケーション作成
app = func.FunctionApp()

# コンテキスト保持用（最大5メッセージ、グローバル共有）
context_memory = []

def load_system_prompt() -> str:
    """システムプロンプトをファイルから読み込み"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, 'system_prompt.txt')
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.error("system_prompt.txt not found, using fallback prompt")
        return """あなたは昭和生まれの温かいおばあちゃん「ろんな」です。
関西弁混じりの優しい口調で、人生経験を活かしたアドバイスをしてください。
80-120文字程度で簡潔に応答してください。"""
    except Exception as e:
        logging.error(f"Error loading system prompt: {str(e)}")
        return "あなたは優しいおばあちゃんろんなです。温かく応答してください。"

def should_respond_to_message(message_text: str) -> Tuple[bool, str]:
    """
    メッセージに応答すべきかを判定し、処理すべきテキストを返す
    
    Returns:
        tuple[bool, str]: (応答すべきか, 処理すべきテキスト)
    """
    if not message_text:
        return False, ""
    
    # メッセージの最初の3文字をチェック
    if message_text[:3].lower() == "ろんな":
        # 「ろんな」以降のテキストを返す
        content = message_text[3:].strip()
        # 内容が空の場合はあいさつとして扱う
        if not content:
            content = "あいさつ"
        return True, content
    
    return False, ""

def update_context(user_message: str) -> list:
    """
    グローバルなコンテキストを更新し、最新の5メッセージを保持する。
    
    Args:
        user_message (str): ユーザーからのメッセージ
    
    Returns:
        list: 更新されたコンテキスト
    """
    global context_memory
    
    # メッセージを追加
    context_memory.append({"role": "user", "content": user_message})
    
    # 最大5メッセージを保持
    if len(context_memory) > 5:
        context_memory = context_memory[-5:]
    
    return context_memory

def generate_grandma_response(user_message: str) -> str:
    """昭和のおばあちゃん風の応答を生成（最新のOpenAI API使用）"""
    global context_memory  # グローバル変数を明示的に宣言

    try:
        system_prompt = load_system_prompt()
        
        # コンテキストを更新
        context = update_context(user_message)
        
        # システムプロンプトを先頭に追加
        messages = [{"role": "system", "content": system_prompt}] + context
        
        # GPT-4o-miniを使用（GPT-3.5-turboより高性能で同等コスト）
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=200,  # 少し余裕を持たせる
            temperature=0.8,
            top_p=0.9,  # より自然な応答のために追加
            frequency_penalty=0.1,  # 繰り返しを少し抑制
        )
        
        generated_text = response.choices[0].message.content.strip()
        
        # 応答の長さをチェックし、必要に応じて調整
        if len(generated_text) > 150:
            # 長すぎる場合は最初の文で区切る
            sentences = re.split(r'[。！？]', generated_text)
            if len(sentences) > 1:
                generated_text = sentences[0] + '。'
        
        return generated_text
        
    except openai.RateLimitError:
        logging.error("OpenAI API rate limit exceeded")
        return "ちょっと忙しくてねえ。少し待ってからまた声かけておくれ。"
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return "あらあら、ちょっと調子が悪いねえ。また後で話しかけておくれ。"
    except Exception as e:
        logging.error(f"Unexpected error in generate_grandma_response: {str(e)}")
        return "ごめんねえ、今ちょっと聞こえなかったわ。もう一回言っておくれ。"

def handle_line_webhook_event(req_body: str, signature: str) -> None:
    """LINE Webhook イベントの処理（SDK 3.x対応）"""
    try:
        events = parser.parse(req_body, signature)
        
        for event in events:
            # isinstance チェックは従来通り
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                user_message = event.message.text
                logging.info(f"Received message: {user_message}")
                
                # 「ろんな」で始まるメッセージかチェック
                should_respond, processed_message = should_respond_to_message(user_message)
                
                # ユーザメッセージをコンテキストに追加
                update_context(user_message)
                
                if should_respond:
                    logging.info(f"Processing message: {processed_message}")
                    
                    # おばあちゃん風の応答を生成
                    grandma_response = generate_grandma_response(processed_message)
                    
                    # 応答が空でないことを確認
                    if not grandma_response:
                        grandma_response = "あらあら、何て言ったらいいか分からないねえ。"
                    
                    # 応答メッセージをコンテキストに追加
                    context_memory.append({"role": "assistant", "content": grandma_response})
                    
                    # LINE返信
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=grandma_response)
                    )
                    
                    logging.info(f"Sent response: {grandma_response}")
                else:
                    logging.info("Message doesn't start with 'ろんな', ignoring")
                    continue
                
    except InvalidSignatureError:
        logging.error("Invalid LINE signature")
        raise
    except LineBotApiError as e:
        logging.error(f"LINE Bot API error: {e}")
        if e.status_code >= 500:
            logging.info("Server error, will not send error message to user")
        else:
            logging.error(f"Client error {e.status_code}: {e.error.message}")
    except Exception as e:
        logging.error(f"Error handling LINE event: {str(e)}")

# HTTP Trigger 関数（v2 デコレーター形式）
@app.route(route="HttpTrigger1", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """LINE Bot Webhook エンドポイント"""
    logging.info('LINE Bot webhook triggered.')
    
    try:
        # リクエストボディとヘッダーを取得
        body = req.get_body().decode('utf-8')
        signature = req.headers.get('x-line-signature', '')
        
        if not body:
            logging.warning("Empty request body")
            return func.HttpResponse("Bad request", status_code=400)
        
        if not signature:
            logging.warning("Missing x-line-signature header")
            return func.HttpResponse("Unauthorized", status_code=401)
        
        logging.info(f"Request body length: {len(body)}")
        
        # LINE Webhook イベント処理
        handle_line_webhook_event(body, signature)
        
        return func.HttpResponse("OK", status_code=200)
        
    except InvalidSignatureError:
        logging.error("Invalid signature")
        return func.HttpResponse("Forbidden", status_code=403)
    except Exception as e:
        logging.error(f"Error in http_trigger: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)