from django.shortcuts import render, redirect
from .models import ContactMessage
from blog.models import Post
from portfolio.models import PortfolioItem

def home(request):
    latest_posts = Post.objects.filter(published=True)[:3]
    latest_works = PortfolioItem.objects.filter(published=True)[:4]
    return render(request, 'main_pages/home.html', {
        'latest_posts': latest_posts,
        'latest_works': latest_works,
    })

def about(request): return render(request, 'main_pages/about.html')

def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name',''), phone=request.POST.get('phone',''),
            message=request.POST.get('message',''))
        return redirect('/contact-us/?ok=1')
    return render(request, 'main_pages/contact.html')