# Django Smart Caching Blog — Full Project Documentation

## What This Project Does

This is a Django REST API with two main responsibilities:

1. A **Blog/Posts API** that demonstrates smart caching strategies to reduce database hits
2. A **Merchant Financing API** that handles merchant registration, financing requests, and async alert notifications

All APIs are protected with JWT authentication, paginated, and filterable.

---

## Project Structure

```
django-smart-caching-blog/
├── alerts/
│   ├── __init__.py
│   └── tasks.py              # Async alert using threading
├── blog/
│   ├── models.py             # (unused, posts app handles models)
│   ├── urls.py               # Blog cache demo routes
│   └── views.py              # PostList + PostDetail with caching logic
├── config/
│   ├── settings.py           # All project settings
│   └── urls.py               # Root URL config
├── financing/
│   ├── migrations/
│   ├── models.py             # FinancingRequest model
│   ├── serializers.py
│   ├── urls.py
│   └── views.py              # FinancingListCreateView
├── merchants/
│   ├── migrations/
│   ├── models.py             # Merchant model
│   ├── serializers.py
│   ├── urls.py               # DefaultRouter wiring
│   └── views.py              # MerchantViewSet
├── posts/
│   ├── migrations/
│   ├── models.py             # Post model
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
├── Procfile
└── db.sqlite3
```

---

## Apps and What They Do

### blog
Demonstrates caching levels using Django's in-memory cache (`LocMemCache`).

- `PostList` — GET lists all posts (cached under `all_posts`), POST creates a post and clears the list cache
- `PostDetail` — GET fetches a single post (cached under `post_<id>`), PUT updates and clears both caches, DELETE removes and clears both caches
- Cache TTL is controlled by a single `CACHE_TTL = 60` constant

Caching levels:
| Level | What it does |
|-------|-------------|
| Level 1 | Full list cached under `all_posts` for 60s |
| Level 2 | Each post cached under its own key `post_<id>` |
| Level 3 | Cache invalidated automatically on create, update, delete |
| Level 4 | Single TTL constant, per-post keys avoid full cache busting |

### posts
Holds the `Post` model (`id`, `title`, `content`) used by the blog app.

### merchants
Full CRUD API for merchant management.

- Model fields: `name`, `email` (unique), `phone`, `created_at`
- Uses `ModelViewSet` with `DefaultRouter` — auto-generates all REST routes
- Protected with `IsAuthenticated` (JWT required)
- Supports filtering by `name` (`?name=foo`) and search (`?search=foo`)
- Results ordered by `id` for consistent pagination

### financing
API for submitting and listing financing requests.

- Model fields: `merchant` (FK), `amount`, `purpose`, `status` (default: `pending`), `created_at`
- `FinancingListCreateView` handles GET (list) and POST (create) on a single endpoint
- On every POST, triggers an async alert via `alerts.tasks.send_financing_alert`
- Results ordered by `-created_at` (newest first)

### alerts
Async notification system — no Celery, no external services needed.

- `send_financing_alert(request_id)` spawns a background thread
- The thread logs: `[ALERT] Financing request {id} processed`
- Non-blocking — API response is returned immediately, alert runs in background

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/token/` | Get JWT access + refresh tokens | No |
| POST | `/api/token/refresh/` | Refresh access token | No |
| GET | `/api/posts/` | List all posts (cached) | No |
| POST | `/api/posts/` | Create a post | No |
| GET | `/api/posts/<id>/` | Get single post (cached per ID) | No |
| PUT | `/api/posts/<id>/` | Update post + invalidate cache | No |
| DELETE | `/api/posts/<id>/` | Delete post + invalidate cache | No |
| GET | `/api/merchants/` | List merchants (paginated, filterable) | Yes |
| POST | `/api/merchants/` | Create a merchant | Yes |
| GET | `/api/merchants/<id>/` | Get a merchant | Yes |
| PUT | `/api/merchants/<id>/` | Update a merchant | Yes |
| DELETE | `/api/merchants/<id>/` | Delete a merchant | Yes |
| GET | `/api/financing/` | List financing requests | No |
| POST | `/api/financing/` | Submit a financing request + trigger alert | No |

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Language |
| Django | 6.0.5 | Web framework |
| Django REST Framework | 3.17.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication |
| django-filter | 25.2 | Filtering support |
| dj-database-url | 3.1.2 | Database URL config |
| psycopg2-binary | 2.9.12 | PostgreSQL driver |
| gunicorn | 26.0.0 | Production WSGI server |
| SQLite | built-in | Local development database |
| LocMemCache | built-in | In-memory caching (no Redis needed) |

---

## Settings Overview (`config/settings.py`)

### Database
Uses `dj_database_url.config()` — reads `DATABASE_URL` env var in production, falls back to SQLite locally:
```python
DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3')
}
```

### Cache
Django's built-in in-memory cache — no Redis or external service needed:
```python
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
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
}
```

### JWT
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

---

## How Authentication Works

1. Create a Django superuser: `python3 manage.py createsuperuser`
2. Get a token:
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```
3. Use the token on protected endpoints:
```bash
curl http://127.0.0.1:8000/api/merchants/ \
  -H "Authorization: Bearer <access_token>"
```
4. Refresh when expired:
```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -d '{"refresh": "<refresh_token>"}'
```

---

## How the Async Alert Works

When a financing request is created:
1. `FinancingListCreateView.perform_create()` saves the record
2. Immediately calls `send_financing_alert(instance.id)`
3. That function spawns a `threading.Thread` — non-blocking
4. The thread runs `_send_alert()` which logs the alert
5. API response is returned to the client without waiting

Evidence of alert firing appears in Django's server logs:
```
[ALERT] Financing request 1 processed
```

---

## Local Setup

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```
