from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, raw=False, **kwargs):
    """Автоматическое создание профиля нового пользователя."""
    if created and not raw:
        Profile.objects.get_or_create(user=instance)