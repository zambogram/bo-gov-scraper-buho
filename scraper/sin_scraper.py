"""
Scraper for Servicio de Impuestos Nacionales (SIN)
"""
from datetime import datetime
from typing import Dict, List, Optional
from scraper.base_scraper import BaseScraper


class SINScraper(BaseScraper):
    """Scraper for SIN website"""

    def __init__(self):
        super().__init__(
            name='sin',
            base_url='https://www.impuestos.gob.bo'
        )

    def scrape(self, limit: Optional[int] = None, only_new: bool = False) -> Dict:
        """Scrape SIN website for tax regulations"""
        existing_index = self.load_index()
        existing_urls = {doc['url']: doc for doc in existing_index}

        stats = {'new': 0, 'modified': 0, 'unchanged': 0, 'errors': 0}
        new_index = []

        # Simulated scraping
        sample_urls = [
            f'{self.base_url}/normativa/resolucion-normativa-{str(i).zfill(4)}-2024.html'
            for i in range(1, (limit or 10) + 1)
        ]

        for i, url in enumerate(sample_urls, 1):
            try:
                doc_id = f'sin-{str(i).zfill(6)}'
                title = f'Resolución Normativa {str(i).zfill(4)}/2024'
                content = f'Contenido simulado de la resolución normativa {i}...'
                md5 = self.compute_md5(content)

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
                    stats['new'] += 1
                    status = 'new'

                document = {
                    'id': doc_id,
                    'site': 'sin',
                    'url': url,
                    'title': title,
                    'content': content,
                    'md5': md5,
                    'status': status,
                    'scraped_at': datetime.now().isoformat(),
                    'metadata': {
                        'tipo': 'Resolución Normativa',
                        'numero': f'{str(i).zfill(4)}/2024',
                        'area': 'Tributación',
                        'fecha': '2024-01-15'
                    }
                }

                new_index.append(document)

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                stats['errors'] += 1

        self.save_index(new_index)
        return stats
