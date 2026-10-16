# Security

## Reporting a problem

Open a private security advisory on the GitHub repository, or email the maintainer. Please do not post
details in a public issue.

## What protects user data

- Only the Supabase anon key is used by the app. The service role key must never be added to secrets or code.
- Row Level Security is enabled on every table with policies that compare `user_id` to `auth.uid()`.
  Tables without their own `user_id` (`outfit_items`) check ownership through their parent rows.
  Policies also stop a user linking another user's wardrobe item or outfit.
- Storage policies only allow uploads, updates and deletes inside a folder named after the signed-in user.
- Each browser session gets its own Supabase client, so one visitor's login can never change another's.
- Every piece of user or database text placed in HTML goes through `utils.ui.esc`. AI replies are rendered as
  Markdown, never as raw HTML.
- Uploaded photos are re-encoded as JPEG, which drops metadata and anything that is not image data. Size and
  type are checked in the app and again by the storage bucket.
- CSV export prefixes cells that start with `=`, `+`, `-` or `@` so spreadsheets do not run them as formulas.
- Login, sign-up, AI tagging, chat and uploads are rate limited per session.
- Error details are hidden from users unless `APP_ENV=development`. Sentry is configured without personal data.

## Operating it safely

- Keep `.streamlit/secrets.toml` and `.env` out of Git (they are in `.gitignore`). Rotate any key that was ever committed.
- Keep Supabase email confirmation on in production and set a minimum password length of 8 in Auth settings.
- Review Dependabot pull requests weekly.

## Known gaps

Rate limits are per session, not per IP. Photos are in a public bucket. There is no multi-factor sign-in
or account deletion screen yet.
