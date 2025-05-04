"""
MANNUNI WhatsApp Chatbot
Advanced AI Assistant created by thexcomrade
"""

from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import openai
import os
from datetime import datetime
import requests
from PIL import Image
import io
import base64
from pathlib import Path
import logging

# ===================================
# FLASK CONFIGURATION FOR D:\MANNUNI
# ===================================
BASE_DIR = Path(r"D:\MANNUNI")
app = Flask(__name__,
            template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))

UPLOAD_FOLDER = BASE_DIR / "static" / "img" / "uploads"
LOG_FOLDER = BASE_DIR / "logs"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

app.config.update(
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SECRET_KEY=os.getenv('FLASK_SECRET', 'mannuni-secret-key-123'),
    MAX_TOKENS=int(os.getenv('MAX_TOKENS', 1500))
)

# Logging
logging.basicConfig(
    filename=LOG_FOLDER / 'mannuni.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MannuniBot')

# ======================
# MANNUNI CONFIGURATION
# ======================
BOT_NAME = os.getenv('BOT_NAME', "🤖 Mannuni")
CREATOR = os.getenv('CREATOR', "created by thexcomrade")
VERSION = "1.0"
WELCOME_MSG = f"""{BOT_NAME} 🤖
_Advanced AI Assistant {CREATOR}_

I can:
• Answer questions in 5 different styles
• Analyze images you send
• Explain complex topics simply
• Remember conversation context

How may I help you today?
"""

# API KEYS
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    logger.error("Missing OpenAI API key")
    raise ValueError("Missing OpenAI API key")

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
    logger.error("Missing Twilio credentials")
    raise ValueError("Missing Twilio credentials")

# RESPONSE STYLES
RESPONSE_STYLES = {
    '1': '🔹 Short answer (1-2 sentences)',
    '2': '📝 Detailed explanation',
    '3': '🔄 Step-by-step guide',
    '4': '👶 Layman\'s terms',
    '5': '⚙️ Technical explanation'
}

# =======================
# CHAT MANAGER
# =======================
class ChatManager:
    def __init__(self):
        self.conversations = {}

    def get_conversation(self, user_id):
        if user_id not in self.conversations:
            self.conversations[user_id] = [
                {"role": "system", "content": f"You are {BOT_NAME}, a helpful AI assistant {CREATOR}."}
            ]
        return self.conversations[user_id]

    def add_message(self, user_id, role, content):
        conversation = self.get_conversation(user_id)
        conversation.append({"role": role, "content": content})
        if len(conversation) > 6:
            conversation.pop(1)

chat_manager = ChatManager()

def get_style_prompt(code):
    return {
        '1': "Respond concisely in 1-2 sentences.",
        '2': "Provide a detailed explanation with examples.",
        '3': "Break it down into clear, numbered steps.",
        '4': "Explain like I'm five years old.",
        '5': "Include technical specifications and detail."
    }.get(code, "")

def save_uploaded_image(file_data):
    try:
        img = Image.open(io.BytesIO(file_data))
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = UPLOAD_FOLDER / filename
        img.save(path, "JPEG")
        return str(path.relative_to(BASE_DIR / "static"))
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        return None

def analyze_image(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        file_data = response.content
        local_path = save_uploaded_image(file_data)
        img = Image.open(io.BytesIO(file_data))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail"},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_base64}"}
                ]
            }],
            max_tokens=500
        )
        output = response.choices[0].message.content
        if local_path:
            output += f"\n\n[Image saved at: /{local_path}]"
        return output
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return f"🚫 Error analyzing image: {e}"

def generate_response(user_id, prompt, style=None, image_url=None):
    try:
        conversation = chat_manager.get_conversation(user_id)
        if image_url:
            image_context = analyze_image(image_url)
            prompt = f"{prompt}\n\nImage context: {image_context}"
        if style:
            prompt = f"{get_style_prompt(style)}\n\n{prompt}"
        chat_manager.add_message(user_id, "user", f"{datetime.now()}\n\n{prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation,
            temperature=0.7,
            max_tokens=app.config['MAX_TOKENS']
        )
        reply = response.choices[0].message.content
        chat_manager.add_message(user_id, "assistant", reply)
        return reply
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return f"🚫 {BOT_NAME} encountered an error: {e}"

# =====================
# ROUTES
# =====================
@app.route('/')
def dashboard():
    return render_template("mannuni_index.html",
                           bot_name=BOT_NAME,
                           creator=CREATOR,
                           version=VERSION)

@app.route('/error')
def error_page():
    return render_template("mannuni_error.html",
                           error="Sample error message",
                           bot_name=BOT_NAME,
                           creator=CREATOR)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0')
    resp = MessagingResponse()

    logger.info(f"[User: {sender}] {incoming_msg[:100]}")

    if incoming_msg.lower() in ['hi', 'hello', 'hey']:
        resp.message(WELCOME_MSG)
    elif incoming_msg.lower() == 'about':
        resp.message(f"{BOT_NAME} v{VERSION}\n{CREATOR}\nPowered by OpenAI GPT-4")
    elif incoming_msg.lower() == 'reset':
        chat_manager.conversations.pop(sender, None)
        resp.message("🔄 Conversation history cleared!")
    elif 'style:' in incoming_msg.lower():
        question = incoming_msg.split('style:', 1)[1].strip()
        menu = "\n".join([f"*{k}*: {v}" for k, v in RESPONSE_STYLES.items()])
        chat_manager.add_message(sender, "user", question)
        resp.message(f"📚 Choose a response style:\n_{question}_\n\n{menu}\n\nReply with a number (1-5)")
    elif incoming_msg.isdigit() and incoming_msg in RESPONSE_STYLES:
        last_q = chat_manager.get_conversation(sender)[-1]["content"]
        answer = generate_response(sender, last_q, incoming_msg, media_url)
        resp.message(f"{BOT_NAME}'s response ({RESPONSE_STYLES[incoming_msg]}):\n\n{answer}")
    else:
        answer = generate_response(sender, incoming_msg, None, media_url)
        resp.message(f"{answer}\n\n- {BOT_NAME} {CREATOR} -")

    return str(resp)

# =====================
# APP START
# =====================
if __name__ == '__main__':
    print(f"\n🚀 {BOT_NAME} WhatsApp Bot v{VERSION}")
    print(f"👉 Local URL: http://localhost:5000")
    print(f"👉 Ngrok URL: https://your-subdomain.ngrok.io")
    print(f"👉 Webhook Endpoint: /whatsapp\n")
    logger.info(f"Starting {BOT_NAME} WhatsApp Bot")
    app.run(host='0.0.0.0', port=5000, debug=True)
