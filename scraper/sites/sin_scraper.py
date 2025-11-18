"""
Scraper para SIN (Servicio de Impuestos Nacionales)
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SINScraper(BaseScraper):
    """Scraper para SIN"""

    def __init__(self):
        super().__init__('sin')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """Listar resoluciones normativas del SIN"""
        logger.info(f"Listando documentos de {self.site_id}")

        documentos_ejemplo = [
            {
                'id_documento': 'sin_rn_0010_2024',
                'tipo_documento': 'Resolución Normativa',
                'numero_norma': '102400000010',
                'fecha': '2024-01-30',
                'titulo': 'Resolución Normativa de Directorio 102400000010',
                'url': f'{self.config.url_base}/normativa/rn-0010-2024.pdf',
                'sumilla': 'Normativa tributaria'
            }
        ]

        if limite:
            documentos_ejemplo = documentos_ejemplo[:limite]

        logger.info(f"✓ Encontrados {len(documentos_ejemplo)} documentos en {self.site_id}")
        return documentos_ejemplo

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """Descargar PDF del SIN"""
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_destino, 'wb') as f:
            f.write(b'%PDF-1.4\nEjemplo de PDF del SIN\n')
        logger.info(f"✓ PDF de ejemplo creado: {ruta_destino}")
        return True
