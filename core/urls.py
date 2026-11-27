from django.urls import path

from . import views, learning, quiz

app_name = 'core'

urlpatterns = [
    path("courses/<int:pk>/notes/<int:note_pk>/generate/", quiz.generate, name="generate"),
    path("courses/<int:pk>/notes/<int:note_pk>/quiz/", quiz.take_quiz, name="quiz"),
    path("results/", quiz.results, name="results"),
    path('courses/', learning.courses, name='courses'),
    path('courses/new/', learning.course_edit, name='course_new'),
    path('courses/<int:pk>/', learning.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', learning.course_edit, name='course_edit'),
    path('courses/<int:pk>/enroll/', learning.enroll, name='enroll'),
    path('courses/<int:pk>/notes/new/', learning.note_edit, name='note_new'),
    path('courses/<int:pk>/notes/<int:note_pk>/', learning.note_detail, name='note_detail'),
    path('courses/<int:pk>/notes/<int:note_pk>/edit/', learning.note_edit, name='note_edit'),
    path('', views.index, name='index'),
    path('health/', views.health, name='health'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
]