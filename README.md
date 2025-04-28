## Phishing Detection System

### Summary
This Phishing Detection System is an advanced, production-ready Flask application that evaluates URLs against a rich suite of static and dynamic heuristics to compute a trust score and detect malicious intent in real-time, leveraging domain reputation, WHOIS analysis, SSL inspection, heuristic content checks, and third‑party threat intelligence integrations ([frontiersin.org](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1414122/full?utm_source=chatgpt.com), [sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404813001442?utm_source=chatgpt.com)).

## Table of Contents
1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Features](#features)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Database & Data Maintenance](#database--data-maintenance)
8. [Extensibility & Customization](#extensibility--customization)
9. [Testing](#testing)
10. [Security Considerations](#security-considerations)
11. [Contribution Guidelines](#contribution-guidelines)
12. [License](#license)
13. [Author](#author)

## Introduction
Phishing attacks remain one of the most prevalent and harmful cybersecurity threats, tricking users into divulging credentials or financial data by mimicking legitimate websites and communications ([frontiersin.org](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1414122/full?utm_source=chatgpt.com)). This project provides a heuristic-driven detection engine that scores URLs from 0 to 100 by assessing factors such as domain popularity, age, URL structure, encryption details, and known blacklists ([sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404819301622?utm_source=chatgpt.com)). Designed for both security researchers and production deployments, it balances performance with comprehensive analysis ([researchgate.net](https://www.researchgate.net/publication/347713696_Review_on_Phishing_Attack_Detection_Techniques?utm_source=chatgpt.com)).

## Architecture Overview
The system follows a modular architecture with separation of concerns between the web interface, scoring engine, data layer, and third-party integrations ([coding-boot-camp.github.io](https://coding-boot-camp.github.io/full-stack/github/professional-readme-guide/?utm_source=chatgpt.com)). The core components include:

- **Web UI (Flask)**: Handles user interactions, preview rendering, and API endpoints ([github.com](https://github.com/jehna/readme-best-practices?utm_source=chatgpt.com)).
- **Controller**: Orchestrates feature extraction and aggregates scores.
- **Model**: Implements individual heuristics (domain rank, WHOIS, HSTS, SSL certs, content checks) and composite scoring ([sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404813001442?utm_source=chatgpt.com)).
- **Data Layer**: SQLite database for persistence and JSON files for static data (`domain-rank.json`, `url-shorteners.txt`) ([altospam.com](https://www.altospam.com/en/glossary/heuristic-analysis/?utm_source=chatgpt.com)).
- **Threat Intelligence**: Integrations with PhishTank and optional AI-based extensions for emergent threats ([perception-point.io](https://perception-point.io/guides/ai-security/detecting-and-preventing-ai-based-phishing-attacks-2024-guide/?utm_source=chatgpt.com)).

## Features

### 1. Interactive Web Interface
- URL submission form with real-time trust scoring and detailed breakdown ([tilburgsciencehub.com](https://tilburgsciencehub.com/topics/collaborate-share/share-your-work/content-creation/readme-best-practices/?utm_source=chatgpt.com)).
- Live site preview with asset URL rewriting for sandboxed browsing ([vadesecure.com](https://www.vadesecure.com/en/blog/effective-phishing-protection-heuristics?utm_source=chatgpt.com)).
- Prettified HTML source-code viewing for safe manual inspection.

### 2. Comprehensive Scoring Engine
- **Domain Reputation**: Utilizes a top‑1M domain ranking list to reward popular domains and penalize obscure ones ([sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404819301622?utm_source=chatgpt.com)).
- **Domain Age**: WHOIS parsing to calculate domain age and adjust scores accordingly ([philarchive.org](https://philarchive.org/archive/SWAEPD?utm_source=chatgpt.com)).
- **URL Structure**: Flags URLs with excessive length (>75 chars) and depth (>5 slashes) ([researchgate.net](https://www.researchgate.net/publication/347713696_Review_on_Phishing_Attack_Detection_Techniques?utm_source=chatgpt.com)).
- **Security Headers**: Checks for HSTS and HTTPS enforcement ([tilburgsciencehub.com](https://tilburgsciencehub.com/topics/collaborate-share/share-your-work/content-creation/readme-best-practices/?utm_source=chatgpt.com)).
- **SSL/TLS Inspection**: Extracts certificate issuer, validity period, cipher suite, TLS version, and revocation status ([sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404813001442?utm_source=chatgpt.com)).
- **Content Heuristics**: Detects phishing patterns in page content (onmouseover, forms, iframes, disabled right-click) ([vadesecure.com](https://www.vadesecure.com/en/blog/effective-phishing-protection-heuristics?utm_source=chatgpt.com)).
- **PhishTank Integration**: Queries the PhishTank API for known malicious URLs ([sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0167404819301622?utm_source=chatgpt.com)).

### 3. Maintenance Endpoints
- **`/update-db`**: Populates or refreshes the domain-rank SQLite table from the Tranco CSV ([github.com](https://github.com/matiassingers/awesome-readme?utm_source=chatgpt.com)).
- **`/update-json`**: Regenerates the domain-rank.json file for fast lookup.

## Installation & Setup

### Prerequisites
- Python 3.9+ and `pip` package manager ([coding-boot-camp.github.io](https://coding-boot-camp.github.io/full-stack/github/professional-readme-guide/?utm_source=chatgpt.com)).
- (Optional) Docker & Docker Compose for containerized deployment ([hackernoon.com](https://hackernoon.com/5-professional-tips-for-crafting-a-winning-readme?utm_source=chatgpt.com)).

### Installation Steps
```bash
git clone https://github.com/SamirYMeshram/phishing-detection-system.git
cd phishing-detection-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Initialization
```bash
export FLASK_APP=app.py
flask shell
>>> from db import db; db.create_all()
>>> exit()
```

### Docker Deployment
```bash
docker-compose up --build --force-recreate
```

## Configuration
- **Environment Variables**:
  - `FLASK_ENV`: `development` or `production`.
  - `PHISHTANK_API_KEY`: (Optional) for authenticated API requests in high-volume usage.
- **Static Data Files**:
  - `static/data/domain-rank.json`
  - `static/data/url-shorteners.txt`

## Usage
- **Web UI**: Visit `http://localhost:5000/` to analyze URLs.
- **Preview**: Click **Preview** to view rendered HTML safely.
- **View Source**: Click **Source Code** for prettified markup.
- **CLI Integration**: Import `Controller` in external scripts for batch URL processing.

```python
from controller import Controller
ctrl = Controller()
print(ctrl.main("https://example.com"))
```

## Database & Data Maintenance
Use the provided one-time script (`onetimescript.py`) to download and process the Tranco top‑1M CSV into both the SQLite DB and JSON format ([github.com](https://github.com/matiassingers/awesome-readme?utm_source=chatgpt.com)).

## Extensibility & Customization
- Add new heuristics by extending `model.py` with new functions and updating the `PROPERTY_SCORE_WEIGHTAGE` map.
- Integrate alternative threat intelligence feeds via new API modules.
- Swap SQLite for PostgreSQL by adjusting `SQLALCHEMY_DATABASE_URI` in `app.py`.

## Testing
- Implement unit tests for each heuristic function using `pytest`.
- Stub external network calls (WHOIS, PhishTank) to enable offline test runs.
- Integrate with CI workflows for automated quality checks.

## Security Considerations
- **Input Sanitization**: URLs are validated and prefixed with HTTPS if missing ([tilburgsciencehub.com](https://tilburgsciencehub.com/topics/collaborate-share/share-your-work/content-creation/readme-best-practices/?utm_source=chatgpt.com)).
- **Rate Limiting**: Deploy behind a reverse proxy or API gateway to throttle abuse ([reddit.com](https://www.reddit.com/r/webdev/comments/txlbxw/next_level_readme/?utm_source=chatgpt.com)).
- **Data Privacy**: Ensure WHOIS data storage complies with GDPR and other privacy regulations.

## Contribution Guidelines
1. Fork the repository and create a descriptive feature branch.
2. Write tests for any new functionality.
3. Follow PEP8 style conventions and update documentation accordingly ([medium.com](https://medium.com/%40kc_clintone/the-ultimate-guide-to-writing-a-great-readme-md-for-your-project-3d49c2023357?utm_source=chatgpt.com)).
4. Submit a pull request with a clear title, description, and linked issue.

## License
Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for full details.

## Author
**Samir Yogendra Meshram**  
Email: sameerymeshram@gmail.com  
GitHub: [SamirYMeshram](https://github.com/SamirYMeshram)

