"""
MAS Investment - Seed Data Script
Run: python manage.py shell < scripts/seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.accounts.models import User, CustomerProfile
from apps.vendors.models import Vendor
from apps.riders.models import Rider
from apps.staff.models import StaffProfile
from apps.products.models import Category, Product
from apps.orders.models import Cart

print("🌱 Seeding MAS Investment database...")

# ── SUPER ADMIN ────────────────────────────────────────────
admin, created = User.objects.get_or_create(
    email='admin@masinvestment.com',
    defaults={
        'first_name': 'Super', 'last_name': 'Admin',
        'role': User.SUPER_ADMIN,
        'is_staff': True, 'is_superuser': True,
        'is_verified': True, 'is_active': True,
        'phone': '+2348000000000',
    }
)
if created:
    admin.set_password('Admin@12345')
    admin.save()
    print(f"  ✅ Super Admin: admin@masinvestment.com / Admin@12345")
else:
    print(f"  ℹ️  Super Admin already exists")

# ── STAFF ──────────────────────────────────────────────────
staff_user, created = User.objects.get_or_create(
    email='staff@masinvestment.com',
    defaults={
        'first_name': 'Jane', 'last_name': 'Staff',
        'role': User.STAFF, 'is_staff': True,
        'is_verified': True, 'is_active': True,
    }
)
if created:
    staff_user.set_password('Staff@12345')
    staff_user.save()
    StaffProfile.objects.create(
        user=staff_user,
        department=StaffProfile.DEPT_OPERATIONS,
        can_verify_payments=True,
        can_manage_orders=True,
    )
    print(f"  ✅ Staff: staff@masinvestment.com / Staff@12345")

# ── VENDOR ────────────────────────────────────────────────
vendor_user, created = User.objects.get_or_create(
    email='vendor@masinvestment.com',
    defaults={
        'first_name': 'Ahmed', 'last_name': 'Vendor',
        'role': User.VENDOR, 'is_verified': True, 'is_active': True,
        'phone': '+2348111111111',
    }
)
if created:
    vendor_user.set_password('Vendor@12345')
    vendor_user.save()
    vendor = Vendor.objects.create(
        user=vendor_user,
        business_name='Ahmed Electronics',
        business_description='Quality electronics and gadgets at affordable prices.',
        business_email='vendor@masinvestment.com',
        business_phone='+2348111111111',
        business_address='15 Electronics Way, Computer Village',
        city='Ikeja', state='Lagos', country='Nigeria',
        status=Vendor.STATUS_APPROVED,
        approved_at=timezone.now(),
        commission_rate=10.00,
        wallet_balance=0,
    )
    print(f"  ✅ Vendor: vendor@masinvestment.com / Vendor@12345")
else:
    vendor = vendor_user.vendor_profile

# ── RIDER ─────────────────────────────────────────────────
rider_user, created = User.objects.get_or_create(
    email='rider@masinvestment.com',
    defaults={
        'first_name': 'Emeka', 'last_name': 'Rider',
        'role': User.RIDER, 'is_verified': True, 'is_active': True,
        'phone': '+2348222222222',
    }
)
if created:
    rider_user.set_password('Rider@12345')
    rider_user.save()
    Rider.objects.create(
        user=rider_user,
        status=Rider.STATUS_ACTIVE,
        vehicle_type=Rider.VEHICLE_MOTORCYCLE,
        vehicle_plate='LSD-123-AA',
        is_available=True,
    )
    print(f"  ✅ Rider: rider@masinvestment.com / Rider@12345")

# ── CUSTOMER ───────────────────────────────────────────────
customer_user, created = User.objects.get_or_create(
    email='customer@masinvestment.com',
    defaults={
        'first_name': 'Fatima', 'last_name': 'Customer',
        'role': User.CUSTOMER, 'is_verified': True, 'is_active': True,
        'phone': '+2348333333333',
    }
)
if created:
    customer_user.set_password('Customer@12345')
    customer_user.save()
    CustomerProfile.objects.create(
        user=customer_user,
        address='5 Palm Close, Victoria Island',
        city='Lagos', state='Lagos', country='Nigeria',
    )
    Cart.objects.create(user=customer_user)
    print(f"  ✅ Customer: customer@masinvestment.com / Customer@12345")

# ── CATEGORIES ────────────────────────────────────────────
categories_data = [
    ('Electronics', 'bi-phone', 'Phones, laptops, gadgets and accessories'),
    ('Fashion', 'bi-bag', 'Clothing, shoes and accessories'),
    ('Food & Grocery', 'bi-cart', 'Fresh food and grocery items'),
    ('Home & Living', 'bi-house', 'Furniture and home essentials'),
    ('Health & Beauty', 'bi-heart-pulse', 'Health products and cosmetics'),
    ('Sports', 'bi-trophy', 'Sports and fitness equipment'),
    ('Books & Education', 'bi-book', 'Books and educational materials'),
    ('Automotive', 'bi-car-front', 'Car parts and accessories'),
]
for i, (name, icon, desc) in enumerate(categories_data):
    cat, created = Category.objects.get_or_create(name=name, defaults={'icon': icon, 'description': desc, 'order': i})
    if created:
        print(f"  ✅ Category: {name}")

# ── PRODUCTS ──────────────────────────────────────────────
if hasattr(vendor_user, 'vendor_profile'):
    v = vendor_user.vendor_profile
    electronics = Category.objects.get(name='Electronics')

    products_data = [
        ('Samsung Galaxy A54 5G', 'Latest Samsung smartphone with 5G capability, 256GB storage, 8GB RAM, and 50MP camera.', 285000, 320000, 25),
        ('Apple AirPods Pro (2nd Gen)', 'Noise-cancelling wireless earbuds with spatial audio and 30-hour battery life.', 195000, 220000, 15),
        ('HP Laptop 15s', '15.6" Full HD laptop with Intel Core i5, 8GB RAM, 512GB SSD, Windows 11.', 450000, 490000, 8),
        ('Xiaomi Power Bank 20000mAh', 'Fast charging power bank with USB-C and dual USB outputs.', 18500, 22000, 50),
        ('JBL Flip 6 Bluetooth Speaker', 'Portable waterproof speaker with 12h battery and powerful sound.', 67000, 75000, 20),
        ('Sony WH-1000XM5 Headphones', 'Industry-leading noise cancelling wireless headphones.', 285000, 310000, 10),
        ('Apple Watch Series 9', 'Advanced GPS smartwatch with health monitoring and crash detection.', 425000, 460000, 5),
        ('Samsung 32" Smart TV', 'Full HD Smart TV with Netflix, YouTube and streaming apps built-in.', 185000, 210000, 12),
    ]

    for name, desc, price, compare, stock in products_data:
        p, created = Product.objects.get_or_create(
            vendor=v, name=name,
            defaults={
                'description': desc,
                'short_description': desc[:150],
                'price': price,
                'compare_price': compare,
                'stock': stock,
                'category': electronics,
                'status': Product.STATUS_ACTIVE,
                'is_featured': True,
            }
        )
        if created:
            print(f"  ✅ Product: {name}")

print("\n🎉 Seed data complete!")
print("\nLogin credentials:")
print("  Super Admin:  admin@masinvestment.com    / Admin@12345")
print("  Staff:        staff@masinvestment.com    / Staff@12345")
print("  Vendor:       vendor@masinvestment.com   / Vendor@12345")
print("  Rider:        rider@masinvestment.com    / Rider@12345")
print("  Customer:     customer@masinvestment.com / Customer@12345")
