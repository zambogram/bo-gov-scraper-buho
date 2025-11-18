"""
Scraper para ASFI - Autoridad de Supervisión del Sistema Financiero
Extrae Resoluciones Administrativas, Circulares y Comunicados
"""
import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scraper.core.base_scraper import BaseScraper
from scraper.core.pdf_parser import PDFParser
from scraper.core.utils import normalize_text, extract_date, extract_numero_documento


class ASFIScraper(BaseScraper):
    """
    Scraper para ASFI
    URL: https://www.asfi.gob.bo
    Extrae Resoluciones Administrativas, Circulares, Comunicados
    """

    def __init__(self, outputs_dir: str = "outputs"):
        super().__init__(
            site_name="asfi",
            base_url="https://www.asfi.gob.bo",
            outputs_dir=outputs_dir
        )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        self.tipos_documento = ['resolucion', 'circular', 'comunicado']

    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene lista de documentos de ASFI

        Returns:
            Lista de documentos
        """
        documents = []

        try:
            documents = self._fetch_from_website()
            if documents:
                return documents
        except Exception as e:
            print(f"  → Advertencia: No se pudo conectar al sitio real: {e}")

        print("  → Usando datos de ejemplo para demostración")
        documents = self._get_example_documents()

        return documents

    def _fetch_from_website(self) -> List[Dict]:
        """
        Scraping del sitio web real de ASFI

        Returns:
            Lista de documentos
        """
        documents = []

        # Intentar por cada tipo de documento
        for tipo in self.tipos_documento:
            try:
                url = f"{self.base_url}/normativa/{tipo}s"
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Buscar enlaces a documentos
                    links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))

                    for link in links[:10]:
                        try:
                            title = normalize_text(link.get_text())
                            url = link.get('href', '')

                            if not url.startswith('http'):
                                url = f"{self.base_url}{url}"

                            doc_id = extract_numero_documento(title) or f"ASFI_{tipo}_{len(documents)}"
                            doc_id = doc_id.replace('/', '_').replace(' ', '_')

                            documents.append({
                                'id': doc_id,
                                'title': title,
                                'url': url,
                                'date': extract_date(title) or datetime.now().strftime('%Y-%m-%d'),
                                'tipo': tipo.upper(),
                            })

                        except Exception as e:
                            continue

            except Exception as e:
                print(f"  Error scrapeando {tipo}: {e}")
                continue

        return documents

    def _get_example_documents(self) -> List[Dict]:
        """
        Documentos de ejemplo

        Returns:
            Lista de ejemplos
        """
        return [
            {
                'id': 'ASFI_RA_001_2024',
                'title': 'RESOLUCIÓN ASFI/001/2024 - Límites de Crédito',
                'url': 'https://example.com/asfi/RA_001_2024.pdf',
                'date': '2024-01-15',
                'tipo': 'RESOLUCION',
                'ejemplo': True,
            },
            {
                'id': 'ASFI_RA_002_2024',
                'title': 'RESOLUCIÓN ASFI/002/2024 - Tasa de Interés',
                'url': 'https://example.com/asfi/RA_002_2024.pdf',
                'date': '2024-01-20',
                'tipo': 'RESOLUCION',
                'ejemplo': True,
            },
            {
                'id': 'ASFI_CIRC_010_2024',
                'title': 'CIRCULAR ASFI/010/2024 - Reportes Financieros',
                'url': 'https://example.com/asfi/CIRC_010_2024.pdf',
                'date': '2024-01-25',
                'tipo': 'CIRCULAR',
                'ejemplo': True,
            },
            {
                'id': 'ASFI_COM_005_2024',
                'title': 'COMUNICADO ASFI/005/2024 - Modificación de Plazos',
                'url': 'https://example.com/asfi/COM_005_2024.pdf',
                'date': '2024-02-01',
                'tipo': 'COMUNICADO',
                'ejemplo': True,
            },
        ]

    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea un documento de ASFI

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Estructura parseada
        """
        parser = PDFParser(pdf_path)

        # Parser genérico con análisis específico
        parsed = parser.parse_generic()

        text = parser.text or ""

        # Información específica de ASFI
        info_adicional = {
            'numero_documento': self._extract_numero(text),
            'tipo_documento': self._extract_tipo(text),
            'dirigido_a': self._extract_destinatario(text),
            'referencia': self._extract_referencia(text),
            'articulos': self._extract_articulos(text),
        }

        parsed['info_adicional'] = info_adicional

        return parsed

    def _extract_numero(self, text: str) -> Optional[str]:
        """Extrae el número de documento"""
        patterns = [
            r'RESOLUCI[OÓ]N\s+ASFI[/-](\d+[/-]\d{4})',
            r'CIRCULAR\s+ASFI[/-](\d+[/-]\d{4})',
            r'COMUNICADO\s+ASFI[/-](\d+[/-]\d{4})',
            r'ASFI[/-](\d+[/-]\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_tipo(self, text: str) -> Optional[str]:
        """Extrae el tipo de documento"""
        text_upper = text.upper()

        if 'RESOLUCIÓN' in text_upper or 'RESOLUCION' in text_upper:
            return 'RESOLUCION_ADMINISTRATIVA'
        elif 'CIRCULAR' in text_upper:
            return 'CIRCULAR'
        elif 'COMUNICADO' in text_upper:
            return 'COMUNICADO'

        return None

    def _extract_destinatario(self, text: str) -> Optional[str]:
        """Extrae a quién va dirigido"""
        patterns = [
            r'(?:A|PARA)\s*:\s*(.+)',
            r'DESTINATARIO\s*:\s*(.+)',
            r'SE\s+DIRIGE\s+A\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_referencia(self, text: str) -> Optional[str]:
        """Extrae la referencia o asunto"""
        patterns = [
            r'REFERENCIA\s*:\s*(.+)',
            r'ASUNTO\s*:\s*(.+)',
            r'REF\.\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_articulos(self, text: str) -> List[Dict[str, str]]:
        """Extrae los artículos del documento"""
        articulos = []

        # Buscar artículos
        pattern = r'ART[IÍ]CULO\s+(\d+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|ÚNICO)[º°]?\.\s*[-–]?\s*(.+?)(?=ART[IÍ]CULO\s+|\Z)'

        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            numero = match.group(1)
            contenido = normalize_text(match.group(2))

            articulos.append({
                'numero': numero,
                'contenido': contenido[:500]  # Limitar longitud
            })

        return articulos

    def download_pdf(self, url: str, doc_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Descarga PDF (con soporte para ejemplos)

        Args:
            url: URL del PDF
            doc_id: ID del documento
            filename: Nombre del archivo

        Returns:
            Ruta del archivo
        """
        if 'example.com' in url:
            return self._create_example_pdf(doc_id, filename)

        return super().download_pdf(url, doc_id, filename)

    def _create_example_pdf(self, doc_id: str, filename: Optional[str] = None) -> str:
        """Crea PDF de ejemplo"""
        if not filename:
            filename = f"{doc_id}.pdf"

        pdf_path = os.path.join(self.pdfs_dir, filename)

        contenido = f"""
RESOLUCIÓN ASFI/001/2024

AUTORIDAD DE SUPERVISIÓN DEL SISTEMA FINANCIERO
ESTADO PLURINACIONAL DE BOLIVIA

La Paz, 15 de enero de 2024

REFERENCIA: Establecimiento de Límites de Crédito para Entidades Financieras

VISTOS:

La Ley N° 393 de Servicios Financieros y sus reglamentos
El Decreto Supremo de creación de ASFI
Las atribuciones conferidas al Director Ejecutivo

CONSIDERANDO:

Que, es necesario establecer límites prudenciales para operaciones de crédito
Que, la estabilidad del sistema financiero requiere regulación apropiada
Que, es competencia de ASFI emitir normas prudenciales

POR TANTO:

El Director Ejecutivo de la Autoridad de Supervisión del Sistema Financiero,
en uso de sus atribuciones,

RESUELVE:

ARTÍCULO 1.- OBJETO
Establecer los límites de crédito individual y grupal para entidades
financieras supervisadas por ASFI.

ARTÍCULO 2.- ÁMBITO DE APLICACIÓN
Las presentes disposiciones son aplicables a:
a) Bancos Múltiples
b) Entidades Financieras de Vivienda
c) Cooperativas de Ahorro y Crédito Abiertas

ARTÍCULO 3.- LÍMITE INDIVIDUAL
El crédito a una sola persona natural o jurídica no podrá exceder el 10%
del patrimonio de la entidad financiera.

ARTÍCULO 4.- LÍMITE GRUPAL
Los créditos a un grupo económico no podrán exceder el 25% del patrimonio
de la entidad financiera.

ARTÍCULO 5.- EXCEPCIONES
Se establecen las siguientes excepciones:
a) Créditos garantizados con depósitos en la misma entidad
b) Créditos garantizados por el Estado

ARTÍCULO 6.- VIGENCIA
La presente resolución entra en vigencia a partir de su publicación.

Regístrese, comuníquese y archívese.

Lic. Ivette Espinoza Salazar
DIRECTORA EJECUTIVA a.i.
AUTORIDAD DE SUPERVISIÓN DEL SISTEMA FINANCIERO
"""

        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(contenido)

        self.stats["total_downloaded"] += 1
        return pdf_path


def scrape_asfi(only_new: bool = False, only_modified: bool = False,
                limit: Optional[int] = None) -> Dict:
    """
    Helper para ejecutar scraper de ASFI

    Args:
        only_new: Solo nuevos
        only_modified: Solo modificados
        limit: Límite

    Returns:
        Estadísticas
    """
    scraper = ASFIScraper()
    return scraper.run(only_new=only_new, only_modified=only_modified, limit=limit)
