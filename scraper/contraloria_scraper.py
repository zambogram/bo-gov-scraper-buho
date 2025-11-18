"""
Scraper for Contraloría General del Estado
"""
from datetime import datetime
from typing import Dict, List, Optional
from scraper.base_scraper import BaseScraper


class ContraloriaScraper(BaseScraper):
    """Scraper for Contraloría website"""

    def __init__(self):
        super().__init__(
            name='contraloria',
            base_url='https://www.contraloria.gob.bo'
        )

    def scrape(self, limit: Optional[int] = None, only_new: bool = False) -> Dict:
        """Scrape Contraloría website for audit reports and regulations"""
        existing_index = self.load_index()
        existing_urls = {doc['url']: doc for doc in existing_index}

        stats = {'new': 0, 'modified': 0, 'unchanged': 0, 'errors': 0}
        new_index = []

        # Simulated scraping
        sample_urls = [
            f'{self.base_url}/informes/informe-auditoria-{str(i).zfill(4)}-2024.html'
            for i in range(1, (limit or 10) + 1)
        ]

        for i, url in enumerate(sample_urls, 1):
            try:
                doc_id = f'contraloria-{str(i).zfill(6)}'
                title = f'Informe de Auditoría {str(i).zfill(4)}/2024'
                content = f'Contenido simulado del informe de auditoría {i}...'
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
                    'site': 'contraloria',
                    'url': url,
                    'title': title,
                    'content': content,
                    'md5': md5,
                    'status': status,
                    'scraped_at': datetime.now().isoformat(),
                    'metadata': {
                        'tipo': 'Informe de Auditoría',
                        'numero': f'{str(i).zfill(4)}/2024',
                        'entidad': 'Entidad Pública',
                        'fecha': '2024-01-15'
                    }
                }

                new_index.append(document)

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                stats['errors'] += 1

        self.save_index(new_index)
        return stats
