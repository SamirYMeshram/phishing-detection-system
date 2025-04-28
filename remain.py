import os
import imaplib
import email
from email.header import decode_header
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Gmail OAuth2
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Google Cloud NLP
from google.cloud import language_v1
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError

# Additional utilities for text cleaning
import unicodedata
from bs4 import BeautifulSoup

# Outlook OAuth2 (MSAL)
import msal

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCOPES_GMAIL = ['https://mail.google.com/']
OUTLOOK_IMAP_HOST = 'outlook.office365.com'
LOCAL_NLP_CREDENTIALS = 'credentials_nlp.json'   # service-account for NLP (may also be OAuth file)
GMAIL_CLI_CREDENTIALS = 'credentials.json'  # OAuth2 client secrets
GMAIL_TOKEN = 'token.json'

# -----------------------------------------------------------------------------
# OAuth2 Redirect Catcher
# -----------------------------------------------------------------------------
class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    code = None
    def do_GET(self):
        if 'code=' in self.path:
            query = self.path.split('?', 1)[1]
            params = dict(qc.split('=') for qc in query.split('&'))
            OAuth2CallbackHandler.code = params.get('code')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body>You may close this window.</body></html>')

def run_local_server(port=8080):
    server = HTTPServer(('localhost', port), OAuth2CallbackHandler)
    Thread(target=server.handle_request, daemon=True).start()
    return server

# -----------------------------------------------------------------------------
# Credential Load/Save Helpers
# -----------------------------------------------------------------------------
def save_credentials(path: str, creds):
    with open(path, 'w') as f:
        f.write(creds.to_json())

def load_credentials(path: str, scopes: list):
    if os.path.exists(path):
        creds = Credentials.from_authorized_user_file(path, scopes)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            save_credentials(path, creds)
            return creds
    return None

# -----------------------------------------------------------------------------
# Header decoding helper
# -----------------------------------------------------------------------------
def decode_mime_header(value):
    if not value:
        return ''
    decoded = decode_header(value)
    parts = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            parts.append(part.decode(enc or 'utf-8', errors='ignore'))
        else:
            parts.append(part)
    return ''.join(parts)

# -----------------------------------------------------------------------------
# NLP Client Factory with graceful fallback
# -----------------------------------------------------------------------------
def make_nlp_client():
    client = None
    # Try explicit service-account file first
    try:
        if os.path.isfile(LOCAL_NLP_CREDENTIALS):
            client = language_v1.LanguageServiceClient.from_service_account_file(LOCAL_NLP_CREDENTIALS)
        else:
            raise FileNotFoundError(f"File not found: {LOCAL_NLP_CREDENTIALS}")
    except (GoogleAuthError, DefaultCredentialsError, ValueError, FileNotFoundError) as e:
        print(f"[Warning] Could not load NLP service-account: {e}")
        print("[Warning] Attempting to use Application Default Credentials...")
        try:
            client = language_v1.LanguageServiceClient()
        except Exception as e2:
            print(f"[Error] Default credentials failed: {e2}")
            print("[Error] NLP features will be disabled.")
            client = None
    return client

# -----------------------------------------------------------------------------
# Text Analysis via Google Cloud NLP (with cleaning and error-handling)
# -----------------------------------------------------------------------------
def analyze_text_nlp(client, content: str):
    if client is None:
        return {
            'sentiment_score': None,
            'sentiment_magnitude': None,
            'entities': [],
            'categories': []
        }

    # 1) Strip any HTML tags
    clean = BeautifulSoup(content, "html.parser").get_text(separator=" ", strip=True)

    # 2) Remove control characters
    clean = "".join(
        ch for ch in clean
        if unicodedata.category(ch)[0] != "C"
    )

    # 3) Truncate to 100,000 chars
    if len(clean) > 100_000:
        clean = clean[:100_000]

    # 4) Build plain-text document
    document = language_v1.Document(
        content=clean,
        type_=language_v1.Document.Type.PLAIN_TEXT
    )

    # 5) Sentiment analysis (with try/except)
    try:
        sentiment_response = client.analyze_sentiment(document=document)
        sent = sentiment_response.document_sentiment
    except Exception as e:
        print(f"[Error] analyze_sentiment failed: {e}")
        return {
            'sentiment_score': None,
            'sentiment_magnitude': None,
            'entities': [],
            'categories': []
        }

    # 6) Entity analysis
    ents_resp = client.analyze_entities(document=document)
    entities = [
        (e.name, language_v1.Entity.Type(e.type_).name, e.salience)
        for e in ents_resp.entities
    ]

    # 7) Text classification (optional)
    cats = []
    try:
        cls_resp = client.classify_text(document=document)
        cats = [(c.name, c.confidence) for c in cls_resp.categories]
    except Exception:
        pass

    return {
        'sentiment_score': sent.score,
        'sentiment_magnitude': sent.magnitude,
        'entities': entities,
        'categories': cats
    }

