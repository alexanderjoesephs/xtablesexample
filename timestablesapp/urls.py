from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    
    path('login',views.user_login,name='user_login'),
    path('logout', views.logoutview, name='user_logout'),
    path('teacher_stats',views.teacher_stats,name='teacher_stats'),
    path('teacher_set_work',views.teacher_set_work,name='teacher_set_work'),
    path('teacher_print_flashcards',views.teacher_print_flashcards,name='teacher_print_flashcards'),
    path('teacher_download_pdf_from=<str:date_from>&to=<str:date_to>',views.teacher_download_pdf,name='teacher_download_pdf'),
    

    path('create_attempt', views.create_attempt, name='create_attempt'),
    path('student',views.student,name='student'),
    path('student_play',views.student_play,name='student_play'),
    path('student_ready',views.student_ready,name='student_ready'),
    path('student_stats',views.student_stats,name='student_stats'),
    path('admin_create_user',views.admin_create_user,name='admin_create_user'),
    path('admin_assign_students',views.admin_assign_students,name='admin_assign_students'),
    path('admin_remove_students',views.admin_remove_students,name='admin_remove_students'),
    path('admin_stats',views.admin_stats,name='admin_stats')
    ]


    
