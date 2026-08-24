from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from blog.models import Post, Category


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'excerpt', 'content', 'featured_image', 'category',
                  'read_time', 'published', 'publish_date']
        widgets = {
            'content': CKEditor5Widget(config_name='extends'),
            'title': forms.TextInput(attrs={'placeholder': 'عنوان مقاله'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'placeholder': 'چکیده کوتاه...'}),
            'read_time': forms.NumberInput(attrs={'min': 1}),
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }