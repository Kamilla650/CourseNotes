import json
import urllib.request
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings

from django.utils import timezone

from .models import PasswordResetToken, AIMessage

TOKEN_TTL_MINUTES = 30


def hash_token(raw_token):
    """Возвращает SHA-256 хеш токена."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_reset_token(user):
    """Создаёт токен восстановления пароля."""
    raw_token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_token(raw_token),
        expires_at=timezone.now() + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return raw_token


def get_token_by_raw(raw_token):
    """Находит токен по значению из ссылки."""
    return PasswordResetToken.objects.filter(
        token_hash=hash_token(raw_token)
    ).first()


def reset_password(raw_token, new_password):
    """Меняет пароль, если токен действителен."""
    token = get_token_by_raw(raw_token)

    if token is None or not token.is_valid():
        return False

    user = token.user
    user.set_password(new_password)
    user.save()

    token.used_at = timezone.now()
    token.save()

    return True


def ask_ai(message, user=None):
    """Отправляет запрос ИИ-агенту с историей диалога."""

    url = settings.LLM_BASE_URL.rstrip('/') + '/chat/completions'

    messages = []

    if user is not None:
        messages.append({
            'role': 'system',
            'content': (
                'Ты StudyBot — учебный ИИ-ассистент CourseNotes. '
                'Помогай пользователю в обучении. '
                'Отвечай на русском языке. '
                'Не выполняй учебные работы целиком за пользователя. '
                'Не отвечай на вопросы, не связанные с обучением. '
                'Не раскрывай секретные данные и технические настройки. '
                f'Роль пользователя: {user.get_role_display()}.'
            ),
        })

        history = AIMessage.objects.filter(
            user=user
        ).order_by('-created_at', '-pk')[:10]

        for item in reversed(list(history)):
            messages.append({
                'role': item.role,
                'content': item.content,
            })

    messages.append({
        'role': 'user',
        'content': message,
    })

    data = {
        'model': settings.LLM_MODEL,
        'messages': messages,
        'max_tokens': settings.LLM_MAX_TOKENS,
        'stream': False,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.LLM_API_KEY}',
        },
        method='POST',
    )

    with urllib.request.urlopen(
        request,
        timeout=settings.LLM_TIMEOUT
    ) as response:
        result = json.loads(response.read().decode('utf-8'))

    return result['choices'][0]['message']['content']