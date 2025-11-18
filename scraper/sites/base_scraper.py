"""
Scraper base para todos los sitios
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import requests
import time
import logging
from datetime import datetime

from scraper.models import Documento
from config import get_site_config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Clase base para todos los scrapers"""

    def __init__(self, site_id: str):
        """
        Inicializar scraper

        Args:
            site_id: ID del sitio (tcp, tsj, etc.)
        """
        self.site_id = site_id
        self.config = get_site_config(site_id)

        if not self.config:
            raise ValueError(f"Configuración no encontrada para sitio: {site_id}")

        # Configuración de requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 BUHO Legal Scraper/1.0'
        })

        # Delay entre requests
        self.delay = self.config.scraper.get('delay_entre_requests', 2)

    @abstractmethod
    def listar_documentos(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Listar documentos disponibles en el sitio

        Args:
            limite: Número máximo de documentos a retornar

        Returns:
            Lista de diccionarios con metadata de documentos
        """
        pass

    @abstractmethod
    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """
        Descargar PDF de un documento

        Args:
            url: URL del PDF
            ruta_destino: Ruta donde guardar el PDF

        Returns:
            True si se descargó correctamente
        """
        pass

    def _download_file(self, url: str, destino: Path, timeout: int = 30) -> bool:
        """
        Método auxiliar para descargar archivos

        Args:
            url: URL del archivo
            destino: Ruta de destino
            timeout: Timeout en segundos

        Returns:
            True si se descargó correctamente
        """
        try:
            # Asegurar que el directorio existe
            destino.parent.mkdir(parents=True, exist_ok=True)

            # Descargar
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            # Guardar
            with open(destino, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"✓ Descargado: {destino.name}")

            # Esperar antes del siguiente request
            time.sleep(self.delay)

            return True

        except Exception as e:
            logger.error(f"✗ Error descargando {url}: {e}")
            return False

    def crear_documento_desde_metadata(self, metadata: Dict[str, Any]) -> Documento:
        """
        Crear objeto Documento desde metadata

        Args:
            metadata: Diccionario con metadata del documento

        Returns:
            Documento inicializado
        """
        return Documento(
            id_documento=metadata.get('id_documento', ''),
            site=self.site_id,
            tipo_documento=metadata.get('tipo_documento', ''),
            numero_norma=metadata.get('numero_norma'),
            fecha=metadata.get('fecha'),
            fecha_publicacion=metadata.get('fecha_publicacion'),
            titulo=metadata.get('titulo'),
            sumilla=metadata.get('sumilla'),
            url_origen=metadata.get('url'),
            metadata=metadata
        )

    def __del__(self):
        """Cerrar sesión al destruir el objeto"""
        if hasattr(self, 'session'):
            self.session.close()
