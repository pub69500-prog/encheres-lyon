import re
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.ERROR)

class LyonAuctionsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.auctions = []

    def format_date(self, fr_date):
        mois = {'janvier':'01', 'février':'02', 'mars':'03', 'avril':'04', 'mai':'05', 'juin':'06',
                'juillet':'07', 'août':'08', 'septembre':'09', 'octobre':'10', 'novembre':'11', 'décembre':'12'}
        match = re.search(r'(\d{1,2})\s*(\w+)\s*(\d{4})', fr_date)  # Amélioré pour espaces variables
        if match:
            jour = match.group(1).zfill(2)
            m = mois.get(match.group(2).lower(), '01')
            an = match.group(3)
            return f"{an}-{m}-{jour}"
        return datetime.now().strftime("%Y-%m-%d")

    def add_auction(self, date, title, house, time, location, url):
        # Filtre pour Lyon/Rhône
        if not location or not any(term in location.lower() for term in ['lyon', 'rhône', '69', 'villeurbanne']):
            return
        self.auctions.append({
            "date": date, "title": title, "house": house,
            "time": time or "", "location": location or "", "url": url or ""
        })

    def scrape_debaecque(self):
        url = "https://www.debaecque.fr/ventes-a-venir"
        try:
            r = self.session.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            ventes = soup.find_all('div', class_='calendrier entry clearfix')
            for vente in ventes:
                col_image = vente.find('div', class_='col-md-2 entry-image couverturecatalogue')
                lien = url
                if col_image and col_image.find('a'):
                    href = col_image.find('a').get('href')
                    if href:
                        lien = "https://www.debaecque.fr/" + href.lstrip('/')
                h2 = vente.find('div', class_='entry-title')
                titre = h2.find('a').text.strip() if h2 and h2.find('a') else h2.text.strip() if h2 else ""
                blocdate = vente.find('div', class_='blocventedate')
                date_heure = blocdate.text.strip() if blocdate else ""
                m = re.search(r'(\w+\s+\d{1,2}\s+\w+\s+\d{4})[^\d]*(\d{1,2}h\d{2}|\d{1,2}h)?', date_heure)
                date, heure = "", ""
                if m:
                    date = self.format_date(m.group(1))
                    heure = m.group(2).replace("h", "h00") if m.group(2) else ""
                bloclieu = vente.find('div', class_='blocventelieui')
                lieu = bloclieu.text.strip() if bloclieu else ""
                self.add_auction(date, titre, "De Baecque & Associés", heure, lieu, lien)
        except Exception as e:
            logging.error(f"Erreur lors du scrape de De Baecque: {e}")

    def scrape_conan(self):
        url = "https://www.conanauction.fr/calendrier"
        try:
            r = self.session.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            ventes = soup.find_all('div', class_='entry')
            for vente in ventes:
                titre_el = vente.find('div', class_='entry-title')
                titre = titre_el.text.strip() if titre_el else ""
                date_el = vente.find('div', class_='entry-date')
                date_str = date_el.text.strip() if date_el else ""
                date_iso = self.format_date(date_str)
                heure_el = vente.find('div', class_='entry-time')
                heure = heure_el.text.strip() if heure_el else ""
                lieu_el = vente.find('div', class_='entry-location')
                lieu = lieu_el.text.strip() if lieu_el else ""
                lien = titre_el.find('a')['href'] if titre_el and titre_el.find('a') else url
                self.add_auction(date
