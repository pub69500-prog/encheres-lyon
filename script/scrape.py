import re
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import tabula  # Pour PDF

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

    # EXEMPLE HTML : Ivoire Lyon / Bérard-Péron-Schintgen
    def scrape_ivoiere_berard(self):
        url = "https://www.lyon-encheres.fr/fr/acheter/ventes_venir/"
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, "html.parser")
        # À compléter SELON HTML réel, méthode brute pour illustrer :
        ventes = soup.find_all('div', class_='vente-block')  # adapte ce sélecteur
        for vente in ventes:
            titre = vente.find('h2').get_text()
            date_raw = vente.find('span', class_='vente-date').get_text()
            heure = vente.find('span', class_='vente-heure').get_text() if vente.find('span', class_='vente-heure') else ""
            lieu = vente.find('span', class_='vente-lieu').get_text() if vente.find('span', class_='vente-lieu') else ""
            lien = vente.find('a')['href'] if vente.find('a') else url
            date_iso = self.format_date(date_raw)
            self.add_auction(date_iso, titre, "Ivoire Lyon / Bérard-Péron-Schintgen", heure, lieu, lien)

    # EXEMPLE PDF : Maison fictive pour illustration (adapte l’URL et le nom !)
    def scrape_maison_pdf(self):
        pdf_url = "https://site-maison.fr/calendrier-maison.pdf"
        pdf_file = "data/maison_temp.pdf"
        r = requests.get(pdf_url, headers=self.headers)
        with open(pdf_file, "wb") as f:
            f.write(r.content)
        tables = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True, lattice=True)
        for table in tables:
            for row in table.values:
                if len(row) < 2:
                    continue
                date_raw, titre = row[0], row[1]
                heure = row[2] if len(row) > 2 else ""
                lieu = row[3] if len(row) > 3 else ""
                date_iso = self.format_date(str(date_raw))
                self.add_auction(date_iso, str(titre), "Maison PDF", str(heure), str(lieu), pdf_url)

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
        self.scrape_ivoiere_berard()      # HTML direct exploitable
        self.scrape_maison_pdf()          # PDF (exemple, adapte à tes vraies URLs)
        # ...Ajoute ici une fonction par maison, en HTML ou PDF selon le cas...

def main():
    scraper = LyonAuctionsScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
