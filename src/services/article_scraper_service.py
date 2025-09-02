import requests
from bs4 import BeautifulSoup
from readability import Document
from newspaper import Article, Config

class ArticleScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.config = Config()
        self.config.browser_user_agent = self.headers['User-Agent']
        self.config.request_timeout = 20

    def _fetch_html(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    def scrape_with_readability(self, url):
        html = self._fetch_html(url)
        if not html:
            return None

        doc = Document(html)
        title = doc.title()
        content = doc.summary()  # Pegando o conteúdo completo

        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)

    def scrape_with_newspaper(self, url):
        try:
            article = Article(url, config=self.config)
            article.download()
            article.parse()
            article.nlp()  # Opcional, se quiser resumo/tags
            return article.text
        except Exception as e:
            print(f"Error scraping with newspaper3k for URL {url}: {e}")
            return None

    def scrape_article_content(self, url):
        # Tenta primeiro com newspaper
        content = self.scrape_with_newspaper(url)
        if content and len(content) > 200:
            return content

        # Fallback para readability se newspaper falhar ou retornar pouco conteúdo
        return self.scrape_with_readability(url)

article_scraper = ArticleScraper()
