"""
Scraper de la Gaceta Oficial de Bolivia

Este módulo descarga documentos legales de la Gaceta Oficial,
extrae metadatos y genera un registro en CSV.

URL base: https://www.gacetaoficialdebolivia.gob.bo/

Autor: BÚHO - Bolivia
Fase: 3 (Metadata Extraction)
"""

import os
import csv
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Importar el extractor de metadatos
from scraper.metadata_extractor import extract_all_metadata


class GacetaScraper:
    """
    Scraper para la Gaceta Oficial de Bolivia.

    Descarga documentos PDF, extrae metadatos y genera logs.
    """

    def __init__(self,
                 output_dir: str = "data",
                 export_dir: str = "exports",
                 max_downloads: Optional[int] = None):
        """
        Inicializa el scraper.

        Args:
            output_dir: Directorio para guardar PDFs descargados
            export_dir: Directorio para guardar CSV de logs
            max_downloads: Límite máximo de documentos a descargar (None = sin límite)
        """
        self.base_url = "https://www.gacetaoficialdebolivia.gob.bo"
        self.output_dir = Path(output_dir)
        self.export_dir = Path(export_dir)
        self.max_downloads = max_downloads

        # Crear directorios si no existen
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Lista de documentos procesados
        self.documentos = []

        # Configuración de requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extraer_links_gaceta(self, url_inicial: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extrae los enlaces a documentos PDF de la Gaceta.

        Args:
            url_inicial: URL inicial para comenzar el scraping
                        Si es None, usa la página principal

        Returns:
            Lista de diccionarios con 'titulo' y 'url_pdf'
        """
        if url_inicial is None:
            # URL de ejemplo - en producción usar la URL real de la Gaceta
            url_inicial = f"{self.base_url}/normas/buscar"

        documentos = []

        try:
            print(f"🔍 Extrayendo enlaces de: {url_inicial}")
            response = self.session.get(url_inicial, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar todos los enlaces a PDF
            # Nota: Estos selectores CSS pueden variar según la estructura real del sitio
            pdf_links = soup.find_all('a', href=True)

            for link in pdf_links:
                href = link.get('href', '')

                # Filtrar solo enlaces a PDF
                if '.pdf' in href.lower() or 'download' in href.lower():
                    url_completa = urljoin(self.base_url, href)

                    # Extraer el título (texto del enlace o parent)
                    titulo = link.get_text(strip=True)
                    if not titulo:
                        # Intentar obtener el título del elemento padre
                        parent = link.find_parent(['div', 'td', 'li'])
                        if parent:
                            titulo = parent.get_text(strip=True)

                    if titulo and url_completa:
                        documentos.append({
                            'titulo': titulo,
                            'url_pdf': url_completa
                        })

                    # Limitar si se especificó max_downloads
                    if self.max_downloads and len(documentos) >= self.max_downloads:
                        print(f"⚠️  Límite de {self.max_downloads} documentos alcanzado")
                        break

        except requests.RequestException as e:
            print(f"❌ Error al extraer enlaces: {e}")

        print(f"✅ Se encontraron {len(documentos)} documentos")
        return documentos

    def descargar_pdf(self, url_pdf: str, nombre_archivo: str) -> bool:
        """
        Descarga un archivo PDF.

        Args:
            url_pdf: URL del PDF
            nombre_archivo: Nombre del archivo de salida

        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        ruta_completa = self.output_dir / nombre_archivo

        # Evitar descargar si ya existe
        if ruta_completa.exists():
            print(f"  ⏩ Ya existe: {nombre_archivo}")
            return True

        try:
            print(f"  📥 Descargando: {nombre_archivo}")
            response = self.session.get(url_pdf, timeout=60, stream=True)
            response.raise_for_status()

            with open(ruta_completa, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"  ✅ Descargado: {nombre_archivo}")
            return True

        except requests.RequestException as e:
            print(f"  ❌ Error al descargar {nombre_archivo}: {e}")
            return False

    def procesar_documento(self, doc_info: Dict[str, str], indice: int) -> Dict:
        """
        Procesa un documento: descarga PDF y extrae metadatos.

        Args:
            doc_info: Diccionario con 'titulo' y 'url_pdf'
            indice: Índice del documento (para nombrar archivo)

        Returns:
            Diccionario con toda la información del documento procesado
        """
        titulo = doc_info['titulo']
        url_pdf = doc_info['url_pdf']

        print(f"\n📄 Procesando documento {indice + 1}:")
        print(f"  Título: {titulo[:80]}...")

        # Extraer metadatos
        metadatos = extract_all_metadata(titulo, url_pdf)

        # Generar nombre de archivo simple (sin renombrar por ahora)
        nombre_archivo = f"doc_{indice + 1:04d}.pdf"

        # Descargar PDF
        descarga_exitosa = self.descargar_pdf(url_pdf, nombre_archivo)

        # Compilar registro completo
        registro = {
            'titulo': titulo,
            'url_pdf': url_pdf,
            'archivo_descargado': nombre_archivo if descarga_exitosa else '',
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'estado': 'descargado' if descarga_exitosa else 'error',
            'tipo_norma': metadatos.get('tipo_norma', 'Desconocido'),
            'numero_norma': metadatos.get('numero_norma', ''),
            'fecha_publicacion_aproximada': metadatos.get('fecha_publicacion_aproximada', ''),
        }

        # Mostrar metadatos extraídos
        print(f"  🏷️  Tipo: {registro['tipo_norma']}")
        print(f"  🔢 Número: {registro['numero_norma'] or 'N/A'}")
        print(f"  📅 Fecha: {registro['fecha_publicacion_aproximada'] or 'N/A'}")

        return registro

    def guardar_csv(self, documentos: List[Dict], nombre_archivo: str = "gaceta_log.csv"):
        """
        Guarda los documentos procesados en un archivo CSV.

        Args:
            documentos: Lista de diccionarios con información de documentos
            nombre_archivo: Nombre del archivo CSV de salida
        """
        ruta_csv = self.export_dir / nombre_archivo

        if not documentos:
            print("⚠️  No hay documentos para guardar en CSV")
            return

        # Definir columnas del CSV
        columnas = [
            'titulo',
            'url_pdf',
            'archivo_descargado',
            'fecha_extraccion',
            'estado',
            'tipo_norma',
            'numero_norma',
            'fecha_publicacion_aproximada',
        ]

        try:
            with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columnas)
                writer.writeheader()
                writer.writerows(documentos)

            print(f"\n✅ CSV guardado: {ruta_csv}")
            print(f"   Total de registros: {len(documentos)}")

        except Exception as e:
            print(f"❌ Error al guardar CSV: {e}")

    def ejecutar(self, url_inicial: Optional[str] = None):
        """
        Ejecuta el proceso completo de scraping.

        Args:
            url_inicial: URL inicial para comenzar (opcional)
        """
        print("="*80)
        print("🦉 BÚHO - Scraper de Gaceta Oficial de Bolivia")
        print("   FASE 3: Extracción de Metadatos")
        print("="*80)

        # Paso 1: Extraer enlaces
        print("\n📋 Paso 1: Extrayendo enlaces...")
        documentos_info = self.extraer_links_gaceta(url_inicial)

        if not documentos_info:
            print("❌ No se encontraron documentos para procesar")
            return

        # Paso 2: Procesar cada documento
        print(f"\n📥 Paso 2: Procesando {len(documentos_info)} documentos...")

        for i, doc_info in enumerate(documentos_info):
            registro = self.procesar_documento(doc_info, i)
            self.documentos.append(registro)

            # Pequeña pausa para no saturar el servidor
            time.sleep(1)

        # Paso 3: Guardar CSV
        print("\n💾 Paso 3: Guardando CSV...")
        self.guardar_csv(self.documentos)

        print("\n" + "="*80)
        print("✅ Proceso completado exitosamente")
        print("="*80)

    def obtener_resumen(self, limit: int = 5) -> List[Dict]:
        """
        Obtiene un resumen de los primeros N documentos procesados.

        Args:
            limit: Número de documentos a incluir en el resumen

        Returns:
            Lista de diccionarios con resumen de metadatos
        """
        return self.documentos[:limit]


