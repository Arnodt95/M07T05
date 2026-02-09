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

### Content & Workflow
- Article creation/editing/submission with an approval workflow
- Image uploads for articles
- Editor review queue
- Newsletter creation and browsing

### Notifications
When an article is approved, subscribers can be notified by email (and optional social posting helpers are included).

### REST API
REST endpoints are provided using Django REST Framework with token authentication.

---

## Tech Stack / Requirements

- Python 3.10+
- Django 4.2+
- Django REST Framework
- MySQL/MariaDB
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Configuration (Do NOT commit secrets)

This project reads configuration from environment variables (loaded locally from a `.env` file via `python-dotenv`).

**Never commit** `.env` (or any access tokens/passwords) to a public repository.

### `.env.example` (copy to `.env` locally)
Create a `.env` file in the same directory as `manage.py`:

```env
# Django
SECRET_KEY=replace-me
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
SITE_BASE_URL=http://127.0.0.1:8000

# Database (MySQL/MariaDB)
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=replace-me
DB_HOST=127.0.0.1
DB_PORT=3306

# Email (dev-friendly default)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@news.local

# X (Twitter) Integration (optional)
X_BEARER_TOKEN=
X_TWEET_ENDPOINT=https://api.x.com/2/tweets
```
---

## Database Setup (MySQL / MariaDB)

### 1) Create database

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2) Create user (recommended)

```sql
CREATE USER 'news_user'@'%' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'%';
FLUSH PRIVILEGES;
```

---

## Run Locally (venv)

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` (see above), then:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## Run with Docker

This repo supports a **Dockerfile-only** workflow (no database container). You must provide a reachable MySQL/MariaDB instance via environment variables.

### Important: MySQL running on your Windows machine
When MySQL is on the Windows host, the container should connect using:
- `DB_HOST=host.docker.internal`
- `DB_PORT=3306`

### 1) Build the image
From the project root (same folder as `manage.py` and `Dockerfile`):

```powershell
docker build -t newsapp:latest .
```

### 2) Run the container
Replace `DB_PASSWORD` and `SECRET_KEY` with your own values:

```powershell
docker run --name newsapp --rm -p 8000:8000 `
  -e SECRET_KEY="replace-me" `
  -e DEBUG="1" `
  -e ALLOWED_HOSTS="127.0.0.1,localhost" `
  -e SITE_BASE_URL="http://127.0.0.1:8000" `
  -e DB_NAME="news_db" `
  -e DB_USER="news_user" `
  -e DB_PASSWORD="replace-me" `
  -e DB_HOST="host.docker.internal" `
  -e DB_PORT="3306" `
  newsapp:latest
```

### 3) Run migrations (recommended)
In a second terminal:

```powershell
docker exec -it newsapp python manage.py migrate
```

### 4) Create a superuser (optional)

```powershell
docker exec -it newsapp python manage.py createsuperuser
```

Then open:
- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## Documentation (Sphinx)

Project documentation is generated from existing docstrings and stored under the `docs/` directory.

Build the HTML docs:

```powershell
cd docs
.\make.bat html
cd ..
```

Open the generated docs in a browser:
- `docs/build/html/index.html`

> Note: The course task requires committing generated documentation under `docs/` so that repository visitors can read it easily.

---

## REST API

### Get a token
`POST /api/login/` with JSON:

```json
{
  "username": "user",
  "password": "password"
}
```

Use the token:

```http
Authorization: Token <your-token>
```

### Example endpoints
- `GET /api/articles/`
- `GET /api/publishers/`
- `GET /api/newsletters/`

---

## Testing

```bash
python manage.py test
```
