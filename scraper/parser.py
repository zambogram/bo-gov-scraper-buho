"""
Legal document parser for extracting structured articles and sections
"""
import re
from typing import Dict, List, Optional


class LegalParser:
    """Parser for legal documents"""

    @staticmethod
    def parse_document(document: Dict) -> List[Dict]:
        """
        Parse a legal document into structured articles

        Args:
            document: Document dictionary with content and metadata

        Returns:
            List of article dictionaries
        """
        content = document.get('content', '')
        doc_id = document.get('id')
        site = document.get('site')

        articles = []

        # Simple parsing strategy - look for article patterns
        # In real implementation, this would be more sophisticated
        article_patterns = [
            r'Artículo\s+(\d+)[°º]?\s*[.-]\s*(.*?)(?=Artículo\s+\d+|$)',
            r'Art\.\s*(\d+)[°º]?\s*[.-]\s*(.*?)(?=Art\.\s*\d+|$)',
            r'ARTÍCULO\s+(\d+)[°º]?\s*[.-]\s*(.*?)(?=ARTÍCULO\s+\d+|$)',
        ]

        found_articles = []
        for pattern in article_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                article_num = match.group(1)
                article_text = match.group(2).strip()
                found_articles.append({
                    'number': int(article_num),
                    'text': article_text
                })

        # If no articles found, create a single article with all content
        if not found_articles:
            found_articles = [{
                'number': 1,
                'text': content
            }]

        # Create article objects
        for i, art in enumerate(found_articles, 1):
            article = {
                'id': f'{doc_id}-art-{str(art["number"]).zfill(3)}',
                'document_id': doc_id,
                'site': site,
                'article_number': art['number'],
                'content': art['text'],
                'metadata': {
                    'document_title': document.get('title'),
                    'document_url': document.get('url'),
                    'document_type': document.get('metadata', {}).get('tipo'),
                    'parsed_at': document.get('scraped_at')
                }
            }
            articles.append(article)

        return articles

    @staticmethod
    def parse_all_documents(documents: List[Dict]) -> List[Dict]:
        """Parse all documents and return list of all articles"""
        all_articles = []
        for doc in documents:
            articles = LegalParser.parse_document(doc)
            all_articles.extend(articles)
        return all_articles
