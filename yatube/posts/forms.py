from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image',
        )
        help_texts = {
            'text': 'Текст публикации',
            'group': 'Группа публикации',
            'image': 'Картинка публикации',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'text',
        )
        help_texts = {
            'text': 'Текст комментария',
        }
