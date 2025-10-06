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

    def scrape_ivoiere_berard(self):
        url = "https://www.lyon-encheres.fr/fr/acheter/ventes_venir/"
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, "html.parser")
        blocks = soup.text.split('### ')
        for block in blocks[1:]:
            titre, reste = block.split('\n', 1)
            date_match = re.search(r'(Mercredi|Samedi|Jeudi|Mardi|Lundi|Vendredi|Dimanche) (\d{2,4}) (\w+) (\d{4}) à ([0-9h]+)', block)
            date_text, time = "", ""
            if date_match:
                dt = f"{date_match.group(2)} {date_match.group(3)} {date_match.group(4)}"
                time = date_match.group(5)
                date_text = self.format_date(dt)
            name = titre.strip()
            self.add_auction(date_text or "", name, "Ivoire Lyon / Bérard-Péron-Schintgen", time, "Corbas ou Lyon", url)

    def scrape_debaecque(self):
        # La page n’affiche que des cookies (vrai calendrier non accessible sans JS+cookies), il faudra le compléter manuellement ou via scraping dynamique plus avancé
        pass

    def scrape_conan(self):
        # La page n’affiche que le consentement cookies pour le calendrier public, pas d’infos sans JS/cookies
        pass

    def scrape_artencheres(self):
        # Le site requiert le consentement, pas de calendrier accessible directement en HTML statique
        pass

    def scrape_aguttes(self):
        # Page de Lyon décrite mais pas de calendrier HTML accessible sans JS
        pass

    def scrape_credit_municipal(self):
        url = "https://www.credit-municipal-lyon.fr/calendrier-enchere-lyon.php"
        # Pas de calendrier structuré dans HTML brut, à voir si page catalogue ou format PDF accessible
        pass

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
        self.scrape_ivoiere_berard()
        # Ajoute ici les autres maisons une fois accès direct HTML ou PDF

def main():
    scraper = LyonAuctionsScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
