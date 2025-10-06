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
            "time": time or "",
            "location": location or "",
            "url": url or ""
        })

    def scrape_debaecque(self):
        url = "https://www.debaecque.fr/ventes-a-venir"
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, "html.parser")
        ventes = soup.find_all('div', class_='calendrier entry clearfix')
        for vente in ventes:
            titre = ""
            h2 = vente.find('div', class_='entry-title')
            if h2 and h2.find('a'):
                titre = h2.find('a').text.strip()
            elif h2:
                titre = h2.text.strip()
            blocdate = vente.find('div', class_='blocventedate')
            date_heure = blocdate.text.strip() if blocdate else ""
            m = re.search(r'(\w+ \d{2} \w+ \d{4})[^\d]*(\d{1,2}h\d{2,2}|\d{1,2}h)?', date_heure)
            date, heure = "", ""
            if m:
                date = self.format_date(m.group(1))
                heure = (m.group(2) or "").replace("h", "h00").strip() if m.group(2) else ""
            bloclieu = vente.find('div', class_='blocventelieui')
            lieu = bloclieu.text.strip() if bloclieu else ""
            lien = url
            if h2 and h2.find('a') and h2.find('a').get('href'):
                lien = "https://www.debaecque.fr/" + h2.find('a').get('href').lstrip('/')
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

    def scrape_interencheres(self):
        api_url = "https://api.interencheres.com/v1/public/vente/search"
        params = {
            "area": "69",
            "limit": 100,
            "offset": 0
        }
        ventes_total = []
        while True:
            r = requests.get(api_url, params=params, headers=self.headers)
            if r.status_code != 200:
                break
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
            url = "https://www.interencheres.com/{}".format(vente.get("url", ""))
            self.add_auction(date, titre, maison, heure, lieu, url)

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
        self.scrape_interencheres()

def main():
    scraper = LyonAuctionsScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
