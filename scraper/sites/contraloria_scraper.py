"""
Scraper para Contraloría General del Estado de Bolivia
Extrae Resoluciones y documentos oficiales
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


class ContraloriaScraper(BaseScraper):
    """
    Scraper para Contraloría General del Estado
    URL: https://www.contraloria.gob.bo
    Extrae Resoluciones con estructura por numerales
    """

    def __init__(self, outputs_dir: str = "outputs"):
        super().__init__(
            site_name="contraloria",
            base_url="https://www.contraloria.gob.bo",
            outputs_dir=outputs_dir
        )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene lista de resoluciones de Contraloría

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
        Scraping del sitio web real

        Returns:
            Lista de documentos
        """
        documents = []

        # URL de resoluciones (ajustar según sitio real)
        resoluciones_url = f"{self.base_url}/resoluciones"

        try:
            response = requests.get(resoluciones_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar enlaces a resoluciones
                links = soup.find_all('a', href=re.compile(r'resoluci[oó]n|cgr', re.I))

                for link in links[:20]:
                    try:
                        title = normalize_text(link.get_text())
                        url = link.get('href', '')

                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"

                        doc_id = extract_numero_documento(title) or f"CGR_{len(documents)}"
                        doc_id = doc_id.replace('/', '_').replace(' ', '_')

                        documents.append({
                            'id': doc_id,
                            'title': title,
                            'url': url,
                            'date': extract_date(title) or datetime.now().strftime('%Y-%m-%d'),
                            'tipo': 'RESOLUCION',
                        })

                    except Exception as e:
                        continue

        except Exception as e:
            print(f"  Error en scraping: {e}")

        return documents

    def _get_example_documents(self) -> List[Dict]:
        """
        Documentos de ejemplo

        Returns:
            Lista de ejemplos
        """
        return [
            {
                'id': 'CGR_RESOLUCION_001_2024',
                'title': 'RESOLUCIÓN CGR-001/2024 - Aprobación de Normas',
                'url': 'https://example.com/contraloria/CGR_001_2024.pdf',
                'date': '2024-01-10',
                'tipo': 'RESOLUCION',
                'ejemplo': True,
            },
            {
                'id': 'CGR_RESOLUCION_002_2024',
                'title': 'RESOLUCIÓN CGR-002/2024 - Responsabilidad por la Función Pública',
                'url': 'https://example.com/contraloria/CGR_002_2024.pdf',
                'date': '2024-01-25',
                'tipo': 'RESOLUCION',
                'ejemplo': True,
            },
            {
                'id': 'CGR_RESOLUCION_003_2024',
                'title': 'RESOLUCIÓN CGR-003/2024 - Auditoría Gubernamental',
                'url': 'https://example.com/contraloria/CGR_003_2024.pdf',
                'date': '2024-02-05',
                'tipo': 'RESOLUCION',
                'ejemplo': True,
            },
        ]

    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea una resolución de Contraloría

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Estructura parseada con numerales
        """
        parser = PDFParser(pdf_path)

        # Usar parser específico para Contraloría
        parsed = parser.parse_contraloria()

        # Extraer información adicional del encabezado
        text = parser.text or ""

        info_adicional = {
            'numero_resolucion': self._extract_numero_resolucion(text),
            'referencia': self._extract_referencia(text),
            'contralor': self._extract_contralor(text),
        }

        parsed['info_adicional'] = info_adicional

        return parsed

    def _extract_numero_resolucion(self, text: str) -> Optional[str]:
        """Extrae el número de resolución"""
        patterns = [
            r'RESOLUCI[OÓ]N\s+(?:CGR|CGE)?\s*[-/]?\s*(\d+[/-]\d{4})',
            r'N[°º]\s*(\d+[/-]\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_referencia(self, text: str) -> Optional[str]:
        """Extrae la referencia o asunto"""
        patterns = [
            r'REFERENCIA\s*:\s*(.+)',
            r'ASUNTO\s*:\s*(.+)',
            r'OBJETO\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_contralor(self, text: str) -> Optional[str]:
        """Extrae el nombre del Contralor General"""
        patterns = [
            r'CONTRALOR\s+GENERAL\s+DEL\s+ESTADO\s*:\s*(.+)',
            r'CONTRALOR\s+GENERAL\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

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
RESOLUCIÓN CGR-001/2024

CONTRALORÍA GENERAL DEL ESTADO
ESTADO PLURINACIONAL DE BOLIVIA

La Paz, 10 de enero de 2024

CONTRALOR GENERAL DEL ESTADO: Dr. Nelson Mérida López

REFERENCIA: Aprobación de Normas de Auditoría Gubernamental

VISTOS Y CONSIDERANDO:

I. ANTECEDENTES

Que, la Ley N° 1178 de Administración y Control Gubernamentales establece
las atribuciones de la Contraloría General del Estado para emitir normas
de auditoría gubernamental.

Que, es necesario actualizar las normas vigentes conforme a estándares
internacionales y la normativa nacional aplicable.

II. FUNDAMENTACIÓN LEGAL

De conformidad con las siguientes disposiciones legales:
- Ley N° 1178 de Administración y Control Gubernamentales
- Decreto Supremo N° 23318-A, Reglamento de Responsabilidad por la Función Pública
- Resoluciones administrativas vigentes

III. RESOLUCIÓN

El Contralor General del Estado, en uso de sus atribuciones,

RESUELVE:

ARTÍCULO 1.- Aprobar las Normas de Auditoría Gubernamental aplicables
a todas las entidades públicas del Estado Plurinacional de Bolivia.

ARTÍCULO 2.- Las presentes normas entran en vigencia a partir de su
publicación en Gaceta Oficial.

ARTÍCULO 3.- Todas las entidades sujetas a control deben adecuar sus
procedimientos a las presentes normas en el plazo de 90 días.

IV. DISPOSICIONES TRANSITORIAS

PRIMERA.- Las auditorías en curso continuarán bajo las normas anteriores
hasta su conclusión.

SEGUNDA.- Se otorga un período de capacitación de 60 días para el personal
de las unidades de auditoría interna.

V. DISPOSICIONES FINALES

Regístrese, comuníquese y archívese.

Dr. Nelson Mérida López
CONTRALOR GENERAL DEL ESTADO
"""

        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(contenido)

        self.stats["total_downloaded"] += 1
        return pdf_path


def scrape_contraloria(only_new: bool = False, only_modified: bool = False,
                       limit: Optional[int] = None) -> Dict:
    """
    Helper para ejecutar scraper de Contraloría

    Args:
        only_new: Solo nuevos
        only_modified: Solo modificados
        limit: Límite

    Returns:
        Estadísticas
    """
    scraper = ContraloriaScraper()
    return scraper.run(only_new=only_new, only_modified=only_modified, limit=limit)