# -----------------------------------------------------------------------------
# Gmail OAuth2 + IMAP
# -----------------------------------------------------------------------------
def login_gmail_oauth(force_relogin: bool = False):
    if force_relogin and os.path.exists(GMAIL_TOKEN):
        os.remove(GMAIL_TOKEN)

    creds = load_credentials(GMAIL_TOKEN, SCOPES_GMAIL)
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CLI_CREDENTIALS, SCOPES_GMAIL)
        creds = flow.run_local_server(port=8080)
        save_credentials(GMAIL_TOKEN, creds)

    svc = build('gmail', 'v1', credentials=creds)
    profile = svc.users().getProfile(userId='me').execute()
    email_addr = profile['emailAddress']

    auth_string = f'user={email_addr}\1auth=Bearer {creds.token}\1\1'
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.authenticate('XOAUTH2', lambda x: auth_string)
    return mail

# -----------------------------------------------------------------------------
# Outlook OAuth2 + IMAP
# -----------------------------------------------------------------------------
def login_outlook_oauth(client_id: str, tenant: str, scopes: list, token_cache_file: str = 'msal_token.json'):
    cache = msal.SerializableTokenCache()
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file,'r').read())

    app = msal.PublicClientApplication(client_id, authority=f'https://login.microsoftonline.com/{tenant}', token_cache=cache)
    accounts = app.get_accounts()
    result = app.acquire_token_silent(scopes, account=accounts[0]) if accounts else None

    if not result:
        auth_url = app.get_authorization_request_url(scopes, redirect_uri='http://localhost:8080')
        server = run_local_server(8080)
        webbrowser.open(auth_url)
        server.handle_request()
        code = OAuth2CallbackHandler.code
        result = app.acquire_token_by_authorization_code(code, scopes=scopes, redirect_uri='http://localhost:8080')

    with open(token_cache_file, 'w') as f:
        f.write(cache.serialize())

    user = result['id_token_claims']['upn']
    token = result['access_token']
    auth_string = f'user={user}\1auth=Bearer {token}\1\1'

    mail = imaplib.IMAP4_SSL(OUTLOOK_IMAP_HOST)
    mail.authenticate('XOAUTH2', lambda x: auth_string)
    return mail

# -----------------------------------------------------------------------------
# Fetch & parse emails
# -----------------------------------------------------------------------------
def fetch_email_messages(mail, folder: str = "INBOX", limit: int = 100):
    mail.select(folder)
    status, data = mail.search(None, 'ALL')
    if status != 'OK':
        return []
    ids = data[0].split()[-limit:]
    out = []
    for eid in ids:
        res, msg_data = mail.fetch(eid, '(RFC822)')
        if res != 'OK': continue
        msg = email.message_from_bytes(msg_data[0][1])
        subject = decode_mime_header(msg.get('Subject'))
        from_   = decode_mime_header(msg.get('From'))
        date    = decode_mime_header(msg.get('Date'))

        parts = []
        if msg.is_multipart():
            for p in msg.walk():
                if p.get_content_type()=='text/plain' and 'attachment' not in str(p.get('Content-Disposition')):
                    parts.append(p.get_payload(decode=True).decode(errors='ignore'))
        else:
            parts.append(msg.get_payload(decode=True).decode(errors='ignore'))
        body = "\n".join(parts)

        out.append({'id': eid.decode(),'from': from_,'date': date,'subject': subject,'body': body})
    return out

# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------
def main():
    print('=== Phishing Detection System with Google Cloud NLP ===')

    # 1) Construct NLP client (graceful fallback)
    nlp_client = make_nlp_client()

    # 2) Choose provider
    provider = input('Choose provider (gmail/outlook): ').strip().lower()
    if provider == 'gmail':
        force = input('Force Gmail re-login? (y/N): ').lower().startswith('y')
        mail = login_gmail_oauth(force_relogin=force)
    elif provider == 'outlook':
        client_id = input('Azure App Client ID: ').strip()
        tenant    = input('Tenant ID: ').strip()
        scopes    = ['https://outlook.office.com/IMAP.AccessAsUser.All']
        mail = login_outlook_oauth(client_id, tenant, scopes)
    else:
        print('Unsupported provider.')
        return

    print('Login successful! Fetching messages...')
    messages = fetch_email_messages(mail, limit=200)
    print(f'Fetched {len(messages)} messages.')

    for i,msg in enumerate(messages, start=1):
        print(f"\n---- Message {i} ----")
        print(f"From: {msg['from']}")
        print(f"Date: {msg['date']}")
        print(f"Subject: {msg['subject']}")
        snippet = msg['body'][:200].replace('\n',' ')
        print(f"Body Snippet: {snippet}…")

        analysis = analyze_text_nlp(nlp_client, msg['body'])
        if analysis['sentiment_score'] is not None:
            print(f"Sentiment: score={analysis['sentiment_score']}, mag={analysis['sentiment_magnitude']}")
        else:
            print("Sentiment: n/a (credentials missing)")
        if analysis['entities']:
            print("Top Entities:")
            for name, etype, sal in analysis['entities'][:5]:
                print(f"  - {name} ({etype}), salience={sal:.3f}")
        if analysis['categories']:
            print("Categories:")
            for cat, conf in analysis['categories']:
                print(f"  - {cat}: {conf:.2f}")

    mail.logout()

if __name__ == '__main__':
    main()