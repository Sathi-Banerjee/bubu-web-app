from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os, requests, json
from openai import OpenAI
from datetime import date

# 🔐 Load environment variables
load_dotenv()

# 🔑 API Keys
client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# 🚀 Flask App
app = Flask(__name__, template_folder="templates", static_folder="static")

# 🧠 Initial chat memory
chat_history = [
    {
        "role": "system",
        "content": (
            "You are Bubu 🧸, an AI assistant created by Sathi Banerjee. "
            "Always use the current date provided by the backend. "
            "Do not assume today's date. Provide accurate weather, news, age, and web info. "
            "If you are unsure, fallback to a web search."
        )
    }
]

# ✅ Get real system date
def get_today():
    return date.today()

# 🎂 Calculate age
def calculate_age(birth_year, birth_month, birth_day):
    today = get_today()
    age = today.year - birth_year
    if (birth_month, birth_day) > (today.month, today.day):
        age -= 1
    return age

# 🌦️ Weather Info
def get_weather(city):
    if not city:
        return "⚠️ Please specify a city like 'weather in Kolkata'."
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"⚠️ Couldn't find weather for '{city}'."
        desc = res["weather"][0]["description"].capitalize()
        temp = res["main"]["temp"]
        return f"🌦️ Weather in {city.title()}: {desc}, {temp:.1f}°C"
    except Exception as e:
        return f"⚠️ [Weather Error] {e}"

# 🗞️ News Info
def get_news(topic=None):
    if topic:
        url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWS_API_KEY}"
    else:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]
        if not articles:
            return "📰 No relevant news found."
        reply = "🗞️ Top Headlines:\n"
        for a in articles:
            reply += f"🔹 {a['title']}\n{a['url']}\n"
        return reply
    except Exception as e:
        return f"⚠️ [News Error] {e}"

# 🔍 Web Search Fallback
def search_web(query):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = json.dumps({"q": query})
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers, data=data)
        results = res.json().get("organic", [])
        if not results:
            return "🔍 No relevant info found online."
        reply = "🔎 Top web results:\n"
        for r in results[:3]:
            reply += f"🔹 {r['title']}\n{r['link']}\n"
        return reply
    except Exception as e:
        return f"⚠️ [Web Search Error] {e}"

# 🏠 Home route
@app.route("/")
def home():
    return render_template("index.html")

# 🤖 Chat route
# 🤖 Chat route
@app.route("/chat", methods=["POST"])
def chat():
    import re  # you can also put this import at the top of your file

    msg = request.json.get("message", "").strip()
    chat_history.append({"role": "user", "content": msg})
    lower_msg = msg.lower()

    # 📅 Today's date
    if "date" in lower_msg or "today" in lower_msg:
        today = get_today()
        g_date = f"📅 Today is {today.strftime('%B %d, %Y')}"
        reply = f"{g_date}"
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🌤️ Weather
    if "weather" in lower_msg:
        city_match = re.search(r'weather\s*(?:in|at|of)?\s*([a-zA-Z\s]+)', msg, re.IGNORECASE)
        if city_match:
            city = city_match.group(1).strip()
        else:
            city = msg.split()[-1]
        reply = get_weather(city)
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 🗞️ News
    if "news" in lower_msg:
        topic = lower_msg.split("news")[-1].strip() or None
        reply = get_news(topic)
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 👤 Virat Kohli age
    if "virat kohli age" in lower_msg or "his age" in lower_msg:
        birth_year, birth_month, birth_day = 1988, 11, 5
        age = calculate_age(birth_year, birth_month, birth_day)
        today_str = get_today().strftime("%B %d, %Y")
        reply = f"Virat Kohli was born on November 5, 1988. As of today, {today_str}, he is {age} years old."
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    # 💬 GPT fallback
    try:
        # 🧠 Remove old date reminders from history
        chat_history[:] = [m for m in chat_history if not m.get("content", "").startswith("📅 Today is")]

        # 📅 Add today's date as system info
        today_str = f"📅 Today is {get_today().strftime('%B %d, %Y')}."
        chat_history.insert(1, {
            "role": "system",
            "content": today_str + " Always use this as the current date."
        })

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=chat_history
        )
        reply = response.choices[0].message.content.strip()

        if any(p in reply.lower() for p in ["i'm not sure", "i don't know", "can't find"]):
            reply = search_web(msg)

        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"⚠️ [Error] {str(e)}"}), 500


# 🔥 Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


