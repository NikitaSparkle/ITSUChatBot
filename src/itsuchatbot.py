import os
import re
from pymongo import MongoClient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from datetime import datetime, timezone
import asyncio

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import OpenAI

from src.keys import openAI_api, tg_bot_token, GOOGLE_DOC_ID, MONGO_URI

# OpenAI API Key
openai = OpenAI(api_key=openAI_api)

# Telegram Bot Token
BOT_TOKEN = tg_bot_token

# MongoDB налаштування
client = MongoClient(MONGO_URI)
db = client["ITSUChatBot"]
logs_collection = db["logs"]

# Google Docs API налаштування
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
GOOGLE_DOC_ID = GOOGLE_DOC_ID


def get_google_doc_content(doc_id):
    creds = None
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('../token.pickle', 'wb') as token:
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


# Завантаження тексту з Google Docs
txt_content = get_google_doc_content(GOOGLE_DOC_ID)


def detect_response_language(user_message: str) -> str:
    if re.search(r"[а-яіїєґ]", user_message.lower()):  # Кирилиця
        return "uk"  # Українська
    return "en"  # Англійська


def format_markdown_v2(reply: str) -> str:
    special_characters = r"_*[]()~`>#+-=|{}.!"
    for char in special_characters:
        reply = reply.replace(char, f"\\{char}")
    reply = re.sub(r"\*\*(.+?)\*\*", r"*\1*", reply)
    return reply


async def log_to_db(user_name, user_question, ai_answer):
    log_entry = {
        "user_name": user_name,
        "user_question": user_question,
        "ai_answer": ai_answer,
        "datetime": datetime.now(timezone.utc)
    }
    await asyncio.to_thread(logs_collection.insert_one, log_entry)


async def process_user_request(user_message, user_name, bot, sent_message):
    try:
        response_language = detect_response_language(user_message)
        system_message = (
            "Ти Telegram-бот, створений для відповіді на запитання про ІТ Степ Університет. "
            "Твоє завдання: "
            "1. Оціни релевантність запитання користувача стосовно університету."
            "2. Якщо запитання стосується університету, знайди відповідь, використовуючи текст із Google Docs."
            "3. Якщо запитання стосується університету, але ти не маєш на нього відповіді, відповідай що не маєш такої "
            "інформації, тобі не потрібно казати, що запитання користувача стосується університету."
            f"Відповідай {response_language} мовою. Ось текст документа для використання: {txt_content}. "
            f"Запитання користувача: {user_message}"
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        # Виклик OpenAI API в окремому потоці
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        print(f"Відповідь бота: {reply}")

        # Форматування відповіді
        safe_reply = format_markdown_v2(reply)

        # Надсилання відповіді
        await bot.edit_message_text(
            chat_id=sent_message.chat_id,
            message_id=sent_message.message_id,
            text=safe_reply,
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # Логування запиту
        await log_to_db(user_name, user_message, reply)

    except Exception as e:
        print(f"Помилка: {str(e)}")
        await bot.edit_message_text(
            chat_id=sent_message.chat_id,
            message_id=sent_message.message_id,
            text=f"Помилка: {str(e)}"
        )


# Команда /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Надайте запитання, яке стосується університету.")


# Обробка тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text
    user_name = update.message.from_user.username or "Anonymous"
    print(f"Запит користувача (@{user_name}): {user_message}")

    bot = context.bot
    sent_message = await update.message.reply_text("Запит прийнято. Очікуйте...")

    # Створення окремого завдання для обробки запиту
    asyncio.create_task(process_user_request(user_message, user_name, bot, sent_message))


# Основна функція запуску бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))

    app.run_polling()


if __name__ == "__main__":
    main()
