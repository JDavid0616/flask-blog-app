
# Simple Blog (Flask + PostgreSQL)

A minimal blog application built with **Flask**, **Flask-Login**, **Flask-WTF**, **Flask-SQLAlchemy**, and **PostgreSQL**.
It includes user authentication (signup, login, logout), CSRF protection, a main entity **Post** with **slug** URLs, and a simple UI.

> Code and comments are written in English.

---

rye run flask --app src/blog_app/run.py --debug run

## Tech Stack (Minimum Versions)
- Python `>= 3.12`
- Flask `>= 3.1.2`
- Flask-WTF `>= 1.2.2`
- Flask-Login `>= 0.6.3`
- Flask-SQLAlchemy `>= 3.1.1`
- PostgreSQL with `psycopg>=3.2.10`
- python-slugify `>= 8.0.4`
- email-validator `>= 2.3.0`
- Package manager: **Rye**

---

## Project Structure
```
src/blog_app/
  run.py          # App factory, routes, login manager
  models.py       # SQLAlchemy models (User, Post)
  forms.py        # WTForms (Signup, Login, Post)
  templates/      # Jinja2 templates
  static/styles.css
```

---

## Features
- User authentication with password hashing (Werkzeug).
- CSRF protection via Flask-WTF.
- Email validation (email-validator via WTForms `Email` validator).
- Post entity with unique slug generation and collision handling.
- Secure redirect validation for the `next` parameter.
- Public routes (home, detail) and a protected route (create post).

---

## Environment Variables
- `DATABASE_URL` (required): `postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME`
- `FLASK_SECRET_KEY` (required in production; default dev fallback exists)

---

## Install with Rye
1. Install Rye (see https://rye.astral.sh/).
2. From the project root:
   ```bash
   rye sync
   ```

---

## PostgreSQL Setup (Example)
```bash
# Create role and database (adjust values to your environment)
psql -U postgres -h localhost -c "CREATE USER bloguser WITH PASSWORD 'blogpass';"
psql -U postgres -h localhost -c "CREATE DATABASE blogdb OWNER bloguser;"
```

Set the environment:
```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql+psycopg://bloguser:blogpass@localhost:5432/blogdb"
$env:FLASK_SECRET_KEY="your-strong-secret"

# macOS/Linux
export DATABASE_URL="postgresql+psycopg://bloguser:blogpass@localhost:5432/blogdb"
export FLASK_SECRET_KEY="your-strong-secret"
```

---

## Run the App
```bash
# Using Flask CLI by file path (works without PYTHONPATH)
rye run flask --app src/blog_app/run.py --debug run

# Or, if you prefer import path, set PYTHONPATH
export PYTHONPATH=src
rye run flask --app blog_app.run --debug run

# Or with Python module execution
export PYTHONPATH=src
rye run python -m blog_app.run
```

The app will create tables automatically on the first request (development convenience).

---

## Routes
| Method  | Path               | Description                              | Auth |
|--------:|--------------------|------------------------------------------|:----:|
| GET     | `/`                | Home page: list all posts                |  No  |
| GET     | `/post/<slug>/`    | Post detail by slug                      |  No  |
| GET/POST| `/login`           | Login with `remember_me`                 |  No  |
| GET/POST| `/signup/`         | Register new user (auto-login)           |  No  |
| GET     | `/logout`          | Logout current user                      | Yes  |
| GET/POST| `/admin/post/`     | Create a new post (current user)         | Yes  |

---

## Data Models
### User
- `id` (PK), `name`, `email` (unique), `password` (hashed)
- Methods: `set_password`, `check_password`, `save`, `get_by_id`, `get_by_email`

### Post
- `id` (PK), `user_id` (FK to `user.id`, `ondelete=CASCADE`), `title`, `category`, `content`, `slug` (unique)
- Methods: `save` (auto slug), `public_url`, `get_by_slug`, `get_all`

---

## Notes
- For production, use proper migrations (e.g., Alembic) and robust secrets management.
- Make sure `FLASK_SECRET_KEY` and `DATABASE_URL` are set in the environment.
