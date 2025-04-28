from flask import Flask, request, render_template, redirect, url_for
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from controller import Controller
import onetimescript
from db import db
import logging
import dns.resolver
import socket
import ssl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import whois

app = Flask(
    __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///domains.db'
db.init_app(app)
with app.app_context():
    db.create_all()

logging.basicConfig(level=logging.DEBUG)

controller = Controller()



@app.route('/', methods=['GET', 'POST'], endpoint='home')
def home():
    try:
        url = request.form.get('url', '')
        result = controller.main(url) if url else None
        return render_template('index.html', output=result)
    except Exception as e:
        app.logger.exception("Error processing URL %s", url)
        return render_template('index.html', output={
            'url': url,
            'error': f"Processing error: {e}"
        })

@app.route('/preview', methods=['POST'])
def preview():
    url = request.form.get('url', '')
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'},
            verify=False
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        for link in soup.find_all('link'):
            if link.get('href'):
                link['href'] = urljoin(url, link['href'])
        for img in soup.find_all('img'):
            if img.get('src'):
                img['src'] = urljoin(url, img['src'])

        return render_template('preview.html', content=soup.prettify())
    except Exception as e:
        app.logger.exception("Preview fetch failed for %s", url)
        return render_template('index.html', output={
            'url': url,
            'error': f"Preview error: {e}"
        })

@app.route('/source-code', methods=['GET', 'POST'])
def view_source_code():
    url = request.form.get('url', '')
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'},
            verify=False
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        formatted_html = soup.prettify()
        return render_template('source_code.html', formatted_html=formatted_html, url=url)
    except Exception as e:
        app.logger.exception("Source fetch failed for %s", url)
        return render_template('index.html', output={
            'url': url,
            'error': f"Source error: {e}"
        })

@app.route('/update-db')
def update_db():
    try:
        with app.app_context():
            response = onetimescript.update_db()
            app.logger.info("Database populated successfully")
            return response, 200
    except Exception as e:
        app.logger.exception("Error updating DB")
        return f"An error occurred: {e}", 500

@app.route('/update-json')
def update_json():
    try:
        with app.app_context():
            response = onetimescript.update_json()
            app.logger.info("JSON updated successfully")
            return response, 200
    except Exception as e:
        app.logger.exception("Error updating JSON")
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