def crear_datos_ejemplo(output_dir: str = "data", export_dir: str = "exports", num_docs: int = 8):
    """
    Crea datos de ejemplo para probar el sistema sin hacer scraping real.

    Útil para desarrollo y pruebas.
    """
    print("🧪 Creando datos de ejemplo para pruebas...")

    # Documentos de ejemplo basados en patrones reales de Bolivia
    docs_ejemplo = [
        {
            'titulo': 'Ley N° 1234 de 15 de enero de 2023 - Ley de Presupuesto General del Estado',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/ley_1234.pdf'
        },
        {
            'titulo': 'Decreto Supremo 4567 del 10 de febrero de 2023',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/ds_4567.pdf'
        },
        {
            'titulo': 'Resolución Ministerial 089-2023 de marzo 2023',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/rm_089.pdf'
        },
        {
            'titulo': 'RM 125/2023 - Reglamento Interno',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/rm_125.pdf'
        },
        {
            'titulo': 'Resolución Administrativa 045 del 5 de abril de 2023',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/ra_045.pdf'
        },
        {
            'titulo': 'DS 890-2022 Reglamento de Contrataciones',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/ds_890.pdf'
        },
        {
            'titulo': 'Sentencia Constitucional 012/2023',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/sc_012.pdf'
        },
        {
            'titulo': 'Ley 999 del 20 de mayo de 2023',
            'url_pdf': 'https://www.gacetaoficialdebolivia.gob.bo/normas/descargar/ley_999.pdf'
        },
    ]

    # Limitar al número solicitado
    docs_ejemplo = docs_ejemplo[:num_docs]

    # Crear instancia del scraper
    scraper = GacetaScraper(output_dir=output_dir, export_dir=export_dir)

    # Procesar cada documento de ejemplo (sin descargar PDF realmente)
    print(f"\n📥 Procesando {len(docs_ejemplo)} documentos de ejemplo...")

    for i, doc_info in enumerate(docs_ejemplo):
        print(f"\n📄 Procesando documento {i + 1}:")
        print(f"  Título: {doc_info['titulo'][:80]}...")

        # Extraer metadatos
        metadatos = extract_all_metadata(doc_info['titulo'], doc_info['url_pdf'])

        # Generar nombre de archivo
        nombre_archivo = f"doc_{i + 1:04d}.pdf"

        # Crear archivo vacío de ejemplo
        ruta_pdf = Path(output_dir) / nombre_archivo
        ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
        ruta_pdf.write_text(f"PDF de ejemplo: {doc_info['titulo']}")

        # Compilar registro
        registro = {
            'titulo': doc_info['titulo'],
            'url_pdf': doc_info['url_pdf'],
            'archivo_descargado': nombre_archivo,
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'estado': 'descargado',
            'tipo_norma': metadatos.get('tipo_norma', 'Desconocido'),
            'numero_norma': metadatos.get('numero_norma', ''),
            'fecha_publicacion_aproximada': metadatos.get('fecha_publicacion_aproximada', ''),
        }

        scraper.documentos.append(registro)

        # Mostrar metadatos
        print(f"  🏷️  Tipo: {registro['tipo_norma']}")
        print(f"  🔢 Número: {registro['numero_norma'] or 'N/A'}")
        print(f"  📅 Fecha: {registro['fecha_publicacion_aproximada'] or 'N/A'}")

    # Guardar CSV
    print("\n💾 Guardando CSV...")
    scraper.guardar_csv(scraper.documentos)

    print("\n✅ Datos de ejemplo creados exitosamente")

    return scraper


if __name__ == "__main__":
    # Modo de prueba con datos de ejemplo
    scraper = crear_datos_ejemplo(num_docs=8)

    print("\n" + "="*80)
    print("📊 RESUMEN DE PRIMEROS 5 DOCUMENTOS")
    print("="*80)

    for i, doc in enumerate(scraper.obtener_resumen(5), 1):
        print(f"\n{i}. {doc['titulo'][:60]}...")
        print(f"   Tipo: {doc['tipo_norma']}")
        print(f"   Número: {doc['numero_norma'] or 'N/A'}")
        print(f"   Fecha: {doc['fecha_publicacion_aproximada'] or 'N/A'}")
