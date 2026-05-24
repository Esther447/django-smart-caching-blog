# Django Smart Caching Blog — Complete Project Documentation

## Overview

This is a Django REST API built in two layers:

1. **Blog API** — demonstrates smart caching strategies using Django's built-in in-memory cache
2. **Merchant Financing API** — handles merchant registration, financing requests, async alerts, filtering, pagination, and JWT authentication

---

## Project Structure

```
django-smart-caching-blog/
├── alerts/
│   ├── __init__.py
│   └── tasks.py                  # Async alert using threading + logging
├── blog/
│   ├── __init__.py
│   ├── models.py                 # Post model (title, content, created_at)
│   ├── urls.py                   # /api/blog/ routes
│   └── views.py                  # PostList + PostDetail with 4 caching levels
├── config/
│   ├── __init__.py
│   ├── settings.py               # All project settings (env vars, cache, DRF, DB)
│   └── urls.py                   # Root URL config
├── financing/
│   ├── migrations/               # DB migrations
│   ├── __init__.py
│   ├── models.py                 # FinancingRequest model with STATUS_CHOICES
│   ├── serializers.py            # Includes amount > 0 validation
│   ├── urls.py                   # list, create, update routes
│   └── views.py                  # FinancingCreateView, FinancingListView, FinancingUpdateView
├── merchants/
│   ├── migrations/               # DB migrations
│   ├── __init__.py
│   ├── models.py                 # Merchant model
│   ├── serializers.py
│   ├── urls.py                   # DefaultRouter auto-generates all CRUD routes
│   └── views.py                  # MerchantViewSet with filtering + search
├── .env                          # Environment variables (never committed to git)
├── .gitignore                    # Excludes venv/, __pycache__/, .env, db.sqlite3
├── manage.py
├── Procfile                      # gunicorn entry point for deployment
├── requirements.txt
└── README.md
```

---

## How We Built It — Step by Step

### Step 1: Project Setup
Created the Django project with a `config/` package as the settings module and separate apps for each concern: `blog`, `merchants`, `financing`, `alerts`.

### Step 2: Blog App — Smart Caching
Built `PostList` and `PostDetail` views using Django's `APIView` with manual cache control.

**4 Caching Levels implemented:**

| Level | What it does | How |
|-------|-------------|-----|
| 🟢 Level 1 | Cache full post list | `cache.set('all_posts', data, timeout=CACHE_TTL)` |
| 🟡 Level 2 | Cache each post individually | `cache.set(f'post_{id}', data, timeout=CACHE_TTL)` |
| 🔵 Level 3 | Invalidate cache on data change | `cache.delete('all_posts')` on create/update/delete |
| 🔴 Level 4 | Single TTL constant from settings | `CACHE_TTL = settings.CACHE_TTL` |

**Extra:** Added `@method_decorator(cache_page(60), name='dispatch')` to `PostList` for view-level HTTP response caching on top of the manual cache layer.

**Why two cache layers?**
- `cache_page` caches the full HTTP response — fast for repeated identical requests
- Manual `cache.get/set` gives fine-grained control to invalidate specific keys when data changes

### Step 3: Merchants App
Built a full CRUD API using `ModelViewSet` with `DefaultRouter` — auto-generates all REST routes.

- Added `IsAuthenticated` permission — JWT token required
- Added `DjangoFilterBackend` for filtering by `name`
- Added `SearchFilter` for search by `name`
- Results ordered by `-created_at` (newest first)

### Step 4: Financing App
Built three separate views for clean separation of concerns:

- `FinancingCreateView` — POST only, triggers async alert on save
- `FinancingListView` — GET only, filterable by `status` and `merchant`
- `FinancingUpdateView` — PUT/PATCH only, for updating status

**Model has STATUS_CHOICES:**
```python
STATUS_CHOICES = [
    ('pending', 'pending'),
    ('approved', 'approved'),
    ('rejected', 'rejected'),
]
```

**Serializer validates amount:**
```python
def validate_amount(self, value):
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return value
```

All three views protected with `IsAuthenticated`.

### Step 5: Async Alert System
When a financing request is created, an alert fires in a background thread — non-blocking.

**How it works:**
1. `FinancingCreateView.perform_create()` saves the record
2. Calls `send_financing_alert(instance.id)`
3. `send_financing_alert` spawns a `threading.Thread`
4. Thread runs `_send_alert()` which logs the alert
5. API response returns immediately — client doesn't wait

