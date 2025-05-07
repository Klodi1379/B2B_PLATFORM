from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Q

from .models import Product, Category
from .forms import ProductSearchForm, CategoryFilterForm
from suppliers.models import Supplier

@login_required
def product_list(request):
    """
    List all products, with optional filtering
    """
    search_form = ProductSearchForm(request.GET)
    
    # Base queryset - only show available products by default
    products = Product.objects.filter(is_available=True)
    
    # Get all categories and suppliers for filter dropdowns
    categories = Category.objects.all().order_by('name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    
    # Apply filters if the form is valid
    if search_form.is_valid():
        data = search_form.cleaned_data
        
        # Apply query filter
        if data.get('query'):
            query = data['query']
            products = products.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query)
            )
        
        # Apply category filter
        if data.get('category'):
            products = products.filter(category=data['category'])
        
        # Apply supplier filter
        if data.get('supplier'):
            products = products.filter(supplier=data['supplier'])
        
        # Apply price range filters
        if data.get('min_price'):
            products = products.filter(price__gte=data['min_price'])
        
        if data.get('max_price'):
            products = products.filter(price__lte=data['max_price'])
        
        # Apply availability filter (if unchecked, show all including unavailable)
        if not data.get('available_only'):
            products = Product.objects.all()  # Reset to all products
            # Re-apply other filters
            if data.get('query'):
                query = data['query']
                products = products.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(sku__icontains=query) |
                    Q(barcode__icontains=query)
                )
            if data.get('category'):
                products = products.filter(category=data['category'])
            if data.get('supplier'):
                products = products.filter(supplier=data['supplier'])
            if data.get('min_price'):
                products = products.filter(price__gte=data['min_price'])
            if data.get('max_price'):
                products = products.filter(price__lte=data['max_price'])
    
    # Add pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        products = paginator.page(paginator.num_pages)
    
    # Get cart items count for shop users
    cart_count = 0
    if request.user.is_shop:
        cart = request.session.get('cart', {})
        cart_count = sum(1 for qty in cart.values() if qty > 0)
    
    context = {
        'products': products,
        'search_form': search_form,
        'categories': categories,
        'suppliers': suppliers,
        'cart_count': cart_count,
    }
    
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, product_id):
    """
    View details of a product
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id)[:5]
    
    context = {
        'product': product,
        'related_products': related_products
    }
    
    return render(request, 'products/product_detail.html', context)

@login_required
def category_list(request):
    """
    List all categories, with optional filtering
    """
    filter_form = CategoryFilterForm(request.GET)
    
    # Base queryset
    categories = Category.objects.all()
    
    # Apply filters if the form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        # Apply supplier filter
        if data.get('supplier'):
            categories = categories.filter(supplier=data['supplier'])
        
        # Apply parent filter
        if data.get('parent'):
            categories = categories.filter(parent=data['parent'])
        else:
            # Default to top-level categories
            categories = categories.filter(parent__isnull=True)
    
    context = {
        'categories': categories,
        'filter_form': filter_form,
    }
    
    return render(request, 'products/category_list.html', context)

@login_required
def category_detail(request, category_id):
    """
    View details of a category and its products
    """
    category = get_object_or_404(Category, id=category_id)
    
    # Get products in this category
    products = Product.objects.filter(category=category)
    
    # Get subcategories
    subcategories = Category.objects.filter(parent=category)
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
    }
    
    return render(request, 'products/category_detail.html', context)

@login_required
def product_search(request):
    """
    Search for products
    """
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )
    else:
        products = Product.objects.none()
    
    context = {
        'query': query,
        'products': products,
    }
    
    return render(request, 'products/product_search.html', context)

# API endpoints

@login_required
def api_product_search(request):
    """
    API endpoint for product search
    """
    query = request.GET.get('q', '')
    supplier_id = request.GET.get('supplier')
    
    products = Product.objects.filter(is_available=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )
    
    if supplier_id:
        products = products.filter(supplier_id=supplier_id)
    
    # Limit results to 20
    products = products[:20]
    
    # Format the response
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.price),
            'unit': product.unit,
            'category': product.category.name if product.category else None,
            'supplier': product.supplier.name,
        })
    
    return JsonResponse({'products': product_list})

@login_required
def api_category_list(request):
    """
    API endpoint for category list
    """
    supplier_id = request.GET.get('supplier')
    parent_only = request.GET.get('parent_only') == 'true'
    
    categories = Category.objects.all()
    
    if supplier_id:
        categories = categories.filter(supplier_id=supplier_id)
    
    if parent_only:
        categories = categories.filter(parent__isnull=True)
    
    # Format the response
    category_list = []
    for category in categories:
        category_list.append({
            'id': category.id,
            'name': category.name,
            'parent_id': category.parent_id,
            'supplier_id': category.supplier_id,
        })
    
    return JsonResponse({'categories': category_list})
