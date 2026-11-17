import hashlib
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import PasswordResetToken

from .decorators import role_required
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm

User = get_user_model()
logger = logging.getLogger(__name__)

# Один и тот же ответ для существующего и несуществующего email
NEUTRAL_MESSAGE = 'Если аккаунт с таким email существует, письмо отправлено.'


def hash_token(raw_token):
    """В базе хранится только SHA-256 от токена, а не сам токен."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно.')
            return redirect('profile')
        messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Вы вошли в систему.')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()},
                    require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('profile')
        messages.error(request, 'Неверный email или пароль.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            user = User.objects.filter(email__iexact=email, is_active=True).first()

            if user:
                raw_token = secrets.token_urlsafe(32)
                lifetime = timedelta(minutes=settings.PASSWORD_RESET_MINUTES)
                with transaction.atomic():
                    # Старые неиспользованные токены пользователя отключаются
                    PasswordResetToken.objects.filter(
                        user=user, used_at__isnull=True
                    ).update(used_at=timezone.now())
                    PasswordResetToken.objects.create(
                        user=user,
                        token_hash=hash_token(raw_token),
                        expires_at=timezone.now() + lifetime,
                    )

                reset_url = request.build_absolute_uri(
                    reverse('reset_password', kwargs={'token': raw_token})
                )
                try:
                    send_mail(
                        'Восстановление пароля CourseNotes',
                        f'Здравствуйте, {user.full_name}!\n\n'
                        f'Для смены пароля перейдите по ссылке:\n{reset_url}\n\n'
                        f'Ссылка действует {settings.PASSWORD_RESET_MINUTES} минут '
                        f'и работает один раз.\n'
                        f'Если вы не запрашивали смену пароля, проигнорируйте это письмо.',
                        None,  # отправитель берётся из DEFAULT_FROM_EMAIL
                        [user.email],
                        fail_silently=False,
                    )
                except (SMTPException, OSError):
                    # Ошибку пишем только в журнал: если показать её пользователю,
                    # по ней можно узнать, что такой email зарегистрирован
                    logger.exception('Не удалось отправить письмо для сброса пароля')

            messages.success(request, NEUTRAL_MESSAGE)
            return redirect('login')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, token):
    reset_token = (
        PasswordResetToken.objects.select_related('user')
        .filter(token_hash=hash_token(token))
        .first()
    )
    if not reset_token or not reset_token.is_valid():
        messages.error(
            request, 'Ссылка недействительна или истёк её срок действия. Запросите новую.'
        )
        return redirect('forgot_password')

    user = reset_token.user
    if request.method == 'POST':
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            with transaction.atomic():
                user.set_password(form.cleaned_data['password'])
                user.save(update_fields=['password'])
                # Токен становится использованным, повторно по ссылке зайти нельзя
                PasswordResetToken.objects.filter(
                    user=user, used_at__isnull=True
                ).update(used_at=timezone.now())
            messages.success(request, 'Пароль успешно изменён. Войдите с новым паролем.')
            return redirect('login')
    else:
        form = ResetPasswordForm(user)
    return render(request, 'accounts/reset_password.html', {'form': form})