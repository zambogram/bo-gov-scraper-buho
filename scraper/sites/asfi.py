"""
Scraper para ASFI (Autoridad de Supervisión del Sistema Financiero).
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional
from random import randint, choice

from scraper.base import BaseSiteScraper, DocumentoScrapeado


class ASFIScraper(BaseSiteScraper):
    """Scraper para la ASFI."""

    TIPOS_NORMA = [
        "Resolución ASFI",
        "Reglamento",
        "Circular",
        "Compendio Normativo"
    ]

    CATEGORIAS = [
        "Entidades Financieras",
        "Prevención de Lavado de Activos",
        "Protección al Consumidor Financiero",
        "Solvencia y Prudencia Financiera",
        "Gobierno Corporativo"
    ]

    def scrape(self, limit: Optional[int] = None, solo_nuevos: bool = True) -> List[DocumentoScrapeado]:
        """Scrapea normativa de ASFI."""
        self.logger.info(f"Iniciando scraping de ASFI (modo_demo={self.modo_demo})")

        if self.modo_demo:
            documentos = self._scrape_modo_demo(limit)
        else:
            documentos = self._scrape_real(limit)

        if solo_nuevos:
            documentos_filtrados = []
            for doc in documentos:
                estado = self._determinar_estado(doc)
                if estado != "sin_cambios":
                    doc.estado = estado
                    documentos_filtrados.append(doc)
            documentos = documentos_filtrados

        self._guardar_documentos(documentos)
        self.logger.info(f"Scraping completado. {len(documentos)} documentos procesados.")

        return documentos

    def _scrape_real(self, limit: Optional[int] = None) -> List[DocumentoScrapeado]:
        """Scraping real del sitio ASFI."""
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.warning("No se pueden importar requests/BeautifulSoup. Usando modo demo.")
            return self._scrape_modo_demo(limit)

        documentos = []

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            self.logger.info(f"Consultando: {self.site_config.url_listado}")
            response = requests.get(self.site_config.url_listado, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            filas = soup.select(self.site_config.selectores.get('tabla_resultados', 'table.normativa-table tbody tr'))

            self.logger.info(f"Encontradas {len(filas)} filas")

            for i, fila in enumerate(filas):
                if limit and i >= limit:
                    break

                try:
                    numero_elem = fila.select_one(self.site_config.selectores.get('numero_resolucion', 'td:nth-child(1)'))
                    titulo_elem = fila.select_one(self.site_config.selectores.get('titulo', 'td:nth-child(2)'))
                    fecha_elem = fila.select_one(self.site_config.selectores.get('fecha', 'td:nth-child(3)'))
                    tipo_elem = fila.select_one(self.site_config.selectores.get('tipo', 'td:nth-child(4)'))
                    pdf_elem = fila.select_one(self.site_config.selectores.get('enlace_pdf', 'td:nth-child(5) a'))

                    if not (numero_elem and titulo_elem and fecha_elem):
                        continue

                    numero = numero_elem.get_text(strip=True)
                    titulo = titulo_elem.get_text(strip=True)
                    fecha_texto = fecha_elem.get_text(strip=True)
                    tipo = tipo_elem.get_text(strip=True) if tipo_elem else "Resolución ASFI"

                    fecha_publicacion = self._parsear_fecha(fecha_texto)

                    url_pdf = None
                    if pdf_elem and pdf_elem.get('href'):
                        url_pdf = pdf_elem.get('href')
                        if not url_pdf.startswith('http'):
                            url_pdf = self.site_config.url_base + url_pdf

                    document_id = self._generar_document_id(tipo, numero, fecha_publicacion)

                    documento = DocumentoScrapeado(
                        site_id=self.site_id,
                        document_id=document_id,
                        titulo=titulo,
                        tipo_norma=tipo,
                        numero_norma=numero,
                        fecha_publicacion=fecha_publicacion,
                        url_detalle=self.site_config.url_listado,
                        url_pdf=url_pdf
                    )

                    documentos.append(documento)

                except Exception as e:
                    self.logger.error(f"Error procesando fila {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error en scraping real: {e}")
            return self._scrape_modo_demo(limit)

        return documentos

    def _scrape_modo_demo(self, limit: Optional[int] = None) -> List[DocumentoScrapeado]:
        """Genera datos de demostración para ASFI."""
        self.logger.info("Generando datos de demostración para ASFI")

        documentos = []
        num_docs = limit if limit else 10

        for i in range(num_docs):
            tipo = self.TIPOS_NORMA[i % len(self.TIPOS_NORMA)]
            categoria = choice(self.CATEGORIAS)
            numero = f"{200 + i}/2024"

            dias_atras = randint(0, 120)
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

            titulo = f"{tipo} {numero} - {categoria}"

            document_id = self._generar_document_id(tipo, numero, fecha)

            documento = DocumentoScrapeado(
                site_id=self.site_id,
                document_id=document_id,
                titulo=titulo,
                tipo_norma=tipo,
                numero_norma=numero,
                fecha_publicacion=fecha,
                url_detalle=f"{self.site_config.url_listado}?id={numero}",
                url_pdf=f"{self.site_config.url_base}/normativa/ASFI_{numero.replace('/', '_')}.pdf",
                metadata_extra={'categoria': categoria, 'modo': 'demo'}
            )

            documentos.append(documento)

        return documentos

    def _parsear_fecha(self, fecha_texto: str) -> str:
        """Parsea fecha a formato ISO."""
        formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]

        for formato in formatos:
            try:
                fecha = datetime.strptime(fecha_texto, formato)
                return fecha.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return datetime.now().strftime("%Y-%m-%d")
