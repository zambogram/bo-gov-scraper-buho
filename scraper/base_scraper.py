"""
Base Scraper class for all government website scrapers
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup


class BaseScraper:
    """Base class for all scrapers"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Create necessary directories
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.index_dir = os.path.join(self.data_dir, 'index')
        self.articles_dir = os.path.join(self.data_dir, 'articles')
        self.exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports', self.name)

        for directory in [self.index_dir, self.articles_dir, self.exports_dir]:
            os.makedirs(directory, exist_ok=True)

    def get_index_path(self) -> str:
        """Get path to index file"""
        return os.path.join(self.index_dir, f'{self.name}_index.json')

    def get_articles_path(self) -> str:
        """Get path to articles file"""
        return os.path.join(self.articles_dir, f'{self.name}_articles.json')

    def load_index(self) -> List[Dict]:
        """Load existing index"""
        index_path = self.get_index_path()
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_index(self, documents: List[Dict]):
        """Save index to file"""
        index_path = self.get_index_path()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

    def load_articles(self) -> List[Dict]:
        """Load existing articles"""
        articles_path = self.get_articles_path()
        if os.path.exists(articles_path):
            with open(articles_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_articles(self, articles: List[Dict]):
        """Save articles to file"""
        articles_path = self.get_articles_path()
        with open(articles_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)

    def compute_md5(self, content: str) -> str:
        """Compute MD5 hash of content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def scrape(self, limit: Optional[int] = None, only_new: bool = False) -> Dict:
        """
        Main scraping method - to be implemented by subclasses

        Returns:
            Dict with keys: new, modified, unchanged, errors
        """
        raise NotImplementedError("Subclasses must implement scrape()")

    def export_jsonl(self):
        """Export documents and articles to JSONL format"""
        # Export documents
        documents = self.load_index()
        docs_path = os.path.join(self.exports_dir, 'documents.jsonl')
        with open(docs_path, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')

        # Export articles
        articles = self.load_articles()
        articles_path = os.path.join(self.exports_dir, 'articles.jsonl')
        with open(articles_path, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        return {
            'documents': len(documents),
            'articles': len(articles),
            'documents_path': docs_path,
            'articles_path': articles_path
        }

    def get_stats(self) -> Dict:
        """Get statistics for this scraper"""
        documents = self.load_index()
        articles = self.load_articles()

        last_update = None
        if documents:
            dates = [doc.get('scraped_at') for doc in documents if doc.get('scraped_at')]
            if dates:
                last_update = max(dates)

        return {
            'name': self.name,
            'total_documents': len(documents),
            'total_articles': len(articles),
            'last_update': last_update
        }
