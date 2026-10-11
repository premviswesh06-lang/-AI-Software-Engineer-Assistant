"""AI Software Engineer Assistant backend: Flask + Groq + Firebase (Firestore).
Run:  pip install flask flask-cors groq firebase-admin python-dotenv
      python app.py
Put index.html inside a folder called  templates/  next to this file.
"""
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from groq import Groq
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---- KEYS GO IN A .env FILE (never in code) ----
# GROQ_API_KEY=your_groq_key_here
# FIREBASE_KEY_PATH=serviceAccountKey.json   (downloaded from Firebase console)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# On your laptop: reads serviceAccountKey.json. On a host (Render): paste the whole
# JSON text into an environment variable called FIREBASE_KEY_JSON instead.
_key_text = os.getenv("FIREBASE_KEY_JSON")
_cred = credentials.Certificate(json.loads(_key_text) if _key_text
                                else os.getenv("FIREBASE_KEY_PATH", "serviceAccountKey.json"))
firebase_admin.initialize_app(_cred)
db = firestore.client()

# Groq changes its model list often. The app tries these in order.
# To force one, add  GROQ_MODEL=model-name  to your .env file.
MODELS = [m for m in [os.getenv("GROQ_MODEL"), "openai/gpt-oss-120b", "openai/gpt-oss-20b"] if m]


def ask_groq(messages):
    last = None
    for m in MODELS:
        try:
            return client.chat.completions.create(model=m, messages=messages).choices[0].message.content
        except Exception as e:
            print(f"Model {m} failed:", e)
            last = e
    raise last
PROMPTS = {
    "ask": ("ask", "You are a programming tutor for beginners. Answer in at most 5 short sentences. Add one short code block only if it helps. No greetings, no extra tips."),
    "debug": ("debugging", "You are a debugging assistant. Reply in exactly this format and nothing else:\n**Problem:** one or two plain sentences.\n**Fixed code:** then one code block with the corrected code. No intro, no extra advice."),
    "gen": ("code_generation", "You are a code generator. Reply with ONLY one code block containing short, clear comments. No introduction, no explanation, no run instructions, no text before or after the code block."),
    "explain": ("explanation", "Explain the code line by line. Use one short line per code line in the form 'Line N: ...' and then one sentence starting with 'Summary:'. No intro, no code repetition."),
}


def handle(kind):
    data = request.get_json(force=True)
    query, lang = data.get("query", "").strip(), data.get("language", "Python")
    if not query:
        return jsonify(error="Empty query"), 400
    qtype, system = PROMPTS[kind]
    try:
        out = ask_groq([{"role": "system", "content": f"{system} Language: {lang}."},
                        {"role": "user", "content": query}])
    except Exception as e:
        print("GROQ ERROR:", e)
        return jsonify(error="Groq error: " + str(e)), 500
    try:
        db.collection("queries").add({
            "user_query": query, "response": out, "query_type": qtype,
            "programming_language": lang, "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        print("FIREBASE SAVE ERROR (answer still returned):", e)
    return jsonify(response=out)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/<kind>")
def api(kind):
    if kind not in PROMPTS:
        return jsonify(error="Unknown feature"), 404
    return handle(kind)


@app.get("/api/history")
def history():
    docs = db.collection("queries").order_by("created_at", direction=firestore.Query.DESCENDING).limit(100).stream()
    return jsonify([{**d.to_dict(), "id": d.id, "created_at": d.to_dict()["created_at"].isoformat()} for d in docs])


@app.get("/api/stats")
def stats():
    counts = {}
    for d in db.collection("queries").stream():
        t = d.to_dict()["query_type"]
        counts[t] = counts.get(t, 0) + 1
    return jsonify(total=sum(counts.values()), by_type=counts)


if __name__ == "__main__":
    app.run(debug=True)
