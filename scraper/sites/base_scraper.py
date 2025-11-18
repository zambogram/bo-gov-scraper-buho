"""
Scraper base para todos los sitios
Soporte para scraping histórico completo y delta updates
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import requests
import time
import logging
from datetime import datetime

from scraper.models import Documento
from config import get_site_config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Clase base para todos los scrapers con soporte para scraping histórico"""

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

        # Items por página
        self.items_por_pagina = self.config.scraper.get('items_por_pagina', 20)

    @abstractmethod
    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Listar documentos disponibles en el sitio

        Args:
            limite: Número máximo de documentos a retornar
            modo: 'full' para histórico completo, 'delta' para solo nuevos
            pagina: Número de página a obtener (para paginación)

        Returns:
            Lista de diccionarios con metadata de documentos
        """
        pass

    def listar_documentos_historico_completo(
        self,
        limite_total: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Listar TODOS los documentos del sitio (scraping histórico completo)

        Recorre todas las páginas disponibles hasta agotar resultados.

        Args:
            limite_total: Límite total de documentos (None = sin límite)
            progress_callback: Función callback para reportar progreso

        Returns:
            Lista completa de documentos
        """
        todos_documentos = []
        pagina = 1
        documentos_obtenidos = 0

        logger.info(f"🔄 Iniciando scraping histórico completo de {self.site_id}")

        while True:
            # Verificar si ya alcanzamos el límite
            if limite_total and documentos_obtenidos >= limite_total:
                logger.info(f"✓ Alcanzado límite de {limite_total} documentos")
                break

            # Calcular cuántos documentos solicitar en esta página
            limite_pagina = None
            if limite_total:
                restantes = limite_total - documentos_obtenidos
                limite_pagina = min(self.items_por_pagina, restantes)

            # Listar documentos de esta página
            try:
                logger.info(f"📄 Obteniendo página {pagina}...")
                documentos_pagina = self.listar_documentos(
                    limite=limite_pagina,
                    modo="full",
                    pagina=pagina
                )

                # Si no hay más documentos, terminar
                if not documentos_pagina:
                    logger.info(f"✓ No hay más documentos en página {pagina}")
                    break

                # Agregar documentos de esta página
                todos_documentos.extend(documentos_pagina)
                documentos_obtenidos += len(documentos_pagina)

                # Callback de progreso
                if progress_callback:
                    progress_callback(
                        f"Página {pagina}: {len(documentos_pagina)} documentos "
                        f"(total: {documentos_obtenidos})"
                    )

                logger.info(
                    f"✓ Página {pagina}: {len(documentos_pagina)} documentos "
                    f"(acumulado: {documentos_obtenidos})"
                )

                # Si obtuvimos menos documentos que el máximo por página,
                # probablemente sea la última página
                if len(documentos_pagina) < self.items_por_pagina:
                    logger.info(f"✓ Última página alcanzada (página {pagina})")
                    break

                # Siguiente página
                pagina += 1

                # Delay entre páginas
                time.sleep(self.delay)

            except Exception as e:
                logger.error(f"✗ Error en página {pagina}: {e}")
                # Continuar con la siguiente página en caso de error
                pagina += 1
                if pagina > 100:  # Máximo de seguridad
                    logger.warning("Alcanzado límite de seguridad de 100 páginas")
                    break

        logger.info(
            f"✅ Scraping histórico completado: {documentos_obtenidos} documentos totales"
        )

        return todos_documentos

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
