from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


ACCOUNT_TYPES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
]

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(max_length=150, required=True)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'account_type',)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user