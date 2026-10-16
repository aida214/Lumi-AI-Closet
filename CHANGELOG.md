# Changelog

## 2.0.0

Rebuilt for production use.

Fixed
- Shared Supabase client let one visitor's login affect another visitor. Now one client per session.
- AI tagging never worked: it used the retired `gemini-1.5-flash` through the deprecated `google-generativeai`
  package and hid the error. Now uses `google-genai`, a configurable model and a colour-detection fallback.
- Uploads failed without storage policies. Policies and the bucket are now in `schema.sql`.
- Dashboard showed invented weather and an invented "combinations" number. Both are replaced with real data.
- Planner wrote to the database on every rerun and mixed up outfits with the same title.
- Chat loaded the oldest 50 messages instead of the newest, and rendered model output as raw HTML.
- Deleting a piece left its photo in storage.
- Deprecated `use_container_width` replaced with `width`.

Added
- Wear tracking, insights, cost per wear, weekly planner navigation, packing from real forecasts, CSV export,
  password change, search, filters, sorting, pagination, favourites for looks.
- Weather-aware outfit engine with colour harmony and recency rules.
- Rate limiting, logging, optional Sentry, health check, Dockerfile, CI, Dependabot, 49 automated tests.
- New visual design: dusty rose and taupe palette, handwritten display type, pill chips.
