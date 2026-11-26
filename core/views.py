import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .services import ask_ai
from .models import AIMessage

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'core/index.html')


def health(request):
    return JsonResponse({'status': 'ok', 'service': 'web'})


@login_required
def ai_chat(request):
    message = ''
    answer = ''
    error = ''

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()

        message = ''.join(
            char for char in message
            if char.isprintable() or char in '\n\t'
        ).strip()

        if not message:
            error = 'Сообщение не может быть пустым.'

        elif len(message) > 2000:
            error = 'Сообщение слишком длинное. Максимум 2000 символов.'

        else:
            try:
                answer = ask_ai(message, request.user)

                with transaction.atomic():
                    AIMessage.objects.create(
                        user=request.user,
                        role='user',
                        content=message,
                    )

                    AIMessage.objects.create(
                        user=request.user,
                        role='assistant',
                        content=answer,
                    )

            except Exception:
                logger.exception('Ошибка работы ИИ-агента')
                answer = ''
                error = (
                    'Сервис ИИ-агента временно недоступен. '
                    'Попробуйте позже.'
                )

    history = AIMessage.objects.filter(
        user=request.user
    ).order_by('created_at', 'pk')

    return render(request, 'core/ai_chat.html', {
        'message': message,
        'answer': answer,
        'error': error,
        'history': history,
    })