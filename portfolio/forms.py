from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import PortfolioItem


class PortfolioItemForm(forms.ModelForm):
    content = forms.CharField(
        label='توضیحات کامل',
        widget=CKEditor5Widget(config_name='extends'),
        required=False,
    )

    class Meta:
        model = PortfolioItem
        fields = [
            'title', 'category', 'summary', 'content',
            'featured_image', 'image_alt', 'material',
            'weight', 'standard', 'meta_description', 'published',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: چرخ‌دنده چدنی GG25'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'توضیح کوتاه'}),
            'image_alt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'متن جایگزین تصویر'}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: چدن خاکستری'}),
            'weight': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: ۱۲ کیلوگرم'}),
            'standard': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: DIN 1691'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'maxlength': 300}),
            'published': forms.CheckboxInput(),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }