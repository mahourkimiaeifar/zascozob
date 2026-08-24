from django import forms
from blog.models import Post


class PostForm(forms.ModelForm):
    # تصویر اختیاری — موقع ویرایش لازم نیست دوباره آپلود بشه
    featured_image = forms.ImageField(required=False, label='تصویر شاخص')
    # زمان مطالعه اختیاری — اگه نیاد، خودکار ۱
    read_time = forms.IntegerField(required=False, min_value=1, label='زمان مطالعه (دقیقه)')

    class Meta:
        model = Post
        fields = ['title', 'excerpt', 'content', 'featured_image', 'category',
                  'read_time', 'published', 'publish_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'عنوان مقاله'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'placeholder': 'چکیده کوتاه...'}),
            'read_time': forms.NumberInput(attrs={'min': 1, 'max': 60}),
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_read_time(self):
        # اگه خالی اومد، مقدار پیش‌فرض ۱ بذار
        return self.cleaned_data.get('read_time') or 1