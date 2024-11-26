import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PyPDF2 import PdfReader
from openai import OpenAI

# OpenAI API Key
openai = OpenAI(
    api_key="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"
)

# Telegram Bot Token
BOT_TOKEN = "8052976387:AAECahYyk789QjvjTvl7wVI0gTOLo8EbJoQ"

# PDF-файл
PDF_FILE = "ITSUChatBot.pdf"

# Витягнення тексту з PDF
def get_pdf_content(pdf_path):
    reader = PdfReader(pdf_path)
    return " ".join(page.extract_text() for page in reader.pages)

# Вміст PDF для аналізу
pdf_content = get_pdf_content(PDF_FILE)

# Ключові слова для перевірки релевантності
KEYWORDS = [
    "ІТ СТЕП Університет", "бакалаврат", "магістратура", "університет", "навчання", "програми",
    "гуртожиток", "вступ", "студент", "сертифікат", "освіта", "стажування", "подання",
    "документи", "екзамен", "запис", "контакт", "курси", "підготовка", "рейтинги",
    "Штучний інтелект", "Комп'ютерні науки", "Маркетинг", "Менеджмент", "Дизайн і нові медіа",
    "Фінтех менеджмент", "прохідний бал", "ЄДЕБО", "Доуніверситетська підготовка", "військовий квиток",
    "ЄВІ", "НМТ", "освітні конференції", "менторство", "студентське ком'юніті", "ліцензія", "акредитація",
    "IT Step University", "bachelor's degree", "master's degree", "university", "education", "programs",
    "dormitory", "admission", "student", "certificate", "training", "internships", "application",
    "documents", "exam", "registration", "contact", "courses", "preparation", "ratings",
    "artificial intelligence", "computer science", "marketing", "management", "design and new media",
    "fintech management", "passing score", "unified state electronic database", "pre-university preparation",
    "military ID", "EVI", "national multi-test", "educational conferences", "mentorship", "student community",
    "license", "accreditation"
]

# Функція для перевірки релевантності питання
def is_relevant_question(question: str) -> bool:
    return any(keyword.lower() in question.lower() for keyword in KEYWORDS)

# Функція для визначення мови відповіді
def detect_response_language(user_message: str) -> str:
    if re.search(r"[а-яіїєґ]", user_message.lower()):  # Кирилиця
        if re.search(r"[аеёиоуыэюя]", user_message):  # Російська
            return "uk"  # Українська для російських запитів
        return "uk"  # Українська для українських запитів
    return "en"  # Англійська для інших

# Функція для команди /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Задайте питання, яке стосується університету.")

# Функція для обробки тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text
    print(f"Запит користувача: {user_message}")  # Логування запиту в консоль

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
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()

        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Помилка: {str(e)}")  # Логування помилок у консоль
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
