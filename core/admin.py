from django.contrib import admin

from .models import Course, Enrollment, Note, PasswordResetToken, Question, Result, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'full_name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'created_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'course')
    search_fields = ('title',)


admin.site.register(Enrollment)
admin.site.register(Question)
admin.site.register(Result)
admin.site.register(PasswordResetToken)
