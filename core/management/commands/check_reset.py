from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import PasswordResetToken, User
from core.services import create_reset_token, reset_password


class Command(BaseCommand):
    help = 'Проверка механизма восстановления пароля'

    def handle(self, *args, **options):
        user = User.objects.create_user('test@coursenotes.ru', 'Тестовый пользователь', password='old_pass_123')

        raw_token = create_reset_token(user)
        token = PasswordResetToken.objects.get(user=user)
        self.stdout.write(f'1. Токен для ссылки в письме: {raw_token[:12]}...')
        self.stdout.write(f'2. В базе хранится только хеш: {token.token_hash[:24]}... (длина {len(token.token_hash)})')
        self.stdout.write(f'3. Токен действует до: {timezone.localtime(token.expires_at):%d.%m.%Y %H:%M}')

        self.stdout.write(f'4. Первая смена пароля по ссылке: {reset_password(raw_token, "new_pass_456")}')
        self.stdout.write(f'5. Повторная смена по той же ссылке: {reset_password(raw_token, "other_pass")}')

        user.refresh_from_db()
        self.stdout.write(f'6. Новый пароль подходит: {user.check_password("new_pass_456")}')
        self.stdout.write(f'7. Пароль в базе хранится как хеш: {user.password[:30]}...')

        user.delete()
        self.stdout.write(self.style.SUCCESS('Проверка завершена, тестовый пользователь удалён'))
