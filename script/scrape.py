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
        match = re.search(r'(\w+)?\s*(\d{1,2})\s*(\w+)\s*(\d{4})', fr_date)  # Amélioré pour jour de la semaine optionnel et espaces
        if match:
            jour = match.group(2).zfill(2)
            m = mois.get(match.group(3).lower(), '01')
            an = match.group(4)
            return f"{an}-{m}-{jour}"
        # Cas pour mois/année seulement (ex: OCTOBRE 2025)
        match_month = re.search(r'(\w+)\s*(\d{4})', fr_date)
        if match_month:
            m = mois.get(match_month.group(1).lower(), '01')
            an = match_month.group(2)
            return f"{an}-{m}-01"  # Approximation au 1er du mois
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
                self.add_auction(date_iso, titre, "Conan Hôtel d’Ainay", heure, lieu, lien)
        except Exception as e:
            logging.error(f"Erreur lors du scrape de Conan: {e}")

    def scrape_interencheres(self):
        api_url = "https://api.interencheres.com/v1/public/vente/search"
        params = {"area": "69", "limit": 100, "offset": 0}
        ventes_total = []
        try:
            while True:
                r = self.session.get(api_url, params=params)
                r.raise_for_status()
                data = r.json()
                ventes = data.get("ventes", [])
                if not ventes:
                    break
                ventes_total.extend(ventes)
                if len(ventes) < params["limit"]:
                    break
                params["offset"] += params["limit"]
            for vente in ventes_total:
                date = vente.get("dateDebut", "").split("T")[0]
                titre = vente.get("titre") or ""
                heure = vente.get("dateDebut", "")[11:16]
                maison = vente.get("etude", {}).get("raisonSociale", "Interencheres")
                lieu = vente.get("lieu", {}).get("libelle", "")
                url = "https://www.interencheres.com/" + vente.get("url", "")
                self.add_auction(date, titre, maison, heure, lieu, url)
        except Exception as e:
            logging.error(f"Erreur lors du scrape d'Interencheres: {e}")

    def scrape_artencheres(self):
        url = "https://www.artencheres.fr/ventes-a-venir/"
        try:
            r = self.session.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            ventes = soup.find_all('div', class_='auction-entry')  # Basé sur la structure inférée
            for vente in ventes:
                titre_el = vente.find('h2', class_='auction-title')
                titre = ""
                lien = url
                if titre_el:
                    a = titre_el.find('a', class_='auction-link')
                    if a:
                        titre = a.text.strip()
                        lien = a['href']
                    else:
                        titre = titre_el.text.strip()
                date_el = vente.find('p', class_='auction-date')
                date_heure = date_el.text.strip() if date_el else ""
                # Parsing de la date et heure
                m = re.search(r'(?:(\w+)\s*)?(\d{1,2})\s*(\w+)\s*(\d{4})\s*(?:à\s*(\d{1,2}h\d{2}|\d{1,2}h\d{0,2}))?', date_heure)
                date_iso, heure = "", ""
                if m:
                    date_iso = self.format_date(f"{m.group(2)} {m.group(3)} {m.group(4)}")
                    heure = m.group(5) or ""
                    if heure and 'h' in heure and len(heure.split('h')[1]) == 0:
                        heure += "00"  # Ajoute minutes si absent
                lieu_el = vente.find('p', class_='auction-location')
                lieu = lieu_el.text.strip() if lieu_el else "Lyon, 2-4, rue Saint-Firmin 69008 Lyon"  # Default observé
                self.add_auction(date_iso, titre, "ArtEnchères", heure, lieu, lien)
        except Exception as e:
            logging.error(f"Erreur lors du scrape d'ArtEnchères: {e}")

    def organize_by_date(self):
        auctions_by_date = {}
        today = datetime.now().date()
        for a in self.auctions:
            try:
                auction_date = datetime.strptime(a["date"], "%Y-%m-%d").date()
                if auction_date < today:
                    continue  # Ignorer les ventes passées
            except ValueError:
                continue
            date = a["date"]
            if date not in auctions_by_date:
                auctions_by_date[date] = {
                    "date": date,
                    "displayDate": date,
                    "auctions": []
                }
            auctions_by_date[date]["auctions"].append({k: a[k] for k in a if k != "date"})
        return [auctions_by_date[d] for d in sorted(auctions_by_date.keys())]

    def save_to_json(self, file_path="data/auctions.json"):
        organized = self.organize_by_date()
        data = {
            "last_update": datetime.now().isoformat(),
            "auctions": organized
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def scrape_all(self):
        self.scrape_debaecque()
        self.scrape_conan()
        self.scrape_interencheres()
        self.scrape_artencheres()  # Ajout de la nouvelle méthode

def main():
    scraper = LyonAuctionsScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
