from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.db import models

from .models import Shop
from .forms import ShopForm, OrderForm, OrderItemForm, SupplierSearchForm, CartAddProductForm
from suppliers.models import Supplier
from products.models import Product, Category
from orders.models import Order, OrderItem

@login_required
def dashboard(request):
    """
    Shop dashboard with overview of orders and suppliers
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access the shop dashboard.'))
        return redirect('users:dashboard')

    # Get shop associated with the user
    try:
        shop = Shop.objects.get(admin=request.user)
    except Shop.DoesNotExist:
        # Create a new shop for this user if one doesn't exist
        shop = Shop.objects.create(
            name=f"{request.user.first_name}'s Shop",
            shop_type="Retail",
            address="",
            city="",
            country="Albania",
            phone=request.user.phone or "",
            admin=request.user
        )
        messages.info(request, _('A new shop has been created for you. Please update your shop details.'))
        return redirect('shops:profile_edit')

    # Get today's date for the dashboard
    today_date = timezone.now().date()

    # Get active orders
    active_orders = Order.objects.filter(
        shop=shop,
        status__in=['SUBMITTED', 'CONFIRMED', 'PROCESSING', 'READY', 'DELIVERING']
    ).order_by('-created_at')[:5]

    # Get recent orders
    recent_orders = Order.objects.filter(shop=shop).order_by('-created_at')[:5]

    # Get connected suppliers
    suppliers = Supplier.objects.filter(
        orders__shop=shop
    ).distinct()[:5]

    # Get favorite suppliers (most ordered from)
    favorite_suppliers = Supplier.objects.filter(
        orders__shop=shop
    ).annotate(
        order_count=Count('orders')
    ).order_by('-order_count')[:4]

    # Get cart items count
    from decimal import Decimal
    cart = request.session.get('cart', {})
    cart_items_count = sum(1 for qty in cart.values() if Decimal(str(qty)) > 0)

    # Get counts for stats
    active_orders_count = Order.objects.filter(
        shop=shop,
        status__in=['SUBMITTED', 'CONFIRMED', 'PROCESSING', 'READY', 'DELIVERING']
    ).count()

    suppliers_count = Supplier.objects.filter(
        orders__shop=shop
    ).distinct().count()

    today_deliveries_count = Order.objects.filter(
        shop=shop,
        status='DELIVERING',
        updated_at__date=today_date
    ).count()

    context = {
        'shop': shop,
        'today_date': today_date,
        'active_orders_count': active_orders_count,
        'suppliers_count': suppliers_count,
        'cart_items_count': cart_items_count,
        'today_deliveries_count': today_deliveries_count,
        'recent_orders': recent_orders,
        'favorite_suppliers': favorite_suppliers,
    }

    return render(request, 'shops/dashboard.html', context)

@login_required
def profile(request):
    """
    Display shop profile information
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    context = {
        'shop': shop,
    }

    return render(request, 'shops/profile.html', context)

@login_required
def profile_edit(request):
    """
    Edit shop profile information
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    if request.method == 'POST':
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, _('Shop profile updated successfully.'))
            return redirect('shops:profile')
    else:
        form = ShopForm(instance=shop)

    context = {
        'form': form,
        'shop': shop,
    }

    return render(request, 'shops/profile_edit.html', context)

# Supplier Management Views

@login_required
def supplier_list(request):
    """
    List all suppliers connected to the shop
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    # Initialize search form
    form = SupplierSearchForm(request.GET)

    # Base queryset - filter suppliers that have at least one order from this shop
    connected_suppliers = Supplier.objects.filter(
        orders__shop=shop
    ).distinct()

    # Get all active suppliers
    all_suppliers = Supplier.objects.filter(is_active=True)

    # Apply search filters if the form is valid
    if form.is_valid():
        data = form.cleaned_data

        # Name filter
        if data.get('name'):
            all_suppliers = all_suppliers.filter(name__icontains=data['name'])

        # City filter
        if data.get('city'):
            all_suppliers = all_suppliers.filter(city__icontains=data['city'])

        # Category filter
        if data.get('category'):
            all_suppliers = all_suppliers.filter(
                categories__name__icontains=data['category']
            ).distinct()

    context = {
        'shop': shop,
        'connected_suppliers': connected_suppliers,
        'all_suppliers': all_suppliers,
        'search_form': form,
    }

    return render(request, 'shops/supplier_list.html', context)

