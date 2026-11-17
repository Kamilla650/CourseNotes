from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password

User = get_user_model()


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(label='ФИО', max_length=150)
    email = forms.EmailField(label='Email', max_length=150)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # При самостоятельной регистрации роль всегда «студент»
        user.role = User.ROLE_STUDENT
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Введите ваш Email', max_length=150)


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label='Новый пароль', strip=False, widget=forms.PasswordInput,
        help_text=password_validators_help_text_html(),
    )
    confirm_password = forms.CharField(
        label='Подтвердите пароль', strip=False, widget=forms.PasswordInput,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password, self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Пароли не совпадают.')
        return cleaned_data