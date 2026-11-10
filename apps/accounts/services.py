import hashlib

from django.core.cache import cache

MAX_LOGIN_FAILURES = 5
LOCKOUT_SECONDS = 10 * 60


def _key(email):
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"login-failures:{digest}"


def login_is_locked(email):
    return cache.get(_key(email), 0) >= MAX_LOGIN_FAILURES


def record_login_failure(email):
    key = _key(email)
    try:
        cache.add(key, 0, LOCKOUT_SECONDS)
        failures = cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOCKOUT_SECONDS)
        failures = 1
    return failures >= MAX_LOGIN_FAILURES


def clear_login_failures(email):
    cache.delete(_key(email))
