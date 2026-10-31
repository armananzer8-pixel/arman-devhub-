# Arman DevHub

**Learn. Build. Innovate.**

Arman DevHub is a Django-powered learning and portfolio project developed while studying Python, web development, and computer science. It combines a public-facing website with authenticated tools for managing contact messages, attachments, and reports.

**Live website:** https://arman-devhub.onrender.com/

## Features

- Home, About, and Contact pages
- User sign-up, login, logout, profile, and password management
- Django administration and staff-restricted workflows
- Contact message management with notes and attachments
- Attachment dashboard, analytics, and CSV export
- Report category creation, editing, filtering, and deletion
- Learning Hub section
- Automated Django tests

Some management features require authentication or staff permissions.

## Tech stack

- **Backend:** Python, Django 6.1
- **Database:** SQLite for local development; PostgreSQL on Render
- **Production server:** Gunicorn
- **Static files:** WhiteNoise
- **Hosting:** Render
- **Version control:** Git and GitHub

## Run locally

1. Clone the repository:

   ```bash
   git clone https://github.com/armananzer8-pixel/arman-devhub-.git
   cd arman-devhub-
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   On Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Configure a **local** secret key. In PowerShell:

   ```powershell
   $env:DJANGO_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(50))")
   ```

   Or on macOS/Linux:

   ```bash
   export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
   ```

   Keep `DJANGO_DEBUG` unset (or set it to `True`) for local development. Leave `DATABASE_URL` unset to use the local SQLite database. **Never use production database credentials for local testing.**

5. Apply migrations and start the server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

   Visit http://127.0.0.1:8000/

## Run tests

```bash
python manage.py test
```

## Deployment

The project is deployed on Render with PostgreSQL. The `build.sh` script installs dependencies, collects static files, and runs Django database migrations. Gunicorn serves the Django WSGI application.

Production configuration uses environment variables, including:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secret key (keep private) |
| `DJANGO_DEBUG` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Allowed website hostnames |
| `DATABASE_URL` | PostgreSQL connection URL (keep private) |
| `DJANGO_SECURE_SSL_REDIRECT` | Optional HTTPS redirect setting |

**Security:** Do not commit passwords, database URLs, secret keys, `.env` files, or local databases. Review configuration before each deployment.

**Note:** Render's free services may take time to wake after inactivity. Local file storage on a free web service is not persistent; a persistent storage solution is needed for long-term user uploads.

## Author

**Mohammed Muneeb Arman Anzar**  
B.Sc. Computer Science student

GitHub: https://github.com/armananzer8-pixel

---

*Arman DevHub is an educational and portfolio project.*
