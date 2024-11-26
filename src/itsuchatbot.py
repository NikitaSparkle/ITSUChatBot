import os
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
KEYWORDS = ["IT Step University", "бакалаврат", "магістратура", "університет", "навчання", "програми",
            "гуртожиток", "вступ", "студент", "сертифікат", "освіта", "стажування", "подання",
            "документи", "екзамен", "запис", "контакт", "курси", "підготовка", "рейтинги"]


# Функція для перевірки релевантності питання
def is_relevant_question(question: str) -> bool:
    return any(keyword.lower() in question.lower() for keyword in KEYWORDS)


# Функція для команди /start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот IT Step University. Задайте питання, яке стосується університету.")


# Функція для обробки тексту від користувача
async def analyze(update: Update, context):
    user_message = update.message.text

    # Перевірка, чи стосується питання IT Step University
    if not is_relevant_question(user_message):
        await update.message.reply_text("Будь ласка, надайте запитання, котре відноситься до IT Step University.")
        return

    try:
        # Формування запиту до OpenAI API
        messages = [
            {"role": "system",
             "content": f"Ти помічник, який відповідає на запитання на основі цього тексту: {pdf_content}"},
            {"role": "user", "content": user_message}
        ]
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
    except Exception as e:
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
