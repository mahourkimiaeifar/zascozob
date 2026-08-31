from django import forms
from blog.models import Post


class PostForm(forms.ModelForm):
    featured_image = forms.ImageField(required=False, label='تصویر شاخص')
    read_time = forms.IntegerField(required=False, min_value=1, label='زمان مطالعه (دقیقه)')

    class Meta:
        model = Post
        fields = ['title', 'excerpt', 'content', 'featured_image', 'category',
                  'read_time', 'published', 'publish_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان مقاله'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'چکیده کوتاه...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'read_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60}),
            'publish_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'published': forms.CheckboxInput(attrs={'style': 'width:20px; height:20px; accent-color:#ff6b00;'}),
        }

    def clean_read_time(self):
        return self.cleaned_data.get('read_time') or 1