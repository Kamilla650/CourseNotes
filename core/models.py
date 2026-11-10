from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Создание пользователей и администратора."""

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Нужно указать email')
        user = self.model(email=self.normalize_email(email), full_name=full_name, **extra_fields)
        user.set_password(password)  # пароль сохраняется только в виде хеша
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('role', User.ROLE_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь системы: студент, преподаватель или администратор."""

    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Студент'),
        (ROLE_TEACHER, 'Преподаватель'),
        (ROLE_ADMIN, 'Администратор'),
    ]

    email = models.EmailField('Email', max_length=150, unique=True)
    password = models.CharField('Хеш пароля', max_length=255, db_column='password_hash')
    full_name = models.CharField('ФИО', max_length=150)
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    is_active = models.BooleanField('Активен', default=True)
    is_staff = models.BooleanField('Доступ к админке', default=False)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=['student', 'teacher', 'admin']),
                name='ck_users_role',
            ),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class Course(models.Model):
    """Учебный курс."""

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='taught_courses',
        verbose_name='Преподаватель',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'courses'
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """Запись студента на курс (связь многие ко многим)."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Студент',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс',
    )
    enrolled_at = models.DateTimeField('Дата записи', auto_now_add=True)

    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='uq_enrollments_student_course'),
        ]

    def __str__(self):
        return f'{self.student} – {self.course}'


class Note(models.Model):
    """Конспект."""

    title = models.CharField('Название', max_length=200)
    content = models.TextField('Текст конспекта')
    summary = models.TextField('Краткое содержание', blank=True, null=True)
    is_published = models.BooleanField('Опубликован', default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Автор',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Курс',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'notes'
        ordering = ['-created_at']
        verbose_name = 'Конспект'
        verbose_name_plural = 'Конспекты'

    def __str__(self):
        return self.title


class Question(models.Model):
    """Вопрос для самопроверки по конспекту."""

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Конспект',
    )
    question_text = models.TextField('Текст вопроса')
    correct_answer = models.CharField('Правильный ответ', max_length=255)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'questions'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.question_text[:50]


class Result(models.Model):
    """Результат прохождения вопросов по конспекту."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Пользователь',
    )
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Конспект',
    )
    correct_count = models.PositiveIntegerField('Правильных ответов')
    total_count = models.PositiveIntegerField('Всего вопросов')
    passed_at = models.DateTimeField('Дата прохождения', auto_now_add=True)

    class Meta:
        db_table = 'results'
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        constraints = [
            models.CheckConstraint(condition=models.Q(total_count__gt=0), name='ck_results_total_positive'),
            models.CheckConstraint(
                condition=models.Q(correct_count__lte=models.F('total_count')),
                name='ck_results_correct_le_total',
            ),
        ]

    def __str__(self):
        return f'{self.user}: {self.correct_count}/{self.total_count}'


class PasswordResetToken(models.Model):
    """Одноразовый токен для восстановления пароля."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        verbose_name='Пользователь',
    )
    token_hash = models.CharField('Хеш токена', max_length=64, unique=True)
    expires_at = models.DateTimeField('Действует до')
    used_at = models.DateTimeField('Использован', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'password_reset_token'
        indexes = [
            models.Index(fields=['user'], name='idx_prt_user_id'),
            models.Index(fields=['expires_at'], name='idx_prt_expires'),
        ]
        verbose_name = 'Токен восстановления пароля'
        verbose_name_plural = 'Токены восстановления пароля'

    def is_valid(self):
        """Токен действителен, если он не использован и срок не истёк."""
        return self.used_at is None and self.expires_at > timezone.now()
