from django.core.cache import cache

AI_REQUEST_LIMIT = 10
AI_REQUEST_WINDOW = 300


def allow_ai_request(user):
    key = f'ai_rate_limit:{user.pk}'

    if cache.add(key, 1, timeout=AI_REQUEST_WINDOW):
        return True

    try:
        count = cache.incr(key)
    except ValueError:
        return cache.add(
            key, 1, timeout=AI_REQUEST_WINDOW
        )

    return count <= AI_REQUEST_LIMIT