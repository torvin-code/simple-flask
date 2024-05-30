import threading
import os
import time
from flask import Flask, request
import requests
import trafilatura
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0'
headers = {'user-agent': USER_AGENT}

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@app.route("/")
def hello():
    return "Hello, our website will be opening soon!"


@app.route("/monitor")
def monitor():
	mess = start_telebot()
	return mess


@app.route("/api", methods=["GET"])
def api_proxy():
    api_key = request.args.get("api_key")
    url = request.args.get("url")
    if api_key != API_KEY:
        return "The requested URL was not found on the server", 404
    response = requests.get(url, headers=headers)
    return response.text, response.status_code


@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)


def start_telebot():
	mess = 'Error'
	try:
		threads_names = []
		main_thread = threading.currentThread()
		for some_thread in threading.enumerate():
			if some_thread != main_thread:
				c_p = some_thread.getName()
				threads_names.append(c_p)
		if 'telebot' not in threads_names:	
			bot_thread = threading.Thread(target=bot_polling, name='telebot', daemon=True)
			bot_thread.start()
			mess = 'Restart'
		else:
			mess = 'Ok'
	except Exception as e:
		mess = e
	return mess


def bot_polling():
    bot.infinity_polling()


if __name__ == "__main__":
	start_telebot()
	app.run(host='0.0.0.0', port=80)