**Used `logging` instead of `print`** — professional standard:
```python
logger = logging.getLogger(__name__)
logger.info(f"[ALERT] request_id={request_id} status=processed timestamp={datetime.now()}")
```

### Step 6: Authentication
Added JWT authentication using `djangorestframework-simplejwt`.

- `POST /api/token/` — returns access + refresh tokens
- `POST /api/token/refresh/` — refreshes access token
- All merchant and financing endpoints require `Authorization: Bearer <token>`

### Step 7: Filtering and Pagination
Configured globally in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
}
```

Financing list supports:
- `?status=pending` — filter by status
- `?merchant=1` — filter by merchant ID
- `?page=2` — paginate results

### Step 8: Environment Variables
Moved all sensitive config out of code into `.env`:

```
DB_NAME=blogdb
DB_USER=esther
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=django-insecure-blog-cache-demo-key
```

`settings.py` reads them via `os.environ.get()`:
```python
'PASSWORD': os.environ.get('DB_PASSWORD', '1234'),
```

`.env` is excluded from git via `.gitignore` — credentials never pushed to GitHub.

---

## All API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/token/` | Get JWT access + refresh tokens | No |
| POST | `/api/token/refresh/` | Refresh access token | No |
| GET | `/api/blog/posts/` | List all posts (cached) | No |
| POST | `/api/blog/posts/` | Create a post + invalidate cache | No |
| GET | `/api/blog/posts/<id>/` | Get single post (cached per ID) | No |
| PUT | `/api/blog/posts/<id>/` | Update post + invalidate cache | No |
| DELETE | `/api/blog/posts/<id>/` | Delete post + invalidate cache | No |
| GET | `/api/merchants/` | List merchants (paginated, filterable) | Yes |
| POST | `/api/merchants/` | Create a merchant | Yes |
| GET | `/api/merchants/<id>/` | Get a merchant | Yes |
| PUT | `/api/merchants/<id>/` | Update a merchant | Yes |
| DELETE | `/api/merchants/<id>/` | Delete a merchant | Yes |
| GET | `/api/financing/` | List financing requests (filterable) | Yes |
| POST | `/api/financing/create/` | Submit financing request + trigger alert | Yes |
| PUT | `/api/financing/<id>/update/` | Update financing request | Yes |
| PATCH | `/api/financing/<id>/update/` | Partially update financing request | Yes |

---

## Settings Overview

### INSTALLED_APPS
```python
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    # Project apps
    'blog',
    'merchants',
    'financing',
    'alerts',
]
```

### Database (PostgreSQL via env vars)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'blogdb'),
        'USER': os.environ.get('DB_USER', 'esther'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '1234'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Cache
```python
CACHE_TTL = 60  # single constant controls all cache timeouts

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-blog-cache',
    }
}
```

### REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
}
```

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Language |
| Django | 6.0.5 | Web framework |
| Django REST Framework | 3.14+ | REST API |
| djangorestframework-simplejwt | 5.0+ | JWT authentication |
| django-filter | 23.0+ | Query filtering |
| psycopg2-binary | 2.9+ | PostgreSQL driver |
| gunicorn | latest | Production WSGI server |
| PostgreSQL | latest | Production database |
| LocMemCache | built-in | In-memory caching |
| threading | built-in | Async alert execution |
| logging | built-in | Professional log output |

---

## How to Run Locally

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Load environment variables
export $(cat .env | xargs)

# 4. Run migrations
python manage.py migrate

# 5. Create superuser (for JWT login)
python manage.py createsuperuser

# 6. Start server
python manage.py runserver
```

---

## How to Use the API

### Get a JWT token
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```

### Use token on protected endpoints
```bash
curl http://127.0.0.1:8000/api/merchants/ \
  -H "Authorization: Bearer <access_token>"
```

### Create a merchant
```bash
curl -X POST http://127.0.0.1:8000/api/merchants/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name": "Test Shop", "email": "shop@test.com", "phone": "0712345678"}'
```

### Submit a financing request
```bash
curl -X POST http://127.0.0.1:8000/api/financing/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"merchant": 1, "amount": "5000.00", "purpose": "Buy stock"}'
```

### Filter financing requests
```bash
curl "http://127.0.0.1:8000/api/financing/?status=pending" \
  -H "Authorization: Bearer <access_token>"
```

### Approve a financing request
```bash
curl -X PATCH http://127.0.0.1:8000/api/financing/1/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"status": "approved"}'
```
