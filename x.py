from flask import Flask, render_template, request
import os
import imaplib
import email
from email.header import decode_header
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.cloud import language_v1
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
import msal

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------
SCOPES_GMAIL           = ['https://mail.google.com/']
OUTLOOK_IMAP_HOST      = 'outlook.office365.com'
LOCAL_NLP_CREDENTIALS  = 'credentials_nlp.json'
GMAIL_CLI_CREDENTIALS  = 'credentials.json'
GMAIL_TOKEN            = 'token.json'

# -------------------------------------------------------------------------
# Simple OAuth2 local‐server to catch the code
# -------------------------------------------------------------------------
class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    code = None
    def do_GET(self):
        query = self.path.split('?', 1)[1]
        params = dict(qc.split('=') for qc in query.split('&'))
        OAuth2CallbackHandler.code = params.get('code')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body><h3>You may now close this window.</h3></body></html>')

def run_local_server(port=8080):
    server = HTTPServer(('localhost', port), OAuth2CallbackHandler)
    Thread(target=server.handle_request, daemon=True).start()
    return server

# -------------------------------------------------------------------------
# Credential helpers
# -------------------------------------------------------------------------
def save_credentials(path, creds):
    with open(path, 'w') as f:
        f.write(creds.to_json())

def load_credentials(path, scopes):
    try:
        if os.path.exists(path):
            creds = Credentials.from_authorized_user_file(path, scopes)
            if creds.valid:
                return creds
            if creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
                save_credentials(path, creds)
                return creds
    except Exception:
        pass
    return None

# -------------------------------------------------------------------------
# Google Cloud NLP client + analysis
# -------------------------------------------------------------------------
def make_nlp_client():
    try:
        # First, try explicit service‐account file
        if os.path.isfile(LOCAL_NLP_CREDENTIALS):
            return language_v1.LanguageServiceClient.from_service_account_file(LOCAL_NLP_CREDENTIALS)
        # Otherwise, ADC
        return language_v1.LanguageServiceClient()
    except (GoogleAuthError, DefaultCredentialsError, ValueError, FileNotFoundError):
        return None

def analyze_text_nlp(client, content):
    if client is None:
        return {
            'sentiment_score': None,
            'sentiment_magnitude': None,
            'entities': [],
            'categories': []
        }
    doc = language_v1.Document(content=content, type_=language_v1.Document.Type.PLAIN_TEXT)
    sent = client.analyze_sentiment(request={'document': doc}).document_sentiment
    ents = client.analyze_entities(request={'document': doc}).entities
    entities = [(e.name, language_v1.Entity.Type(e.type_).name, e.salience) for e in ents]
    cats = []
    try:
        for c in client.classify_text(request={'document': doc}).categories:
            cats.append((c.name, c.confidence))
    except Exception:
        pass
    return {
        'sentiment_score': sent.score,
        'sentiment_magnitude': sent.magnitude,
        'entities': entities,
        'categories': cats
    }

# -------------------------------------------------------------------------
# Gmail OAuth2 + IMAP
# -------------------------------------------------------------------------
def login_gmail_oauth(force_relogin=False):
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

    auth_str = f'user={email_addr}\1auth=Bearer {creds.token}\1\1'
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.authenticate('XOAUTH2', lambda x: auth_str)
    return mail

# -------------------------------------------------------------------------
# Outlook OAuth2 + IMAP
# -------------------------------------------------------------------------
def login_outlook_oauth(client_id, tenant, scopes, token_cache_file='msal_token.json'):
    cache = msal.SerializableTokenCache()
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file, 'r').read())

    app = msal.PublicClientApplication(
        client_id,
        authority=f'https://login.microsoftonline.com/{tenant}',
        token_cache=cache
    )
    accounts = app.get_accounts()
    result = app.acquire_token_silent(scopes, account=accounts[0]) if accounts else None

    if not result:
        auth_url = app.get_authorization_request_url(scopes, redirect_uri='http://localhost:8080')
        server = run_local_server(8080)
        webbrowser.open(auth_url)
        server.handle_request()
        code = OAuth2CallbackHandler.code
        result = app.acquire_token_by_authorization_code(
            code, scopes=scopes, redirect_uri='http://localhost:8080'
        )

    with open(token_cache_file, 'w') as f:
        f.write(cache.serialize())

    user  = result['id_token_claims']['upn']
    token = result['access_token']
    auth = f'user={user}\1auth=Bearer {token}\1\1'
    mail = imaplib.IMAP4_SSL(OUTLOOK_IMAP_HOST)
    mail.authenticate('XOAUTH2', lambda x: auth)
    return mail

# -------------------------------------------------------------------------
# Fetch & parse email bodies
# -------------------------------------------------------------------------
def fetch_email_messages(mail, folder='INBOX', limit=100):
    mail.select(folder)
    status, data = mail.search(None, 'ALL')
    if status != 'OK':
        return []

    ids = data[0].split()[-limit:]
    out = []
    for eid in ids:
        res, msg_data = mail.fetch(eid, '(RFC822)')
        if res != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        # decode headers
        def clean(hdr):
            parts = decode_header(hdr or '')
            return ''.join(
                p.decode(enc or 'utf-8', errors='ignore') if isinstance(p, bytes) else p
                for (p, enc) in parts
            )

        subject = clean(msg.get('Subject'))
        sender  = clean(msg.get('From'))
        date     = clean(msg.get('Date'))

        # get plain-text body
        parts = []
        if msg.is_multipart():
            for p in msg.walk():
                if p.get_content_type()=='text/plain' and 'attachment' not in str(p.get('Content-Disposition')):
                    parts.append(p.get_payload(decode=True).decode(errors='ignore'))
        else:
            parts.append(msg.get_payload(decode=True).decode(errors='ignore'))

        body = "\n".join(parts)
        out.append({'from': sender, 'date': date, 'subject': subject, 'body': body})

    return out

# -------------------------------------------------------------------------
# Flask application
# -------------------------------------------------------------------------
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    messages = []
    error = None

    if request.method == 'POST':
        provider = request.form.get('provider')
        nlp_client = make_nlp_client()

        try:
            if provider == 'gmail':
                force = request.form.get('forceRelogin') == 'on'
                mail = login_gmail_oauth(force_relogin=force)
            elif provider == 'outlook':
                client_id = request.form.get('clientId')
                tenant    = request.form.get('tenant')
                scopes    = ['https://outlook.office365.com/IMAP.AccessAsUser.All']
                mail = login_outlook_oauth(client_id, tenant, scopes)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            raw = fetch_email_messages(mail, limit=50)
            for msg in raw:
                analysis = analyze_text_nlp(nlp_client, msg['body'])
                msg.update(analysis)
                messages.append(msg)

            mail.logout()

        except Exception as e:
            # Capture and display any login/fetch errors
            error = str(e)

    return render_template('index2.html', messages=messages, error=error)

if __name__ == '__main__':
    app.run(debug=True)
