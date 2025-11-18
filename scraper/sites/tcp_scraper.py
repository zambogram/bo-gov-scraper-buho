"""
Scraper para Tribunal Constitucional Plurinacional de Bolivia (TCP)
Extrae Sentencias Constitucionales: SC, SCP, SCA
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


class TCPScraper(BaseScraper):
    """
    Scraper para el Tribunal Constitucional Plurinacional
    URL: https://www.tcpbolivia.bo o https://buscador.tcpbolivia.bo
    """

    def __init__(self, outputs_dir: str = "outputs"):
        super().__init__(
            site_name="tcp",
            base_url="https://buscador.tcpbolivia.bo",
            outputs_dir=outputs_dir
        )

        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene lista de sentencias del TCP

        Para implementación real, se conectaría al buscador oficial.
        Esta versión incluye lógica de scraping + datos de ejemplo.

        Returns:
            Lista de documentos encontrados
        """
        documents = []

        # OPCIÓN 1: Scraping real (si el sitio está disponible)
        try:
            documents = self._fetch_from_website()
            if documents:
                return documents
        except Exception as e:
            print(f"  → Advertencia: No se pudo conectar al sitio real: {e}")

        # OPCIÓN 2: Datos de ejemplo para demostración
        print("  → Usando datos de ejemplo para demostración")
        documents = self._get_example_documents()

        return documents

    def _fetch_from_website(self) -> List[Dict]:
        """
        Intenta obtener documentos del sitio web real

        Returns:
            Lista de documentos o lista vacía si falla
        """
        documents = []

        # URL del buscador (ajustar según sitio real)
        search_url = f"{self.base_url}/sentencias"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar enlaces a sentencias
            # NOTA: Estos selectores deben ajustarse al HTML real del sitio
            sentencia_links = soup.find_all('a', href=re.compile(r'sentencia|SC|SCP', re.I))

            for link in sentencia_links[:20]:  # Limitar a 20 para demo
                try:
                    title = normalize_text(link.get_text())
                    url = link.get('href', '')

                    if not url.startswith('http'):
                        url = f"{self.base_url}{url}"

                    # Extraer ID del documento
                    doc_id = extract_numero_documento(title) or f"TCP_{len(documents)}"
                    doc_id = doc_id.replace('/', '_').replace(' ', '_')

                    # Extraer fecha si está disponible
                    fecha = extract_date(title)

                    documents.append({
                        'id': doc_id,
                        'title': title,
                        'url': url,
                        'date': fecha or datetime.now().strftime('%Y-%m-%d'),
                        'tipo': self._detect_tipo_sentencia(title),
                    })

                except Exception as e:
                    print(f"    Error parseando enlace: {e}")
                    continue

        except Exception as e:
            print(f"  Error en scraping real: {e}")

        return documents

    def _get_example_documents(self) -> List[Dict]:
        """
        Retorna documentos de ejemplo para demostración

        Returns:
            Lista de documentos de ejemplo
        """
        return [
            {
                'id': 'SCP_0001_2024',
                'title': 'SCP 0001/2024 - Amparo Constitucional contra resolución judicial',
                'url': 'https://example.com/tcp/SCP_0001_2024.pdf',
                'date': '2024-01-15',
                'tipo': 'SCP',
                'ejemplo': True,
            },
            {
                'id': 'SCP_0002_2024',
                'title': 'SCP 0002/2024 - Acción de Libertad',
                'url': 'https://example.com/tcp/SCP_0002_2024.pdf',
                'date': '2024-01-20',
                'tipo': 'SCP',
                'ejemplo': True,
            },
            {
                'id': 'SC_0100_2024',
                'title': 'SC 0100/2024 - Inconstitucionalidad de Ley',
                'url': 'https://example.com/tcp/SC_0100_2024.pdf',
                'date': '2024-02-10',
                'tipo': 'SC',
                'ejemplo': True,
            },
            {
                'id': 'SCA_0050_2024',
                'title': 'SCA 0050/2024 - Acción de Cumplimiento',
                'url': 'https://example.com/tcp/SCA_0050_2024.pdf',
                'date': '2024-03-05',
                'tipo': 'SCA',
                'ejemplo': True,
            },
        ]

    def _detect_tipo_sentencia(self, title: str) -> str:
        """
        Detecta el tipo de sentencia

        Args:
            title: Título del documento

        Returns:
            Tipo: SCP, SC, SCA, u otro
        """
        title_upper = title.upper()

        if 'SCP' in title_upper:
            return 'SCP'
        elif 'SCA' in title_upper:
            return 'SCA'
        elif 'SC' in title_upper:
            return 'SC'
        else:
            return 'SENTENCIA'

    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea un documento del TCP

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Estructura parseada con secciones
        """
        parser = PDFParser(pdf_path)

        # Usar el parser específico del TCP
        parsed = parser.parse_tribunal_constitucional()

        # Análisis adicional específico del TCP
        text = parser.text or ""

        # Extraer información del encabezado
        info_adicional = {
            'magistrado_relator': self._extract_magistrado(text),
            'sala': self._extract_sala(text),
            'tipo_accion': self._extract_tipo_accion(text),
        }

        parsed['info_adicional'] = info_adicional

        return parsed

    def _extract_magistrado(self, text: str) -> Optional[str]:
        """Extrae el nombre del magistrado relator"""
        patterns = [
            r'MAGISTRADO\s+RELATOR\s*:\s*(.+)',
            r'RELATOR\s*:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(1).split('\n')[0])

        return None

    def _extract_sala(self, text: str) -> Optional[str]:
        """Extrae información de la sala"""
        patterns = [
            r'SALA\s+(\w+)',
            r'(PRIMERA|SEGUNDA|TERCERA|CUARTA)\s+SALA',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return normalize_text(match.group(0))

        return None

    def _extract_tipo_accion(self, text: str) -> Optional[str]:
        """Extrae el tipo de acción constitucional"""
        acciones = [
            'AMPARO CONSTITUCIONAL',
            'ACCIÓN DE LIBERTAD',
            'ACCIÓN DE PROTECCIÓN DE PRIVACIDAD',
            'ACCIÓN DE CUMPLIMIENTO',
            'ACCIÓN POPULAR',
            'ACCIÓN DE INCONSTITUCIONALIDAD',
        ]

        text_upper = text.upper()

        for accion in acciones:
            if accion in text_upper:
                return accion

        return None

    def download_pdf(self, url: str, doc_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Sobrescribe método de descarga para manejar ejemplos

        Args:
            url: URL del PDF
            doc_id: ID del documento
            filename: Nombre del archivo

        Returns:
            Ruta del archivo o None
        """
        # Si es un ejemplo, crear PDF de muestra
        if 'example.com' in url:
            return self._create_example_pdf(doc_id, filename)

        # Si es URL real, usar método padre
        return super().download_pdf(url, doc_id, filename)

    def _create_example_pdf(self, doc_id: str, filename: Optional[str] = None) -> str:
        """
        Crea un PDF de ejemplo con contenido simulado

        Args:
            doc_id: ID del documento
            filename: Nombre del archivo

        Returns:
            Ruta del PDF creado
        """
        from scraper.core.utils import ensure_dir

        if not filename:
            filename = f"{doc_id}.pdf"

        pdf_path = os.path.join(self.pdfs_dir, filename)

        # Crear un archivo de texto simulando el contenido del PDF
        # En producción real, esto sería un PDF descargado
        contenido_ejemplo = f"""
SENTENCIA CONSTITUCIONAL PLURINACIONAL {doc_id.replace('_', ' ')}

TRIBUNAL CONSTITUCIONAL PLURINACIONAL
SALA PRIMERA

MAGISTRADO RELATOR: Dr. Juan Pérez Rodríguez

ACCIÓN: AMPARO CONSTITUCIONAL

VISTOS:
La presente acción de amparo constitucional interpuesta por el ciudadano
solicitando la protección de sus derechos fundamentales...

ANTECEDENTES:
El accionante señala que en fecha 10 de enero de 2024 fue notificado
con una resolución administrativa que vulnera sus derechos...

PROBLEMÁTICA:
Se debe determinar si la autoridad demandada vulneró los derechos
constitucionales del accionante al emitir la resolución cuestionada...

CONSIDERANDO:
El Tribunal Constitucional Plurinacional en análisis del caso considera:

I. Sobre la tutela constitucional
Los derechos fundamentales gozan de protección reforzada...

II. Análisis del caso concreto
En el presente caso se evidencia que...

FUNDAMENTOS JURÍDICOS:
Conforme a los artículos 128 y siguientes de la CPE, el amparo constitucional
procede contra actos u omisiones ilegales o indebidas...

POR TANTO:
El Tribunal Constitucional Plurinacional, en virtud de la autoridad que
le confiere la Constitución Política del Estado, RESUELVE:

1° CONCEDER la tutela solicitada
2° DISPONER que la autoridad demandada deje sin efecto la resolución impugnada

Regístrese, notifíquese y publíquese.

Magistrado Relator
Dr. Juan Pérez Rodríguez
"""

        # Guardar como archivo de texto (simulando PDF)
        # En producción, aquí se descargaría el PDF real
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(contenido_ejemplo)

        self.stats["total_downloaded"] += 1
        return pdf_path


# Función helper para uso directo
def scrape_tcp(only_new: bool = False, only_modified: bool = False,
               limit: Optional[int] = None) -> Dict:
    """
    Función helper para ejecutar el scraper del TCP

    Args:
        only_new: Solo documentos nuevos
        only_modified: Solo documentos modificados
        limit: Límite de documentos

    Returns:
        Estadísticas de ejecución
    """
    scraper = TCPScraper()
    return scraper.run(only_new=only_new, only_modified=only_modified, limit=limit)
