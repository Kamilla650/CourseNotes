from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class APITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com',
            full_name='Тестовый пользователь',
            role='student',
            is_active=True,
        )
        self.user.set_password('TestPassword123!')
        self.user.save()

    def test_login_success(self):
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'test@example.com',
                'password': 'TestPassword123!',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'test@example.com',
                'password': 'WrongPassword',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_notes_without_token(self):
        response = self.client.get('/api/notes/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_notes_with_token(self):
        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )

        response = self.client.get('/api/notes/')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_access_denied(self):
        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )

        response = self.client.get('/api/admin/users/')

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )