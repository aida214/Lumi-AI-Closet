import streamlit as st
from database.supabase_client import supabase, is_configured


def _sync_profile(user):
    """Make sure a row exists in `profiles` for this auth user (id + email-derived username)."""
    try:
        existing = (
            supabase.table("profiles")
            .select("id")
            .eq("id", str(user.id))
            .execute()
        )
        if not existing.data:
            username = (user.email or "").split("@")[0]
            supabase.table("profiles").insert(
                {
                    "id": str(user.id),
                    "username": username,
                    "full_name": username,
                }
            ).execute()
    except Exception:
        # Profile sync failing shouldn't block login -- the rest of the
        # app degrades gracefully if a profile row is missing.
        pass


def show_auth_screen():
    left, middle, right = st.columns([1, 1.3, 1])

    with middle:
        st.markdown(
            """
            <div style="text-align:center; margin-top:30px; margin-bottom:8px;">
                <div style="font-size:2.4rem;">🩷</div>
                <h1 style="margin:6px 0 2px 0;">Lumi Closet</h1>
                <p class="lc-muted" style="font-size:1.05rem;">
                    Your personal AI fashion stylist
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not is_configured():
            st.warning(
                "Lumi Closet isn't connected to a database yet. Add "
                "`SUPABASE_URL` and `SUPABASE_ANON_KEY` to "
                "`.streamlit/secrets.toml` to enable login.",
                icon="🔌",
            )
            return

        st.markdown('<div class="lc-card">', unsafe_allow_html=True)

        menu = st.radio(
            "auth_mode",
            ["Login", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        email = st.text_input("📧 Email", placeholder="you@example.com")
        password = st.text_input(
            "🔒 Password", type="password", placeholder="At least 6 characters"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if menu == "Login":
            if st.button("✨ Login", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please enter both your email and password.")
                else:
                    try:
                        response = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
                        st.session_state.user = response.user
                        st.session_state.logged_in = True
                        _sync_profile(response.user)
                        st.success("Welcome back! 🩷")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

        else:
            if st.button("🩷 Create Account", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please enter both an email and a password.")
                elif len(password) < 6:
                    st.error("Password should be at least 6 characters.")
                else:
                    try:
                        response = supabase.auth.sign_up(
                            {"email": email, "password": password}
                        )
                        if response.user:
                            _sync_profile(response.user)
                        st.success(
                            "🎉 Account created! Check your email to verify it, "
                            "then log in."
                        )
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<p class='lc-muted' style='text-align:center; margin-top:14px; font-size:0.85rem;'>"
            "Pinterest energy, Apple polish, Seoul softness ♡"
            "</p>",
            unsafe_allow_html=True,
        )
