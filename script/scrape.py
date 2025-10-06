#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re
from typing import List, Dict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuctionScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.auctions = []
    
    def parse_date(self, date_str: str) -> str:
        """Convertit une date française en format ISO"""
        months = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        try:
            # Pattern pour "6 octobre 2025"
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str.lower())
            if match:
                day, month, year = match.groups()
                month_num = months.get(month, '01')
                return f"{year}-{month_num}-{day.zfill(2)}"
        except Exception as e:
            logger.error(f"Erreur parsing date: {e}")
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_display_date(self, date_iso: str) -> str:
        """Convertit une date ISO en format d'affichage français"""
        try:
            date_obj = datetime.strptime(date_iso, '%Y-%m-%d')
            days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                     'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
            
            day_name = days[date_obj.weekday()]
            month_name = months[date_obj.month - 1]
            
            return f"{day_name} {date_obj.day} {month_name} {date_obj.year}"
        except Exception as e:
            logger.error(f"Erreur display date: {e}")
            return date_iso
    
    def scrape_debaecque(self):
        """Scrape De Baecque et Associés"""
        try:
            logger.info("Scraping De Baecque...")
            url = "https://www.debaecque.fr/ventes-a-venir"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Logique de scraping spécifique à De Baecque
            # À adapter selon la structure réelle du site
            
            logger.info("De Baecque scraped successfully")
        except Exception as e:
            logger.error(f"Erreur scraping De Baecque: {e}")
    
    def scrape_conan(self):
        """Scrape Conan Hôtel d'Ainay"""
        try:
            logger.info("Scraping Conan...")
            url = "https://www.conanauction.fr/calendrier"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Logique de scraping spécifique à Conan
            
            logger.info("Conan scraped successfully")
        except Exception as e:
            logger.error(f"Erreur scraping Conan: {e}")
    
    def scrape_artencheres(self):
        """Scrape ArtEnchères"""
        try:
            logger.info("Scraping ArtEnchères...")
            url = "https://www.artencheres.fr/ventes-a-venir"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Logique de scraping spécifique à ArtEnchères
            
            logger.info("ArtEnchères scraped successfully")
        except Exception as e:
            logger.error(f"Erreur scraping ArtEnchères: {e}")
    
    def scrape_all(self):
        """Lance tous les scrapers"""
        logger.info("Début du scraping...")
        
        self.scrape_debaecque()
        self.scrape_conan()
        self.scrape_artencheres()
        
        logger.info(f"Scraping terminé. {len(self.auctions)} ventes trouvées.")
        return self.auctions
    
    def organize_by_date(self, auctions: List[Dict]) -> List[Dict]:
        """Organise les ventes par date"""
        auctions_by_date = {}
        
        for auction in auctions:
            date = auction['date']
            if date not in auctions_by_date:
                auctions_by_date[date] = {
                    'date': date,
                    'displayDate': self.get_display_date(date),
                    'auctions': []
                }
            auctions_by_date[date]['auctions'].append({
                'title': auction['title'],
                'house': auction['house'],
                'time': auction['time'],
                'location': auction['location'],
                'url': auction.get('url', '')
            })
        
        # Trier par date
        sorted_auctions = sorted(auctions_by_date.values(), key=lambda x: x['date'])
        return sorted_auctions
    
    def save_to_json(self, output_file: str = 'data/auctions.json'):
        """Sauvegarde les données en JSON"""
        try:
            organized_auctions = self.organize_by_date(self.auctions)
            
            data = {
                'last_update': datetime.now().isoformat(),
                'auctions': organized_auctions
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Données sauvegardées dans {output_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde JSON: {e}")

def main():
    scraper = AuctionScraper()
    scraper.scrape_all()
    scraper.save_to_json()

if __name__ == "__main__":
    main()
