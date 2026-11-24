import hashlib
import secrets

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Note, PasswordResetToken, User

from .permissions import IsAdmin
from .serializers import (
    NoteSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

RESET_MINUTES = 30


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class LoginView(APIView):
    """Авторизация и получение JWT-токенов."""

    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Не указаны email и/или пароль.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            email=email,
            password=password,
        )

        if not user:
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """Отправка ссылки для восстановления пароля."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(
            data=request.data
        )

        if serializer.is_valid():
            email = serializer.validated_data['email']

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user:
                raw_token = secrets.token_urlsafe(32)

                PasswordResetToken.objects.create(
                    user=user,
                    token_hash=_hash_token(raw_token),
                    expires_at=(
                        timezone.now()
                        + timezone.timedelta(minutes=RESET_MINUTES)
                    ),
                )

                reset_url = request.build_absolute_uri(
                    reverse(
                        'reset_password',
                        kwargs={'token': raw_token},
                    )
                )

                send_mail(
                    subject='Сброс пароля CourseNotes',
                    message=(
                        'Здравствуйте!\n\n'
                        'Вы запросили восстановление пароля '
                        'в CourseNotes.\n\n'
                        'Для установки нового пароля '
                        'перейдите по ссылке:\n\n'
                        f'{reset_url}\n\n'
                        'Ссылка действительна 30 минут.\n\n'
                        'Если вы не запрашивали восстановление '
                        'пароля, проигнорируйте это письмо.\n\n'
                        'С уважением,\n'
                        'Команда CourseNotes'
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

            return Response(
                {
                    'message':
                    'Ссылка для сброса пароля отправлена на email.'
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PasswordResetConfirmView(APIView):
    """Установка нового пароля."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(
            data=request.data
        )

        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data[
                'new_password'
            ]

            reset = PasswordResetToken.objects.filter(
                token_hash=_hash_token(token),
                used_at__isnull=True,
            ).first()

            if not reset or not reset.is_valid():
                return Response(
                    {
                        'detail':
                        'Токен недействителен или срок его '
                        'действия истёк.'
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            user = reset.user
            user.set_password(new_password)
            user.save()

            reset.used_at = timezone.now()
            reset.save()

            return Response(
                {'message': 'Пароль успешно изменён.'},
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class NoteListCreateView(APIView):
    """Получение списка и создание конспектов."""

    def get(self, request):
        notes = Note.objects.all()
        serializer = NoteSerializer(notes, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = NoteSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(author=request.user)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class NoteDetailView(APIView):
    """Просмотр, изменение и удаление конспекта."""

    def _get_or_404(self, pk):
        try:
            return Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk):
        note = self._get_or_404(pk)

        if note is None:
            return Response(
                {'detail': 'Конспект не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            NoteSerializer(note).data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        note = self._get_or_404(pk)

        if note is None:
            return Response(
                {'detail': 'Конспект не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = NoteSerializer(
            note,
            data=request.data,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def delete(self, request, pk):
        note = self._get_or_404(pk)

        if note is None:
            return Response(
                {'detail': 'Конспект не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        note.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class AdminUserListView(APIView):
    """Список пользователей для администратора."""

    permission_classes = (IsAdmin,)

    def get(self, request):
        users = User.objects.all().order_by('-created_at')

        return Response(
            UserSerializer(users, many=True).data,
            status=status.HTTP_200_OK,
        )