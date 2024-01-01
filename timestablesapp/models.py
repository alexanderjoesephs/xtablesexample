from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return(self.user.username)
    

class Teacher(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add any additional fields for the teacher model
    def __str__(self):
        return(self.user.username)

class Student(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='find')
    # Add any additional fields for the student model
    classes = models.ForeignKey(Teacher,on_delete=models.CASCADE,null=True)
    def __str__(self):
        return(self.user.username)

class Classroom(models.Model):
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name='classrooms')
    


class Test(models.Model):
    user_tested = models.ForeignKey(User, on_delete=models.CASCADE,default=None)
    table_tested = models.IntegerField(validators=[
            MaxValueValidator(limit_value=12),
            MinValueValidator(limit_value=2),
        ])
    set = models.BooleanField(default=True)

    def __str__(self) -> str:
        if self.set:
            return f"{self.user_tested} set {self.table_tested} times table"
        else:
            return f"{self.user_tested} not set {self.table_tested} times table"


# Create your models here.
class Question(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    @property
    def answer(self):
        return self.x * self.y
    
    def __str__(self):
        return f"{self.x} x {self.y}"
    
    #had to only work with one field for simplicity sake for now

class Attempt(models.Model):
    user_asked = models.ForeignKey(User, on_delete=models.CASCADE,default=None)
    question_asked = models.ForeignKey(Question, on_delete=models.CASCADE,default=None)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created",null=True)

    correct = models.BooleanField(default=True)
    time_taken = models.IntegerField(default=None, null=True)
    @property
    def x(self):
        return self.question_asked.x
    @property
    def y(self):
        return self.question_asked.y
    def __str__(self):
        if self.correct==True:
            return f'{self.user_asked} answered {self.question_asked} correctly in {self.time_taken} ms'
        else:
            return f'{self.user_asked} answered {self.question_asked} incorrectly'
        
class Settings(models.Model):
    number_of_questions = models.IntegerField(default=25,validators=[
            MaxValueValidator(limit_value=100),
            MinValueValidator(limit_value=1),
        ])
    number_of_seconds = models.IntegerField(default=6,validators=[
            MaxValueValidator(limit_value=30),
            MinValueValidator(limit_value=3),
        ])
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return(f'{self.user.username} answers {self.number_of_questions} questions in {self.number_of_seconds} seconds each')
        