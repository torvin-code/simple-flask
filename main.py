import os
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0'
headers = {'user-agent': USER_AGENT}

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, our website will be opening soon!"

@app.route("/api", methods=["GET"])
def api_proxy():
    api_key = request.args.get("api_key")
    url = request.args.get("url")

    if api_key != API_KEY:
        return "The requested URL was not found on the server", 404

    response = requests.get(url, headers=headers)
    return response.text, response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)