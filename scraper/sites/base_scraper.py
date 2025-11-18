"""
Scraper base para todos los sitios
Soporte para scraping histórico completo y delta updates
Con manejo robusto de errores y verificación de disponibilidad
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
from datetime import datetime
import urllib3

from scraper.models import Documento
from config import get_site_config

logger = logging.getLogger(__name__)

# Desactivar warnings de SSL para sitios con certificados mal configurados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

        # Configuración de requests con retry automático
        self.session = requests.Session()

        # Configurar retry strategy (3 intentos con backoff exponencial)
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,  # 2s, 4s, 8s
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 BUHO Legal Scraper/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })

        # Delay entre requests
        self.delay = self.config.scraper.get('delay_entre_requests', 2)

        # Items por página
        self.items_por_pagina = self.config.scraper.get('items_por_pagina', 20)

        # Estado de disponibilidad (se actualiza con check_availability)
        self._is_available = None
        self._last_availability_check = None

    def check_availability(self, force: bool = False) -> Tuple[bool, str]:
        """
        Verificar si el sitio está disponible y accesible

        Args:
            force: Forzar verificación incluso si hay un check reciente

        Returns:
            Tupla (is_available, message) con el estado y mensaje descriptivo
        """
        # Si tenemos un check reciente (< 5 minutos) y no se fuerza, usar cache
        if not force and self._last_availability_check:
            tiempo_desde_check = (datetime.now() - self._last_availability_check).total_seconds()
            if tiempo_desde_check < 300:  # 5 minutos
                mensaje = "Disponible (cache)" if self._is_available else "No disponible (cache)"
                return self._is_available, mensaje

        logger.info(f"🔍 Verificando disponibilidad de {self.site_id}...")

        # Intentar acceder a la URL base
        try:
            response = self.session.head(
                self.config.url_base,
                timeout=10,
                verify=False,  # Ignorar errores SSL
                allow_redirects=True
            )

            # Considerar disponible si: 200, 301, 302, 403 (algunos sitios bloquean HEAD)
            if response.status_code in [200, 301, 302, 403]:
                self._is_available = True
                self._last_availability_check = datetime.now()
                mensaje = f"✅ Disponible (status {response.status_code})"
                logger.info(mensaje)
                return True, mensaje

            # Si HEAD falló, intentar GET ligero
            response = self.session.get(
                self.config.url_base,
                timeout=10,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                self._is_available = True
                self._last_availability_check = datetime.now()
                mensaje = "✅ Disponible (GET exitoso)"
                logger.info(mensaje)
                return True, mensaje

            # Código de error
            self._is_available = False
            self._last_availability_check = datetime.now()
            mensaje = f"❌ Error HTTP {response.status_code}"
            logger.warning(f"{self.site_id}: {mensaje}")
            return False, mensaje

        except requests.exceptions.SSLError as e:
            # Error SSL - sitio existe pero certificado mal configurado
            self._is_available = False
            self._last_availability_check = datetime.now()
            mensaje = "⚠️ Error SSL (certificado mal configurado)"
            logger.warning(f"{self.site_id}: {mensaje}")
            return False, mensaje

        except requests.exceptions.Timeout:
            self._is_available = False
            self._last_availability_check = datetime.now()
            mensaje = "⏱️ Timeout (servidor no responde)"
            logger.warning(f"{self.site_id}: {mensaje}")
            return False, mensaje

        except requests.exceptions.ConnectionError as e:
            self._is_available = False
            self._last_availability_check = datetime.now()
            mensaje = "🔌 Error de conexión (servidor caído)"
            logger.warning(f"{self.site_id}: {mensaje}")
            return False, mensaje

        except Exception as e:
            self._is_available = False
            self._last_availability_check = datetime.now()
            mensaje = f"❌ Error inesperado: {type(e).__name__}"
            logger.error(f"{self.site_id}: {mensaje} - {e}")
            return False, mensaje

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

    def _validar_pdf(self, content: bytes, url: str) -> bool:
        """
        Validar que el contenido descargado sea realmente un PDF

        Args:
            content: Contenido descargado en bytes
            url: URL original (para logging)

        Returns:
            True si es un PDF válido, False si no
        """
        # Verificar que no esté vacío
        if not content or len(content) == 0:
            logger.warning(f"⚠️ Contenido vacío desde: {url}")
            return False

        # Verificar magic bytes de PDF (%PDF)
        if not content.startswith(b'%PDF'):
            logger.warning(f"⚠️ El archivo NO es un PDF (magic bytes incorrectos): {url}")
            logger.warning(f"   Primeros 50 bytes: {content[:50]}")
            return False

        return True

    def _download_file(self, url: str, destino: Path, timeout: int = 30, validar_pdf: bool = True) -> bool:
        """
        Método auxiliar para descargar archivos con validación de PDF

        Args:
            url: URL del archivo
            destino: Ruta de destino
            timeout: Timeout en segundos
            validar_pdf: Si True, valida que sea un PDF real

        Returns:
            True si se descargó correctamente
        """
        try:
            # Asegurar que el directorio existe
            destino.parent.mkdir(parents=True, exist_ok=True)

            # Descargar
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            # Verificar Content-Type si está disponible
            content_type = response.headers.get('Content-Type', '')
            if validar_pdf and content_type:
                if 'text/html' in content_type:
                    logger.warning(f"⚠️ La URL retorna HTML, no PDF: {url}")
                    logger.warning(f"   Content-Type: {content_type}")
                    return False

            # Leer contenido completo para validación
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk

            # Validar que sea PDF si se solicitó
            if validar_pdf:
                if not self._validar_pdf(content, url):
                    return False

            # Guardar
            with open(destino, 'wb') as f:
                f.write(content)

            logger.info(f"✓ Descargado: {destino.name} ({len(content)} bytes)")

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
