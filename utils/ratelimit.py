"""Small sliding-window rate limiter.

Streamlit has no request layer of its own, so limits are kept per browser
session (in session_state) for the costly actions: AI calls and uploads.
The limiter itself is plain Python so it can be unit tested.
"""
import time


class RateLimiter:
    def __init__(self, max_calls, per_seconds):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls = []

    def allow(self, now=None):
        now = time.monotonic() if now is None else now
        cutoff = now - self.per_seconds
        self.calls = [t for t in self.calls if t > cutoff]
        if len(self.calls) >= self.max_calls:
            return False
        self.calls.append(now)
        return True

    def retry_after(self, now=None):
        now = time.monotonic() if now is None else now
        if not self.calls:
            return 0
        wait = self.calls[0] + self.per_seconds - now
        return max(0, int(wait) + 1)


def session_limiter(state, name, max_calls, per_seconds):
    """Fetch (or create) a limiter stored in a session_state-like mapping."""
    key = f"_limiter_{name}"
    if key not in state:
        state[key] = RateLimiter(max_calls, per_seconds)
    return state[key]
