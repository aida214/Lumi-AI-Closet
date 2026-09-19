<<<<<<< HEAD
# 🩷 Lumi Closet

Your personal AI fashion stylist & digital wardrobe — redesigned with a
soft Korean/coquette aesthetic (blush pink, lavender, cream, glassy
rounded cards, pill buttons) on top of the original Streamlit +
Supabase backend.

## Run it

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# fill in SUPABASE_URL / SUPABASE_ANON_KEY (and optionally the two AI keys)
streamlit run app.py
```

Then, in your Supabase project's SQL editor, run `schema.sql` (safe to
re-run — every statement is `if not exists` / idempotent). It also
turns on Row Level Security, so make sure you're using the **anon**
key, not the service-role key, in secrets.toml.

Finally, create a **public** storage bucket named `wardrobe` (Storage →
New bucket) if it doesn't already exist — that's where clothing
photos are uploaded to.

## What's here

- `app.py` — entrypoint: auth gate, theme, sidebar navigation, page routing
- `app_pages/` — dashboard, wardrobe, AI stylist, outfit builder, saved
  looks, weekly planner, packing assistant, profile
- `components/` — clothing card, upload form, auth screen, sidebar nav,
  metric row
- `database/supabase_client.py` — the one shared Supabase client
- `utils/theme.py` — the design system (colors, type, component CSS)
- `utils/autotagger.py` — Gemini-powered photo tagging, with a graceful
  no-op fallback if `GEMINI_API_KEY` isn't set
- `schema.sql` — table definitions + RLS policies

## What changed from the original

Preserved as-is: the Supabase schema's shape, the upload → AI-tag →
save flow, the wardrobe search/filter logic, the favorite/edit/delete
actions, and manual (non-native-multipage) navigation.

Fixed:
- **Two conflicting Supabase clients.** `app.py` created its own client
  with the anon key for auth, while every page imported a *second*
  client built with the **service-role key** — which bypasses Row
  Level Security entirely and has no business running client-side.
  There's now one shared client (anon key), and RLS policies (added to
  `schema.sql`) enforce that a user can only see their own data.
- **The service key was being printed to the console** in
  `supabase_client.py` — removed.
- **`wardrobe` had no `name` column**, even though the upload form
  always tried to save one — every item's name was silently dropped.
  Added the column.
- **The `pages/` package name collided with Streamlit's automatic
  multipage feature** (a folder literally named `pages/` next to
  `app.py` gets auto-detected and given its own sidebar page list,
  fighting with this app's manual navigation). Renamed to `app_pages/`.
- **`requirements.txt` was a raw `pip freeze` from a Windows machine** —
  it pinned Windows-only packages (`pywin32`, `pypiwin32`, `comtypes`,
  `pyttsx3`) that fail to install on Linux/macOS/Streamlit Cloud, plus
  ~2GB of unrelated ML libraries (TensorFlow, PyTorch, LangChain,
  OpenCV, scikit-learn) nothing in the app imports. Trimmed to what's
  actually used.

Added: outfit builder, saved looks (Pinterest-style grid), weekly
planner, packing assistant, profile page with style preferences, the
AI stylist chat UI with a working chat-history table and a graceful
fallback when no OpenAI key is set, and the full visual redesign.
=======
# Lumi-AI-Closet
>>>>>>> be9a7354d94094fa5848041192c4fd144ea2af01
