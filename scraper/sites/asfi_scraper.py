"""
Scraper para ASFI (Autoridad de Supervisión del Sistema Financiero)

NOTA: Este scraper utiliza datos de ejemplo para demostración.
Para implementación real, reemplazar con requests HTTP reales al sitio de ASFI.

Estructura esperada del sitio real:
- URL base: https://www.asfi.gob.bo
- Búsqueda: /normativa/busqueda
- Paginación: parámetros de query string
- PDFs: /normativa/resoluciones/{año}/ra-{numero}-{año}.pdf
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ASFIScraper(BaseScraper):
    """
    Scraper para ASFI con soporte para scraping histórico completo

    Implementación actual: Datos de ejemplo
    TODO: Implementar scraping real con requests al sitio web
    """

    def __init__(self):
        super().__init__('asfi')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Listar resoluciones de ASFI

        Args:
            limite: Número máximo de documentos
            modo: 'full' o 'delta'
            pagina: Número de página (para paginación)

        Returns:
            Lista de metadata de documentos
        """
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}, página: {pagina}")

        # =====================================================================
        # IMPLEMENTACIÓN CON DATOS DE EJEMPLO
        # =====================================================================
        # En producción, aquí iría:
        # 1. Construir URL con paginación: f"{self.config.url_search}?page={pagina}"
        # 2. Hacer request HTTP: response = self.session.get(url)
        # 3. Parsear HTML con BeautifulSoup: soup = BeautifulSoup(response.text)
        # 4. Extraer datos de cada resolución: titulo, número, fecha, URL PDF
        # 5. Retornar lista de diccionarios con metadata
        # =====================================================================

        # Generar datos de ejemplo por página
        documentos_por_pagina = self.items_por_pagina

        # Simular que tenemos 80 documentos totales divididos en páginas
        total_documentos = 80
        max_paginas = (total_documentos + documentos_por_pagina - 1) // documentos_por_pagina

        # Si la página solicitada excede el máximo, retornar vacío
        if pagina > max_paginas:
            logger.info(f"Página {pagina} excede máximo ({max_paginas}), retornando vacío")
            return []

        # Calcular índices para esta página
        inicio = (pagina - 1) * documentos_por_pagina
        fin = min(inicio + documentos_por_pagina, total_documentos)

        documentos_pagina = []

        # Generar documentos de ejemplo para esta página
        for i in range(inicio, fin):
            numero_resolucion = f"{i+1:03d}/2024"
            fecha = datetime(2024, 1, 1) + timedelta(days=i*3)

            # Alternar entre diferentes tipos de resoluciones
            tipos = [
                'Resolución Administrativa',
                'Resolución de Directorio',
                'Circular',
                'Reglamento'
            ]
            tipo = tipos[i % len(tipos)]

            # Temas bancarios/financieros
            temas = [
                'Normativa bancaria',
                'Supervisión de entidades financieras',
                'Regulación de tasas de interés',
                'Protección al consumidor financiero',
                'Gestión de riesgos',
                'Normativa de seguros',
                'Prevención de lavado de dinero'
            ]
            tema = temas[i % len(temas)]

            doc = {
                'id_documento': f'asfi_ra_{i+1:03d}_2024',
                'tipo_documento': tipo,
                'numero_norma': numero_resolucion,
                'fecha': fecha.strftime('%Y-%m-%d'),
                'titulo': f'{tipo} ASFI {numero_resolucion}',
                'url': f'{self.config.url_base}/normativa/ra-{i+1:03d}-2024.pdf',
                'sumilla': self._generar_sumilla_ejemplo(i, tema)
            }

            documentos_pagina.append(doc)

        # Aplicar límite si se especifica
        if limite:
            documentos_pagina = documentos_pagina[:limite]

        logger.info(f"✓ Página {pagina}: {len(documentos_pagina)} documentos")

        return documentos_pagina

    def _generar_sumilla_ejemplo(self, idx: int, tema: str) -> str:
        """Generar sumilla de ejemplo variada según tema"""
        sumillas_base = [
            f'Regulación sobre {tema} - establece nuevos parámetros',
            f'Modificación de normativa vigente sobre {tema}',
            f'Directrices para implementación de {tema}',
            f'Actualización de procedimientos relacionados a {tema}',
            f'Aprobación de nuevo marco regulatorio para {tema}'
        ]
        return sumillas_base[idx % len(sumillas_base)]

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """
        Descargar PDF de ASFI

        Args:
            url: URL del PDF
            ruta_destino: Ruta donde guardar

        Returns:
            True si se descargó correctamente
        """
        logger.info(f"Descargando PDF: {url}")

        # =====================================================================
        # IMPLEMENTACIÓN CON DATOS DE EJEMPLO
        # =====================================================================
        # En producción, descomentar y usar:
        # return self._download_file(url, ruta_destino)
        # =====================================================================

        # Por ahora, crear un PDF de prueba vacío
        logger.warning("MODO DEMO: Creando PDF de prueba vacío")

        try:
            ruta_destino.parent.mkdir(parents=True, exist_ok=True)

            # Crear PDF de prueba con reportlab
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from io import BytesIO

                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                c.drawString(100, 750, "AUTORIDAD DE SUPERVISIÓN DEL SISTEMA FINANCIERO")
                c.drawString(100, 730, "RESOLUCIÓN ADMINISTRATIVA DE EJEMPLO")
                c.drawString(100, 700, f"Fuente: {url}")
                c.drawString(100, 650, "Este es un PDF de ejemplo generado para demostración.")
                c.drawString(100, 630, "En producción, aquí iría el contenido real descargado del sitio.")

                # Añadir artículos de ejemplo
                y = 580
                c.drawString(100, y, "CONSIDERANDO:")
                y -= 30
                c.drawString(120, y, "Que es necesario regular...")
                y -= 50
                c.drawString(100, y, "RESUELVE:")
                y -= 30
                for i in range(1, 5):
                    c.drawString(120, y, f"Artículo {i}.- Contenido del artículo {i}...")
                    y -= 30

                c.save()

                # Guardar el PDF
                buffer.seek(0)
                with open(ruta_destino, 'wb') as f:
                    f.write(buffer.getvalue())

                logger.info(f"✓ PDF de prueba creado: {ruta_destino.name}")
                return True

            except ImportError:
                # Si no está reportlab, crear archivo vacío
                logger.warning("reportlab no disponible, creando archivo vacío")
                ruta_destino.touch()
                return True

        except Exception as e:
            logger.error(f"✗ Error creando PDF de prueba: {e}")
            return False
