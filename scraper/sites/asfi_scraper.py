"""
Scraper para ASFI (Autoridad de Supervisión del Sistema Financiero)
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ASFIScraper(BaseScraper):
    """Scraper para ASFI"""

    def __init__(self):
        super().__init__('asfi')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """Listar resoluciones de ASFI"""
        logger.info(f"Listando documentos de {self.site_id}")

        documentos_ejemplo = [
            {
                'id_documento': 'asfi_ra_0050_2024',
                'tipo_documento': 'Resolución Administrativa',
                'numero_norma': '050/2024',
                'fecha': '2024-01-25',
                'titulo': 'Resolución Administrativa ASFI 050/2024',
                'url': f'{self.config.url_base}/normativa/ra-050-2024.pdf',
                'sumilla': 'Normativa bancaria'
            }
        ]

        if limite:
            documentos_ejemplo = documentos_ejemplo[:limite]

        logger.info(f"✓ Encontrados {len(documentos_ejemplo)} documentos en {self.site_id}")
        return documentos_ejemplo

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """Descargar PDF de ASFI"""
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_destino, 'wb') as f:
            f.write(b'%PDF-1.4\nEjemplo de PDF de ASFI\n')
        logger.info(f"✓ PDF de ejemplo creado: {ruta_destino}")
        return True
