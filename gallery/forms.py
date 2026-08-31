from django import forms
from gallery.models import GalleryAlbum


# ═══ ویجت سفارشی برای آپلود چند فایل ═══
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


# ═══ فرم‌های گالری ═══
class GalleryAlbumForm(forms.ModelForm):
    class Meta:
        model = GalleryAlbum
        fields = ['title', 'description', 'published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'مثلاً: رویداد نمایشگاه صنعت ۱۴۰'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'توضیحات آلبوم...'
            }),
            'published': forms.CheckboxInput(attrs={
                'style': 'width:20px; height:20px; accent-color:#ff6b00;'
            }),
        }


class MultipleImageUploadForm(forms.Form):
    """فرم آپلود چند تصویر همزمان"""
    images = MultipleFileField(
        label='انتخاب تصاویر',
        help_text='می‌توانید چند تصویر را همزمان انتخاب کنید (Ctrl+Click)'
    )