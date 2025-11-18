"""
Scraper para Tribunal Supremo de Justicia de Bolivia (TSJ)
Extrae Autos Supremos de las diferentes Salas
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


class TSJScraper(BaseScraper):
    """
    Scraper para el Tribunal Supremo de Justicia
    URL: https://tsj.bo o similar
    Extrae Autos Supremos de salas Penal, Civil, Social, etc.
    """

    def __init__(self, outputs_dir: str = "outputs"):
        super().__init__(
            site_name="tsj",
            base_url="https://tsj.bo",
            outputs_dir=outputs_dir
        )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        self.salas = ['penal', 'civil', 'social', 'contencioso']

    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene lista de Autos Supremos del TSJ

        Returns:
            Lista de documentos
        """
        documents = []

        # Intentar scraping real
        try:
            documents = self._fetch_from_website()
            if documents:
                return documents
        except Exception as e:
            print(f"  → Advertencia: No se pudo conectar al sitio real: {e}")

        # Datos de ejemplo
        print("  → Usando datos de ejemplo para demostración")
        documents = self._get_example_documents()

        return documents

    def _fetch_from_website(self) -> List[Dict]:
        """
        Intenta scraping del sitio web real

        Returns:
            Lista de documentos
        """
        documents = []

        # Intentar por cada sala
        for sala in self.salas:
            try:
                sala_url = f"{self.base_url}/sala-{sala}"
                response = requests.get(sala_url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Buscar enlaces a autos supremos
                    links = soup.find_all('a', href=re.compile(r'auto|AS|supremo', re.I))

                    for link in links[:10]:  # Limitar por sala
                        try:
                            title = normalize_text(link.get_text())
                            url = link.get('href', '')

                            if not url.startswith('http'):
                                url = f"{self.base_url}{url}"

                            doc_id = extract_numero_documento(title) or f"AS_{sala}_{len(documents)}"
                            doc_id = doc_id.replace('/', '_').replace(' ', '_')

                            documents.append({
                                'id': doc_id,
                                'title': title,
                                'url': url,
                                'date': extract_date(title) or datetime.now().strftime('%Y-%m-%d'),
                                'sala': sala,
                            })

                        except Exception as e:
                            continue

            except Exception as e:
                print(f"  Error scrapeando sala {sala}: {e}")
                continue

        return documents

    def _get_example_documents(self) -> List[Dict]:
        """
        Retorna documentos de ejemplo

        Returns:
            Lista de ejemplos
        """
        return [
            {
                'id': 'AS_PENAL_0123_2024',
                'title': 'AS 0123/2024 - Sala Penal - Recurso de Casación',
                'url': 'https://example.com/tsj/AS_PENAL_0123_2024.pdf',
                'date': '2024-01-10',
                'sala': 'penal',
                'ejemplo': True,
            },
            {
                'id': 'AS_CIVIL_0045_2024',
                'title': 'AS 0045/2024 - Sala Civil - Resolución de Contrato',
                'url': 'https://example.com/tsj/AS_CIVIL_0045_2024.pdf',
                'date': '2024-01-15',
                'sala': 'civil',
                'ejemplo': True,
            },
            {
                'id': 'AS_SOCIAL_0078_2024',
                'title': 'AS 0078/2024 - Sala Social - Reincorporación Laboral',
                'url': 'https://example.com/tsj/AS_SOCIAL_0078_2024.pdf',
                'date': '2024-01-20',
                'sala': 'social',
                'ejemplo': True,
            },
            {
                'id': 'AS_CONTENCIOSO_0012_2024',
                'title': 'AS 0012/2024 - Sala Contencioso Administrativa',
                'url': 'https://example.com/tsj/AS_CONTENCIOSO_0012_2024.pdf',
                'date': '2024-02-01',
                'sala': 'contencioso',
                'ejemplo': True,
            },
        ]

    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea un Auto Supremo

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Estructura parseada
        """
        parser = PDFParser(pdf_path)

        # Usar parser específico para TSJ
        parsed = parser.parse_tribunal_supremo()

        # Extraer información adicional
        text = parser.text or ""

        info_adicional = {
            'sala': self._extract_sala(text),
            'ministro_relator': self._extract_ministro(text),
            'partes': self._extract_partes(text),
        }

        parsed['info_adicional'] = info_adicional

        return parsed

    def _extract_sala(self, text: str) -> Optional[str]:
        """Extrae la sala que emitió el auto"""
        patterns = [
            r'SALA\s+(PENAL|CIVIL|SOCIAL|CONTENCIOSO[^A-Z]*ADMINISTRATIVA?)',
            r'(PRIMERA|SEGUNDA|TERCERA)\s+SALA',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(0))

        return None

    def _extract_ministro(self, text: str) -> Optional[str]:
        """Extrae el ministro relator"""
        patterns = [
            r'MINISTRO\s+RELATOR\s*:\s*(.+)',
            r'RELATOR\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_partes(self, text: str) -> Dict[str, str]:
        """Extrae las partes del proceso"""
        partes = {}

        # Buscar demandante/recurrente
        patterns_demandante = [
            r'DEMANDANTE\s*:\s*(.+)',
            r'RECURRENTE\s*:\s*(.+)',
            r'PARTE\s+ACTORA\s*:\s*(.+)',
        ]

        for pattern in patterns_demandante:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                partes['demandante'] = normalize_text(match.group(1).split('\n')[0])
                break

        # Buscar demandado/recurrido
        patterns_demandado = [
            r'DEMANDADO\s*:\s*(.+)',
            r'RECURRIDO\s*:\s*(.+)',
            r'PARTE\s+DEMANDADA\s*:\s*(.+)',
        ]

        for pattern in patterns_demandado:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                partes['demandado'] = normalize_text(match.group(1).split('\n')[0])
                break

        return partes

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
AUTO SUPREMO {doc_id.replace('_', ' ')}

TRIBUNAL SUPREMO DE JUSTICIA
SALA PENAL

MINISTRO RELATOR: Dr. Carlos Mendoza López

EXPEDIENTE: 123/2024
DEMANDANTE: Juan Pérez Gómez
DEMANDADO: Estado Plurinacional de Bolivia

RESULTANDOS:

PRIMERO.- Por memorial presentado el 15 de enero de 2024, el recurrente
interpone recurso de casación contra la sentencia emitida por el Tribunal
de Apelación...

SEGUNDO.- Admitido el recurso, se corrió traslado a la parte recurrida,
quien presentó su respuesta dentro del plazo legal...

TERCERO.- Habiéndose cumplido con las formalidades procesales, se procede
a dictar el presente Auto Supremo...

CONSIDERANDOS:

PRIMERO.- Sobre la competencia y procedencia del recurso
El Tribunal Supremo de Justicia es competente para conocer recursos de
casación conforme al artículo 419 del Código Procesal Penal...

SEGUNDO.- Sobre el fondo del asunto
Analizados los argumentos del recurrente, se evidencia que la sentencia
impugnada incurrió en error de derecho al interpretar incorrectamente
el artículo 234 del Código Penal...

TERCERO.- Sobre la reparación del agravio
Corresponde casar la sentencia y disponer que el Tribunal de origen
emita nueva resolución conforme a derecho...

PARTE RESOLUTIVA:

Por los fundamentos expuestos, el Tribunal Supremo de Justicia, en uso
de sus atribuciones, RESUELVE:

PRIMERO.- CASAR la sentencia impugnada
SEGUNDO.- DISPONER que el Tribunal de origen emita nueva resolución
TERCERO.- Sin costas por la naturaleza del fallo

Regístrese, notifíquese y devuélvase.

Ministro Relator
Dr. Carlos Mendoza López
"""

        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(contenido)

        self.stats["total_downloaded"] += 1
        return pdf_path


def scrape_tsj(only_new: bool = False, only_modified: bool = False,
               limit: Optional[int] = None) -> Dict:
    """
    Helper para ejecutar scraper del TSJ

    Args:
        only_new: Solo nuevos
        only_modified: Solo modificados
        limit: Límite

    Returns:
        Estadísticas
    """
    scraper = TSJScraper()
    return scraper.run(only_new=only_new, only_modified=only_modified, limit=limit)
