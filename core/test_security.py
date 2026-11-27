from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from core.rate_limit import allow_ai_request

User = get_user_model()


class AIRateLimitTests(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='security@example.com',
            full_name='Тестовый студент',
            password='TestPassword123!'
        )
        self.client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    @patch('core.views.ask_ai')
    def test_ai_rate_limit(self, mock_ai):
        mock_ai.return_value = 'Тестовый ответ'

        for i in range(10):
            response = self.client.post(
                '/ai-chat/',
                {'message': 'Тестовый запрос'}
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/ai-chat/',
            {'message': 'Одиннадцатый запрос'}
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(mock_ai.call_count, 10)

        print('\nRATE LIMIT: 10 requests allowed')
        print('Request 11: HTTP 429')

    def test_rate_limit_user_isolation(self):
        second_user = User.objects.create_user(
            email='second@example.com',
            full_name='Второй студент',
            password='TestPassword123!'
        )

        for i in range(10):
            self.assertTrue(allow_ai_request(self.user))

        self.assertFalse(allow_ai_request(self.user))
        self.assertTrue(allow_ai_request(second_user))

        print('\nUSER ISOLATION: OK')