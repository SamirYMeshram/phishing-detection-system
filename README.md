# Phishing Detection & Email Analysis System

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache2.0-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/) [![Build Status](https://img.shields.io/badge/CI-pending-lightgrey.svg)]()

A comprehensive security toolkit offering:

- **URL Phishing Detection Web Service**: Real-time trust scoring of URLs via Flask, combining reputation data, WHOIS analysis, SSL/TLS inspection, content heuristics, and threat intelligence.
- **Email Threat Analysis CLI** (`xx.py`): Secure OAuth2 access to Gmail and Outlook IMAP, with Google Cloud NLP for sentiment, entity, and category analysis to detect phishing or malicious patterns.

---

## 🔖 Table of Contents
1. [Key Features](#key-features)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Full Setup Guide](#full-setup-guide)
   - [Environment Variables & .env](#environment-variables--env)
   - [Python Virtual Environment](#python-virtual-environment)
   - [Dependency Installation](#dependency-installation)
   - [Database Initialization & Migrations](#database-initialization--migrations)
   - [Running in Development](#running-in-development)
   - [Production Deployment (Gunicorn + Nginx)](#production-deployment-gunicorn--nginx)
   - [Docker & Docker Compose](#docker--docker-compose)
5. [Configuration Details](#configuration-details)
6. [Usage Examples](#usage-examples)
7. [Project Structure](#project-structure)
8. [Extensibility & Plugin System](#extensibility--plugin-system)
9. [Testing & CI Integration](#testing--ci-integration)
10. [Performance & Monitoring](#performance--monitoring)
11. [Security Best Practices](#security-best-practices)
12. [Contribution Guide](#contribution-guide)
13. [Changelog](#changelog)
14. [License](#license)
15. [Author](#author)

---

## 💡 Key Features

### URL Phishing Detection Web Service
- **Trust Scoring Engine**: 0–100 score combining:
  - Domain rank from Tranco Top‑1M
  - Domain age via WHOIS
  - HSTS and HTTPS enforcement
  - URL structure (length & depth)
  - IP address in URL detection
  - Redirect chain analysis
  - Content heuristics (onmouseover, disabled context menus, forms, iframes, pop-ups)
  - SSL/TLS certificate inspection: issuer, validity period, cipher suite, TLS version, revocation
  - PhishTank API integration for blacklist lookup
- **Web UI**: Intuitive interface with detailed breakdown and color‑coded risk levels
- **Live Preview & Source View**: Sandbox preview with asset URL rewriting; prettified HTML source display
- **Data Refresh Endpoints**: `/update-db` and `/update-json` for scheduled domain‑rank updates

### Email Threat Analysis CLI (`xx.py`)
- **OAuth2 Authentication**: Gmail via `google-auth-oauthlib` and Outlook via MSAL
- **IMAP Fetching**: Securely retrieve messages, handle MIME decoding, attachments omitted
- **Text Cleaning**: HTML stripping and Unicode normalization
- **NLP Analysis**: Google Cloud Natural Language for sentiment, entity recognition, and text classification
- **Interactive Console Report**: Summary table of messages with phishing indicators highlighted

---

## 🏗️ System Architecture

```plaintext
+-----------------+      +--------------------+      +-------------------+
|                 |----->|   Flask Web App    |----->|    Controller     |
|  User Browser   |      |  (app.py / Gunicorn)|      |(controller.py /   |
|                 |<-----|                    |<-----|   model.py)       |
+-----------------+      +--------------------+      +-------------------+
                                                  |       |
                                                  v       v
                                          +---------------+    +------------------------+
                                          | SQLite / JSON |    | Third-Party Services   |
                                          | domain-rank   |    | - WHOIS                |
                                          |   storage     |    | - PhishTank API        |
                                          +---------------+    | - SSL/TLS endpoints    |
                                                               +------------------------+

+-----------------+      +--------------------+      +-------------------+
| CLI User (TTY)  |----->|  Email CLI Script  |----->|  Google NLP Client|
| (`xx.py`)       |      |                    |      +-------------------+
+-----------------+      +--------------------+
| MSAL / OAuth2   |----->| Outlook / Gmail    |
+-----------------+      +--------------------+
```

---

## ⚙️ Prerequisites

- **Operating System**: Linux / macOS / Windows 10+ with WSL2
- **Python**: 3.9 or higher
- **Node.js**: (Optional, for future front-end enhancements)
- **Docker**: 20.10+ and Docker Compose 1.29+ (for containerized deployments)
- **Google Cloud Service Account**: JSON key with `language.googleapis.com` enabled
- **Gmail API OAuth2 credentials** (`credentials.json`)
- **Azure AD App Registration**: Client ID and Tenant ID with IMAP.AccessAsUser.All scope

---

## 🛠️ Full Setup Guide

### Environment Variables & `.env`
Create a `.env` file in project root:

```ini
# Flask settings\NFLASK_ENV=development
FLASK_APP=app.py
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000

# Database
database_uri=sqlite:///domains.db

# Google NLP
GOOGLE_APPLICATION_CREDENTIALS=credentials_nlp.json

# Gmail CLI
GMAIL_CLI_CREDENTIALS=credentials.json
gmail_token_path=token.json

# Outlook CLI
OUTLOOK_IMAP_HOST=outlook.office365.com
MSAL_CLIENT_ID=<your-azure-client-id>
MSAL_TENANT_ID=<your-azure-tenant-id>
msal_token_cache=msal_token.json

# PhishTank (Optional)
PHISHTANK_API_KEY=<your-api-key>
``` 

> **Note**: Use [python-dotenv](https://github.com/theskumar/python-dotenv) to load this file automatically.

### Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate.bat      # Windows
pip install --upgrade pip setuptools wheel
```

### Dependency Installation

```bash
pip install -r requirements.txt
```  
Dependencies: Flask, Flask-SQLAlchemy, requests, beautifulsoup4, dnspython, selenium, google-auth, google-auth-oauthlib, google-api-python-client, google-cloud-language, msal, python-dotenv

### Database Initialization & Migrations

```bash
flask db init                  # If using Flask-Migrate
flask db migrate -m "Initial"
flask db upgrade
# Or simple:
python -c "from db import db; db.init_app(__import__('app').app); db.create_all()"
```

### Running in Development

```bash
export FLASK_ENV=development
flask run
```  
Visit `http://localhost:5000`

### Production Deployment (Gunicorn + Nginx)

```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```  
Configure Nginx as reverse proxy with SSL termination, caching static assets, and rate limiting.

### Docker & Docker Compose

1. **Build & Run**
   ```bash
docker-compose up --build -d
```  
2. **Access Services**
   - Web UI: `http://localhost:5000`
   - CLI: attach to container via `docker exec -it phishing_app bash`

```yaml
# docker-compose.yml (excerpt)
version: '3.8'
services:
  web:
    build: .
    env_file: .env
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    depends_on:
      - db
  db:
    image: sqlite:latest
    volumes:
      - ./domains.db:/data/databases/domains.db
``` 

---

## 🔧 Configuration Details

| Variable                     | Description                                            | Default                |
|------------------------------|--------------------------------------------------------|------------------------|
| `FLASK_ENV`                  | Flask environment (`development` / `production`)       | `development`          |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google NLP service-account JSON             | `credentials_nlp.json` |
| `GMAIL_CLI_CREDENTIALS`      | OAuth2 client secrets for Gmail API                   | `credentials.json`     |
| `gmail_token_path`           | File path for storing Gmail OAuth token               | `token.json`           |
| `OUTLOOK_IMAP_HOST`          | IMAP server for Outlook                               | `outlook.office365.com`|
| `MSAL_CLIENT_ID`             | Azure AD App Client ID                                 | –                      |
| `MSAL_TENANT_ID`             | Azure AD Tenant ID                                     | –                      |
| `msal_token_cache`           | File path for MSAL token cache                        | `msal_token.json`      |
| `PHISHTANK_API_KEY`          | API key for PhishTank (optional, improves rate limits)| –                      |

---

## 🚀 Usage Examples

### URL Scanner (Web)

```bash
# Start server
git pull origin main
source venv/bin/activate
flask run
# Open browser at http://localhost:5000
```

Enter URL, view detailed risk report, use **Preview**/**Source Code** features.

### Email Analysis CLI

```bash
python xx.py
```

```
=== Phishing Detection System with Google Cloud NLP ===
Choose provider (gmail/outlook): gmail
# (OAuth browser flow)...
Fetched 50 messages.
---- Message 1 ----
From: alerts@example.com
Date: Mon, 28 Apr 2025 12:45:00 +0530
Subject: Account Verification Required
Sentiment: score=-0.25, mag=0.31
Top Entities:
  - ExampleCorp (ORGANIZATION), salience=0.76
Categories:
  - /Security/Authentication: 0.88
```

---

## 🗂️ Project Structure

```plaintext
phishing-detection-system/
phishing_detection
└── phishing detection
    ├── .dockerignore
    ├── .idea
    │   ├── .gitignore
    │   ├── SafeSurf-main.iml
    │   ├── git_toolbox_blame.xml
    │   ├── inspectionProfiles
    │   │   └── profiles_settings.xml
    │   ├── misc.xml
    │   ├── modules.xml
    │   ├── vcs.xml
    │   └── workspace.xml
    ├── Dockerfile
    ├── LICENSE
    ├── README.md
    ├── __pycache__
    │   ├── app.cpython-311.pyc
    │   ├── controller.cpython-311.pyc
    │   ├── db.cpython-311.pyc
    │   ├── model.cpython-311.pyc
    │   ├── onetimescript.cpython-311.pyc
    │   └── xx.cpython-311.pyc
    ├── app.py
    ├── app_original.py
    ├── controller.py
    ├── credentials.json
    ├── credentials_nlp.json
    ├── db.py
    ├── docker-compose.yml
    ├── gmail-client-secrets.json.json
    ├── instance
    │   └── domains.db
    ├── model.py
    ├── onetimescript.py
    ├── remain.css
    ├── remain.html
    ├── remain.py
    ├── requirements.txt
    ├── static
    │   ├── android-chrome-192x192.png
    │   ├── android-chrome-512x512.png
    │   ├── app2.js
    │   ├── apple-touch-icon.png
    │   ├── css
    │   │   └── style.css
    │   ├── data
    │   │   ├── domain-rank.json
    │   │   └── url-shorteners.txt
    │   ├── favicon-16x16.png
    │   ├── favicon-32x32.png
    │   ├── favicon.ico
    │   ├── js
    │   │   └── main.js
    │   ├── phishing.jpg
    │   ├── safesurf-normal.png
    │   ├── safesurf-screenshot.png
    │   ├── safesurf.png
    │   ├── site.webmanifest
    │   ├── style2.css
    │   └── surfsafe-normal.png
    ├── study.py
    ├── study2.py
    ├── templates
    │   ├── base.html
    │   ├── index.html
    │   ├── index2.html
    │   ├── preview.html
    │   └── source_code.html
    ├── token.json
    ├── url_inspector.py
    ├── x.py
    └── xx.py

``` 

---

## 🧩 Extensibility & Plugin System

- **Add New Heuristics**: Implement in `model.py` and register weight in `PROPERTY_SCORE_WEIGHTAGE`.
- **Custom Threat Feed**: Create modules under `integrations/` and call from `controller.py`.
- **Alternative DB**: Swap SQLite for PostgreSQL by updating `SQLALCHEMY_DATABASE_URI` and installing `psycopg2`.
- **Plugin Hooks**: Expose pre- and post-analysis hooks in `Controller` for third-party extensions.

---

## ✅ Testing & CI Integration

1. **Unit Tests**:
   ```bash
   pytest --maxfail=1 --disable-warnings -q
   ```
2. **CI Pipeline**: Configure GitHub Actions or GitLab CI to:
   - Run linters (flake8, black check)
   - Execute tests
   - Build Docker image

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with: { python-version: '3.9' }
      - run: pip install -r requirements.txt
      - run: pytest
```  

---

## 📈 Performance & Monitoring

- **Profiling**: Use `cProfile` on heavy heuristics (WHOIS, SSL inspection)
- **Caching**:
  - In-memory caching (e.g., `functools.lru_cache`) for repeated WHOIS and SSL calls
  - Redis/Memcached for shared environments
- **Logging**:
  - Configure Python `logging` with rotating file handlers
  - Use Sentry or Logstash for centralized error tracking

---

## 🔒 Security Best Practices

- Sanitize URLs before any network calls
- Rate-limit endpoints using Flask-Limiter or API gateway
- Store secrets securely (Vault, AWS Secrets Manager)
- Enforce HTTPS and HSTS in production
- Validate OAuth tokens and handle refresh securely

---

## 🤝 Contribution Guide

- Fork repository & create feature branch (`feat/`, `fix/`, `doc/` prefixes)
- Write clear, atomic commits with semantic messages
- Run tests and linters before pushing
- Open PR against `main` with issue reference
- Maintain backward compatibility

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

---

## 📜 License

Apache License 2.0. See [LICENSE](LICENSE).

---

## 👤 Author

**Samir Yogendra Meshram**  
Email: sameerymeshram@gmail.com  
GitHub: [SamirYMeshram](https://github.com/SamirYMeshram)

---

