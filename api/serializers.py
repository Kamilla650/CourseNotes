from rest_framework import serializers

from core.models import Note, PasswordResetToken, User


class UserSerializer(serializers.ModelSerializer):
    """Пользователь для админ-эндпоинта."""

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'created_at')


class NoteSerializer(serializers.ModelSerializer):
    """Конспект с семантической валидацией (для ответа 422)."""

    class Meta:
        model = Note
        fields = ('id', 'title', 'content', 'summary', 'is_published',
                  'author', 'course', 'created_at')
        read_only_fields = ('author', 'created_at')

    def validate_title(self, value):
        value = (value or '').strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                'Название конспекта должно содержать не менее 3 символов.'
            )
        return value

    def validate_content(self, value):
        value = (value or '').strip()
        if len(value) < 10:
            raise serializers.ValidationError(
                'Текст конспекта должен содержать не менее 10 символов.'
            )
        return value

    def validate_summary(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError(
                'Краткое содержание не должно превышать 500 символов.'
            )
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация: проверка сложности пароля и совпадения."""

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'password_confirm')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже зарегистрирован.'
            )
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать не менее 8 символов.'
            )
        if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
            raise serializers.ValidationError(
                'Пароль должен содержать буквы и цифры.'
            )
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Пароли не совпадают.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать не менее 8 символов.'
            )
        if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
            raise serializers.ValidationError(
                'Пароль должен содержать буквы и цифры.'
            )
        return value