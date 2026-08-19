from django.shortcuts import render, redirect
from .models import ContactMessage

def home(request): return render(request, 'main_pages/home.html')
def about(request): return render(request, 'main_pages/about.html')
def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name',''), phone=request.POST.get('phone',''),
            message=request.POST.get('message',''))
        return redirect('/contact/?ok=1')
    return render(request, 'main_pages/contact.html')