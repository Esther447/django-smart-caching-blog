# Django Smart Caching Blog API

A Django REST API demonstrating smart caching strategies to reduce database hits and speed up repeated requests.

## What It Does

Every API request normally hits the database. This project saves responses in an in-memory cache so repeated requests are served instantly — no database query needed.

## Project Structure

```
django-smart-caching-blog/
├── blog/
│   ├── models.py      # Post model
│   ├── views.py       # All caching logic
│   └── urls.py        # API routes
├── config/
│   ├── settings.py    # Cache configuration
│   └── urls.py        # Root URL config
├── manage.py
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts/` | List all posts |
| POST | `/api/posts/` | Create a new post |
| GET | `/api/posts/<id>/` | Get a single post |
| PUT | `/api/posts/<id>/` | Update a post |
| DELETE | `/api/posts/<id>/` | Delete a post |

## Caching Levels

### 🟢 Level 1 — Basic Cache
The full posts list is cached under the key `all_posts` for 60 seconds.  
First request hits the database. Every request after that is served from cache.

### 🟡 Level 2 — Granular Cache
Each individual post is cached under its own key `post_<id>`.  
`/api/posts/1/` and `/api/posts/2/` are cached independently.

### 🔵 Level 3 — Cache Invalidation
Cache is cleared automatically when data changes:
- **Create** → clears `all_posts`
- **Update** → clears `post_<id>` and `all_posts`
- **Delete** → clears `post_<id>` and `all_posts`

### 🔴 Level 4 — Optimization
- Single `CACHE_TTL = 60` constant controls all timeouts
- Per-post keys mean updating one post doesn't bust every other post's cache

## Cache Configuration

Defined in `config/settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-blog-cache',
    }
}
```

Uses Django's built-in in-memory cache — no Redis or external service needed.

## Example Usage

```bash
# Create a post
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Post", "content": "Hello World"}'

# List all posts (cached after first hit)
curl http://127.0.0.1:8000/api/posts/

# Get a single post (cached per ID)
curl http://127.0.0.1:8000/api/posts/1/

# Update a post (invalidates cache)
curl -X PUT http://127.0.0.1:8000/api/posts/1/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Delete a post (invalidates cache)
curl -X DELETE http://127.0.0.1:8000/api/posts/1/
```

## Tech Stack

- Python 3.12
- Django 4.2+
- Django REST Framework 3.14+
- SQLite (default database)
- LocMemCache (in-memory cache)
