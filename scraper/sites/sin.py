"""
Scraper para SIN (Servicio de Impuestos Nacionales).
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional
from random import randint, choice

from scraper.base import BaseSiteScraper, DocumentoScrapeado


class SINScraper(BaseSiteScraper):
    """Scraper para el SIN."""

    TIPOS_NORMA = [
        "Resolución Normativa de Directorio (RND)",
        "Resolución Administrativa (RA)",
        "Circular",
        "Instructivo"
    ]

    TEMAS = [
        "Impuesto al Valor Agregado (IVA)",
        "Impuesto a las Transacciones (IT)",
        "Régimen Complementario al IVA (RC-IVA)",
        "Impuesto a las Utilidades de las Empresas (IUE)",
        "Régimen Tributario Simplificado (RTS)",
        "Facturación Electrónica",
        "Procedimientos Tributarios"
    ]

    def scrape(self, limit: Optional[int] = None, solo_nuevos: bool = True) -> List[DocumentoScrapeado]:
        """Scrapea normativa del SIN."""
        self.logger.info(f"Iniciando scraping de SIN (modo_demo={self.modo_demo})")

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
        """Scraping real del sitio SIN."""
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
            items = soup.select(self.site_config.selectores.get('tabla_resultados', 'div.normativa-list .item'))

            self.logger.info(f"Encontrados {len(items)} items")

            for i, item in enumerate(items):
                if limit and i >= limit:
                    break

                try:
                    numero_elem = item.select_one(self.site_config.selectores.get('numero_norma', 'span.numero'))
                    titulo_elem = item.select_one(self.site_config.selectores.get('titulo', 'h5.titulo'))
                    fecha_elem = item.select_one(self.site_config.selectores.get('fecha', 'span.fecha'))
                    tipo_elem = item.select_one(self.site_config.selectores.get('tipo', 'span.tipo-norma'))
                    pdf_elem = item.select_one(self.site_config.selectores.get('enlace_pdf', 'a.descargar'))

                    if not (numero_elem and titulo_elem and fecha_elem):
                        continue

                    numero = numero_elem.get_text(strip=True)
                    titulo = titulo_elem.get_text(strip=True)
                    fecha_texto = fecha_elem.get_text(strip=True)
                    tipo = tipo_elem.get_text(strip=True) if tipo_elem else "RND"

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
                    self.logger.error(f"Error procesando item {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error en scraping real: {e}")
            return self._scrape_modo_demo(limit)

        return documentos

    def _scrape_modo_demo(self, limit: Optional[int] = None) -> List[DocumentoScrapeado]:
        """Genera datos de demostración para SIN."""
        self.logger.info("Generando datos de demostración para SIN")

        documentos = []
        num_docs = limit if limit else 10

        for i in range(num_docs):
            tipo = self.TIPOS_NORMA[i % len(self.TIPOS_NORMA)]
            tema = choice(self.TEMAS)

            # Números realistas para RND y RA
            if "RND" in tipo:
                numero = f"{10024 + i:05d}"
            elif "RA" in tipo:
                numero = f"{5024 + i:05d}"
            else:
                numero = f"{i+1:03d}/2024"

            dias_atras = randint(0, 180)
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

            titulo = f"{tipo} Nº {numero} - {tema}"

            document_id = self._generar_document_id(tipo, numero, fecha)

            documento = DocumentoScrapeado(
                site_id=self.site_id,
                document_id=document_id,
                titulo=titulo,
                tipo_norma=tipo,
                numero_norma=numero,
                fecha_publicacion=fecha,
                url_detalle=f"{self.site_config.url_listado}?id={numero}",
                url_pdf=f"{self.site_config.url_base}/normativa/{tipo.split()[0]}_{numero}.pdf",
                metadata_extra={'tema': tema, 'modo': 'demo'}
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
