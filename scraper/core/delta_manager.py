"""
Sistema de actualización incremental (Delta Update)
Gestiona índices de documentos procesados para evitar duplicados
"""
import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime
from .utils import calculate_hash, ensure_dir, format_timestamp


class DeltaUpdateManager:
    """
    Gestor de actualización incremental
    Mantiene índice de documentos procesados con sus hashes
    """

    def __init__(self, site_name: str, outputs_dir: str = "outputs"):
        """
        Inicializa el gestor de delta updates

        Args:
            site_name: Nombre del sitio (tcp, tsj, contraloria, etc.)
            outputs_dir: Directorio raíz de salidas
        """
        self.site_name = site_name
        self.outputs_dir = os.path.join(outputs_dir, site_name)
        self.index_file = os.path.join(self.outputs_dir, "index.json")

        ensure_dir(self.outputs_dir)

        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Carga el índice desde disco o crea uno nuevo"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando índice: {e}. Creando nuevo índice.")

        # Índice inicial
        return {
            "site": self.site_name,
            "created_at": format_timestamp(),
            "last_updated": format_timestamp(),
            "total_documents": 0,
            "documents": {},
            "statistics": {
                "total_processed": 0,
                "total_new": 0,
                "total_modified": 0,
                "total_skipped": 0,
                "last_run": None
            }
        }

    def _save_index(self) -> None:
        """Guarda el índice a disco"""
        self.index["last_updated"] = format_timestamp()

        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando índice: {e}")

    def is_new_document(self, doc_id: str) -> bool:
        """
        Verifica si un documento es nuevo

        Args:
            doc_id: ID único del documento

        Returns:
            True si el documento es nuevo
        """
        return doc_id not in self.index["documents"]

    def is_modified_document(self, doc_id: str, file_path: str) -> bool:
        """
        Verifica si un documento ha sido modificado

        Args:
            doc_id: ID único del documento
            file_path: Ruta al archivo PDF

        Returns:
            True si el documento existe pero su hash cambió
        """
        if doc_id not in self.index["documents"]:
            return False

        if not os.path.exists(file_path):
            return False

        current_hash = calculate_hash(file_path)
        stored_hash = self.index["documents"][doc_id].get("hash", "")

        return current_hash != stored_hash

    def register_document(self, doc_id: str, metadata: Dict) -> None:
        """
        Registra un documento en el índice

        Args:
            doc_id: ID único del documento
            metadata: Metadatos del documento (hash, url, fecha, etc.)
        """
        is_new = self.is_new_document(doc_id)

        self.index["documents"][doc_id] = {
            **metadata,
            "registered_at": format_timestamp(),
            "status": "processed"
        }

        if is_new:
            self.index["statistics"]["total_new"] += 1
        else:
            self.index["statistics"]["total_modified"] += 1

        self.index["statistics"]["total_processed"] += 1
        self.index["total_documents"] = len(self.index["documents"])

        self._save_index()

    def mark_as_skipped(self, doc_id: str) -> None:
        """
        Marca un documento como omitido (ya procesado)

        Args:
            doc_id: ID único del documento
        """
        self.index["statistics"]["total_skipped"] += 1
        self._save_index()

    def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """
        Obtiene información de un documento

        Args:
            doc_id: ID único del documento

        Returns:
            Metadatos del documento o None si no existe
        """
        return self.index["documents"].get(doc_id)

    def get_all_document_ids(self) -> Set[str]:
        """
        Obtiene todos los IDs de documentos registrados

        Returns:
            Set con todos los IDs
        """
        return set(self.index["documents"].keys())

    def start_run(self) -> None:
        """Inicia una nueva ejecución del scraper"""
        self.index["statistics"]["last_run"] = format_timestamp()
        self.index["statistics"]["total_processed"] = 0
        self.index["statistics"]["total_new"] = 0
        self.index["statistics"]["total_modified"] = 0
        self.index["statistics"]["total_skipped"] = 0
        self._save_index()

    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de la última ejecución

        Returns:
            Diccionario con estadísticas
        """
        return self.index["statistics"].copy()

    def remove_document(self, doc_id: str) -> bool:
        """
        Elimina un documento del índice

        Args:
            doc_id: ID único del documento

        Returns:
            True si se eliminó, False si no existía
        """
        if doc_id in self.index["documents"]:
            del self.index["documents"][doc_id]
            self.index["total_documents"] = len(self.index["documents"])
            self._save_index()
            return True
        return False

    def cleanup_missing_files(self, pdfs_dir: str) -> int:
        """
        Limpia del índice documentos cuyos archivos ya no existen

        Args:
            pdfs_dir: Directorio donde están los PDFs

        Returns:
            Número de documentos eliminados
        """
        removed = 0
        docs_to_remove = []

        for doc_id, info in self.index["documents"].items():
            pdf_path = info.get("pdf_path")
            if pdf_path and not os.path.exists(pdf_path):
                docs_to_remove.append(doc_id)

        for doc_id in docs_to_remove:
            self.remove_document(doc_id)
            removed += 1

        if removed > 0:
            print(f"Limpiados {removed} documentos sin archivos")

        return removed

    def export_report(self, output_path: str) -> None:
        """
        Exporta un reporte del índice

        Args:
            output_path: Ruta del archivo de salida
        """
        report = {
            "site": self.site_name,
            "generated_at": format_timestamp(),
            "summary": {
                "total_documents": self.index["total_documents"],
                "last_updated": self.index["last_updated"],
            },
            "statistics": self.index["statistics"],
            "documents_list": [
                {
                    "id": doc_id,
                    "title": info.get("title", ""),
                    "date": info.get("date", ""),
                    "registered_at": info.get("registered_at", ""),
                }
                for doc_id, info in self.index["documents"].items()
            ]
        }

        ensure_dir(os.path.dirname(output_path))

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"Reporte exportado a: {output_path}")
