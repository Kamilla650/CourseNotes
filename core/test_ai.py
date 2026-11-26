import json
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.models import User, AIMessage
from core.services import ask_ai


class AIAgentTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Тестовый студент',
            password='TestPassword123!'
        )
        self.client.force_login(self.user)

    @patch('core.services.urllib.request.urlopen')
    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError('timed out')

        response = self.client.post('/ai-chat/', {
            'message': 'Что такое Python?'
        })

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Сервис ИИ-агента временно недоступен'
        )

        self.assertEqual(
            AIMessage.objects.filter(user=self.user).count(),
            0
        )

    @override_settings(
        LLM_BASE_URL='https://test-provider.example/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
        LLM_TIMEOUT=60,
        LLM_MAX_TOKENS=256
    )
    @patch('core.services.urllib.request.urlopen')
    def test_provider_switch(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value

        mock_response.read.return_value = json.dumps({
            'choices': [
                {
                    'message': {
                        'content': 'Тестовый ответ'
                    }
                }
            ]
        }).encode('utf-8')

        answer = ask_ai('Что такое Python?', self.user)

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode('utf-8'))

        self.assertEqual(
            request.full_url,
            'https://test-provider.example/v1/chat/completions'
        )

        self.assertEqual(
            request.get_header('Authorization'),
            'Bearer test-api-key'
        )

        self.assertEqual(payload['model'], 'test-model')
        self.assertEqual(payload['max_tokens'], 256)
        self.assertEqual(mock_urlopen.call_args.kwargs['timeout'], 60)
        self.assertEqual(answer, 'Тестовый ответ')