from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse

from .forms import ContactForm, SearchForm
from users.models import User
from suppliers.models import Supplier
from shops.models import Shop
from products.models import Product
from orders.models import Order

def home(request):
    """
    Home page for the site
    """
    context = {
        'title': _('Lidhje Biznesi - B2B Platform'),
    }
    
    return render(request, 'common/home.html', context)

def about(request):
    """
    About page
    """
    context = {
        'title': _('About Us'),
    }
    
    return render(request, 'common/about.html', context)

def contact(request):
    """
    Contact page with form
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real application, you would send an email or save to the database
            # For now, just show a success message
            messages.success(request, _('Thank you for your message. We will get back to you soon.'))
            return redirect('common:contact')
    else:
        form = ContactForm()
    
    context = {
        'title': _('Contact Us'),
        'form': form,
    }
    
    return render(request, 'common/contact.html', context)

def faq(request):
    """
    Frequently Asked Questions page
    """
    context = {
        'title': _('FAQ'),
    }
    
    return render(request, 'common/faq.html', context)

def terms(request):
    """
    Terms and Conditions page
    """
    context = {
        'title': _('Terms and Conditions'),
    }
    
    return render(request, 'common/terms.html', context)

def privacy(request):
    """
    Privacy Policy page
    """
    context = {
        'title': _('Privacy Policy'),
    }
    
    return render(request, 'common/privacy.html', context)

@login_required
def global_search(request):
    """
    Global search functionality
    """
    search_form = SearchForm(request.GET)
    query = request.GET.get('query', '')
    search_type = request.GET.get('search_type', 'ALL')
    
    suppliers = []
    shops = []
    products = []
    orders = []
    
    if query:
        user = request.user
        
        # Filter based on user type and search type
        if search_type in ['ALL', 'SUPPLIERS']:
            if user.is_supplier:
                # Suppliers see only their own supplier
                suppliers = Supplier.objects.filter(admin=user)
            elif user.is_shop:
                # Shops see suppliers they've ordered from
                shop = user.managed_shops.first()
                if shop:
                    suppliers = Supplier.objects.filter(
                        orders__shop=shop
                    ).filter(
                        Q(name__icontains=query) | Q(description__icontains=query)
                    ).distinct()
            else:
                # Admins see all suppliers
                suppliers = Supplier.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )
        
        if search_type in ['ALL', 'SHOPS']:
            if user.is_shop:
                # Shops see only their own shop
                shops = Shop.objects.filter(admin=user)
            elif user.is_supplier:
                # Suppliers see shops that have ordered from them
                supplier = user.managed_suppliers.first()
                if supplier:
                    shops = Shop.objects.filter(
                        orders__supplier=supplier
                    ).filter(
                        Q(name__icontains=query) | Q(address__icontains=query)
                    ).distinct()
            else:
                # Admins see all shops
                shops = Shop.objects.filter(
                    Q(name__icontains=query) | Q(address__icontains=query)
                )
        
        if search_type in ['ALL', 'PRODUCTS']:
            if user.is_supplier:
                # Suppliers see only their products
                supplier = user.managed_suppliers.first()
                if supplier:
                    products = Product.objects.filter(
                        supplier=supplier
                    ).filter(
                        Q(name__icontains=query) | 
                        Q(description__icontains=query) |
                        Q(sku__icontains=query) |
                        Q(barcode__icontains=query)
                    )
            elif user.is_shop:
                # Shops see products from suppliers they've ordered from
                shop = user.managed_shops.first()
                if shop:
                    products = Product.objects.filter(
                        supplier__orders__shop=shop
                    ).filter(
                        Q(name__icontains=query) | 
                        Q(description__icontains=query) |
                        Q(sku__icontains=query) |
                        Q(barcode__icontains=query)
                    ).distinct()
            else:
                # Admins see all products
                products = Product.objects.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(sku__icontains=query) |
                    Q(barcode__icontains=query)
                )
        
        if search_type in ['ALL', 'ORDERS']:
            if user.is_supplier:
                # Suppliers see orders from their supplier
                supplier = user.managed_suppliers.first()
                if supplier:
                    orders = Order.objects.filter(
                        supplier=supplier
                    ).filter(
                        Q(id__icontains=query) | 
                        Q(shop__name__icontains=query) |
                        Q(notes__icontains=query)
                    )
            elif user.is_shop:
                # Shops see their own orders
                shop = user.managed_shops.first()
                if shop:
                    orders = Order.objects.filter(
                        shop=shop
                    ).filter(
                        Q(id__icontains=query) | 
                        Q(supplier__name__icontains=query) |
                        Q(notes__icontains=query)
                    )
            else:
                # Admins see all orders
                orders = Order.objects.filter(
                    Q(id__icontains=query) | 
                    Q(shop__name__icontains=query) |
                    Q(supplier__name__icontains=query) |
                    Q(notes__icontains=query)
                )
    
    context = {
        'title': _('Search Results'),
        'search_form': search_form,
        'query': query,
        'search_type': search_type,
        'suppliers': suppliers[:10],
        'shops': shops[:10],
        'products': products[:10],
        'orders': orders[:10],
        'suppliers_count': suppliers.count() if query else 0,
        'shops_count': shops.count() if query else 0,
        'products_count': products.count() if query else 0,
        'orders_count': orders.count() if query else 0,
    }
    
    return render(request, 'common/search_results.html', context)

@login_required
def system_settings(request):
    """
    System settings page (admin only)
    """
    if not request.user.is_staff:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')
    
    # Get system settings from Configuration model
    from .models import Configuration
    
    settings = Configuration.objects.all()
    
    context = {
        'title': _('System Settings'),
        'settings': settings,
    }
    
    return render(request, 'common/system_settings.html', context)

def error_404(request, exception):
    """
    Custom 404 error page
    """
    context = {
        'title': _('Page Not Found'),
    }
    
    return render(request, 'common/error_404.html', context, status=404)

def error_500(request):
    """
    Custom 500 error page
    """
    context = {
        'title': _('Server Error'),
    }
    
    return render(request, 'common/error_500.html', context, status=500)
