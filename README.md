# Django News Application

A Django-based News Management Application that allows journalists and editors to manage articles, while readers can browse articles, subscribe to publishers, and receive notifications when new articles are approved. The project includes both a web interface and a REST API with token-based authentication.

---

## Features

### User Roles

The system uses a custom user model with role-based access:

- **Reader**
  - View published articles
  - Subscribe to publishers and journalists
  - Receive notifications for approved articles

- **Journalist**
  - Create and submit articles
  - Edit their own articles
  - Create newsletters

- **Editor**
  - Review articles
  - Approve or reject submissions
  - Manage publication workflow

### Article Management

- Create, edit, and submit articles
- Article approval workflow
- Article images supported
- Editor review queue

### Publisher & Newsletter Support

- Publishers can be created and managed
- Users can subscribe to publishers and journalists
- Newsletter creation, listing, and detail views

### Notifications

When an article is approved:
- Subscribers are notified via email
- Social posting integration is supported (via helper functions)

### REST API

The project provides REST endpoints using Django REST Framework. Includes:
- Token authentication
- Article endpoints
- Publisher endpoints
- Newsletter endpoints
- Subscriber article feeds

### Authentication

Supports: - Django session authentication - Token authentication for API
usage


---

## Project Structure

```
M06T08/
│
├── manage.py
├── .env
│
├── news_app_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── news_app/
    ├── models.py
    ├── views.py
    ├── api_views.py
    ├── serializers.py
    ├── forms.py
    ├── signals.py
    ├── admin.py
    ├── urls.py
    ├── urls_api.py
    ├── templates/
    ├── static/
    ├── migrations/
    └── functions/
        ├── notify.py
        └── x_post.py
```

---

## Requirements

Typical dependencies include:
- Python 3.10+
- Django (4.2+)
- Django REST Framework
- MySQL/MariaDB client libraries
- python-dotenv
- Pillow (image uploads)

Install:
```bash
pip install -r requirements.txt
```

---

## Environment Configuration

The project uses a `.env` file for configuration (loaded via `python-dotenv`).

Example `.env`:
```env
SECRET_KEY=your-secret-key
DEBUG=1

# Database (MySQL/MariaDB)
DB_NAME=news_db
DB_USER=root
DB_PASSWORD=password
DB_HOST=127.0.0.1
DB_PORT=3306

ALLOWED_HOSTS=127.0.0.1,localhost
SITE_BASE_URL=http://127.0.0.1:8000

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@news.local

# X (Twitter) Integration (Optional)
X_BEARER_TOKEN=your_x_bearer_token_here
X_TWEET_ENDPOINT=https://api.x.com/2/tweets
```

---

## Database Setup (MySQL / MariaDB)

This project is configured to use the Django MySQL backend, which is compatible with MySQL and MariaDB when the server and driver are correctly installed.

1. Create the database:
```sql
CREATE DATABASE news_db;
```

2. Apply migrations:
```bash
python manage.py migrate
```

3. Create an admin user:
```bash
python manage.py createsuperuser
```

---

## Running the Application

Start the development server:
```bash
python manage.py runserver
```

Open in browser:
- Home: `http://127.0.0.1:8000`
- Admin: `http://127.0.0.1:8000/admin`

---

## REST API Usage

### Obtain API Token
Token authentication is provided via DRF’s token endpoint: `POST /api/login/`.

Request:
```http
POST /api/login/
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

Response:
```json
{
  "token": "abc123..."
}
```

Use token in headers:
```http
Authorization: Token <your-token>
```

### API Endpoints

#### Articles
- `GET /api/articles/`
- `GET /api/articles/{id}/`
- `GET /api/articles/subscribed/`

#### Publishers
- `GET /api/publishers/`
- `GET /api/publishers/{id}/`

#### Newsletters
- `GET /api/newsletters/`
- `GET /api/newsletters/{id}/`

---

## Signals & Automation

Signals are used to detect when an article transitions from `approved=False` to `approved=True` and then trigger subscriber notifications and optional X posting.

Location:
- `news_app/signals.py`

---

## X (Twitter) API Integration

When an editor approves an article, the app can:
1. Email subscribers with an excerpt and link
2. Attempt to create a post on X using the configured endpoint

### 1) Get X API access & credentials

To use X posting you need an X developer account and an app created in the developer console. You must obtain credentials (such as a Bearer Token) from your app’s “Keys and tokens”.

Note: Posting privileges and required authorization may depend on your X plan and authentication method.

### 2) Provide credentials via environment variables

Set the following in your `.env` (recommended), and ensure `.env` is not committed to source control:

```env
X_BEARER_TOKEN=your_x_bearer_token_here
X_TWEET_ENDPOINT=https://api.x.com/2/tweets
```

- If `X_TWEET_ENDPOINT` is not set, the code defaults to `https://api.x.com/2/tweets`.

### 3) Important note about the current implementation

The current implementation in `news_app/functions/x_post.py` retrieves the bearer token using an environment variable name that is hard-coded as a long literal string.

To align with the `.env` instructions above, update the code to load:
- `os.getenv("X_BEARER_TOKEN", "")`

instead of the current literal.

### 4) Disabling X posting

If `X_BEARER_TOKEN` is unset or empty, the X posting function returns `False` and does nothing. This allows you to run the app without X integration enabled.

### 5) Security best practices

- Guard keys/tokens carefully
- Avoid committing secrets to source control
- Use environment variables or excluded secret files
- Rotate/regenerate credentials if exposed

---

## Static and Media Files

Static files:
- `/static/`

Uploaded media:
- `/media/`

Ensure media serving is configured correctly in production.

---

## Testing

Run tests with:
```bash
python manage.py test