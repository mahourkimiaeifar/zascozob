from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import PortfolioItem, PortfolioCategory


def portfolio_list(request):
    items = PortfolioItem.objects.filter(published=True, is_deleted=False).select_related('category')
    sidebar_categories = PortfolioCategory.objects.filter(is_deleted=False).annotate(
        num_items=Count('items', filter=Q(items__published=True, items__is_deleted=False))
    ).order_by('order', 'title')

    search_query = request.GET.get('q', '').strip()
    current_category = request.GET.get('category', '').strip()

    if search_query:
        items = items.filter(Q(title__icontains=search_query) | Q(summary__icontains=search_query) | Q(content__icontains=search_query))
    if current_category:
        items = items.filter(category__slug=current_category)

    total_items = items.count()

    paginator = Paginator(items, 6)
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
        'sidebar_categories': sidebar_categories,
        'search_query': search_query,
        'current_category': current_category,
        'extra_get': extra_get,
        'total_items': total_items,
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

    latest_items = PortfolioItem.objects.filter(published=True, is_deleted=False).exclude(id=item.id).select_related('category')[:4]
    sidebar_categories = PortfolioCategory.objects.filter(is_deleted=False).annotate(
        num_items=Count('items', filter=Q(items__published=True, items__is_deleted=False))
    ).filter(num_items__gt=0)

    return render(request, 'main_pages/portfolio_detail.html', {
        'item': item,
        'related': related,
        'latest_items': latest_items,
        'sidebar_categories': sidebar_categories,
    })