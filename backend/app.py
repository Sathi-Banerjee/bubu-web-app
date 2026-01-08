from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date, timedelta
from pathlib import Path
from PIL import Image
import pytesseract
import os, requests, json, re

# =========================
# 🔐 ENV & CONFIG
# =========================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# =========================
# 🚀 FLASK APP
# =========================
app = Flask(__name__, template_folder="templates", static_folder="static")

# =========================
# 🧠 MEMORY & PERSONALITY
# =========================
chat_history = [
    {
        "role": "system",
        "content": (
            "You are Bubu 🧸, a friendly, warm, human-like AI assistant "
            "created by Sathi Banerjee.\n\n"
            "RULES:\n"
            "- NEVER guess dates or time\n"
            "- Always rely on backend date logic\n"
            "- Always say your name is Bubu 🧸\n"
            "- Be polite, simple, and friendly\n"
            "- Do not hallucinate facts\n"
        )
    }
]

MAX_HISTORY = 12
last_intent = None
last_city = None

# =========================
# 🛠️ HELPERS
# =========================
def today():
    return date.today()

def extract_city(text):
    m = re.search(r"(?:in|at|of)\s+([a-zA-Z\s]+)", text, re.I)
    return m.group(1).strip() if m else ""

def is_greeting(text):
    return text in ["hi", "hello", "hey", "hii", "hola"]

# =========================
# 🌦️ WEATHER
# =========================
def get_weather(city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )
    try:
        r = requests.get(url, timeout=5).json()
        if r.get("cod") != 200:
            return f"😕 I couldn’t find weather for {city.title()}."

        return (
            f"🌦️ Weather in {city.title()}:\n"
            f"• Condition: {r['weather'][0]['description'].title()}\n"
            f"• Temperature: {r['main']['temp']:.1f}°C\n"
            f"• Humidity: {r['main']['humidity']}%"
        )
    except:
        return "⚠️ Weather service is unavailable right now."

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

    if not msg:
        return jsonify({"reply": "Say something 🧸"})

    chat_history.append({"role": "user", "content": msg})
    chat_history[:] = chat_history[-MAX_HISTORY:]

    # 👋 GREETING
    if is_greeting(lower):
        reply = "Heyyy! 🧸✨ How are you feeling today?"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # ❓ CONFUSED INPUT
    if lower in ["?", "ok", "okay", "yes", "yeah", "yep"]:
        reply = "😊 I’m here! What would you like to know?"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🧸 NAME
    if "your name" in lower or "who are you" in lower:
        reply = "I’m Bubu 🧸 — your friendly AI assistant created by Sathi 💙"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 📅 DATE
    if "date" in lower or "today" in lower:
        reply = f"📅 Today is {today().strftime('%B %d, %Y')}"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 📆 TOMORROW
    if "tomorrow" in lower:
        tmr = today() + timedelta(days=1)
        reply = f"📆 Tomorrow will be {tmr.strftime('%B %d, %Y')}"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🌦️ WEATHER
    if "weather" in lower:
        city = extract_city(msg)
        if city:
            last_city = city
            last_intent = None
            reply = get_weather(city)
        else:
            last_intent = "weather"
            reply = "☁️ Sure! Which city’s weather should I check?"

        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🌆 WEATHER FOLLOW-UP
    if last_intent == "weather":
        last_city = msg
        last_intent = None
        reply = get_weather(msg)
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🤖 GPT FALLBACK (SAFE)
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=chat_history,
            temperature=0.6,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception:
        return jsonify({"reply": "⚠️ I’m having trouble right now. Please try again."})

# =========================
# 📷 IMAGE OCR
# =========================
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    img_file = request.files["image"]
    path = BASE_DIR / "temp.png"
    img_file.save(path)

    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)[:2000]
        return jsonify({"text": f"📷 I found this text:\n\n{text}"})
    finally:
        if path.exists():
            path.unlink()

# =========================
# ❤️ HEALTH CHECK (RENDER)
# =========================
@app.route("/healthz")
def health():
    return "ok", 200

# =========================
# 🔥 RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