@login_required
def supplier_detail(request, supplier_id):
    """
    View details of a supplier
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)

    # Check if the shop has ordered from this supplier before
    has_ordered = Order.objects.filter(shop=shop, supplier=supplier).exists()

    # Get recent orders from this supplier
    recent_orders = Order.objects.filter(
        shop=shop,
        supplier=supplier
    ).order_by('-created_at')[:5]

    context = {
        'shop': shop,
        'supplier': supplier,
        'has_ordered': has_ordered,
        'recent_orders': recent_orders,
    }

    return render(request, 'shops/supplier_detail.html', context)

@login_required
def supplier_add(request):
    """
    Add a new supplier connection
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # This is just a search page to find suppliers to connect with
    form = SupplierSearchForm()

    context = {
        'search_form': form,
    }

    return render(request, 'shops/supplier_add.html', context)

@login_required
def supplier_remove(request, supplier_id):
    """
    Remove a supplier connection
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # This endpoint doesn't actually remove a connection as there's no direct Shop-Supplier relation
    # Instead, we just redirect back to the supplier list with a message
    messages.info(request, _('Supplier connections are automatically created when you place an order.'))
    return redirect('shops:supplier_list')

# Catalog Browsing Views

@login_required
def supplier_catalog(request, supplier_id):
    """
    Browse a supplier's product catalog
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)

    # Get all categories for this supplier
    categories = Category.objects.filter(supplier=supplier, parent__isnull=True)

    # Get all products for this supplier
    products_queryset = Product.objects.filter(supplier=supplier)

    # Apply availability filter if specified
    available_only = request.GET.get('available_only')
    if available_only:
        products_queryset = products_queryset.filter(is_available=True)

    # Apply category filter if specified
    category_id = request.GET.get('category')
    selected_category = None

    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id, supplier=supplier)

            # Include products from this category and its subcategories
            category_ids = [selected_category.id]
            subcategories = Category.objects.filter(parent=selected_category)
            category_ids.extend(subcategory.id for subcategory in subcategories)

            products_queryset = products_queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            pass

    # Apply search filter if specified
    query = request.GET.get('q', '')
    if query:
        products_queryset = products_queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )

    # Apply price range filter if specified
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            min_price = float(min_price)
            products_queryset = products_queryset.filter(price__gte=min_price)
        except ValueError:
            pass

    max_price = request.GET.get('max_price')
    if max_price:
        try:
            max_price = float(max_price)
            products_queryset = products_queryset.filter(price__lte=max_price)
        except ValueError:
            pass

    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    products_queryset = products_queryset.order_by(sort_by)

    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(products_queryset, 12)  # Show 12 products per page
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        products = paginator.page(paginator.num_pages)

    # Get cart count for the cart icon
    from decimal import Decimal
    cart = request.session.get('cart', {})
    cart_count = sum(1 for qty in cart.values() if Decimal(str(qty)) > 0)

    context = {
        'shop': shop,
        'supplier': supplier,
        'categories': categories,
        'selected_category': selected_category,
        'products': products,
        'query': query,
        'cart_count': cart_count,
    }

    return render(request, 'shops/supplier_catalog.html', context)

