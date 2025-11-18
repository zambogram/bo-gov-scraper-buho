"""
Scraper para Tribunal Supremo de Justicia (TSJ)
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TSJScraper(BaseScraper):
    """Scraper para TSJ"""

    def __init__(self):
        super().__init__('tsj')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """Listar autos supremos y sentencias del TSJ"""
        logger.info(f"Listando documentos de {self.site_id}")

        documentos_ejemplo = [
            {
                'id_documento': 'tsj_as_0100_2024',
                'tipo_documento': 'Auto Supremo',
                'numero_norma': '100/2024',
                'fecha': '2024-01-10',
                'titulo': 'Auto Supremo 100/2024',
                'url': f'{self.config.url_base}/autos/2024/as-0100-2024.pdf',
                'sumilla': 'Materia Civil'
            },
            {
                'id_documento': 'tsj_as_0101_2024',
                'tipo_documento': 'Auto Supremo',
                'numero_norma': '101/2024',
                'fecha': '2024-01-15',
                'titulo': 'Auto Supremo 101/2024',
                'url': f'{self.config.url_base}/autos/2024/as-0101-2024.pdf',
                'sumilla': 'Materia Penal'
            }
        ]

        if limite:
            documentos_ejemplo = documentos_ejemplo[:limite]

        logger.info(f"✓ Encontrados {len(documentos_ejemplo)} documentos en {self.site_id}")
        return documentos_ejemplo

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """Descargar PDF del TSJ"""
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_destino, 'wb') as f:
            f.write(b'%PDF-1.4\nEjemplo de PDF del TSJ\n')
        logger.info(f"✓ PDF de ejemplo creado: {ruta_destino}")
        return True
