import logging
import telebot
import jdatetime
import gspread
import os
from telebot import types
from oauth2client.service_account import ServiceAccountCredentials

# Logging
logging.basicConfig(level=logging.INFO)

# تنظیمات توکن و Sheet
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID"))
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# اتصال به Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = eval(GOOGLE_CREDENTIALS)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# خواندن پروژه‌ها از شیت (ردیف اول)
def get_projects():
    return sheet.row_values(1)[1:]

# شروع
@bot.message_handler(commands=["start"])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in get_projects():
        markup.add(p)
    msg = bot.send_message(message.chat.id, "نام خود را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    name = message.text
    user_states[message.chat.id] = {"name": name}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in get_projects():
        markup.add(p)
    msg = bot.send_message(message.chat.id, "پروژه‌ای که روی آن کار کردی را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_project)

def process_project(message):
    user_states[message.chat.id]["project"] = message.text
    msg = bot.send_message(message.chat.id, "چند ساعت کار کردی؟ (عدد وارد کن)")
    bot.register_next_step_handler(msg, process_hours)

def process_hours(message):
    try:
        hours = float(message.text)
    except:
        msg = bot.send_message(message.chat.id, "عدد معتبر وارد کن:")
        bot.register_next_step_handler(msg, process_hours)
        return

    state = user_states[message.chat.id]
    today = jdatetime.date.today().strftime("%Y/%m/%d")
    sheet.append_row([today, state["name"], state["project"], hours])
    bot.send_message(message.chat.id, "✅ گزارش با موفقیت ثبت شد.")
    user_states.pop(message.chat.id)

# شروع ربات
bot.polling()