"""
Clases base para los scrapers de sitios gubernamentales.
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from scraper.catalog import SiteConfig


logger = logging.getLogger(__name__)


@dataclass
class DocumentoScrapeado:
    """Representa un documento scrapeado de un sitio gubernamental."""
    site_id: str
    document_id: str
    titulo: str
    tipo_norma: str
    numero_norma: str
    fecha_publicacion: str  # Formato ISO: YYYY-MM-DD
    url_detalle: Optional[str] = None
    url_pdf: Optional[str] = None
    path_pdf: Optional[str] = None
    hash_contenido: Optional[str] = None
    estado: str = "nuevo"  # nuevo, modificado, sin_cambios
    metadata_extra: Optional[Dict[str, Any]] = None
    fecha_scraping: Optional[str] = None

    def __post_init__(self):
        """Inicializa valores después de la creación."""
        if self.fecha_scraping is None:
            self.fecha_scraping = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convierte el documento a diccionario."""
        return asdict(self)

    def calcular_hash(self) -> str:
        """Calcula el hash del contenido del documento."""
        # Usar campos clave para el hash
        contenido = f"{self.titulo}|{self.tipo_norma}|{self.numero_norma}|{self.fecha_publicacion}|{self.url_pdf}"
        return hashlib.md5(contenido.encode()).hexdigest()


class DocumentIndex:
    """Gestiona el índice de documentos scrapeados para evitar duplicados."""

    def __init__(self, site_id: str, index_dir: Optional[Path] = None):
        """
        Inicializa el índice de documentos.

        Args:
            site_id: ID del sitio
            index_dir: Directorio donde guardar los índices
        """
        self.site_id = site_id

        if index_dir is None:
            project_root = Path(__file__).parent.parent
            index_dir = project_root / "data" / "index"

        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.index_dir / f"{site_id}.json"
        self.index_data: Dict[str, dict] = {}
        self._load_index()

    def _load_index(self):
        """Carga el índice desde el archivo JSON."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
        else:
            self.index_data = {}

    def save_index(self):
        """Guarda el índice en el archivo JSON."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index_data, f, indent=2, ensure_ascii=False)

    def document_exists(self, document_id: str) -> bool:
        """Verifica si un documento ya existe en el índice."""
        return document_id in self.index_data

    def get_document_hash(self, document_id: str) -> Optional[str]:
        """Obtiene el hash de un documento del índice."""
        doc = self.index_data.get(document_id)
        return doc.get('hash') if doc else None

    def has_changed(self, document_id: str, new_hash: str) -> bool:
        """Verifica si un documento ha cambiado comparando hashes."""
        old_hash = self.get_document_hash(document_id)
        return old_hash is not None and old_hash != new_hash

    def update_document(self, documento: DocumentoScrapeado):
        """Actualiza o agrega un documento al índice."""
        if documento.hash_contenido is None:
            documento.hash_contenido = documento.calcular_hash()

        self.index_data[documento.document_id] = {
            'hash': documento.hash_contenido,
            'titulo': documento.titulo,
            'fecha_publicacion': documento.fecha_publicacion,
            'fecha_ultima_vez_visto': datetime.now().isoformat(),
            'estado': documento.estado,
            'url_pdf': documento.url_pdf
        }

    def get_stats(self) -> dict:
        """Obtiene estadísticas del índice."""
        return {
            'total_documentos': len(self.index_data),
            'ultima_actualizacion': max(
                [doc['fecha_ultima_vez_visto'] for doc in self.index_data.values()],
                default=None
            )
        }


class BaseSiteScraper(ABC):
    """Clase base abstracta para todos los scrapers de sitios."""

    def __init__(self, site_config: SiteConfig, modo_demo: bool = False):
        """
        Inicializa el scraper.

        Args:
            site_config: Configuración del sitio desde el catálogo
            modo_demo: Si es True, genera datos de demostración en lugar de scrapear
        """
        self.site_config = site_config
        self.site_id = site_config.site_id
        self.modo_demo = modo_demo

        # Configurar directorios
        project_root = Path(__file__).parent.parent
        self.data_dir = project_root / "data" / "raw" / self.site_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_dir = self.data_dir / "pdfs"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar índice
        self.index = DocumentIndex(self.site_id)

        # Logger
        self.logger = logging.getLogger(f"scraper.{self.site_id}")

    @abstractmethod
    def scrape(self, limit: Optional[int] = None, solo_nuevos: bool = True) -> List[DocumentoScrapeado]:
        """
        Scrapea documentos del sitio.

        Args:
            limit: Límite de documentos a scrapear
            solo_nuevos: Si es True, solo procesa documentos nuevos o modificados

        Returns:
            Lista de documentos scrapeados
        """
        pass

    def _generar_document_id(self, tipo: str, numero: str, fecha: str) -> str:
        """Genera un ID único para un documento."""
        # Formato: SITEID-TIPO-NUMERO-FECHA
        tipo_clean = tipo.replace(' ', '-').upper()
        numero_clean = numero.replace('/', '-').replace(' ', '')
        fecha_clean = fecha.replace('-', '')
        return f"{self.site_id.upper()}-{tipo_clean}-{numero_clean}-{fecha_clean}"

    def _determinar_estado(self, documento: DocumentoScrapeado) -> str:
        """Determina el estado de un documento (nuevo, modificado, sin_cambios)."""
        if not self.index.document_exists(documento.document_id):
            return "nuevo"

        doc_hash = documento.calcular_hash()
        if self.index.has_changed(documento.document_id, doc_hash):
            return "modificado"

        return "sin_cambios"

    def _guardar_documentos(self, documentos: List[DocumentoScrapeado]):
        """Guarda los documentos y actualiza el índice."""
        for doc in documentos:
            # Calcular hash si no existe
            if doc.hash_contenido is None:
                doc.hash_contenido = doc.calcular_hash()

            # Determinar estado
            doc.estado = self._determinar_estado(doc)

            # Actualizar índice
            self.index.update_document(doc)

        # Guardar índice
        self.index.save_index()

        # Guardar documentos en JSON
        output_file = self.data_dir / "documentos.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [doc.to_dict() for doc in documentos],
                f,
                indent=2,
                ensure_ascii=False
            )

        self.logger.info(f"Guardados {len(documentos)} documentos en {output_file}")

    def generar_resumen(self, documentos: List[DocumentoScrapeado]) -> dict:
        """Genera un resumen de los documentos scrapeados."""
        nuevos = sum(1 for d in documentos if d.estado == "nuevo")
        modificados = sum(1 for d in documentos if d.estado == "modificado")
        sin_cambios = sum(1 for d in documentos if d.estado == "sin_cambios")

        return {
            'site_id': self.site_id,
            'total_encontrados': len(documentos),
            'nuevos': nuevos,
            'modificados': modificados,
            'sin_cambios': sin_cambios,
            'con_pdf': sum(1 for d in documentos if d.url_pdf),
            'fecha_scraping': datetime.now().isoformat()
        }
