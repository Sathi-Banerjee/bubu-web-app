from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date
from pathlib import Path
from PIL import Image
import pytesseract
import os, requests, json, re

# =========================
# 🔐 ENV & CONFIG
# =========================
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# =========================
# 🚀 FLASK APP
# =========================
app = Flask(__name__, template_folder="templates", static_folder="static")

# =========================
# 🧠 MEMORY
# =========================
chat_history = [
    {
        "role": "system",
        "content": (
            "You are Bubu 🧸, a warm, friendly, emotionally intelligent AI assistant "
            "created by Sathi Banerjee.\n"
            "Talk naturally like a human. Be caring and friendly. "
            "Never say you lack real-time data."
        )
    }
]

MAX_HISTORY = 10
last_intent = None
last_city = None

# =========================
# 🛠️ HELPERS
# =========================
def get_today():
    return date.today()

def extract_city(text):
    match = re.search(r"(?:in|at|of)\s+([a-zA-Z\s]+)", text, re.I)
    return match.group(1).strip() if match else ""

def is_greeting(text):
    return any(w in text for w in [
        "hi", "hello", "hey", "hii", "hola", "good morning", "good evening"
    ])

def detect_emotion(text):
    if any(w in text for w in ["sad", "cry", "lonely", "depressed", "tired"]):
        return "sad"
    if any(w in text for w in ["happy", "excited", "great", "awesome"]):
        return "happy"
    if any(w in text for w in ["angry", "mad", "annoyed"]):
        return "angry"
    return None

def is_news_keyword(text):
    return "news" in text

# =========================
# 🌦️ WEATHER
# =========================
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"Hmm 🤔 I couldn’t find weather for {city.title()}."

        desc = res["weather"][0]["description"].capitalize()
        temp = res["main"]["temp"]
        hum = res["main"]["humidity"]

        return (
            f"🌦️ Weather in {city.title()}:\n"
            f"• Condition: {desc}\n"
            f"• Temperature: {temp:.1f}°C\n"
            f"• Humidity: {hum}%"
        )
    except:
        return "Oops 😵 weather service is having trouble."

# =========================
# 🗞️ NEWS
# =========================
def get_news(topic=None):
    url = (
        f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWS_API_KEY}"
        if topic else
        f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    )
    try:
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]

        if not articles:
            return "No news right now 🗞️"

        reply = "📰 Here’s the latest:\n\n"
        for a in articles:
            reply += f"🔹 {a['title']}\n{a['url']}\n\n"
        return reply
    except:
        return "News service is unavailable 😴"

# =========================
# 🔍 WEB SEARCH
# =========================
def search_web(query):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = json.dumps({"q": query})
    res = requests.post("https://google.serper.dev/search", headers=headers, data=data)
    results = res.json().get("organic", [])[:3]

    if not results:
        return "I couldn’t find anything useful 😔"

    reply = "🔎 I found this:\n\n"
    for r in results:
        reply += f"🔹 {r['title']}\n{r['link']}\n\n"
    return reply

# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# 🤖 CHAT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    global last_intent, last_city

    msg = request.json.get("message", "").strip()
    lower = msg.lower()

    chat_history.append({"role": "user", "content": msg})
    chat_history[:] = chat_history[-MAX_HISTORY:]

    # 👋 Greeting
    if is_greeting(lower):
        reply = "Heyyy! 🧸✨ How are you feeling today?"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 💖 Emotion
    emotion = detect_emotion(lower)
    if emotion == "sad":
        reply = "Aww 🫂 I’m here for you. Want to talk about it?"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    if emotion == "happy":
        reply = "That’s lovely 😄✨ Tell me more!"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    if emotion == "angry":
        reply = "I can feel the frustration 😤 I’m listening."
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🌦️ WEATHER REQUEST
    if "weather" in lower:
        city = extract_city(msg)

        if city:
            last_city = city
            reply = get_weather(city)
            last_intent = None
        else:
            last_intent = "weather"
            reply = "Sure ☁️ Which city’s weather should I check?"

        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🌆 WEATHER FOLLOW-UP
    if last_intent == "weather":
        city = msg.strip()
        last_city = city
        reply = get_weather(city)
        last_intent = None

        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # ❓ WHERE?
    if lower in ["where", "where?", "which place"] and last_city:
        reply = f"In {last_city.title()} 🌆"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🗞️ NEWS
    if is_news_keyword(lower):
        reply = get_news()
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 📅 DATE
    if "date" in lower or "today" in lower:
        reply = f"📅 Today is {get_today().strftime('%B %d, %Y')}"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🤖 GPT FALLBACK
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=chat_history,
            temperature=0.8,
            max_tokens=800
        )

        reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error 😢 {e}"}), 500

# =========================
# 📷 IMAGE OCR
# =========================
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    image = request.files["image"]
    os.makedirs("temp", exist_ok=True)
    path = os.path.join("temp", image.filename)
    image.save(path)

    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)[:2000]
        return jsonify({"text": f"📷 I found this text:\n\n{text}"})
    finally:
        os.remove(path)

# =========================
# 🔥 RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
