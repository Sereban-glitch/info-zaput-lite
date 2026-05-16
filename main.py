import os
import telebot
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from ai import configure_ai, process_text, process_voice
from db import init_db, log_request, get_pending_requests, mark_replied

# Конфигурация
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

bot = telebot.TeleBot(TOKEN)

def send_mail(to_email, subject, body):
    """Отправка письма через SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        return msg.get('Message-ID', 'unknown')

def check_mail():
    """Проверка почты на наличие ответов."""
    updates = []
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            # Ищем непрочитанные письма
            _, data = mail.search(None, 'UNSEEN')
            for num in data[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = msg['Subject']
                sender = msg['From']
                in_reply_to = msg.get('In-Reply-To', '')
                
                # Здесь можно добавить логику сопоставления по In-Reply-To или теме
                updates.append(f"📩 Ответ от {sender}\nТема: {subject}")
                # Помечаем как прочитанное (автоматически при fetch RFC822)
    except Exception as e:
        print(f"IMAP Error: {e}")
    return updates

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "👋 Вітаю! Я Info-Zaput-Lite. Надсилайте текст або голос для формування запиту.")

@bot.message_handler(commands=['check'])
def manual_check(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(ADMIN_ID, "🔍 Перевіряю пошту...")
    updates = check_mail()
    if updates:
        for upd in updates: bot.send_message(ADMIN_ID, upd)
    else:
        bot.send_message(ADMIN_ID, "📭 Нових відповідей не знайдено.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id != ADMIN_ID: return
    status = bot.reply_to(message, "🤖 Обробляю текст через Gemini 2.5 Flash...")
    try:
        res = process_text(message.text)
        send_confirm_menu(message.chat.id, res)
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    if message.from_user.id != ADMIN_ID: return
    status = bot.reply_to(message, "🎧 Слухаю голос через Gemini 2.5 Flash...")
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        res = process_voice(downloaded_file)
        send_confirm_menu(message.chat.id, res)
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка аудіо: {e}")

def send_confirm_menu(chat_id, data):
    text = f"📝 *Проєкт запиту:*\n\n🏛 *Орган:* {data.get('recipientHint', 'Не вказано')}\n📂 *Тема:* {data['subject']}\n\n{data['body']}"
    # Сохраняем чернетку в памяти (упрощенно для Lite версии)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Надіслати", callback_data="send_mail"))
    markup.add(telebot.types.InlineKeyboardButton("❌ Скасувати", callback_data="cancel"))
    
    # Временное хранение данных в контексте бота (для прототипа)
    bot.last_draft = data 
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "send_mail":
        data = getattr(bot, 'last_draft', None)
        if not data: return
        
        bot.answer_callback_query(call.id, "Надсилаю...")
        try:
            # В реальности email должен быть в data или справочнике
            target_email = "publicinquiry69@gmail.com" 
            msg_id = send_mail(target_email, data['subject'], data['body'])
            log_request(msg_id, call.message.chat.id, call.from_user.id, data.get('recipientHint'), target_email, data['subject'])
            bot.edit_message_text("🚀 Запит успішно надіслано!", call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Помилка пошти: {e}")
    elif call.data == "cancel":
        bot.edit_message_text("❌ Скасовано.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    init_db()
    configure_ai()
    print("🚀 Info-Zaput-Lite (2.5 Flash) запущен!")
    bot.infinity_polling()
