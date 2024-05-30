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
GEMINI_TOKEN = os.getenv('GEMINI_TOKEN')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
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


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "gemini":
        message_id = call.message.message_id
        chat_id = call.message.chat.id
        text = call.message.text
        substring = "http"
        if substring in text:
            lines = text.split("\n")
            link = lines[-1].strip()
            if link.startswith(substring):
                text = lines[0].replace('[Перевод]', '').strip()
                if "habr.com" in link:
                    link = link.split('?')[0]
                text_article = parser(link)
                if text_article is None:
                    return
                promt = f"Сделай краткое изложение (2500-3000 символа) статьи: {text_article}"
                text_gemini = gemini_send_message(promt)
                try:
                    new_text = f"{text}\n\n{text_gemini}\n\n{link}"
                    if len(new_text) > 4000:
                        splitted_text = telebot.util.smart_split(new_text, chars_per_string=4000)
                        chank_marker = 1
                        chank_title = "Часть "
                        for text_sm in splitted_text:
                            if chank_marker > 1:
                                text_sm = chank_title + str(chank_marker) + "\n\n" + text_sm
                            try:
                                bot.send_message(chat_id, text_sm, parse_mode='Markdown', reply_markup=keyboard())
                            except Exception as e:
                                text_sm = text_sm.replace("*", "")
                                bot.send_message(chat_id, text_sm, parse_mode='HTML', reply_markup=keyboard())
                            chank_marker += 1
                    else:
                        try:
                            bot.edit_message_text(new_text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard())
                        except Exception as e:
                            text_gemini = text_gemini.replace("*", "")
                            new_text = f"<strong>{text}</strong>\n\n{text_gemini}\n\n{link}"
                            bot.edit_message_text(new_text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard())
                except Exception as e:
                    try:
                        new_text = f"{text}\n\nОшибка отправки ответа в Телеграм\n\n<a href=\"{link}\">{link}</a>"
                        bot.edit_message_text(new_text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard())
                    except:
                        pass


@bot.channel_post_handler(content_types=['text'])
def new_channel_post(message):
    bot.edit_message_text(message.text, message.chat.id, message.message_id, parse_mode='HTML', reply_markup=keyboard())


def gemini_send_message(promt):
    answer = 'Неизвестная ошибка'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_TOKEN}'
    data = {
        "contents":[{"role":"user", "parts":[{"text": "Always answer in Russian"}]},{"role":"user", "parts":[{"text":promt}]}],
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        data = response.json()
        try:
            answer = data['candidates'][0]['content']['parts'][0]['text']
        except:
            answer = str(data)
    else:
        answer = f"Ошибка запроса, код ответа: {response.status_code}"  
    return answer  


def parser(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            html = response.text
            if len(html) > 0:
                text = trafilatura.extract(html)
                if text is not None:
                    if len(text) > 0:
                        return text
    except:
        pass


def keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Отправить Gemini", callback_data="gemini"))
    return markup


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
