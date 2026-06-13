# PawPost — Flask App

## Setup
```
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
python app.py
```
Visit http://localhost:5000

## How it works
- `db.py` rebuilds `pawpost.db` (SQLite) from the CSVs in `/data` every time
  the app boots. Replace this step later with a Postgres connection when you
  need data to persist permanently.
- `app.py` — Flask routes, landing page, and the `/api/chat` endpoint which
  calls Gemini 2.5 Flash via the `google-genai` SDK (`genai.Client`).
- `knowledge.py` — company background fed to the assistant as a system
  instruction, taken from the PawPost profile doc.
- `templates/index.html` + `static/` — the brown/cream landing page with
  services, areas, sitter spotlight, FAQ, and the floating chat widget.

## Next layers (not built yet)
- Booking follow-up / status lookup for customers
- Sitter payment follow-up
- Auth for sitters/customers
