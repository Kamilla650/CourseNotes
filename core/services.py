import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import PasswordResetToken

TOKEN_TTL_MINUTES = 30  # срок жизни токена


def hash_token(raw_token):
    """Возвращает SHA-256 хеш токена (64 символа)."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_reset_token(user):
    """Создаёт токен. В базу сохраняется только хеш, сам токен отправляется письмом."""
    raw_token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_token(raw_token),
        expires_at=timezone.now() + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return raw_token


def get_token_by_raw(raw_token):
    """Находит токен по значению из ссылки."""
    return PasswordResetToken.objects.filter(token_hash=hash_token(raw_token)).first()


def reset_password(raw_token, new_password):
    """Меняет пароль, если токен действителен, и отмечает токен как использованный."""
    token = get_token_by_raw(raw_token)
    if token is None or not token.is_valid():
        return False
    user = token.user
    user.set_password(new_password)  # новый пароль сохраняется только в виде хеша
    user.save()
    token.used_at = timezone.now()  # токен становится одноразовым
    token.save()
    return True
