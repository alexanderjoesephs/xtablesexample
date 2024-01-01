from django.contrib import admin

# Register your models here.

from .models import Question, Attempt,Classroom,Student,Teacher,Test, Admin, Settings  # Import your models

admin.site.register(Question)
admin.site.register(Attempt)
admin.site.register(Classroom)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Test)
admin.site.register(Admin)
admin.site.register(Settings)
