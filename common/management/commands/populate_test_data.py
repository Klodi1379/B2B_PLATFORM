import random
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from users.models import User
from suppliers.models import Supplier
from shops.models import Shop
from products.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with test data'

    def add_arguments(self, parser):
        parser.add_argument('--suppliers', type=int, default=5, help='Number of suppliers to create')
        parser.add_argument('--shops', type=int, default=10, help='Number of shops to create')
        parser.add_argument('--products', type=int, default=50, help='Number of products to create')
        parser.add_argument('--orders', type=int, default=20, help='Number of orders to create')

    def handle(self, *args, **options):
        num_suppliers = options['suppliers']
        num_shops = options['shops']
        num_products = options['products']
        num_orders = options['orders']
        
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        try:
            with transaction.atomic():
                # Create users, suppliers, and shops
                supplier_users = self.create_supplier_users(num_suppliers)
                shop_users = self.create_shop_users(num_shops)
                
                suppliers = self.create_suppliers(supplier_users)
                shops = self.create_shops(shop_users)
                
                # Create categories and products
                categories = self.create_categories(suppliers)
                products = self.create_products(categories, suppliers, num_products)
                
                # Create orders
                orders = self.create_orders(shops, suppliers, products, num_orders)
                
            self.stdout.write(self.style.SUCCESS('Successfully populated the database!'))
            self.stdout.write(f'Created {len(supplier_users)} supplier users')
            self.stdout.write(f'Created {len(shop_users)} shop users')
            self.stdout.write(f'Created {len(suppliers)} suppliers')
            self.stdout.write(f'Created {len(shops)} shops')
            self.stdout.write(f'Created {len(categories)} categories')
            self.stdout.write(f'Created {len(products)} products')
            self.stdout.write(f'Created {len(orders)} orders')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating database: {str(e)}'))
            raise
    
    def create_supplier_users(self, count):
        self.stdout.write('Creating supplier users...')
        users = []
        
        for i in range(1, count + 1):
            username = f'supplier{i}@example.com'
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                users.append(User.objects.get(username=username))
                continue
                
            user = User.objects.create_user(
                username=username,
                email=username,
                password='password123',
                first_name=f'Supplier{i}',
                last_name=f'User{i}',
                user_type='SUPPLIER',
                phone=f'+355 69 {random.randint(1000000, 9999999)}'
            )
            users.append(user)
            
        return users
    
    def create_shop_users(self, count):
        self.stdout.write('Creating shop users...')
        users = []
        
        for i in range(1, count + 1):
            username = f'shop{i}@example.com'
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                users.append(User.objects.get(username=username))
                continue
                
            user = User.objects.create_user(
                username=username,
                email=username,
                password='password123',
                first_name=f'Shop{i}',
                last_name=f'User{i}',
                user_type='SHOP',
                phone=f'+355 69 {random.randint(1000000, 9999999)}'
            )
            users.append(user)
            
        return users
    
    def create_suppliers(self, users):
        self.stdout.write('Creating suppliers...')
        suppliers = []
        
        cities = ['Tiranë', 'Durrës', 'Vlorë', 'Shkodër', 'Elbasan', 'Fier', 'Korçë']
        supplier_types = ['Distributor', 'Manufacturer', 'Wholesaler', 'Importer']
        
        for user in users:
            # Skip if supplier already exists for this user
            if Supplier.objects.filter(admin=user).exists():
                suppliers.append(Supplier.objects.get(admin=user))
                continue
                
            city = random.choice(cities)
            supplier = Supplier.objects.create(
                name=f'{user.first_name} {random.choice(supplier_types)}',
                description=f'A {random.choice(supplier_types).lower()} specializing in various products.',
                address=f'Rruga {random.randint(1, 100)}, {city}',
                city=city,
                country='Albania',
                tax_id=f'AL{random.randint(10000000, 99999999)}',
                email=user.email,
                phone=user.phone,
                admin=user
            )
            suppliers.append(supplier)
            
        return suppliers
    
    def create_shops(self, users):
        self.stdout.write('Creating shops...')
        shops = []
        
        cities = ['Tiranë', 'Durrës', 'Vlorë', 'Shkodër', 'Elbasan', 'Fier', 'Korçë', 
                 'Berat', 'Lushnjë', 'Kavajë', 'Pogradec', 'Lezhë', 'Gjirokastër']
        shop_types = ['Minimarket', 'Supermarket', 'Convenience Store', 'Grocery Store', 'Kiosk']
        
        # Tirana coordinates for random location generation
        tirana_lat, tirana_lng = 41.3275, 19.8187
        
        for user in users:
            # Skip if shop already exists for this user
            if Shop.objects.filter(admin=user).exists():
                shops.append(Shop.objects.get(admin=user))
                continue
                
            city = random.choice(cities)
            
            # Generate random coordinates near Tirana
            lat = tirana_lat + (random.random() - 0.5) * 0.1
            lng = tirana_lng + (random.random() - 0.5) * 0.1
            
            shop = Shop.objects.create(
                name=f'{user.first_name}\'s {random.choice(shop_types)}',
                shop_type=random.choice(shop_types),
                address=f'Rruga {random.randint(1, 100)}, {city}',
                city=city,
                country='Albania',
                latitude=lat,
                longitude=lng,
                tax_id=f'AL{random.randint(10000000, 99999999)}',
                email=user.email,
                phone=user.phone,
                admin=user
            )
            shops.append(shop)
            
        return shops
    
    def create_categories(self, suppliers):
        self.stdout.write('Creating categories...')
        categories = []
        
        category_names = [
            'Dairy', 'Beverages', 'Snacks', 'Bakery', 'Canned Goods', 
            'Frozen Foods', 'Produce', 'Meat', 'Cleaning Supplies', 'Personal Care',
            'Baby Products', 'Pet Supplies', 'Office Supplies', 'Electronics'
        ]
        
        for supplier in suppliers:
            # Create 3-5 categories per supplier
            num_categories = random.randint(3, 5)
            selected_categories = random.sample(category_names, num_categories)
            
            for name in selected_categories:
                # Skip if category already exists for this supplier
                if Category.objects.filter(name=name, supplier=supplier).exists():
                    categories.append(Category.objects.get(name=name, supplier=supplier))
                    continue
                    
                category = Category.objects.create(
                    name=name,
                    description=f'{name} products from {supplier.name}',
                    supplier=supplier
                )
                categories.append(category)
                
        return categories
    
    def create_products(self, categories, suppliers, count):
        self.stdout.write('Creating products...')
        products = []
        
        product_names = {
            'Dairy': ['Milk', 'Cheese', 'Yogurt', 'Butter', 'Cream', 'Ice Cream'],
            'Beverages': ['Water', 'Juice', 'Soda', 'Coffee', 'Tea', 'Energy Drink'],
            'Snacks': ['Chips', 'Cookies', 'Crackers', 'Nuts', 'Chocolate', 'Candy'],
            'Bakery': ['Bread', 'Rolls', 'Cake', 'Pastry', 'Muffins', 'Donuts'],
            'Canned Goods': ['Beans', 'Soup', 'Tuna', 'Corn', 'Tomatoes', 'Fruit'],
            'Frozen Foods': ['Pizza', 'Vegetables', 'Meals', 'Ice Cream', 'Meat', 'Fish'],
            'Produce': ['Apples', 'Bananas', 'Oranges', 'Potatoes', 'Onions', 'Tomatoes'],
            'Meat': ['Chicken', 'Beef', 'Pork', 'Lamb', 'Sausage', 'Bacon'],
            'Cleaning Supplies': ['Detergent', 'Soap', 'Bleach', 'Wipes', 'Spray', 'Sponges'],
            'Personal Care': ['Shampoo', 'Soap', 'Toothpaste', 'Deodorant', 'Lotion', 'Razor'],
            'Baby Products': ['Diapers', 'Formula', 'Baby Food', 'Wipes', 'Shampoo', 'Lotion'],
            'Pet Supplies': ['Dog Food', 'Cat Food', 'Treats', 'Toys', 'Litter', 'Accessories'],
            'Office Supplies': ['Paper', 'Pens', 'Notebooks', 'Folders', 'Tape', 'Staples'],
            'Electronics': ['Batteries', 'Chargers', 'Cables', 'Headphones', 'Speakers', 'Adapters']
        }
        
        units = {
            'Dairy': ['liter', 'kg', 'piece'],
            'Beverages': ['liter', 'bottle', 'can', 'pack'],
            'Snacks': ['pack', 'box', 'bag', 'kg'],
            'Bakery': ['piece', 'loaf', 'pack', 'kg'],
            'Canned Goods': ['can', 'piece', 'pack'],
            'Frozen Foods': ['pack', 'box', 'kg'],
            'Produce': ['kg', 'piece', 'bag'],
            'Meat': ['kg', 'pack', 'piece'],
            'Cleaning Supplies': ['bottle', 'pack', 'piece'],
            'Personal Care': ['bottle', 'pack', 'piece'],
            'Baby Products': ['pack', 'box', 'piece'],
            'Pet Supplies': ['kg', 'pack', 'piece'],
            'Office Supplies': ['pack', 'box', 'piece'],
            'Electronics': ['piece', 'pack', 'box']
        }
        
        # Create products for each category
        for category in categories:
            # Create 3-8 products per category
            num_products = random.randint(3, 8)
            
            if category.name in product_names:
                available_products = product_names[category.name]
                selected_products = random.sample(available_products, min(num_products, len(available_products)))
                
                for name in selected_products:
                    # Generate a unique SKU
                    sku = f'{category.supplier.id}-{category.id}-{random.randint(1000, 9999)}'
                    
                    # Skip if product with this SKU already exists
                    if Product.objects.filter(sku=sku, supplier=category.supplier).exists():
                        products.append(Product.objects.get(sku=sku, supplier=category.supplier))
                        continue
                    
                    # Choose appropriate unit
                    unit = random.choice(units.get(category.name, ['piece']))
                    
                    # Generate price based on unit
                    if unit == 'kg':
                        price = round(Decimal(random.uniform(1.5, 15.0)), 2)
                    elif unit in ['liter', 'bottle']:
                        price = round(Decimal(random.uniform(0.8, 5.0)), 2)
                    elif unit in ['pack', 'box']:
                        price = round(Decimal(random.uniform(2.0, 10.0)), 2)
                    else:  # piece, can, etc.
                        price = round(Decimal(random.uniform(0.5, 8.0)), 2)
                    
                    # Generate min order quantity
                    if unit in ['kg', 'liter']:
                        min_order = Decimal('0.5')
                    elif unit == 'piece' and price < 1:
                        min_order = 5
                    else:
                        min_order = 1
                    
                    product = Product.objects.create(
                        name=f'{name}',
                        description=f'Quality {name.lower()} from {category.supplier.name}',
                        sku=sku,
                        barcode=f'{random.randint(1000000000000, 9999999999999)}',
                        unit=unit,
                        price=price,
                        is_available=random.random() > 0.1,  # 90% chance of being available
                        min_order_quantity=min_order,
                        supplier=category.supplier,
                        category=category
                    )
                    products.append(product)
                    
                    # Stop if we've reached the desired count
                    if len(products) >= count:
                        break
            
            # Stop if we've reached the desired count
            if len(products) >= count:
                break
                
        return products
    
    def create_orders(self, shops, suppliers, products, count):
        self.stdout.write('Creating orders...')
        orders = []
        
        # Create orders
        for i in range(count):
            # Select random shop and supplier
            shop = random.choice(shops)
            supplier = random.choice(suppliers)
            
            # Get products from this supplier
            supplier_products = [p for p in products if p.supplier == supplier]
            
            if not supplier_products:
                continue
                
            # Select random status
            status_weights = [
                ('DRAFT', 0.05),
                ('SUBMITTED', 0.1),
                ('CONFIRMED', 0.15),
                ('PROCESSING', 0.2),
                ('READY', 0.15),
                ('DELIVERING', 0.1),
                ('DELIVERED', 0.2),
                ('CANCELLED', 0.05)
            ]
            status = random.choices(
                [s[0] for s in status_weights],
                weights=[s[1] for s in status_weights],
                k=1
            )[0]
            
            # Generate dates
            created_date = timezone.now() - datetime.timedelta(days=random.randint(0, 30))
            
            # Create order
            order = Order.objects.create(
                shop=shop,
                supplier=supplier,
                status=status,
                notes=f'Test order {i+1}' if random.random() > 0.7 else '',
                created_at=created_date
            )
            
            # Set submitted_at if status is not DRAFT
            if status != 'DRAFT':
                order.submitted_at = created_date + datetime.timedelta(hours=random.randint(1, 24))
                
            # Set delivery date if status is beyond CONFIRMED
            if status in ['PROCESSING', 'READY', 'DELIVERING', 'DELIVERED']:
                delivery_date = order.submitted_at + datetime.timedelta(days=random.randint(1, 7))
                order.delivery_date = delivery_date.date()
                
                # Set delivery time window
                time_windows = ['Morning (8:00-12:00)', 'Afternoon (12:00-16:00)', 'Evening (16:00-20:00)']
                order.delivery_time_window = random.choice(time_windows)
            
            order.save()
            
            # Create order items
            num_items = random.randint(2, 8)
            selected_products = random.sample(supplier_products, min(num_items, len(supplier_products)))
            
            for product in selected_products:
                # Generate quantity
                if product.unit in ['kg', 'liter']:
                    quantity = round(Decimal(random.uniform(0.5, 10.0)), 1)
                else:
                    quantity = random.randint(1, 20)
                
                # Ensure minimum order quantity
                quantity = max(quantity, product.min_order_quantity)
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    total_price=quantity * product.price
                )
            
            # Update order total
            order.save()
            orders.append(order)
            
        return orders
