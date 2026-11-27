
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Course, Enrollment, Note, Result


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description']


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'summary', 'is_published']

    def clean_title(self):
        value = self.cleaned_data['title'].strip()
        if len(value) < 3:
            raise forms.ValidationError('Минимум 3 символа.')
        return value

    def clean_content(self):
        value = self.cleaned_data['content'].strip()
        if len(value) < 10:
            raise forms.ValidationError('Минимум 10 символов.')
        return value

    def clean_summary(self):
        value = self.cleaned_data['summary']
        if value and len(value) > 500:
            raise forms.ValidationError('Максимум 500 символов.')
        return value


def manages(user, course):
    return user.role == 'admin' or (
        user.role == 'teacher'
        and course.teacher_id == user.pk
    )


def participates(user, course):
    return manages(user, course) or (
        user.role == 'student'
        and Enrollment.objects.filter(
            student=user,
            course=course
        ).exists()
    )


def visible_notes(user, course):
    notes = course.notes.all()

    if manages(user, course):
        return notes

    if participates(user, course):
        return notes.filter(
            Q(author=user) | Q(is_published=True)
        )

    return notes.none()


@login_required
def courses(request):
    items = Course.objects.select_related(
        'teacher'
    ).order_by('title')

    return render(request, 'core/courses.html', {
        'courses': items
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    can_manage = manages(request.user, course)

    students = Enrollment.objects.none()
    student_results = Result.objects.none()

    if can_manage:
        students = Enrollment.objects.filter(
            course=course
        ).select_related('student').order_by(
            'student__full_name'
        )

        student_results = Result.objects.filter(
            note__course=course,
            user_id__in=students.values('student_id')
        ).select_related(
            'user', 'note'
        ).order_by('-passed_at')

    return render(request, 'core/course_detail.html', {
        'course': course,
        'notes': visible_notes(request.user, course),
        'can_manage': can_manage,
        'can_note': participates(request.user, course),
        'enrolled': Enrollment.objects.filter(
            student=request.user,
            course=course
        ).exists(),
        'students': students,
        'student_count': students.count(),
        'student_results': student_results,
    })


@login_required
def course_edit(request, pk=None):
    course = get_object_or_404(
        Course, pk=pk
    ) if pk else None

    if (
        (course and not manages(request.user, course))
        or (
            not course
            and request.user.role not in ('teacher', 'admin')
        )
    ):
        raise PermissionDenied

    form = CourseForm(
        request.POST if request.method == 'POST' else None,
        instance=course
    )

    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)

        if not course:
            obj.teacher = request.user

        obj.save()

        return redirect('core:course_detail', pk=obj.pk)

    return render(request, 'core/learning_form.html', {
        'form': form,
        'heading': (
            'Редактирование курса' if course else 'Новый курс'
        )
    })


@login_required
@require_POST
def enroll(request, pk):
    if request.user.role != 'student':
        raise PermissionDenied

    course = get_object_or_404(Course, pk=pk)

    Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    return redirect('core:course_detail', pk=pk)


@login_required
def note_edit(request, pk, note_pk=None):
    course = get_object_or_404(Course, pk=pk)

    note = get_object_or_404(
        Note, pk=note_pk, course=course
    ) if note_pk else None

    if not participates(request.user, course) or (
        note and not (
            note.author_id == request.user.pk
            or manages(request.user, course)
        )
    ):
        raise PermissionDenied

    form = NoteForm(
        request.POST if request.method == 'POST' else None,
        instance=note
    )

    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)

        if not note:
            obj.author = request.user
            obj.course = course

        obj.save()

        return redirect(
            'core:note_detail',
            pk=course.pk,
            note_pk=obj.pk
        )

    return render(request, 'core/learning_form.html', {
        'form': form,
        'heading': (
            'Редактирование конспекта'
            if note else 'Новый конспект'
        )
    })


@login_required
def note_detail(request, pk, note_pk):
    course = get_object_or_404(Course, pk=pk)

    note = get_object_or_404(
        visible_notes(request.user, course),
        pk=note_pk
    )

    return render(request, 'core/note_detail.html', {
        'note': note,
        'can_edit': (
            note.author_id == request.user.pk
            or manages(request.user, course)
        )
    })
