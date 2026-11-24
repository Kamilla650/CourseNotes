from django.urls import path

from .views import (
    AdminUserListView,
    LoginView,
    NoteDetailView,
    NoteListCreateView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)

app_name = 'api'

urlpatterns = [
    # Аутентификация и восстановление пароля
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # CRUD конспектов
    path('notes/', NoteListCreateView.as_view(), name='note-list-create'),
    path('notes/<int:pk>/', NoteDetailView.as_view(), name='note-detail'),

    # Админский эндпоинт (для демонстрации 403)
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
]