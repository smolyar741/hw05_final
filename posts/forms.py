from django import forms
from django.db import models
from django.forms import ModelForm
from django.forms.widgets import Textarea
from .models import Post
from posts.models import Comment, Follow


class PostForm(forms.ModelForm):
        class Meta:
                model = Post
                fields = ["group", "text", "image"]

class CommentForm(forms.ModelForm):
        class Meta:
                model = Comment
                fields = ["text"]

class FollowForm(forms.ModelForm):
        class Meta:
                model = Follow
                fields = ["user", "author"]


