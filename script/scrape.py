def scrape_debaecque(self):
    url = "https://www.debaecque.fr/ventes-a-venir"
    r = requests.get(url, headers=self.headers)
    soup = BeautifulSoup(r.text, "html.parser")
    ventes = soup.find_all('div', class_='calendrier entry clearfix')
    for vente in ventes:
        # Récupère lien catalogue
        col_image = vente.find('div', class_='col-md-2 entry-image couverturecatalogue')
        lien = url
        if col_image and col_image.find('a') and col_image.find('a').get('href'):
            href = col_image.find('a').get('href')
            lien = "https://www.debaecque.fr/" + href.lstrip('/')

        # Titre
        titre = ""
        h2 = vente.find('div', class_='entry-title')
        if h2 and h2.find('a'):
            titre = h2.find('a').text.strip()
        elif h2:
            titre = h2.text.strip()

        # Date et heure
        blocdate = vente.find('div', class_='blocventedate')
        date_heure = blocdate.text.strip() if blocdate else ""
        m = re.search(r'(\w+ \d{2} \w+ \d{4})[^\d]*(\d{1,2}h\d{2,2}|\d{1,2}h)?', date_heure)
        date, heure = "", ""
        if m:
            date = self.format_date(m.group(1))
            heure = (m.group(2) or "").replace("h", "h00").strip() if m.group(2) else ""

        # Lieu
        bloclieu = vente.find('div', class_='blocventelieui')
        lieu = bloclieu.text.strip() if bloclieu else ""

        self.add_auction(date, titre, "De Baecque & Associés", heure, lieu, lien)
