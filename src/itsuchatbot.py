import os
import re
from difflib import SequenceMatcher

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PyPDF2 import PdfReader
from openai import OpenAI

from src.keys import openAI_api, tg_bot_token

# OpenAI API Key
openai = OpenAI(api_key=openAI_api)

# Telegram Bot Token
BOT_TOKEN = tg_bot_token

# # PDF-файл
# PDF_FILE = "ITSUChatBot.pdf"


# Витягнення тексту з PDF
# def get_pdf_content(pdf_path):
#     reader = PdfReader(pdf_path)
#     return " ".join(page.extract_text() for page in reader.pages)


# # Вміст PDF для аналізу
# pdf_content = get_pdf_content(PDF_FILE)

#txt-file
TXT_FILE = "ITSUChatBot2.txt"

# Завантаження тексту з файлу ITSUChatBot2.txt
def get_text_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

txt_content = get_text_content(TXT_FILE)


# Ключові слова для перевірки релевантності запитання
# KEYWORDS = [
#     # Українською
#     "ІТ СТЕП Університет", "бакалаврат", "бакалаврські програми", "освітні програми бакалаврату",
#     "детально про бакалаврат", "програми навчання бакалавра", "програми бакалавра", "дисципліни бакалаврату",
#     "магістратура", "магістерські програми", "детально про магістратуру", "університет", "навчання", "програми",
#     "детально про програми", "гуртожиток", "вступ", "студент", "сертифікат", "освіта", "стажування", "подання",
#     "документи", "екзамен", "запис", "контакт", "курси", "підготовка", "рейтинги", "які іспити треба скласти",
#     "що з військовим квитком", "військовий квиток", "як зв'язатися з адміністрацією", "зв'язатися з адміністрацією",
#     "Штучний інтелект", "Комп'ютерні науки", "Маркетинг", "Менеджмент", "Дизайн і нові медіа",
#     "Фінтех менеджмент", "прохідний бал", "ЄДЕБО", "Доуніверситетська підготовка", "ЄВІ", "НМТ",
#     "освітні конференції", "менторство", "студентське ком'юніті", "ліцензія", "акредитація",
#     "освітня програма", "співбесіда", "вступні іспити", "творчий конкурс", "гранти", "контракт",
#     "подвійна освіта", "закордонні поїздки", "ментор", "студентські клуби", "зручна інфраструктура",
#     "комфортні умови", "освітня методика", "практичні навички", "інновації", "партнери", "сучасні знання",
#     "освітня платформа", "електронний кабінет", "студентський квиток", "рейтинговий список", "зарахування",
#     "софт-скілс", "освітні заходи", "практичне навчання", "індивідуальні проєкти", "комп'ютерні науки",
#     "штучний інтелект", "дизайн і нові медіа", "фінтех", "менеджмент", "маркетинг", "інформаційні технології",
#     "професійний розвиток", "диплом", "міжнародні сертифікати", "освітні інструменти", "як вступити",
#     "що робити після цього", "отримання результатів",
#
#     # Англійською
#     "IT Step University", "bachelor's degree", "bachelor's programs", "educational programs for bachelor's degree",
#     "detailed bachelor's programs", "bachelor's courses", "bachelor's curriculum", "master's degree",
#     "master's programs", "detailed master's programs", "university", "education", "programs", "detailed programs",
#     "dormitory", "admission", "student", "certificate", "training", "internships", "application",
#     "documents", "exam", "registration", "contact", "courses", "preparation", "ratings",
#     "artificial intelligence", "computer science", "marketing", "management", "design and new media",
#     "fintech management", "passing score", "unified state electronic database", "pre-university preparation",
#     "military ID", "EVI", "national multi-test", "educational conferences", "mentorship", "student community",
#     "license", "accreditation", "educational program", "interview", "entrance exams", "creative contest",
#     "grants", "contract", "dual education", "study abroad", "mentor", "student clubs", "convenient infrastructure",
#     "comfortable conditions", "educational methodology", "practical skills", "innovations", "partners",
#     "modern knowledge", "educational platform", "electronic cabinet", "student card", "rating list", "enrollment",
#     "soft skills", "educational events", "practical training", "individual projects", "professional development",
#     "degree", "international certificates", "educational tools", "what exams are required",
#     "what about the military ID", "how to contact the administration", "exam results", "how to enroll",
#     "how to submit documents", "university contacts", "admission process"
# ]


# Функція для перевірки релевантності питання
# def is_relevant_question(question: str) -> bool:
#     question_lower = question.lower()
#     for keyword in KEYWORDS:
#         if keyword.lower() in question_lower:
#             return True
#     return False


# Функція для визначення мови відповіді
def detect_response_language(user_message: str) -> str:
    if re.search(r"[а-яіїєґ]", user_message.lower()):  # Кирилиця
        return "uk"  # Українська
    return "en"  # Англійська


# Функція для форматування тексту в Markdown v2
def format_markdown_v2(reply: str) -> str:
    # Екранування спеціальних символів Telegram Markdown v2
    special_characters = r"_*[]()~`>#+-=|{}.!"
    for char in special_characters:
        reply = reply.replace(char, f"\\{char}")
    # Замінюємо **bold** на формат для Markdown v2
    reply = re.sub(r"\*\*(.+?)\*\*", r"*\1*", reply)
    return reply



# Функція для команди /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Надайте запитання, яке стосується університету.")


# Функція для обробки тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text
    user_name = update.message.from_user.username
    print(f"Запит користувача (@{user_name}): {user_message}")


    try:
        response_language = detect_response_language(user_message)
        system_message = (
            "Ти Telegram-бот, створений для відповіді на запитання про ІТ Степ Університет. "
            "Твоє завдання: "
            "1. Оціни релевантність запитання користувача стосовно університету. "
            "2. Якщо запитання стосується університету, знайди відповідь, використовуючи текст документа 'ITSUChatBot2.txt'. "
            f"Відповідай {response_language} мовою. Ось текст документа для використання: {txt_content}. "
            f"Запитання користувача: {user_message}"
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        bot = context.bot
        sent_message = await update.message.reply_text("Запит прийнято. Очікуйте...")

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        print(f"Відповідь бота: {reply}")

        # Екранування спеціальних символів у відповіді
        safe_reply = format_markdown_v2(reply)
        await bot.edit_message_text(
            chat_id=sent_message.chat_id,
            message_id=sent_message.message_id,
            text=safe_reply,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        print(f"Помилка: {str(e)}")
        await update.message.reply_text(f"Помилка: {str(e)}")


# Основна функція запуску бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))

    app.run_polling()


if __name__ == "__main__":
    main()
