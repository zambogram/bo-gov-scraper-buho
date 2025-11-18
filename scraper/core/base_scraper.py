"""
Clase base abstracta para todos los scrapers
Define la interfaz común que deben implementar todos los scrapers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os
import json
from .delta_manager import DeltaUpdateManager
from .pdf_parser import PDFParser
from .utils import ensure_dir, download_file, calculate_hash, format_timestamp


class BaseScraper(ABC):
    """
    Clase base para scrapers de sitios gubernamentales
    """

    def __init__(self, site_name: str, base_url: str, outputs_dir: str = "outputs"):
        """
        Inicializa el scraper base

        Args:
            site_name: Nombre identificador del sitio
            base_url: URL base del sitio web
            outputs_dir: Directorio raíz para outputs
        """
        self.site_name = site_name
        self.base_url = base_url
        self.outputs_dir = os.path.join(outputs_dir, site_name)
        self.pdfs_dir = os.path.join(self.outputs_dir, "pdfs")
        self.json_dir = os.path.join(self.outputs_dir, "json")

        # Crear directorios
        ensure_dir(self.outputs_dir)
        ensure_dir(self.pdfs_dir)
        ensure_dir(self.json_dir)

        # Gestor de delta updates
        self.delta_manager = DeltaUpdateManager(site_name, outputs_dir)

        # Estadísticas de la ejecución actual
        self.stats = {
            "total_found": 0,
            "total_new": 0,
            "total_modified": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "total_downloaded": 0,
            "total_parsed": 0,
        }

    @abstractmethod
    def fetch_document_list(self) -> List[Dict]:
        """
        Obtiene la lista de documentos disponibles en el sitio

        Returns:
            Lista de diccionarios con información de documentos
            Cada dict debe tener al menos: id, title, url, date
        """
        pass

    @abstractmethod
    def parse_document(self, pdf_path: str) -> Dict:
        """
        Parsea un documento PDF específico del sitio

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con estructura parseada
        """
        pass

    def download_pdf(self, url: str, doc_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Descarga un PDF

        Args:
            url: URL del PDF
            doc_id: ID del documento
            filename: Nombre del archivo (opcional)

        Returns:
            Ruta del archivo descargado o None si falla
        """
        if not filename:
            filename = f"{doc_id}.pdf"

        pdf_path = os.path.join(self.pdfs_dir, filename)

        # Si ya existe, verificar si necesita actualización
        if os.path.exists(pdf_path):
            if not self.delta_manager.is_modified_document(doc_id, pdf_path):
                return pdf_path

        # Descargar
        if download_file(url, pdf_path):
            self.stats["total_downloaded"] += 1
            return pdf_path

        self.stats["total_errors"] += 1
        return None

    def process_document(self, doc_info: Dict, only_new: bool = False,
                        only_modified: bool = False) -> Optional[Dict]:
        """
        Procesa un documento completo: descarga, parsea y guarda

        Args:
            doc_info: Información del documento
            only_new: Solo procesar documentos nuevos
            only_modified: Solo procesar documentos modificados

        Returns:
            Documento procesado o None si se omite
        """
        doc_id = doc_info["id"]

        # Verificar si debe procesarse
        is_new = self.delta_manager.is_new_document(doc_id)

        if only_new and not is_new:
            self.stats["total_skipped"] += 1
            self.delta_manager.mark_as_skipped(doc_id)
            return None

        # Descargar PDF
        pdf_path = self.download_pdf(doc_info["url"], doc_id)
        if not pdf_path:
            return None

        # Verificar si está modificado
        is_modified = self.delta_manager.is_modified_document(doc_id, pdf_path)

        if only_modified and not is_modified and not is_new:
            self.stats["total_skipped"] += 1
            self.delta_manager.mark_as_skipped(doc_id)
            return None

        if not is_new and not is_modified:
            self.stats["total_skipped"] += 1
            self.delta_manager.mark_as_skipped(doc_id)
            return None

        # Parsear documento
        try:
            parsed_data = self.parse_document(pdf_path)
            self.stats["total_parsed"] += 1

            # Combinar con información original
            full_data = {
                **doc_info,
                "parsed_data": parsed_data,
                "processed_at": format_timestamp(),
            }

            # Guardar JSON
            json_path = os.path.join(self.json_dir, f"{doc_id}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

            # Registrar en índice
            file_hash = calculate_hash(pdf_path)
            self.delta_manager.register_document(doc_id, {
                "id": doc_id,
                "title": doc_info.get("title", ""),
                "date": doc_info.get("date", ""),
                "url": doc_info.get("url", ""),
                "hash": file_hash,
                "pdf_path": pdf_path,
                "json_path": json_path,
            })

            if is_new:
                self.stats["total_new"] += 1
            else:
                self.stats["total_modified"] += 1

            return full_data

        except Exception as e:
            print(f"Error procesando {doc_id}: {e}")
            self.stats["total_errors"] += 1
            return None

    def run(self, only_new: bool = False, only_modified: bool = False,
            limit: Optional[int] = None) -> Dict:
        """
        Ejecuta el scraper completo

        Args:
            only_new: Solo procesar documentos nuevos
            only_modified: Solo procesar documentos modificados
            limit: Limitar número de documentos a procesar

        Returns:
            Estadísticas de ejecución
        """
        print(f"\n{'='*60}")
        print(f"Iniciando scraper: {self.site_name.upper()}")
        print(f"URL: {self.base_url}")
        print(f"{'='*60}\n")

        # Iniciar ejecución
        self.delta_manager.start_run()

        # Obtener lista de documentos
        print("Obteniendo lista de documentos...")
        documents = self.fetch_document_list()
        self.stats["total_found"] = len(documents)

        print(f"  → Encontrados: {len(documents)} documentos")

        if limit:
            documents = documents[:limit]
            print(f"  → Limitando a: {limit} documentos")

        # Procesar cada documento
        print(f"\nProcesando documentos...")
        for i, doc_info in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] {doc_info.get('title', doc_info['id'])}")
            self.process_document(doc_info, only_new, only_modified)

        # Resumen final
        print(f"\n{'='*60}")
        print(f"RESUMEN - {self.site_name.upper()}")
        print(f"{'='*60}")
        print(f"Total encontrados:  {self.stats['total_found']}")
        print(f"Nuevos:            {self.stats['total_new']}")
        print(f"Modificados:       {self.stats['total_modified']}")
        print(f"Omitidos:          {self.stats['total_skipped']}")
        print(f"Errores:           {self.stats['total_errors']}")
        print(f"Descargados:       {self.stats['total_downloaded']}")
        print(f"Parseados:         {self.stats['total_parsed']}")
        print(f"{'='*60}\n")

        return self.stats

    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas del scraper

        Returns:
            Diccionario con estadísticas
        """
        return {
            "current_run": self.stats,
            "historical": self.delta_manager.get_statistics(),
            "total_documents": self.delta_manager.index["total_documents"],
        }
