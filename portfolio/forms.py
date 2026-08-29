from django import forms
from .models import PortfolioItem

class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            'title', 'category', 'summary', 'content',
            'featured_image', 'image_alt', 'material',
            'weight', 'standard', 'meta_description', 'published',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: چرخ‌دنده چدنی GG25'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image_alt': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.TextInput(attrs={'class': 'form-control'}),
            'standard': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'published': forms.CheckboxInput(),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            # برای content هیچ ویجتی تعریف نکن، خودش خودکار CKEditor میشه
        }