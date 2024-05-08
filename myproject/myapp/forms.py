# myapp/forms.py

from django import forms
from .models import TestCase


class CommentForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ['comment']
