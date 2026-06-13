"""
PawPost — Flask application

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY="your-key-here"
    python app.py

On every boot, db.init_db() rebuilds pawpost.db from the CSVs in /data.
This is intentional for now (see db.py docstring) — when PawPost moves to
a more permanent store, this is the line to change.
"""

import os

from flask import Flask, jsonify, render_template, request

import db
from knowledge import FAQ_HINTS, PAWPOST_CONTEXT

# --- Gemini setup (new google-genai SDK) ---------------------------------
from google import genai
from google.genai import types

GEMINI_MODEL = "gemini-2.5-flash"
_gemini_client = None


def get_gemini_client():
    """Lazily create the Gemini client so the app can still boot (and the
    landing page still load) even if GEMINI_API_KEY isn't set yet."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# --- App setup -------------------------------------------------------------

app = Flask(__name__)

# Rebuild the DB from CSVs every time the app boots
db.init_db()


SERVICES = [
    {
        "name": "Dog Walking",
        "price": "£12",
        "unit": "per walk",
        "blurb": "30–60 minutes, solo or small group walks around the local park.",
        "icon": "walk",
    },
    {
        "name": "Day Care",
        "price": "£25",
        "unit": "per day",
        "blurb": "Your pet spends the day with a sitter — walks, lunch, garden time.",
        "icon": "sun",
    },
    {
        "name": "Overnight Sitting",
        "price": "£35",
        "unit": "per night",
        "blurb": "Our most popular service — a sitter stays over, often for several nights.",
        "icon": "moon",
    },
    {
        "name": "Cat Visits",
        "price": "£10",
        "unit": "per visit",
        "blurb": "Feeding, litter and a check-in for cats while you're away.",
        "icon": "cat",
    },
    {
        "name": "Pet Taxi",
        "price": "£15",
        "unit": "per trip",
        "blurb": "A lift to the vet, groomer, or to meet a sitter.",
        "icon": "car",
    },
]

AREAS = ["Leeds", "Bradford", "Wakefield", "York", "Sheffield", "Manchester"]


@app.route("/")
def index():
    conn = db.get_connection()
    sitter_count = conn.execute("SELECT COUNT(*) FROM sitters").fetchone()[0]
    customer_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    top_sitters = conn.execute(
        "SELECT name, city, rating, services FROM sitters ORDER BY rating DESC LIMIT 4"
    ).fetchall()
    conn.close()

    return render_template(
        "index.html",
        services=SERVICES,
        areas=AREAS,
        sitter_count=sitter_count,
        customer_count=customer_count,
        top_sitters=top_sitters,
        faq_hints=FAQ_HINTS,
    )


@app.route("/api/sitters")
def api_sitters():
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT sitter_id, name, city, rating, joined_date, services FROM sitters ORDER BY rating DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []  # [{role: "user"|"model", text: "..."}]

    if not message:
        return jsonify({"error": "message is required"}), 400

    client = get_gemini_client()
    if client is None:
        return jsonify(
            {
                "reply": (
                    "Thanks for your message! Our AI assistant isn't fully "
                    "switched on yet — pop your details in the booking form "
                    "and one of us will get back to you."
                )
            }
        )

    # Build conversation contents for Gemini
    contents = []
    for turn in history:
        role = "model" if turn.get("role") == "model" else "user"
        text = (turn.get("text") or "").strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=PAWPOST_CONTEXT,
                temperature=0.6,
                max_output_tokens=300,
            ),
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "Sorry, I didn't quite catch that — could you rephrase?"
    except Exception as exc:  # pragma: no cover - surfaced to the UI
        reply = (
            "Sorry, I'm having trouble answering right now. "
            "Please try again in a moment, or use our booking form."
        )
        app.logger.error("Gemini error: %s", exc)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
