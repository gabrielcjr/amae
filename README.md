<div align="center">
  <h1>🌍 AMAE</h1>
  <p><strong>Agência Missionária de Apoio Estratégico</strong></p>
  <p>A dedicated platform connecting investors with missionaries across Brazil, streamlining financial adoptions, and tracking mission fields with comprehensive reporting.</p>
</div>

---

## 🚀 Features

*   **👥 Portals for Missionaries & Investors:** Custom login flows and dashboards tailored for different user roles.
*   **🗺️ Mission Field Management:** Track specific mission locations (villages, lat/lng coordinates) and the missionaries assigned to them via interactive Google Maps.
*   **🤝 Financial Adoptions:** Seamlessly connect investors with missionaries through monthly financial support (BRL).
*   **📊 Advanced Financial Reporting:** Admin-exclusive tools to manage transactions, auto-generate PDF receipts, and produce comprehensive HTML/PDF financial reports.
*   **📝 Integrated CMS:** Built-in tools for managing static pages, FAQs, testimonials, and global site images.

## 🛠️ Technology Stack

Our modern stack focuses on server-side rendering with reactive UI components:

*   **Backend:** Python 3.14 & Django 6.0.5
*   **Database:** PostgreSQL 18
*   **Frontend:** Django Templates + Tailwind CSS 4 (`@tailwindcss/cli`) + HTMX 2
*   **Testing:** pytest + pytest-django (parallel execution via pytest-xdist)
*   **Reporting:** Reportlab (for PDF generation)

## ⚙️ Quick Start (Docker)

The easiest way to get the project running locally is using Docker Compose. We have configured the environment to spin up the database, the Django web server, and the Tailwind CSS watcher automatically.

### 1. Environment Setup

Clone the repository and set up your environment variables:

```bash
git clone <repository-url>
cd amae
cp .env.sample .env
```
*(Make sure to populate your `.env` with a `SECRET_KEY`, `GOOGLE_MAPS_API_KEY`, and database credentials.)*

### 2. Start the Application

Run the following command to build the images and start the services:

```bash
docker compose up --build
```

This will start:
- **`db`**: PostgreSQL 18 database.
- **`web`**: Django development server (accessible at `http://localhost:8000`), running as a secure, non-root user. It will also automatically run database migrations on startup.
- **`tailwind`**: Node.js service that watches for CSS changes and compiles your Tailwind styles on the fly.

### 3. Load Seed Data

In a new terminal window, load the initial Brazilian fixture data:

```bash
docker compose exec web python manage.py seed
```

## 🧪 Testing

We use `pytest` for running our test suite. To run the tests inside the Docker container:

```bash
# Run the entire test suite in parallel
docker compose exec web pytest

# Run tests for a specific app
docker compose exec web pytest missions/tests.py
```

## 🧹 Code Quality

Formatting and linting are strictly enforced using Black, isort, and Flake8.

```bash
# Check for linting issues
docker compose exec web make run-check-linters

# Auto-fix formatting
docker compose exec web make run-fix-linters
```

## 🏗️ Architecture

The platform is divided into four main Django applications:

1.  **`missions`**: The core domain. Contains models for `MissionField`, `Location`, `Missionary`, `Investor`, and `Adoption`. Handles the public-facing views.
2.  **`finance`**: An admin-only app for managing `Transactions` and `FinancialCategories`. Includes custom views for generating PDF reports.
3.  **`pages`**: A lightweight CMS for managing dynamic content (`Page`, `FAQ`, `Testimonial`, `SiteImage`).
4.  **`accounts`**: Manages user registration, profiles, and authentication flows.

> For more in-depth architectural decisions, domain relationships, and development guidelines, please refer to [CLAUDE.md](CLAUDE.md).
