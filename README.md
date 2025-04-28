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
14. [Screenshot](#screenshot)
15. [License](#license)
16. [Author](#author)

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
phishing_detection/                          # Root of the project
└── phishing detection/                       # Main application directory
    ├── .dockerignore                         # Files to exclude from Docker build context
    ├── .idea/                                # IDE metadata (PyCharm/WebStorm settings)
    │   ├── .gitignore                        # Ignored IDE configs
    │   ├── SafeSurf-main.iml                 # Project module file for IDE
    │   ├── git_toolbox_blame.xml             # Git blame plugin settings
    │   ├── inspectionProfiles/               # Code inspection configurations
    │   │   └── profiles_settings.xml
    │   ├── misc.xml                          # Miscellaneous IDE settings
    │   ├── modules.xml                       # Module definitions
    │   ├── vcs.xml                           # VCS integration settings
    │   └── workspace.xml                     # UI layout & workspace state
    ├── Dockerfile                            # Instructions to build Docker image
    ├── LICENSE                               # Apache 2.0 license text
    ├── README.md                             # Project overview and setup guide
    ├── __pycache__/                          # Compiled Python bytecode (auto-generated)
    │   ├── app.cpython-311.pyc
    │   ├── controller.cpython-311.pyc
    │   ├── db.cpython-311.pyc
    │   ├── model.cpython-311.pyc
    │   ├── onetimescript.cpython-311.pyc
    │   └── xx.cpython-311.pyc
    ├── app.py                                # Entry point for Flask web server
    ├── app_original.py                       # Backup or alternative version of app.py
    ├── controller.py                         # Coordinates URL analysis and scoring engine
    ├── credentials.json                      # OAuth2 client secrets for Gmail API
    ├── credentials_nlp.json                  # Service-account for Google Cloud NLP
    ├── db.py                                 # SQLAlchemy models and DB initialization
    ├── docker-compose.yml                    # Defines multi-container Docker services
    ├── gmail-client-secrets.json.json        # Duplicate or alternate Gmail credentials file
    ├── instance/                             # Local instance-specific files
    │   └── domains.db                        # SQLite database storing domain-rank table
    ├── model.py                              # Heuristic functions and score calculation logic
    ├── onetimescript.py                      # One-time ingestion script for domain-rank data
    ├── remain.css                            # Stylesheet for the email inspection UI
    ├── remain.html                           # Front-end for email base64 inspector
    ├── remain.py                             # Flask route or logic for email inspection UI
    ├── requirements.txt                      # Python package dependencies
    ├── static/                               # Static assets (images, JS, CSS, data)
    │   ├── android-chrome-192x192.png        # PWA icons
    │   ├── android-chrome-512x512.png
    │   ├── app2.js                            # Custom front-end JS logic
    │   ├── apple-touch-icon.png              # iOS home-screen icon
    │   ├── css/                              # Additional CSS directory
    │   │   └── style.css                     # Main stylesheet
    │   ├── data/                             # Flat data files
    │   │   ├── domain-rank.json              # Precomputed domain ranks
    │   │   └── url-shorteners.txt            # Known URL shortener list
    │   ├── favicon-16x16.png                 # Browser favicon
    │   ├── favicon-32x32.png
    │   ├── favicon.ico
    │   ├── js/                               # JavaScript directory
    │   │   └── main.js                       # Client-side logic
    │   ├── phishing.jpg                      # Asset for landing or docs
    │   ├── safesurf-normal.png               # UI/branding images
    │   ├── safesurf-screenshot.png
    │   ├── safesurf.png
    │   ├── site.webmanifest                  # PWA manifest
    │   ├── style2.css                        # Alternate CSS theme
    │   └── surfsafe-normal.png
    ├── study.py                              # Experimental or research script
    ├── study2.py                             # Alternate experimental script
    ├── templates/                            # Jinja2 HTML templates
    │   ├── base.html                         # Base template with common layout
    │   ├── index.html                        # Home page for URL analysis
    │   ├── index2.html                       # Alternate home page version
    │   ├── preview.html                      # Template for live site preview
    │   └── source_code.html                  # Template for prettified source view
    ├── token.json                            # Stored OAuth token for Gmail
    ├── url_inspector.py                      # CLI tool for URL parsing & HTTP metadata
    ├── x.py                                  # Placeholder or alternative script
    └── xx.py                                 # Email analysis CLI with NLP integration

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
## 📝 Screenshots
![image](https://github.com/user-attachments/assets/0782a230-09d5-44e3-becf-8dafcd0e0d47)
![image](https://github.com/user-attachments/assets/4794773f-16ab-410f-8f9c-a459b19d8166)
![image](https://github.com/user-attachments/assets/739aeea5-802a-483a-a1e4-b71919f56808)
![image](https://github.com/user-attachments/assets/5b3a79d4-fa9a-4b3a-865b-c016c5c37217)
![image](https://github.com/user-attachments/assets/e4333e1e-ad92-4113-8970-09aa9dbeaf08)


## 📜 License

Apache License 2.0. See [LICENSE](LICENSE).

---

## 👤 Author

**Samir Yogendra Meshram**  
Email: sameerymeshram@gmail.com  
GitHub: [SamirYMeshram](https://github.com/SamirYMeshram)

---

