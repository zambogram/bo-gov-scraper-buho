"""
Gestor del catálogo de sitios gubernamentales.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SiteConfig:
    """Configuración de un sitio gubernamental."""
    site_id: str
    nombre: str
    descripcion: str
    prioridad: int
    categoria: str
    url_base: str
    url_listado: str
    estado_scraper: str
    frecuencia_actualizacion: str
    tipo_documentos: List[str]
    formato_disponible: str
    notas: str
    selectores: Dict[str, str]


class CatalogManager:
    """Gestiona el catálogo de sitios gubernamentales."""

    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Inicializa el gestor del catálogo.

        Args:
            catalog_path: Ruta al archivo YAML del catálogo.
                         Si es None, usa la ruta por defecto.
        """
        if catalog_path is None:
            project_root = Path(__file__).parent.parent
            catalog_path = project_root / "config" / "sites_catalog.yaml"

        self.catalog_path = Path(catalog_path)
        self._catalog_data: Optional[dict] = None
        self._sites: Dict[str, SiteConfig] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Carga el catálogo desde el archivo YAML."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"No se encontró el catálogo en: {self.catalog_path}"
            )

        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self._catalog_data = yaml.safe_load(f)

        # Parsear sitios
        for site_id, site_data in self._catalog_data.get('sitios', {}).items():
            self._sites[site_id] = SiteConfig(
                site_id=site_id,
                nombre=site_data.get('nombre', ''),
                descripcion=site_data.get('descripcion', ''),
                prioridad=site_data.get('prioridad', 99),
                categoria=site_data.get('categoria', ''),
                url_base=site_data.get('url_base', ''),
                url_listado=site_data.get('url_listado', ''),
                estado_scraper=site_data.get('estado_scraper', 'pendiente'),
                frecuencia_actualizacion=site_data.get('frecuencia_actualizacion', ''),
                tipo_documentos=site_data.get('tipo_documentos', []),
                formato_disponible=site_data.get('formato_disponible', ''),
                notas=site_data.get('notas', ''),
                selectores=site_data.get('selectores', {})
            )

    def get_site(self, site_id: str) -> Optional[SiteConfig]:
        """Obtiene la configuración de un sitio por su ID."""
        return self._sites.get(site_id)

    def list_sites(
        self,
        prioridad: Optional[int] = None,
        categoria: Optional[str] = None,
        estado_scraper: Optional[str] = None
    ) -> List[SiteConfig]:
        """
        Lista sitios con filtros opcionales.

        Args:
            prioridad: Filtrar por prioridad (1, 2, etc.)
            categoria: Filtrar por categoría (legislativo, judicial, etc.)
            estado_scraper: Filtrar por estado (implementado, pendiente, etc.)

        Returns:
            Lista de configuraciones de sitios que cumplen los filtros.
        """
        sites = list(self._sites.values())

        if prioridad is not None:
            sites = [s for s in sites if s.prioridad == prioridad]

        if categoria is not None:
            sites = [s for s in sites if s.categoria == categoria]

        if estado_scraper is not None:
            sites = [s for s in sites if s.estado_scraper == estado_scraper]

        # Ordenar por prioridad y luego por nombre
        sites.sort(key=lambda s: (s.prioridad, s.nombre))

        return sites

    def get_ola1_site_ids(self) -> List[str]:
        """Obtiene la lista de IDs de sitios de la Ola 1."""
        ola1_data = self._catalog_data.get('olas', {}).get('ola_1', {})
        return ola1_data.get('site_ids', [])

    def get_ola2_site_ids(self) -> List[str]:
        """Obtiene la lista de IDs de sitios de la Ola 2."""
        ola2_data = self._catalog_data.get('olas', {}).get('ola_2', {})
        return ola2_data.get('site_ids', [])

    def get_config_value(self, key: str, default=None):
        """Obtiene un valor de la configuración general."""
        return self._catalog_data.get('configuracion', {}).get(key, default)

    def site_exists(self, site_id: str) -> bool:
        """Verifica si un sitio existe en el catálogo."""
        return site_id in self._sites

    def get_total_sites(self) -> int:
        """Retorna el número total de sitios en el catálogo."""
        return len(self._sites)

    def get_sites_by_priority(self) -> Dict[int, List[SiteConfig]]:
        """Agrupa sitios por prioridad."""
        by_priority = {}
        for site in self._sites.values():
            if site.prioridad not in by_priority:
                by_priority[site.prioridad] = []
            by_priority[site.prioridad].append(site)
        return by_priority


# Constante global para facilitar el acceso
OLA1_SITE_IDS = [
    "gaceta_oficial",
    "tsj_genesis",
    "tcp",
    "asfi",
    "sin"
]
