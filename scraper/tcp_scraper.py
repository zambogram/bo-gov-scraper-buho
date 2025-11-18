"""
Scraper for Tribunal Constitucional Plurinacional (TCP)
"""
from datetime import datetime
from typing import Dict, List, Optional
from scraper.base_scraper import BaseScraper


class TCPScraper(BaseScraper):
    """Scraper for TCP website"""

    def __init__(self):
        super().__init__(
            name='tcp',
            base_url='https://www.tcpbolivia.bo'
        )

    def scrape(self, limit: Optional[int] = None, only_new: bool = False) -> Dict:
        """Scrape TCP website for constitutional rulings"""
        existing_index = self.load_index()
        existing_urls = {doc['url']: doc for doc in existing_index}

        stats = {'new': 0, 'modified': 0, 'unchanged': 0, 'errors': 0}
        new_index = []

        # Simulated scraping - in real implementation, this would fetch actual pages
        # For now, we'll create realistic sample data
        sample_urls = [
            f'{self.base_url}/sentencias/constitucional/2024/SC-{str(i).zfill(4)}-2024.html'
            for i in range(1, (limit or 10) + 1)
        ]

        for i, url in enumerate(sample_urls, 1):
            try:
                # Simulate fetching document
                doc_id = f'tcp-{str(i).zfill(6)}'
                title = f'Sentencia Constitucional SC-{str(i).zfill(4)}/2024'
                content = f'Contenido simulado de la sentencia constitucional {i}...'
                md5 = self.compute_md5(content)

                # Check if exists
                if url in existing_urls:
                    existing_doc = existing_urls[url]
                    if existing_doc.get('md5') == md5:
                        stats['unchanged'] += 1
                        new_index.append(existing_doc)
                        continue
                    else:
                        stats['modified'] += 1
                        status = 'modified'
                else:
                    if only_new:
                        stats['new'] += 1
                        status = 'new'
                    else:
                        stats['new'] += 1
                        status = 'new'

                document = {
                    'id': doc_id,
                    'site': 'tcp',
                    'url': url,
                    'title': title,
                    'content': content,
                    'md5': md5,
                    'status': status,
                    'scraped_at': datetime.now().isoformat(),
                    'metadata': {
                        'tipo': 'Sentencia Constitucional',
                        'numero': f'SC-{str(i).zfill(4)}/2024',
                        'fecha': '2024-01-15'
                    }
                }

                new_index.append(document)

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                stats['errors'] += 1

        # Save updated index
        self.save_index(new_index)

        return stats
