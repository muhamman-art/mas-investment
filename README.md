# MAS INVESTMENT — Multi-Vendor E-Commerce Platform

A production-ready Django 5+ multi-vendor e-commerce and delivery management platform.

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Django 5, Django REST Framework |
| Database | PostgreSQL 16 |
| Authentication | JWT (SimpleJWT) + Session |
| Frontend | Bootstrap 5, Vanilla JS |
| Server | Gunicorn + Nginx |
| Container | Docker + Docker Compose |

---

## 🏗️ Project Structure

```
mas_investment/
├── config/                   # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/             # Users, auth, customer profiles
│   ├── products/             # Products, categories, cart, wishlist
│   ├── orders/               # Orders, checkout, payment receipts
│   ├── vendors/              # Vendor profiles, withdrawals
│   ├── riders/               # Rider profiles, deliveries
│   ├── staff/                # Staff panel, admin panel views
│   ├── support/              # Support tickets
│   └── notifications/        # Notification system
├── templates/
│   ├── base/                 # base.html, dashboard_base.html
│   ├── auth/                 # login, register, password reset
│   ├── customer/             # shop, cart, checkout, orders
│   ├── vendor/               # vendor dashboard
│   ├── rider/                # rider dashboard
│   ├── staff/                # staff dashboard, receipt review
│   ├── admin_panel/          # super admin dashboard
│   ├── emails/               # email templates
│   └── partials/             # reusable components
├── static/
│   ├── css/main.css
│   ├── css/dashboard.css
│   ├── js/main.js
│   └── js/dashboard.js
├── media/                    # User uploads
├── docker/
│   ├── Dockerfile
│   └── nginx.conf
├── scripts/
│   └── seed_data.py
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

## 👥 User Roles

| Role | Access |
|---|---|
| **Super Admin** | Full platform management, analytics, all dashboards |
| **Staff** | Verify payments, manage orders, handle tickets, assign riders |
| **Vendor** | Manage products, view orders, wallet, withdrawals |
| **Rider** | Accept/update deliveries, view assigned orders |
| **Customer** | Shop, cart, checkout, order tracking, support |

---

## ⚙️ Setup

### Prerequisites
- Python 3.13+
- PostgreSQL 16+
- Docker & Docker Compose (for production)

### Local Development

```bash
# 1. Clone and setup virtual environment
git clone https://github.com/your-org/mas-investment.git
cd mas-investment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL database
psql -U postgres
CREATE DATABASE mas_investment_db;
CREATE USER mas_user WITH PASSWORD 'mas_secure_password_2024';
GRANT ALL PRIVILEGES ON DATABASE mas_investment_db TO mas_user;
\q

# 4. Configure environment variables (optional, defaults work for dev)
cp .env.example .env
# Edit .env as needed

# 5. Run migrations
python manage.py migrate

# 6. Seed demo data
python manage.py shell < scripts/seed_data.py

# 7. Create static files
python manage.py collectstatic --noinput

# 8. Run development server
python manage.py runserver
```

Open: http://localhost:8000

### Docker (Production)

```bash
# Build and start all services
docker-compose up --build -d

# Run migrations
docker-compose exec web python manage.py migrate

# Seed data
docker-compose exec web python manage.py shell < scripts/seed_data.py

# Logs
docker-compose logs -f web
```

---

## 🔐 Demo Credentials

| Role | Email | Password |
|---|---|---|
| Super Admin | admin@masinvestment.com | Admin@12345 |
| Staff | staff@masinvestment.com | Staff@12345 |
| Vendor | vendor@masinvestment.com | Vendor@12345 |
| Rider | rider@masinvestment.com | Rider@12345 |
| Customer | customer@masinvestment.com | Customer@12345 |

---

## 📦 Order Workflow

```
Customer places order
        ↓
Selects Bank Transfer → Uploads Receipt
        ↓
Staff reviews receipt → Approve / Reject
        ↓ (Approved)
Order status: Paid → Processing
        ↓
Vendor prepares order
        ↓
Staff assigns rider
        ↓
Rider: Accepted → Picked Up → Out for Delivery
        ↓
Delivered ✅ (Customer & Vendor notified)
```

---

## 🔌 API Endpoints (REST)

- `POST /auth/login/` — Login
- `POST /auth/register/` — Register
- `GET /shop/` — Product listing
- `GET /shop/product/<slug>/` — Product detail
- `POST /shop/cart/add/<id>/` — Add to cart
- `POST /orders/checkout/` — Place order
- `GET /customer/orders/` — Order history

JWT authentication via `Authorization: Bearer <token>` header.

---

## 🛡️ Security

- JWT token rotation with blacklist
- CSRF protection on all forms
- Role-based access control decorators
- File upload validation (type + size)
- XSS protection headers
- Password hashing (Django PBKDF2)
- Secure file storage paths

---

## 📧 Email Configuration

For production, update `settings.py` or set environment variables:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 🏦 Payment Flow

**Bank Transfer:**
1. Customer selects Bank Transfer at checkout
2. Customer uploads payment receipt (JPG/JPEG/PNG/PDF, max 10MB)
3. Order status → `Awaiting Verification`
4. Staff reviews receipt image in Staff Dashboard
5. Staff approves → Order status → `Paid → Processing`
6. Staff rejects → Customer notified with reason

**Cash on Delivery:**
- Order goes directly to `Processing` status

---

## 📊 Admin Dashboard Features

- Revenue, Orders, Customers, Vendors, Riders KPI cards
- 30-day Sales & Revenue Chart (Chart.js)
- Vendor approval queue
- Withdrawal request management
- Complete order management
- Customer support ticket system

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open Pull Request

---

## 📄 License

MIT License — © 2024 MAS Investment

---

*Built with ❤️ using Django 5 + Bootstrap 5*
