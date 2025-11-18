"""
Módulo para descarga de PDFs
"""
import os
import requests
from typing import List, Dict
import pandas as pd
from tqdm import tqdm
import time


class PDFDownloader:
    """Descargador de PDFs"""

    def __init__(self, output_dir: str = "data/pdfs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_pdf(self, url: str, filename: str, max_retries: int = 3) -> Dict:
        """
        Descarga un PDF individual

        Args:
            url: URL del PDF
            filename: Nombre del archivo
            max_retries: Número de reintentos

        Returns:
            Dict con información de la descarga
        """
        filepath = os.path.join(self.output_dir, filename)

        # Si es una URL de ejemplo, crear un archivo dummy
        if 'ejemplo.gob.bo' in url:
            with open(filepath, 'wb') as f:
                f.write(b'%PDF-1.4\n%Documento de ejemplo\n')
            return {
                'url': url,
                'filepath': filepath,
                'size': 30,
                'status': 'ejemplo',
                'error': None
            }

        for intento in range(max_retries):
            try:
                response = self.session.get(url, timeout=30, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))

                with open(filepath, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                return {
                    'url': url,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath),
                    'status': 'ok',
                    'error': None
                }

            except Exception as e:
                if intento < max_retries - 1:
                    time.sleep(2 ** intento)  # Backoff exponencial
                    continue
                else:
                    return {
                        'url': url,
                        'filepath': None,
                        'size': 0,
                        'status': 'error',
                        'error': str(e)
                    }

    def download_batch(self, documentos: pd.DataFrame, force_redownload: bool = False) -> pd.DataFrame:
        """
        Descarga un lote de PDFs

        Args:
            documentos: DataFrame con información de documentos
            force_redownload: Forzar re-descarga

        Returns:
            DataFrame actualizado con información de descarga
        """
        print(f"\n{'='*60}")
        print(f"DESCARGA DE PDFs")
        print(f"{'='*60}")

        resultados = []

        for idx, doc in tqdm(documentos.iterrows(), total=len(documentos), desc="Descargando PDFs"):
            filename = f"{doc['id_documento']}.pdf"
            filepath = os.path.join(self.output_dir, filename)

            # Verificar si ya existe
            if os.path.exists(filepath) and not force_redownload:
                print(f"  ⊙ Ya existe: {filename}")
                resultado = {
                    'url': doc['url_pdf'],
                    'filepath': filepath,
                    'size': os.path.getsize(filepath),
                    'status': 'cached',
                    'error': None
                }
            else:
                print(f"  ↓ Descargando: {filename}")
                resultado = self.download_pdf(doc['url_pdf'], filename)

            resultados.append(resultado)
            time.sleep(0.5)  # Ser amable con el servidor

        # Agregar columnas al DataFrame
        docs_updated = documentos.copy()
        docs_updated['pdf_filepath'] = [r['filepath'] for r in resultados]
        docs_updated['pdf_size'] = [r['size'] for r in resultados]
        docs_updated['download_status'] = [r['status'] for r in resultados]
        docs_updated['download_error'] = [r['error'] for r in resultados]

        exitosos = sum(1 for r in resultados if r['status'] in ['ok', 'cached', 'ejemplo'])
        print(f"\n✓ Descarga completada: {exitosos}/{len(documentos)} PDFs")

        return docs_updated


def download_pdfs(documentos: pd.DataFrame, output_dir: str = "data/pdfs",
                  force_redownload: bool = False) -> pd.DataFrame:
    """
    Función principal para descarga de PDFs

    Args:
        documentos: DataFrame con información de documentos
        output_dir: Directorio de salida
        force_redownload: Forzar re-descarga

    Returns:
        DataFrame actualizado
    """
    downloader = PDFDownloader(output_dir)
    return downloader.download_batch(documentos, force_redownload)
