"""
Configuración y carga del catálogo de sitios
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class SiteConfig:
    """Configuración de un sitio web"""
    id: str
    nombre: str
    tipo: str
    categoria: str
    url_base: str
    url_search: str
    prioridad: int
    ola: int
    activo: bool
    metadatos: Dict[str, Any] = field(default_factory=dict)
    scraper: Dict[str, Any] = field(default_factory=dict)

    @property
    def raw_pdf_dir(self) -> Path:
        """Directorio para PDFs crudos"""
        return BASE_DIR / "data" / "raw" / self.id / "pdfs"

    @property
    def normalized_text_dir(self) -> Path:
        """Directorio para texto normalizado"""
        return BASE_DIR / "data" / "normalized" / self.id / "text"

    @property
    def normalized_json_dir(self) -> Path:
        """Directorio para JSON normalizado"""
        return BASE_DIR / "data" / "normalized" / self.id / "json"

    @property
    def index_file(self) -> Path:
        """Archivo de índice para delta updates"""
        return BASE_DIR / "data" / "index" / self.id / "index.json"

    @property
    def logs_dir(self) -> Path:
        """Directorio para logs del sitio"""
        return BASE_DIR / "logs" / self.id

    def ensure_directories(self) -> None:
        """Crear directorios si no existen"""
        for dir_path in [
            self.raw_pdf_dir,
            self.normalized_text_dir,
            self.normalized_json_dir,
            self.index_file.parent,
            self.logs_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    """Configuración global de la aplicación"""
    data_base_dir: Path = BASE_DIR / "data"
    logs_dir: Path = BASE_DIR / "logs"
    exports_dir: Path = BASE_DIR / "exports"

    max_concurrent_downloads: int = 3
    timeout_requests: int = 30
    retry_attempts: int = 3
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) BUHO Legal Scraper/1.0"

    # Catálogo de sitios
    sites: Dict[str, SiteConfig] = field(default_factory=dict)

    def __post_init__(self):
        """Cargar catálogo de sitios después de inicializar"""
        self._load_sites_catalog()

    def _load_sites_catalog(self) -> None:
        """Cargar catálogo de sitios desde YAML"""
        catalog_path = BASE_DIR / "config" / "sites_catalog.yaml"

        if not catalog_path.exists():
            print(f"⚠️  Catálogo de sitios no encontrado en {catalog_path}")
            return

        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Cargar configuración global
        global_config = data.get('global_config', {})
        if 'max_concurrent_downloads' in global_config:
            self.max_concurrent_downloads = global_config['max_concurrent_downloads']
        if 'timeout_requests' in global_config:
            self.timeout_requests = global_config['timeout_requests']
        if 'retry_attempts' in global_config:
            self.retry_attempts = global_config['retry_attempts']
        if 'user_agent' in global_config:
            self.user_agent = global_config['user_agent']

        # Cargar sitios
        sites_data = data.get('sites', {})
        for site_id, site_data in sites_data.items():
            self.sites[site_id] = SiteConfig(
                id=site_data.get('id', site_id),
                nombre=site_data.get('nombre', ''),
                tipo=site_data.get('tipo', ''),
                categoria=site_data.get('categoria', ''),
                url_base=site_data.get('url_base', ''),
                url_search=site_data.get('url_search', ''),
                prioridad=site_data.get('prioridad', 99),
                ola=site_data.get('ola', 99),
                activo=site_data.get('activo', True),
                metadatos=site_data.get('metadatos', {}),
                scraper=site_data.get('scraper', {})
            )

    def get_site(self, site_id: str) -> Optional[SiteConfig]:
        """Obtener configuración de un sitio por ID"""
        return self.sites.get(site_id)

    def list_active_sites(self) -> List[SiteConfig]:
        """Listar todos los sitios activos"""
        return [site for site in self.sites.values() if site.activo]

    def list_all_sites(self) -> List[SiteConfig]:
        """Listar todos los sitios (activos e inactivos)"""
        return list(self.sites.values())


# Instancia global de configuración
settings = Settings()


def get_site_config(site_id: str) -> Optional[SiteConfig]:
    """
    Obtener configuración de un sitio específico

    Args:
        site_id: ID del sitio (tcp, tsj, asfi, etc.)

    Returns:
        SiteConfig o None si no existe
    """
    return settings.get_site(site_id)


def list_active_sites() -> List[SiteConfig]:
    """
    Listar todos los sitios activos

    Returns:
        Lista de configuraciones de sitios activos
    """
    return settings.list_active_sites()


def get_last_update_date(site_id: str) -> Optional[datetime]:
    """
    Obtener fecha de última actualización de un sitio

    Args:
        site_id: ID del sitio

    Returns:
        Fecha de última actualización o None
    """
    site = get_site_config(site_id)
    if not site:
        return None

    # Revisar el archivo de índice para obtener la fecha más reciente
    if site.index_file.exists():
        import json
        try:
            with open(site.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                if 'last_update' in index_data:
                    return datetime.fromisoformat(index_data['last_update'])
        except:
            pass

    return None
