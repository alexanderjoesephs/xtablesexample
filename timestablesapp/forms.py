
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


ACCOUNT_TYPES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
]

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    class_name = forms.CharField(max_length=50, required=True)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'class_name', 'account_type',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = f"{self.cleaned_data['first_name'].lower()}{self.cleaned_data['class_name'].lower()}"
        if commit:
            user.save()
        return user
    
   