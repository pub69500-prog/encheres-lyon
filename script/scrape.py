import re
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class LyonAuctionsScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.auctions = []

    def format_date(self, fr_date):
        mois = {'janvier':'01','février':'02','mars':'03','avril':'04','mai':'05','juin':'06','juillet':'07','août':'08','septembre':'09','octobre':'10','novembre':'11','décembre':'12'}
        match = re.search(r'(\d{1,2}) (\w+) (\d{4})', fr_date)
        if match:
            jour = match.group(1)
            m = mois.get(match.group(2), '01')
            an = match.group(3)
            return f"{an}-{m}-{jour.zfill(2)}"
        return datetime.now().strftime("%Y-%m-%d")

    def add_auction(self, date, title, house, time, location, url):
        self.auctions.append({
            "date": date,
            "title": title,
            "house": house,
            "time": time if time else "",
            "location": location if location else "",
            "url": url if url else ""
        })

    def scrape_debaecque(self):
        url = "https://www.debaecque.fr/ventes-a-venir"
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, "html.parser")
        ventes = soup.find_all('div', class_='calendrier entry clearfix')
        for vente in ventes:
            h2 = vente.find('div', class_='entry-title')
            titre = h2.text.strip() if h2 else ""
            blocdate = vente.find('div', class_='blocventedate')
            date_heure = blocdate.text.strip() if blocdate else ""
            m = re.search(r'(\w+ \d{2} \w+ \d{4})[^\d]*(\d{1,2}h\d{2}|\d{1,2}h)?', date_heure)
            date, heure = "", ""
            if m:
                date = self.format_date(m.group(1))
                heure = (m.group(2) or "").replace("h", "h00").strip() if m.group(2) else ""
            lieu = ""
            bloclieu = vente.find('div', class_='blocventelieui')
            if bloclieu:
                lieu = bloclieu.text.strip()
            a = vente.find('div', class_='entry-title').find('a') if vente.find('div', class_='entry-title') else None
            lien = url
            if a and a.get('href'):
                lien = "https://www.debaecque.fr/" + a.get('href').lstrip('/')
            self.add_auction(date, titre, "De Baecque & Associés", heure, lieu, lien)

    def scrape_conan(self):
        url = "https://www.conanauction.fr/calendrier"
        r = requests.get(url, headers=self.headers)
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

    def organize_by_date(self):
        auctions_by_date = {}
        for a in self.auctions:
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

def main():
    scraper = LyonAuctionsScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