@login_required
def supplier_catalog_category(request, supplier_id, category_id):
    """
    Browse products in a specific category
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)
    category = get_object_or_404(Category, id=category_id, supplier=supplier)

    # Get all products in this category and its subcategories
    category_ids = [category.id]
    subcategories = Category.objects.filter(parent=category)
    category_ids.extend(subcategory.id for subcategory in subcategories)

    products = Product.objects.filter(
        supplier=supplier,
        is_available=True,
        category_id__in=category_ids
    )

    # Apply search filter if specified
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )

    context = {
        'shop': shop,
        'supplier': supplier,
        'category': category,
        'subcategories': subcategories,
        'products': products,
        'query': query,
    }

    return render(request, 'shops/supplier_catalog_category.html', context)

@login_required
def product_detail(request, supplier_id, product_id):
    """
    View details of a product
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)
    product = get_object_or_404(Product, id=product_id, supplier=supplier)

    # Initialize cart add form
    form = CartAddProductForm(product=product)

    context = {
        'shop': shop,
        'supplier': supplier,
        'product': product,
        'cart_form': form,
    }

    return render(request, 'shops/product_detail.html', context)

@login_required
def catalog_search(request, supplier_id):
    """
    Search products in a supplier's catalog
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)

    query = request.GET.get('q', '')

    if query:
        products = Product.objects.filter(
            supplier=supplier,
            is_available=True
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )
    else:
        products = Product.objects.none()

    context = {
        'shop': shop,
        'supplier': supplier,
        'products': products,
        'query': query,
    }

    return render(request, 'shops/catalog_search.html', context)

# Shopping Cart Views

@login_required
def cart_view(request):
    """
    View the shopping cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    # Get cart from session
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    supplier = None

    if cart:
        # Check if all products are from the same supplier
        product_ids = list(cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        suppliers = set(product.supplier_id for product in products)

        if len(suppliers) > 1:
            messages.error(request, _('Cart contains products from multiple suppliers. Only one supplier per order is allowed.'))
            request.session['cart'] = {}
            return redirect('shops:supplier_list')

        # Get supplier for the cart
        if suppliers:
            supplier_id = list(suppliers)[0]
            supplier = Supplier.objects.get(id=supplier_id)

        # Build cart items list
        from decimal import Decimal
        for product in products:
            quantity_str = cart.get(str(product.id), '0')
            # Convert quantity to Decimal for comparison and calculation
            try:
                decimal_quantity = Decimal(str(quantity_str))
            except:
                decimal_quantity = Decimal('0')

            if decimal_quantity > 0:
                item_total = product.price * decimal_quantity
                cart_items.append({
                    'product': product,
                    'quantity': decimal_quantity,  # Use the decimal quantity for consistency
                    'price': product.price,
                    'total': item_total,
                })
                total += item_total

    context = {
        'shop': shop,
        'cart_items': cart_items,
        'total': total,
        'supplier': supplier,
    }

    return render(request, 'shops/cart_view.html', context)

@login_required
def cart_add(request):
    """
    Add a product to the cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', '1')

        try:
            from decimal import Decimal
            product = Product.objects.get(id=product_id, is_available=True)

            # Convert quantity to Decimal
            try:
                quantity = Decimal(str(quantity))
            except:
                quantity = Decimal('1.0')

            # Ensure quantity is at least the minimum order quantity
            if quantity < product.min_order_quantity:
                quantity = Decimal(str(product.min_order_quantity))

            # Get cart from session
            cart = request.session.get('cart', {})

            # Check if cart already has items from a different supplier
            if cart:
                cart_product_ids = list(cart.keys())
                if cart_product_ids:  # Only check if there are actual products in the cart
                    cart_products = Product.objects.filter(id__in=cart_product_ids)
                    cart_suppliers = set(p.supplier_id for p in cart_products)

                    if cart_suppliers and product.supplier_id not in cart_suppliers:
                        # Ask user if they want to clear cart and start a new order
                        request.session['pending_product'] = {
                            'id': product.id,
                            'quantity': quantity,
                            'supplier_id': product.supplier_id,
                            'next': request.POST.get('next', 'shops:cart_view')
                        }
                        return redirect('shops:cart_switch_supplier')

            # Add/update product in cart - store as string to ensure it can be serialized in session
            cart[str(product_id)] = str(quantity)
            request.session['cart'] = cart

            messages.success(request, _('Product added to cart.'))

        except Product.DoesNotExist:
            messages.error(request, _('Product not found or not available.'))
        except ValueError:
            messages.error(request, _('Invalid quantity.'))

    # Redirect back to previous page or supplier catalog
    next_url = request.POST.get('next', 'shops:cart_view')
    return redirect(next_url)

@login_required
def cart_update(request):
    """
    Update product quantity in the cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', '0')

        try:
            from decimal import Decimal
            product = Product.objects.get(id=product_id)

            # Convert quantity to Decimal
            try:
                quantity = Decimal(str(quantity))
            except:
                quantity = Decimal('0.0')

            # Get cart from session
            cart = request.session.get('cart', {})

            if quantity > 0:
                # Ensure quantity is at least the minimum order quantity
                if quantity < product.min_order_quantity:
                    quantity = Decimal(str(product.min_order_quantity))

                # Update product quantity - store as string to ensure it can be serialized in session
                cart[str(product_id)] = str(quantity)
                messages.success(request, _('Cart updated.'))
            else:
                # Remove product from cart
                if str(product_id) in cart:
                    del cart[str(product_id)]
                    messages.success(request, _('Product removed from cart.'))

            request.session['cart'] = cart

        except Product.DoesNotExist:
            messages.error(request, _('Product not found.'))
        except ValueError:
            messages.error(request, _('Invalid quantity.'))

    return redirect('shops:cart_view')

@login_required
def cart_remove(request):
    """
    Remove a product from the cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')

        # Get cart from session
        cart = request.session.get('cart', {})

        # Remove product from cart
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
            messages.success(request, _('Product removed from cart.'))

    return redirect('shops:cart_view')

@login_required
def cart_clear(request):
    """
    Clear the cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Clear cart in session
    request.session['cart'] = {}

    messages.success(request, _('Cart cleared.'))
    return redirect('shops:cart_view')

@login_required
def cart_switch_supplier(request):
    """
    Handle switching suppliers in cart
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get pending product info
    pending_product = request.session.get('pending_product')

    if not pending_product:
        messages.error(request, _('No pending product found.'))
        return redirect('shops:cart_view')

    # If user confirmed the switch
    if request.method == 'POST':
        # Clear current cart
        request.session['cart'] = {}

        # Add the pending product to cart
        from decimal import Decimal
        cart = {}
        cart[str(pending_product['id'])] = str(pending_product['quantity'])
        request.session['cart'] = cart

        # Clear pending product
        del request.session['pending_product']

        messages.success(request, _('Cart updated with new supplier.'))

        # Redirect to the next URL or cart view
        next_url = pending_product.get('next', 'shops:cart_view')
        return redirect(next_url)

    # Get supplier information for display
    try:
        current_product_ids = list(request.session.get('cart', {}).keys())
        current_supplier = None

        if current_product_ids:
            current_product = Product.objects.filter(id__in=current_product_ids).first()
            if current_product:
                current_supplier = current_product.supplier

        new_supplier = Supplier.objects.get(id=pending_product['supplier_id'])
        pending_product_obj = Product.objects.get(id=pending_product['id'])

        context = {
            'current_supplier': current_supplier,
            'new_supplier': new_supplier,
            'pending_product': pending_product_obj,
            'quantity': pending_product['quantity']
        }

        return render(request, 'shops/cart_switch_supplier.html', context)

    except (Supplier.DoesNotExist, Product.DoesNotExist):
        messages.error(request, _('Invalid product or supplier.'))
        return redirect('shops:cart_view')

# Order Management Views

@login_required
def order_list(request):
    """
    List all orders placed by the shop
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    # Get all orders for this shop
    orders = Order.objects.filter(shop=shop).order_by('-created_at')

    # Apply filters if specified
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    supplier_id = request.GET.get('supplier')
    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Get cart items count for the quick actions section
    from decimal import Decimal
    cart = request.session.get('cart', {})
    cart_items_count = sum(1 for qty in cart.values() if Decimal(str(qty)) > 0)

    # Add a custom filter for the template
    from django.template.defaulttags import register

    @register.filter
    def filter_by_status(orders, status):
        return [order for order in orders if order.status == status]

    context = {
        'shop': shop,
        'orders': orders,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'suppliers': Supplier.objects.filter(orders__shop=shop).distinct(),
        'cart_items_count': cart_items_count,
    }

    return render(request, 'shops/order_list.html', context)

@login_required
def order_create(request):
    """
    Create a new order
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    # Check if cart is empty
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, _('Your cart is empty. Please add products before creating an order.'))
        return redirect('shops:supplier_list')

    # Get cart items
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids)

    # Check if all products are from the same supplier
    suppliers = set(product.supplier_id for product in products)
    if len(suppliers) > 1:
        messages.error(request, _('Cart contains products from multiple suppliers. Only one supplier per order is allowed.'))
        request.session['cart'] = {}
        return redirect('shops:supplier_list')

    # Get supplier for the order
    supplier_id = list(suppliers)[0]
    supplier = Supplier.objects.get(id=supplier_id)

    if request.method == 'POST':
        # Add supplier to initial data to ensure it's included in the form
        form = OrderForm(request.POST, user=request.user, initial={'supplier': supplier})
        if form.is_valid():
            order = form.save(commit=False)
            order.shop = shop
            order.supplier = supplier
            order.status = 'DRAFT'
            order.save()
        else:
            # Print form errors for debugging
            print(f"Form errors: {form.errors}")

        if form.is_valid():
            # Add items from cart to order
            from decimal import Decimal
            for product in products:
                quantity_str = cart.get(str(product.id), '0')
                # Convert quantity to Decimal for comparison and calculation
                try:
                    decimal_quantity = Decimal(str(quantity_str))
                except:
                    decimal_quantity = Decimal('0')

                if decimal_quantity > 0:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=decimal_quantity,
                        unit_price=product.price,
                        total_price=product.price * decimal_quantity
                    )

            # Clear cart
            request.session['cart'] = {}

            messages.success(request, _('Order created successfully.'))
            return redirect('shops:order_detail', order_id=order.id)
    else:
        form = OrderForm(user=request.user, initial={'supplier': supplier})

    # Calculate cart totals
    from decimal import Decimal
    cart_items = []
    total = 0
    for product in products:
        quantity_str = cart.get(str(product.id), '0')
        # Convert quantity to Decimal for comparison and calculation
        try:
            decimal_quantity = Decimal(str(quantity_str))
        except:
            decimal_quantity = Decimal('0')

        if decimal_quantity > 0:
            item_total = product.price * decimal_quantity
            cart_items.append({
                'product': product,
                'quantity': decimal_quantity,  # Use the decimal quantity for consistency
                'price': product.price,
                'total': item_total,
            })
            total += item_total

    context = {
        'shop': shop,
        'supplier': supplier,
        'form': form,
        'cart_items': cart_items,
        'total': total,
    }

    return render(request, 'shops/order_create.html', context)

@login_required
def order_detail(request, order_id):
    """
    View details of an order
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    # Get all items for this order
    order_items = order.items.all()

    context = {
        'shop': shop,
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'shops/order_detail.html', context)

@login_required
def order_reorder(request, order_id):
    """
    Create a new order based on a previous one
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    original_order = get_object_or_404(Order, id=order_id, shop=shop)

    # Clear current cart
    cart = {}

    # Add items from original order to cart
    for item in original_order.items.all():
        # Check if product is still available
        try:
            product = Product.objects.get(id=item.product.id, is_available=True)
            cart[str(product.id)] = str(item.quantity)
        except Product.DoesNotExist:
            # Skip unavailable products
            pass

    # Save cart to session
    request.session['cart'] = cart

    if not cart:
        messages.warning(request, _('None of the products from the original order are available.'))
        return redirect('shops:supplier_catalog', supplier_id=original_order.supplier.id)

    messages.success(request, _('Order items added to cart. You can now modify the order before submitting.'))
    return redirect('shops:cart_view')

@login_required
def order_cancel(request, order_id):
    """
    Cancel an order
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    # Check if order can be cancelled
    if order.status not in ['DRAFT', 'SUBMITTED', 'CONFIRMED']:
        messages.error(request, _('This order cannot be cancelled.'))
        return redirect('shops:order_detail', order_id=order.id)

    if request.method == 'POST':
        # Update order status
        old_status = order.status
        order.status = 'CANCELLED'
        order.save()

        # Send notification
        from notifications.tasks import send_order_status_notification
        send_order_status_notification.delay(order.id, old_status, 'CANCELLED')

        messages.success(request, _('Order cancelled successfully.'))
        return redirect('shops:order_detail', order_id=order.id)

    context = {
        'shop': shop,
        'order': order,
    }

    return render(request, 'shops/order_cancel.html', context)

@login_required
def order_submit(request, order_id):
    """
    Submit a draft order to the supplier
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    # Check if order can be submitted
    if order.status != 'DRAFT':
        messages.error(request, _('This order has already been submitted.'))
        return redirect('shops:order_detail', order_id=order.id)

    # Update order status
    old_status = order.status
    order.status = 'SUBMITTED'
    order.submitted_at = timezone.now()
    order.save()

    # Send notification
    try:
        from notifications.tasks import send_order_status_notification
        send_order_status_notification.delay(order.id, old_status, 'SUBMITTED')
    except:
        # Handle case where notification module is not available
        pass

    messages.success(request, _('Order submitted successfully.'))
    return redirect('shops:order_detail', order_id=order.id)

@login_required
def add_order_message(request, order_id):
    """
    Add a message to an order
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    if request.method == 'POST':
        message_content = request.POST.get('message', '').strip()

        if message_content:
            # Create message
            from orders.models import OrderMessage
            OrderMessage.objects.create(
                order=order,
                user=request.user,
                content=message_content,
                is_from_shop=True
            )

            messages.success(request, _('Message sent successfully.'))
        else:
            messages.error(request, _('Message cannot be empty.'))

    return redirect('shops:order_detail', order_id=order.id)

@login_required
def download_invoice(request, order_id):
    """
    Generate and download an invoice for an order
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    # For now, just redirect back to the order detail page with a message
    messages.info(request, _('Invoice generation is not yet implemented.'))
    return redirect('shops:order_detail', order_id=order.id)

@login_required
def track_delivery(request, delivery_id):
    """
    Track a delivery
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    shop = get_object_or_404(Shop, admin=request.user)

    # Get the delivery
    from orders.models import Delivery
    delivery = get_object_or_404(Delivery, id=delivery_id, order__shop=shop)

    context = {
        'shop': shop,
        'delivery': delivery,
        'order': delivery.order,
    }

    return render(request, 'shops/track_delivery.html', context)

# API Endpoints

@login_required
def api_quick_reorder(request):
    """
    API endpoint for quick reorder functionality and cart status
    """
    # Ensure user is a shop
    if not request.user.is_shop:
        return JsonResponse({'error': 'Permission denied'})

    # Get cart count
    from decimal import Decimal
    cart = request.session.get('cart', {})
    cart_count = sum(1 for qty in cart.values() if Decimal(str(qty)) > 0)

    return JsonResponse({
        'cart_count': cart_count,
    })
