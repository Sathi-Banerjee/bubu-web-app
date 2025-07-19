from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os

# Load .env variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# OpenAI client for OpenRouter
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# Flask app config
app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").lower().strip()

    # Predefined introduction triggers
    greetings = ["hi", "hello", "hii", "hey"]
    identity_questions = ["who created you", "who are you", "what are you"]

    if any(greet in user_input for greet in greetings) or any(q in user_input for q in identity_questions):
        reply = "Hello! I am Bubu 🧸, an AI assistant created by Sathi Banerjee. How can I help you today?"
        return jsonify({"reply": reply})

    try:
        system_message = (
            "You are Bubu 🧸, a helpful AI assistant created by Sathi Banerjee. "
            "Do not repeatedly introduce yourself. Just answer the user clearly and helpfully."
        )

        messages = [{"role": "system", "content": system_message}]
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"[Error] {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
