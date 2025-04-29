from bs4 import BeautifulSoup
import requests
import os
import re

def sanitize_filename(name):
    """Nettoie une chaîne pour l'utiliser comme nom de fichier."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()[:100]  # Limite la longueur du nom

def scrape_page(url):
    """Scrape une page et extrait son titre et son contenu."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.title.string.strip() if soup.title else "Titre non disponible"

        article_content = ""
        article_tags = soup.find_all("p", class_=lambda x: x and "article__paragraph" in x.lower())
        if not article_tags:
            article_tags = soup.find_all("p")

        for tag in article_tags:
            article_content += tag.get_text(separator=" ", strip=True) + "\n"

        if not article_content.strip():
            article_content = "Contenu non disponible"

        print(f"Scrapé : {url}\nTitre : {title}\n---\n")
        return title, article_content
    except Exception as e:
        print(f"Erreur lors du scraping de {url} : {e}")
        return None, None

def scrape_from_file(file_path, output_dir):
    """Lit les URLs depuis un fichier et sauvegarde chaque article dans un fichier distinct."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            urls = [url.strip() for url in file.readlines() if url.strip()]

        os.makedirs(output_dir, exist_ok=True)

        for i, url in enumerate(urls, start=1):
            title, content = scrape_page(url)
            if title and content:
                filename = f"{i:03d}_{sanitize_filename(title)}.txt"
                output_path = os.path.join(output_dir, filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\nTitre: {title}\n\n{content}")

    except Exception as e:
        print(f"Erreur lors de l'ouverture du fichier {file_path} : {e}")

input_file = "urls_economie.txt"
output_dir = "../data/economie" #N'oubliez pas de changer le chemin'

scrape_from_file(input_file, output_dir)
