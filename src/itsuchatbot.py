import os
import re
import asyncio
from difflib import SequenceMatcher

import telegram
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PyPDF2 import PdfReader
from openai import OpenAI

from src.keys import openAI_api, tg_bot_token

# OpenAI API Key
openai = OpenAI(
    api_key=openAI_api
)

# Telegram Bot Token
BOT_TOKEN = tg_bot_token

# PDF-файл
PDF_FILE = "ITSUChatBot.pdf"


# Витягнення тексту з PDF
def get_pdf_content(pdf_path):
    reader = PdfReader(pdf_path)
    return " ".join(page.extract_text() for page in reader.pages)


# Вміст PDF для аналізу
pdf_content = get_pdf_content(PDF_FILE)

# Ключові слова для перевірки релевантності запитання
KEYWORDS = [
    # Українською
    "ІТ СТЕП Університет", "бакалаврат", "бакалаврські програми", "освітні програми бакалаврату",
    "детально про бакалаврат", "програми навчання бакалавра", "програми бакалавра", "дисципліни бакалаврату",
    "магістратура", "магістерські програми", "детально про магістратуру", "університет", "навчання", "програми",
    "детально про програми", "гуртожиток", "вступ", "студент", "сертифікат", "освіта", "стажування", "подання",
    "документи", "екзамен", "запис", "контакт", "курси", "підготовка", "рейтинги", "які іспити треба скласти",
    "що з військовим квитком", "військовий квиток", "як зв'язатися з адміністрацією", "зв'язатися з адміністрацією",
    "Штучний інтелект", "Комп'ютерні науки", "Маркетинг", "Менеджмент", "Дизайн і нові медіа",
    "Фінтех менеджмент", "прохідний бал", "ЄДЕБО", "Доуніверситетська підготовка", "ЄВІ", "НМТ",
    "освітні конференції", "менторство", "студентське ком'юніті", "ліцензія", "акредитація",
    "освітня програма", "співбесіда", "вступні іспити", "творчий конкурс", "гранти", "контракт",
    "подвійна освіта", "закордонні поїздки", "ментор", "студентські клуби", "зручна інфраструктура",
    "комфортні умови", "освітня методика", "практичні навички", "інновації", "партнери", "сучасні знання",
    "освітня платформа", "електронний кабінет", "студентський квиток", "рейтинговий список", "зарахування",
    "софт-скілс", "освітні заходи", "практичне навчання", "індивідуальні проєкти", "комп'ютерні науки",
    "штучний інтелект", "дизайн і нові медіа", "фінтех", "менеджмент", "маркетинг", "інформаційні технології",
    "професійний розвиток", "диплом", "міжнародні сертифікати", "освітні інструменти", "як вступити",
    "що робити після цього", "отримання результатів",

    # Англійською
    "IT Step University", "bachelor's degree", "bachelor's programs", "educational programs for bachelor's degree",
    "detailed bachelor's programs", "bachelor's courses", "bachelor's curriculum", "master's degree",
    "master's programs", "detailed master's programs", "university", "education", "programs", "detailed programs",
    "dormitory", "admission", "student", "certificate", "training", "internships", "application",
    "documents", "exam", "registration", "contact", "courses", "preparation", "ratings",
    "artificial intelligence", "computer science", "marketing", "management", "design and new media",
    "fintech management", "passing score", "unified state electronic database", "pre-university preparation",
    "military ID", "EVI", "national multi-test", "educational conferences", "mentorship", "student community",
    "license", "accreditation", "educational program", "interview", "entrance exams", "creative contest",
    "grants", "contract", "dual education", "study abroad", "mentor", "student clubs", "convenient infrastructure",
    "comfortable conditions", "educational methodology", "practical skills", "innovations", "partners",
    "modern knowledge", "educational platform", "electronic cabinet", "student card", "rating list", "enrollment",
    "soft skills", "educational events", "practical training", "individual projects", "professional development",
    "degree", "international certificates", "educational tools", "what exams are required",
    "what about the military ID", "how to contact the administration", "exam results", "how to enroll",
    "how to submit documents", "university contacts", "admission process"
]


# Функція для перевірки релевантності питання
def is_relevant_question(question: str) -> bool:
    question_lower = question.lower()
    question_words = question_lower.split()  # Розбиваємо на окремі слова

    log_matches = []  # Для діагностики збігів

    for keyword in KEYWORDS:
        keyword_lower = keyword.lower()

        # Якщо ключове слово повністю є в запиті
        if keyword_lower in question_lower:
            log_matches.append(f"Exact match: {keyword}")
            return True

        # Пошук збігів за словами
        for word in question_words:
            if word in keyword_lower:
                log_matches.append(f"Partial match: {keyword} -> {word}")
                return True

    # Логування збігів для діагностики
    print(f"No relevant keywords found. Matches attempted: {log_matches}")
    return False


# Функція для визначення мови відповіді
def detect_response_language(user_message: str) -> str:
    if re.search(r"[а-яіїєґ]", user_message.lower()):  # Кирилиця
        if re.search(r"[аеёиоуыэюя]", user_message):  # Російська
            return "uk"  # Українська для російських запитів
        return "uk"  # Українська для українських запитів
    return "en"  # Англійська для інших


# Функція для форматування жирного тексту для Telegram Markdown
def format_bold_text(reply: str) -> str:
    formatted_reply = re.sub(r"\*\*(.+?)\*\*", r"*\1*", reply)  # Замінює `**` на `*` для Telegram Markdown
    return formatted_reply


# Функція для команди /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Надайте запитання, яке стосується університету.")


# Функція для обробки тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text
    user_name = update.message.from_user.username
    print(f"Запит користувача (@{user_name}): {user_message}")

    # Перевірка, чи стосується питання IT Step University
    if not is_relevant_question(user_message):
        await update.message.reply_text("Будь ласка, надайте запитання, котре відноситься до IT Step University.")
        return

    try:
        response_language = detect_response_language(user_message)
        system_message = (f"Відповідай {response_language}. "
                          f"Українською для запитів українською чи російською мовами. "
                          f"Англійською для інших. Ось текст документа: {pdf_content}")
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        # Відправити повідомлення "Очікуйте"
        bot = context.bot
        sent_message = await update.message.reply_text("Запит прийнято. Очікуйте.")

        # Отримати відповідь від OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        print(f"Відповідь бота: {reply}")

        # Форматувати жирний текст для Telegram Markdown
        formatted_reply = format_bold_text(reply)

        # Оновити повідомлення з відповіддю
        await bot.edit_message_text(
            chat_id=sent_message.chat_id,
            message_id=sent_message.message_id,
            text=formatted_reply,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Помилка: {str(e)}")
        await update.message.reply_text(f"Помилка: {str(e)}")


# Основна функція запуску бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обробники
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))

    # Запуск бота
    app.run_polling()


if __name__ == "__main__":
    main()
