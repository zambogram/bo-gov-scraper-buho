"""
Scraper para Gaceta Oficial de Bolivia.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional
from random import randint

from scraper.base import BaseSiteScraper, DocumentoScrapeado


class GacetaOficialScraper(BaseSiteScraper):
    """Scraper para la Gaceta Oficial de Bolivia."""

    TIPOS_NORMA = [
        "Ley",
        "Decreto Supremo",
        "Resolución Ministerial",
        "Resolución Suprema",
        "Resolución Administrativa"
    ]

    def scrape(self, limit: Optional[int] = None, solo_nuevos: bool = True) -> List[DocumentoScrapeado]:
        """
        Scrapea documentos de la Gaceta Oficial.

        Args:
            limit: Límite de documentos a scrapear
            solo_nuevos: Si es True, solo procesa documentos nuevos o modificados

        Returns:
            Lista de documentos scrapeados
        """
        self.logger.info(f"Iniciando scraping de Gaceta Oficial (modo_demo={self.modo_demo})")

        if self.modo_demo:
            documentos = self._scrape_modo_demo(limit)
        else:
            documentos = self._scrape_real(limit)

        # Filtrar solo nuevos si se requiere
        if solo_nuevos:
            documentos_filtrados = []
            for doc in documentos:
                estado = self._determinar_estado(doc)
                if estado != "sin_cambios":
                    doc.estado = estado
                    documentos_filtrados.append(doc)
            documentos = documentos_filtrados

        # Guardar documentos e índice
        self._guardar_documentos(documentos)

        self.logger.info(f"Scraping completado. {len(documentos)} documentos procesados.")

        return documentos

    def _scrape_real(self, limit: Optional[int] = None) -> List[DocumentoScrapeado]:
        """
        Scraping real del sitio de Gaceta Oficial.

        NOTA: Este método requiere requests y BeautifulSoup.
        Por ahora incluye la estructura pero puede fallar si no hay conexión.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.warning("No se pueden importar requests/BeautifulSoup. Usando modo demo.")
            return self._scrape_modo_demo(limit)

        documentos = []

        try:
            # Configuración de la petición
            headers = {
                'User-Agent': self.site_config.selectores.get('user_agent',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            }

            # Hacer petición al listado
            self.logger.info(f"Consultando: {self.site_config.url_listado}")
            response = requests.get(
                self.site_config.url_listado,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            # Parsear HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar tabla de resultados usando selectores del catálogo
            selector_tabla = self.site_config.selectores.get('tabla_resultados', 'table tbody tr')
            filas = soup.select(selector_tabla)

            self.logger.info(f"Encontradas {len(filas)} filas en la tabla")

            for i, fila in enumerate(filas):
                if limit and i >= limit:
                    break

                try:
                    # Extraer datos usando selectores
                    tipo_elem = fila.select_one(self.site_config.selectores.get('tipo_norma', 'td:nth-child(1)'))
                    titulo_elem = fila.select_one(self.site_config.selectores.get('titulo', 'td:nth-child(2)'))
                    fecha_elem = fila.select_one(self.site_config.selectores.get('fecha', 'td:nth-child(3)'))
                    pdf_elem = fila.select_one(self.site_config.selectores.get('enlace_pdf', 'td:nth-child(4) a'))

                    if not (tipo_elem and titulo_elem and fecha_elem):
                        continue

                    tipo_norma = tipo_elem.get_text(strip=True)
                    titulo = titulo_elem.get_text(strip=True)
                    fecha_texto = fecha_elem.get_text(strip=True)

                    # Extraer número de norma del título (ejemplo: "Ley 1234" -> "1234")
                    numero_match = re.search(r'(\d+/\d+|\d+)', titulo)
                    numero_norma = numero_match.group(1) if numero_match else f"SN-{i+1}"

                    # Parsear fecha
                    fecha_publicacion = self._parsear_fecha(fecha_texto)

                    # URL del PDF
                    url_pdf = None
                    if pdf_elem and pdf_elem.get('href'):
                        url_pdf = pdf_elem.get('href')
                        if not url_pdf.startswith('http'):
                            url_pdf = self.site_config.url_base + url_pdf

                    # Generar document_id único
                    document_id = self._generar_document_id(tipo_norma, numero_norma, fecha_publicacion)

                    # Crear documento
                    documento = DocumentoScrapeado(
                        site_id=self.site_id,
                        document_id=document_id,
                        titulo=titulo,
                        tipo_norma=tipo_norma,
                        numero_norma=numero_norma,
                        fecha_publicacion=fecha_publicacion,
                        url_detalle=self.site_config.url_listado,
                        url_pdf=url_pdf,
                        path_pdf=None,
                        metadata_extra={'indice_fila': i}
                    )

                    documentos.append(documento)

                except Exception as e:
                    self.logger.error(f"Error procesando fila {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error en scraping real: {e}")
            self.logger.info("Fallback a modo demo")
            return self._scrape_modo_demo(limit)

        return documentos

    def _scrape_modo_demo(self, limit: Optional[int] = None) -> List[DocumentoScrapeado]:
        """Genera datos de demostración para pruebas."""
        self.logger.info("Generando datos de demostración para Gaceta Oficial")

        documentos = []
        num_docs = limit if limit else 10

        for i in range(num_docs):
            # Generar datos realistas de ejemplo
            tipo_norma = self.TIPOS_NORMA[i % len(self.TIPOS_NORMA)]
            numero = f"{1400 + i}"

            # Fecha entre 30 días atrás y hoy
            dias_atras = randint(0, 30)
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

            # Generar título realista
            titulo = self._generar_titulo_demo(tipo_norma, numero)

            document_id = self._generar_document_id(tipo_norma, numero, fecha)

            documento = DocumentoScrapeado(
                site_id=self.site_id,
                document_id=document_id,
                titulo=titulo,
                tipo_norma=tipo_norma,
                numero_norma=numero,
                fecha_publicacion=fecha,
                url_detalle=f"{self.site_config.url_listado}?id={numero}",
                url_pdf=f"{self.site_config.url_base}/pdf/gaceta_{numero}.pdf",
                path_pdf=None,
                metadata_extra={'modo': 'demo', 'indice': i}
            )

            documentos.append(documento)

        return documentos

    def _generar_titulo_demo(self, tipo_norma: str, numero: str) -> str:
        """Genera un título realista para modo demo."""
        titulos = {
            "Ley": [
                f"Ley {numero} - Ley de modificación al Código Tributario Boliviano",
                f"Ley {numero} - Ley de regulación del sector financiero",
                f"Ley {numero} - Ley de fortalecimiento institucional"
            ],
            "Decreto Supremo": [
                f"Decreto Supremo {numero} - Reglamentación de la Ley de Empresas",
                f"Decreto Supremo {numero} - Normas complementarias al régimen tributario",
                f"Decreto Supremo {numero} - Designación de autoridades ministeriales"
            ],
            "Resolución Ministerial": [
                f"Resolución Ministerial {numero} - Aprobación de procedimientos administrativos",
                f"Resolución Ministerial {numero} - Normas técnicas de gestión pública",
                f"Resolución Ministerial {numero} - Directrices operativas"
            ],
            "Resolución Suprema": [
                f"Resolución Suprema {numero} - Designación de funcionarios públicos",
                f"Resolución Suprema {numero} - Aprobación de convenios internacionales"
            ],
            "Resolución Administrativa": [
                f"Resolución Administrativa {numero} - Normas internas de gestión",
                f"Resolución Administrativa {numero} - Procedimientos administrativos"
            ]
        }

        opciones = titulos.get(tipo_norma, [f"{tipo_norma} {numero}"])
        return opciones[int(numero) % len(opciones)]

    def _parsear_fecha(self, fecha_texto: str) -> str:
        """
        Parsea diferentes formatos de fecha a ISO (YYYY-MM-DD).

        Args:
            fecha_texto: Texto de la fecha (ej: "15/01/2025", "15-01-2025", etc.)

        Returns:
            Fecha en formato ISO
        """
        # Intentar diferentes formatos
        formatos = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d de %B de %Y",  # 15 de enero de 2025
        ]

        for formato in formatos:
            try:
                fecha = datetime.strptime(fecha_texto, formato)
                return fecha.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Si no se puede parsear, usar fecha actual
        self.logger.warning(f"No se pudo parsear fecha: {fecha_texto}. Usando fecha actual.")
        return datetime.now().strftime("%Y-%m-%d")
