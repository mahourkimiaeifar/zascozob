from django.shortcuts import render,get_object_or_404
from portfolio.models import PortfolioItem, PortfolioCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def portfolio_list(request):
    items = PortfolioItem.objects.filter(published=True, is_deleted=False).select_related('category')
    categories = PortfolioCategory.objects.filter(is_deleted=False)

    current_category = request.GET.get('category', '').strip()
    if current_category:
        items = items.filter(category__slug=current_category)

    paginator = Paginator(items, 9)
    try:
        items = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    params = request.GET.copy()
    params.pop('page', None)
    extra_get = params.urlencode()
    if extra_get:
        extra_get += '&'

    return render(request, 'main_pages/portfolio_list.html', {
        'items': items,
        'categories': categories,
        'current_category': current_category,
        'extra_get': extra_get,
    })


def portfolio_detail(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug, published=True, is_deleted=False)

    if not request.session.get(f'viewed_portfolio_{item.id}'):
        item.views += 1
        item.save(update_fields=['views'])
        request.session[f'viewed_portfolio_{item.id}'] = True

    related = PortfolioItem.objects.filter(published=True, is_deleted=False).exclude(id=item.id).select_related('category')
    if item.category:
        related = related.filter(category=item.category)
    related = related[:3]

    return render(request, 'main_pages/portfolio_detail.html', {'item': item, 'related': related})
