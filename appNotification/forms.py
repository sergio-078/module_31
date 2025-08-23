from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Post, Response, News
from ckeditor.widgets import CKEditorWidget


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['category', 'title', 'content']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter post title')
            }),
        }
        labels = {
            'category': _('Category'),
            'title': _('Title'),
            'content': _('Content'),
        }

    content = forms.CharField(widget=CKEditorWidget(config_name='default'), label=_('Content'))

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise forms.ValidationError(_('Title must be at least 5 characters long'))
        return title

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 20:
            raise forms.ValidationError(_('Content must be at least 20 characters long'))
        return content


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Write your response here...')
            }),
        }
        labels = {
            'text': _('Response text'),
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) < 10:
            raise forms.ValidationError(_('Response must be at least 10 characters long'))
        return text


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter news title')
            }),
        }
        labels = {
            'title': _('Title'),
            'content': _('Content'),
        }

    content = forms.CharField(widget=CKEditorWidget(config_name='default'), label=_('Content'))

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise forms.ValidationError(_('Title must be at least 5 characters long'))
        return title

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 20:
            raise forms.ValidationError(_('Content must be at least 20 characters long'))
        return content
