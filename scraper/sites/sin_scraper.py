"""
Scraper para SIN - Servicio de Impuestos Nacionales
Extrae RND, Resoluciones Administrativas, Resoluciones Ministeriales
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


class SINScraper(BaseScraper):
    """
    Scraper para Servicio de Impuestos Nacionales
    URL: https://www.impuestos.gob.bo
    Extrae RND (Normas de Directorio), RA (Resoluciones Administrativas),
    RM (Resoluciones Ministeriales)
    """

    def __init__(self, outputs_dir: str = "outputs"):
        super().__init__(
            site_name="sin",
            base_url="https://www.impuestos.gob.bo",
            outputs_dir=outputs_dir
        )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        self.tipos_documento = ['rnd', 'ra', 'rm']

    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene lista de documentos del SIN

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
        Scraping del sitio web real del SIN

        Returns:
            Lista de documentos
        """
        documents = []

        # URL de normativa (ajustar según sitio real)
        normativa_url = f"{self.base_url}/normativa"

        try:
            response = requests.get(normativa_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar enlaces a documentos normativos
                links = soup.find_all('a', href=re.compile(r'rnd|\.pdf', re.I))

                for link in links[:20]:
                    try:
                        title = normalize_text(link.get_text())
                        url = link.get('href', '')

                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"

                        doc_id = extract_numero_documento(title) or f"SIN_{len(documents)}"
                        doc_id = doc_id.replace('/', '_').replace(' ', '_')

                        tipo = self._detect_tipo(title)

                        documents.append({
                            'id': doc_id,
                            'title': title,
                            'url': url,
                            'date': extract_date(title) or datetime.now().strftime('%Y-%m-%d'),
                            'tipo': tipo,
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
                'id': 'RND_10_0025_2024',
                'title': 'RND 10-0025-24 - Declaraciones Juradas Tributarias',
                'url': 'https://example.com/sin/RND_10_0025_24.pdf',
                'date': '2024-01-10',
                'tipo': 'RND',
                'ejemplo': True,
            },
            {
                'id': 'RND_10_0026_2024',
                'title': 'RND 10-0026-24 - Facturación Electrónica',
                'url': 'https://example.com/sin/RND_10_0026_24.pdf',
                'date': '2024-01-20',
                'tipo': 'RND',
                'ejemplo': True,
            },
            {
                'id': 'RA_05_0123_2024',
                'title': 'RA 05-0123-24 - Procedimiento de Devolución Impositiva',
                'url': 'https://example.com/sin/RA_05_0123_24.pdf',
                'date': '2024-02-01',
                'tipo': 'RA',
                'ejemplo': True,
            },
            {
                'id': 'RM_318_2024',
                'title': 'RM 318/2024 - Modificación Código Tributario',
                'url': 'https://example.com/sin/RM_318_2024.pdf',
                'date': '2024-02-15',
                'tipo': 'RM',
                'ejemplo': True,
            },
        ]

    def _detect_tipo(self, title: str) -> str:
        """
        Detecta el tipo de documento

        Args:
            title: Título del documento

        Returns:
            Tipo: RND, RA, RM
        """
        title_upper = title.upper()

        if 'RND' in title_upper or 'NORMA DE DIRECTORIO' in title_upper:
            return 'RND'
        elif 'RA' in title_upper or 'RESOLUCIÓN ADMINISTRATIVA' in title_upper:
            return 'RA'
        elif 'RM' in title_upper or 'RESOLUCIÓN MINISTERIAL' in title_upper:
            return 'RM'
        else:
            return 'NORMATIVA'

    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea un documento del SIN

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Estructura parseada
        """
        parser = PDFParser(pdf_path)

        # Parser genérico con análisis específico
        parsed = parser.parse_generic()

        text = parser.text or ""

        # Información específica del SIN
        info_adicional = {
            'numero_documento': self._extract_numero(text),
            'tipo_documento': self._extract_tipo_documento(text),
            'presidente_directorio': self._extract_presidente(text),
            'vigencia': self._extract_vigencia(text),
            'articulos': self._extract_articulos(text),
        }

        parsed['info_adicional'] = info_adicional

        return parsed

    def _extract_numero(self, text: str) -> Optional[str]:
        """Extrae el número de documento"""
        patterns = [
            r'RND\s+(\d{2}-\d{4}-\d{2})',
            r'RA\s+(\d{2}-\d{4}-\d{2})',
            r'RM\s+(\d+/\d{4})',
            r'NORMA\s+DE\s+DIRECTORIO\s+N[°º]\s*(\d{2}-\d{4}-\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_tipo_documento(self, text: str) -> Optional[str]:
        """Extrae el tipo de documento"""
        text_upper = text.upper()

        if 'NORMA DE DIRECTORIO' in text_upper or 'RND' in text_upper:
            return 'NORMA_DIRECTORIO'
        elif 'RESOLUCIÓN ADMINISTRATIVA' in text_upper or 'RA' in text_upper:
            return 'RESOLUCION_ADMINISTRATIVA'
        elif 'RESOLUCIÓN MINISTERIAL' in text_upper or 'RM' in text_upper:
            return 'RESOLUCION_MINISTERIAL'

        return None

    def _extract_presidente(self, text: str) -> Optional[str]:
        """Extrae el presidente del directorio o firmante"""
        patterns = [
            r'PRESIDENTE\s+(?:DEL\s+)?DIRECTORIO\s*:\s*(.+)',
            r'PRESIDENTE\s+EJECUTIVO\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_vigencia(self, text: str) -> Optional[str]:
        """Extrae la fecha de vigencia"""
        patterns = [
            r'VIGENCIA\s*:\s*(.+)',
            r'ENTRA\s+EN\s+VIGENCIA\s+(?:A\s+PARTIR\s+DE\s+)?(.+)',
            r'VIGENTE\s+DESDE\s+(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fecha_texto = match.group(1).split('\n')[0]
                return extract_date(fecha_texto) or normalize_text(fecha_texto)

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
NORMA DE DIRECTORIO N° 10-0025-24

SERVICIO DE IMPUESTOS NACIONALES
ESTADO PLURINACIONAL DE BOLIVIA

La Paz, 10 de enero de 2024

PRESIDENTE EJECUTIVO: Lic. Mario Guillén Suárez

CONSIDERANDO:

Que, el artículo 66 de la Ley N° 2492 (Código Tributario Boliviano) faculta
al Servicio de Impuestos Nacionales a emitir normas administrativas.

Que, es necesario establecer procedimientos claros para la presentación
de declaraciones juradas tributarias.

Que, la implementación de sistemas electrónicos requiere normativa específica.

POR TANTO:

El Presidente Ejecutivo del Servicio de Impuestos Nacionales, en uso de
sus atribuciones conferidas por Ley,

RESUELVE:

ARTÍCULO 1.- OBJETO
Establecer los procedimientos para la presentación de declaraciones juradas
tributarias a través del Sistema de Gestión Tributaria (SGT).

ARTÍCULO 2.- ALCANCE
Las presentes disposiciones son aplicables a todos los contribuyentes
inscritos en el padrón del Servicio de Impuestos Nacionales.

ARTÍCULO 3.- DECLARACIONES OBLIGATORIAS
Los contribuyentes deberán presentar las siguientes declaraciones:
a) Declaración Jurada del IVA (Form. 200)
b) Declaración Jurada del IT (Form. 400)
c) Declaración Jurada del IUE (Form. 500)

ARTÍCULO 4.- PLAZOS
Los plazos para la presentación de declaraciones son:
- IVA: Hasta el día 10 de cada mes
- IT: Hasta el día 15 de cada mes
- IUE: Hasta el día 120 de cada gestión fiscal

ARTÍCULO 5.- MEDIOS DE PRESENTACIÓN
Las declaraciones deberán presentarse obligatoriamente a través de:
a) Oficina Virtual del SIN
b) Plataformas habilitadas oficialmente

ARTÍCULO 6.- SANCIONES
El incumplimiento de las presentes disposiciones será sancionado conforme
al Código Tributario Boliviano.

ARTÍCULO 7.- VIGENCIA
La presente norma entra en vigencia a partir de su publicación en la
página web institucional.

DISPOSICIONES TRANSITORIAS

PRIMERA.- Los contribuyentes tendrán un plazo de 30 días para adecuarse
a las presentes disposiciones.

SEGUNDA.- Se mantienen vigentes los formularios en uso hasta la implementación
completa del nuevo sistema.

Regístrese, publíquese y archívese.

Lic. Mario Guillén Suárez
PRESIDENTE EJECUTIVO
SERVICIO DE IMPUESTOS NACIONALES
"""

        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(contenido)

        self.stats["total_downloaded"] += 1
        return pdf_path


def scrape_sin(only_new: bool = False, only_modified: bool = False,
               limit: Optional[int] = None) -> Dict:
    """
    Helper para ejecutar scraper del SIN

    Args:
        only_new: Solo nuevos
        only_modified: Solo modificados
        limit: Límite

    Returns:
        Estadísticas
    """
    scraper = SINScraper()
    return scraper.run(only_new=only_new, only_modified=only_modified, limit=limit)
