import os
import re
from pymongo import MongoClient
from datetime import datetime, timezone
import asyncio

from flask import Flask, request
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import openai
from llama_index.core import VectorStoreIndex, Document

# Ініціалізація Flask додатку
app = Flask(__name__)

# Секретні змінні (завантажуються з середовища)
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Ініціалізація OpenAI API
openai.api_key = OPENAI_API_KEY

# Налаштування MongoDB
client = MongoClient(MONGO_URI)
db = client["ITSUChatBot"]
logs_collection = db["logs"]

# Завантаження тексту з Google Docs
def get_google_doc_content(doc_id):
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle

    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('docs', 'v1', credentials=creds)
    document = service.documents().get(documentId=doc_id).execute()

    content = ''
    for element in document.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for text_element in element['paragraph'].get('elements', []):
                if 'textRun' in text_element:
                    content += text_element['textRun']['content']
    return content

# Створення індексу з тексту
def build_index_from_text(content):
    documents = [Document(text=content)]
    index = VectorStoreIndex.from_documents(documents)
    return index

# Завантаження документа з Google Docs та створення індексу
try:
    txt_content = get_google_doc_content(GOOGLE_DOC_ID)
    index = build_index_from_text(txt_content)
    query_engine = index.as_query_engine()
    google_doc_full_content = txt_content
except Exception as e:
    print(f"Помилка завантаження документа: {e}")
    google_doc_full_content = ""
    query_engine = None

# Визначення мови відповіді
def detect_response_language(user_message: str) -> str:
    if re.search(r"[а-яіїєґ]", user_message.lower()):
        return "uk"  # Українська
    return "en"  # Англійська

# Форматування тексту для Telegram Markdown V2
def format_markdown_v2(reply: str) -> str:
    special_characters = r"_[]()~`>#+-=|{}.!"
    for char in special_characters:
        reply = reply.replace(char, f"\\{char}")
    reply = re.sub(r"\\*\\*(.+?)\\*\\*", r"*\1*", reply)
    return reply

# Логування запитів у базу даних
async def log_to_db(user_name, user_question, ai_answer):
    log_entry = {
        "user_name": user_name,
        "user_question": user_question,
        "ai_answer": ai_answer,
        "datetime": datetime.now(timezone.utc)
    }
    await asyncio.to_thread(logs_collection.insert_one, log_entry)

# Обробка запиту користувача
async def process_user_request(user_message, user_name):
    try:
        if not query_engine:
            raise ValueError("Індекс недоступний.")

        # Пошук релевантного контексту через QueryEngine
        response = query_engine.query(user_message)
        relevant_context = response.response  # Відповідь від LlamaIndex

        response_language = detect_response_language(user_message)
        system_message = (
            "Ти Telegram-бот, створений для відповіді на запитання про ІТ Степ Університет. "
            "Твоє завдання: "
            "1. Оціни релевантність запитання користувача стосовно університету. "
            "2. Якщо запитання стосується університету, знайди відповідь, використовуючи наданий текст. "
            "3. Якщо запитання стосується університету, але ти не маєш на нього відповіді, відповідай, що не маєш такої інформації. "
            f"Відповідай {response_language} мовою."
            f"Ось релевантний текст для використання: {relevant_context}. "
            f"Ось повний текст документа для контексту: {google_doc_full_content}. "
            f"Запитання користувача: {user_message}"
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        await log_to_db(user_name, user_message, reply)
        return format_markdown_v2(reply)

    except Exception as e:
        return f"Помилка: {str(e)}"

# Команда /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Надайте запитання, яке стосується університету.")

# Обробка тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text
    user_name = update.message.from_user.username or "Anonymous"
    reply = await process_user_request(user_message, user_name)
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN_V2)

# Вебхук для Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), Bot(token=BOT_TOKEN))
    await application.process_update(update)
    return "OK", 200

# Ініціалізація додатку
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))

if __name__ == "__main__":
    app.run(port=3000)
