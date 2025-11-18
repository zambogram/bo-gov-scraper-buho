"""
MÓDULO 1: GACETA SCRAPER
========================
Este módulo se encarga de:
1. Navegar la página de la Gaceta Oficial de Bolivia
2. Encontrar enlaces a PDFs de normas legales
3. Descargar los PDFs a la carpeta data/pdfs/
4. Retornar información básica sobre los documentos descargados

Autor: Sistema BÚHO
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import re


class GacetaScraper:
    """
    Clase para descargar PDFs de la Gaceta Oficial de Bolivia.

    La Gaceta Oficial publica normas legales en formato PDF.
    Este scraper navega el sitio, encuentra los PDFs y los descarga.
    """

    def __init__(self, output_dir: str = "data/pdfs"):
        """
        Inicializa el scraper.

        Args:
            output_dir: Carpeta donde se guardarán los PDFs descargados
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        # Headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)

    def get_pdf_links_from_page(self, url: str) -> List[Dict[str, str]]:
        """
        Extrae todos los enlaces a PDFs de una página de la Gaceta.

        Args:
            url: URL de la página de listado de la Gaceta

        Returns:
            Lista de diccionarios con información de cada PDF:
            - 'url': URL del PDF
            - 'title': Título del documento (si está disponible)
            - 'source_page': URL de la página de donde se obtuvo
        """
        try:
            print(f"  → Accediendo a: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            pdf_links = []

            # Buscar todos los enlaces que apuntan a PDFs
            # Esto incluye enlaces directos y enlaces en botones/divs
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Verificar si es un enlace a PDF
                if href.lower().endswith('.pdf') or '/pdf/' in href.lower():
                    # Convertir a URL absoluta
                    absolute_url = urljoin(url, href)

                    # Extraer título (puede estar en el texto del enlace o en atributos)
                    title = link.get_text(strip=True) or link.get('title', '') or ''

                    pdf_links.append({
                        'url': absolute_url,
                        'title': title,
                        'source_page': url
                    })

            print(f"  ✓ Encontrados {len(pdf_links)} PDFs en la página")
            return pdf_links

        except Exception as e:
            print(f"  ✗ Error al obtener enlaces de {url}: {str(e)}")
            return []

    def download_pdf(self, pdf_url: str, custom_filename: Optional[str] = None) -> Optional[Dict[str, any]]:
        """
        Descarga un PDF desde una URL.

        Args:
            pdf_url: URL del PDF a descargar
            custom_filename: Nombre personalizado para el archivo (opcional)

        Returns:
            Diccionario con información del archivo descargado:
            - 'filename': Nombre del archivo guardado
            - 'filepath': Ruta completa del archivo
            - 'url': URL original
            - 'size_bytes': Tamaño en bytes
            - 'download_date': Fecha de descarga

            None si la descarga falla
        """
        try:
            print(f"    → Descargando: {pdf_url}")

            # Descargar el PDF
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            # Determinar nombre de archivo
            if custom_filename:
                filename = custom_filename
            else:
                # Extraer nombre de la URL
                filename = os.path.basename(urlparse(pdf_url).path)
                # Si no tiene extensión .pdf, agregarla
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'

            # Sanitizar nombre de archivo (eliminar caracteres no válidos)
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

            # Ruta completa
            filepath = os.path.join(self.output_dir, filename)

            # Verificar si ya existe
            if os.path.exists(filepath):
                print(f"    ⚠ El archivo ya existe: {filename}")
                return {
                    'filename': filename,
                    'filepath': filepath,
                    'url': pdf_url,
                    'size_bytes': os.path.getsize(filepath),
                    'download_date': datetime.now().isoformat(),
                    'already_existed': True
                }

            # Guardar el archivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(filepath)
            print(f"    ✓ Descargado: {filename} ({file_size / 1024:.1f} KB)")

            return {
                'filename': filename,
                'filepath': filepath,
                'url': pdf_url,
                'size_bytes': file_size,
                'download_date': datetime.now().isoformat(),
                'already_existed': False
            }

        except Exception as e:
            print(f"    ✗ Error al descargar {pdf_url}: {str(e)}")
            return None

    def scrape_gaceta(self, start_url: str, max_documents: int = 5) -> List[Dict[str, any]]:
        """
        FUNCIÓN PRINCIPAL: Descarga PDFs de la Gaceta Oficial.

        Esta es la función que debes llamar para descargar documentos.

        Args:
            start_url: URL de inicio (página de listado de la Gaceta)
            max_documents: Número máximo de documentos a descargar

        Returns:
            Lista de diccionarios con información de cada documento descargado
        """
        print(f"\n{'='*60}")
        print(f"INICIANDO SCRAPING DE LA GACETA OFICIAL")
        print(f"{'='*60}")
        print(f"URL inicial: {start_url}")
        print(f"Límite de documentos: {max_documents}")
        print(f"Directorio de salida: {self.output_dir}")
        print(f"{'='*60}\n")

        # Paso 1: Obtener enlaces a PDFs
        print("PASO 1: Buscando enlaces a PDFs...")
        pdf_links = self.get_pdf_links_from_page(start_url)

        if not pdf_links:
            print("⚠ No se encontraron PDFs en la página proporcionada.")
            return []

        # Limitar al número máximo de documentos
        pdf_links = pdf_links[:max_documents]

        # Paso 2: Descargar cada PDF
        print(f"\nPASO 2: Descargando {len(pdf_links)} documentos...")
        downloaded_docs = []

        for i, pdf_info in enumerate(pdf_links, 1):
            print(f"\n  Documento {i}/{len(pdf_links)}:")

            result = self.download_pdf(pdf_info['url'])

            if result:
                # Agregar información adicional
                result['title'] = pdf_info['title']
                result['source_page'] = pdf_info['source_page']
                result['download_order'] = i
                downloaded_docs.append(result)

            # Pausa corta entre descargas para no sobrecargar el servidor
            if i < len(pdf_links):
                time.sleep(1)

        # Resumen final
        print(f"\n{'='*60}")
        print(f"RESUMEN DE DESCARGA")
        print(f"{'='*60}")
        print(f"PDFs encontrados: {len(pdf_links)}")
        print(f"PDFs descargados exitosamente: {len(downloaded_docs)}")
        print(f"PDFs que ya existían: {sum(1 for d in downloaded_docs if d.get('already_existed', False))}")
        print(f"PDFs nuevos: {sum(1 for d in downloaded_docs if not d.get('already_existed', False))}")
        print(f"{'='*60}\n")

        return downloaded_docs


def main():
    """
    Función de prueba del scraper.

    NOTA PARA EL USUARIO:
    Esta es solo una función de prueba. Para usar el scraper en el pipeline
    completo, debes llamarlo desde main.py usando run_full_pipeline().
    """
    # URL de ejemplo de la Gaceta Oficial de Bolivia
    # IMPORTANTE: Esta URL debe ser actualizada con una URL real de la Gaceta
    test_url = "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar"

    scraper = GacetaScraper()
    docs = scraper.scrape_gaceta(test_url, max_documents=3)

    print(f"\nSe descargaron {len(docs)} documentos.")
    for doc in docs:
        print(f"  - {doc['filename']}")


if __name__ == "__main__":
    main()
