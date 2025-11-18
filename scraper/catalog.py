"""
Módulo de gestión del catálogo de sitios estatales bolivianos.

Este módulo provee funciones para:
- Cargar y parsear el catálogo YAML
- Buscar sitios por ID, prioridad, estado, etc.
- Actualizar metadatos (última actualización, contadores)
- Validar entradas del catálogo

Autor: BÚHO LegalTech
Fecha: 2025-01-18
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json


# ========================================
# CONFIGURACIÓN
# ========================================

PROJECT_ROOT = Path(__file__).parent.parent
CATALOG_PATH = PROJECT_ROOT / "config" / "sites_catalog.yaml"


# ========================================
# MODELO DE DATOS
# ========================================

@dataclass
class SiteInfo:
    """Información de un sitio estatal boliviano."""

    # Identificación
    site_id: str
    nombre: str
    nivel: str
    tipo_fuente: str
    prioridad: int
    estado_scraper: str

    # URLs
    url_base: str
    url_busqueda: Optional[str] = None
    url_listado: Optional[str] = None

    # Características técnicas
    formato_documento: str = "pdf"
    requiere_selenium: bool = False
    requiere_login: bool = False
    tiene_api: bool = False

    # Estructura legal
    estructura_texto: str = "articulos"
    tipos_documentos: List[str] = None

    # Metadatos operacionales
    frecuencia_actualizacion: str = "semanal"
    ultima_actualizacion: Optional[str] = None
    documentos_totales: int = 0
    articulos_totales: int = 0

    # Observaciones
    notas: Optional[str] = None

    def __post_init__(self):
        """Inicializar valores por defecto."""
        if self.tipos_documentos is None:
            self.tipos_documentos = []

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return asdict(self)

    def to_json(self) -> str:
        """Convertir a JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ========================================
# CLASE PRINCIPAL: CATALOG MANAGER
# ========================================

class CatalogManager:
    """Gestor del catálogo de sitios."""

    def __init__(self, catalog_path: Path = CATALOG_PATH):
        """
        Inicializar el gestor del catálogo.

        Args:
            catalog_path: Ruta al archivo YAML del catálogo
        """
        self.catalog_path = catalog_path
        self._catalog_data: Optional[Dict] = None
        self._sites: Optional[List[SiteInfo]] = None

        # Cargar catálogo al inicializar
        self.reload()

    def reload(self) -> None:
        """Recargar el catálogo desde disco."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"Catálogo no encontrado en: {self.catalog_path}\n"
                f"Asegúrate de que config/sites_catalog.yaml existe."
            )

        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self._catalog_data = yaml.safe_load(f)

        # Parsear sitios
        self._sites = [
            SiteInfo(**site_data)
            for site_data in self._catalog_data.get('sites', [])
        ]

    def save(self) -> None:
        """Guardar cambios al catálogo en disco."""
        # Actualizar datos
        self._catalog_data['sites'] = [site.to_dict() for site in self._sites]
        self._catalog_data['actualizado'] = datetime.now().strftime("%Y-%m-%d")

        # Escribir a disco
        with open(self.catalog_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self._catalog_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )

    # ========================================
    # CONSULTAS
    # ========================================

    def get_all_sites(self) -> List[SiteInfo]:
        """Obtener todos los sitios del catálogo."""
        return self._sites.copy()

    def get_site(self, site_id: str) -> Optional[SiteInfo]:
        """
        Obtener un sitio por su ID.

        Args:
            site_id: Identificador único del sitio

        Returns:
            SiteInfo si existe, None si no se encuentra
        """
        for site in self._sites:
            if site.site_id == site_id:
                return site
        return None

    def get_sites_by_prioridad(self, prioridad: int) -> List[SiteInfo]:
        """
        Obtener sitios por prioridad.

        Args:
            prioridad: 1 (crítico), 2 (importante), 3 (complementario)

        Returns:
            Lista de sitios con esa prioridad
        """
        return [site for site in self._sites if site.prioridad == prioridad]

    def get_sites_by_estado(self, estado: str) -> List[SiteInfo]:
        """
        Obtener sitios por estado de scraper.

        Args:
            estado: pendiente | en_progreso | implementado | deshabilitado

        Returns:
            Lista de sitios con ese estado
        """
        return [site for site in self._sites if site.estado_scraper == estado]

    def get_sites_by_nivel(self, nivel: str) -> List[SiteInfo]:
        """
        Obtener sitios por nivel gubernamental.

        Args:
            nivel: nacional | departamental | municipal

        Returns:
            Lista de sitios de ese nivel
        """
        return [site for site in self._sites if site.nivel == nivel]

    def get_sites_by_tipo(self, tipo_fuente: str) -> List[SiteInfo]:
        """
        Obtener sitios por tipo de fuente.

        Args:
            tipo_fuente: normativa | jurisprudencia | regulador

        Returns:
            Lista de sitios de ese tipo
        """
        return [site for site in self._sites if site.tipo_fuente == tipo_fuente]

    def get_ola1_sites(self) -> List[SiteInfo]:
        """
        Obtener sitios de la Ola 1 (MVP crítico).

        Returns:
            Lista de sitios prioritarios (prioridad 1)
        """
        return self.get_sites_by_prioridad(1)

    def search_sites(
        self,
        prioridad: Optional[int] = None,
        estado: Optional[str] = None,
        nivel: Optional[str] = None,
        tipo_fuente: Optional[str] = None
    ) -> List[SiteInfo]:
        """
        Búsqueda avanzada con múltiples filtros.

        Args:
            prioridad: Filtrar por prioridad (1, 2, 3)
            estado: Filtrar por estado (pendiente, implementado, etc.)
            nivel: Filtrar por nivel (nacional, departamental, municipal)
            tipo_fuente: Filtrar por tipo (normativa, jurisprudencia, regulador)

        Returns:
            Lista de sitios que cumplen todos los criterios
        """
        results = self._sites.copy()

        if prioridad is not None:
            results = [s for s in results if s.prioridad == prioridad]

        if estado is not None:
            results = [s for s in results if s.estado_scraper == estado]

        if nivel is not None:
            results = [s for s in results if s.nivel == nivel]

        if tipo_fuente is not None:
            results = [s for s in results if s.tipo_fuente == tipo_fuente]

        return results

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del catálogo.

        Returns:
            Diccionario con métricas clave
        """
        total = len(self._sites)
        implementados = len(self.get_sites_by_estado("implementado"))
        pendientes = len(self.get_sites_by_estado("pendiente"))
        en_progreso = len(self.get_sites_by_estado("en_progreso"))

        total_docs = sum(site.documentos_totales for site in self._sites)
        total_arts = sum(site.articulos_totales for site in self._sites)

        return {
            "total_sitios": total,
            "implementados": implementados,
            "pendientes": pendientes,
            "en_progreso": en_progreso,
            "porcentaje_completado": round((implementados / total * 100) if total > 0 else 0, 1),
            "total_documentos": total_docs,
            "total_articulos": total_arts,
            "por_prioridad": {
                1: len(self.get_sites_by_prioridad(1)),
                2: len(self.get_sites_by_prioridad(2)),
                3: len(self.get_sites_by_prioridad(3))
            },
            "por_nivel": {
                "nacional": len(self.get_sites_by_nivel("nacional")),
                "departamental": len(self.get_sites_by_nivel("departamental")),
                "municipal": len(self.get_sites_by_nivel("municipal"))
            },
            "por_tipo": {
                "normativa": len(self.get_sites_by_tipo("normativa")),
                "jurisprudencia": len(self.get_sites_by_tipo("jurisprudencia")),
                "regulador": len(self.get_sites_by_tipo("regulador"))
            }
        }

    # ========================================
    # ACTUALIZACIÓN DE METADATOS
    # ========================================

    def update_site_metadata(
        self,
        site_id: str,
        documentos_nuevos: int = 0,
        articulos_nuevos: int = 0,
        actualizar_timestamp: bool = True
    ) -> bool:
        """
        Actualizar metadatos de un sitio después de scraping.

        Args:
            site_id: ID del sitio
            documentos_nuevos: Cantidad de documentos procesados
            articulos_nuevos: Cantidad de artículos extraídos
            actualizar_timestamp: Si actualizar la fecha de última actualización

        Returns:
            True si se actualizó correctamente, False si el sitio no existe
        """
        site = self.get_site(site_id)
        if not site:
            return False

        # Actualizar contadores
        site.documentos_totales += documentos_nuevos
        site.articulos_totales += articulos_nuevos

        # Actualizar timestamp
        if actualizar_timestamp:
            site.ultima_actualizacion = datetime.now().isoformat()

        # Guardar cambios
        self.save()

        return True

    def set_site_estado(self, site_id: str, nuevo_estado: str) -> bool:
        """
        Cambiar el estado de un sitio.

        Args:
            site_id: ID del sitio
            nuevo_estado: Nuevo estado (pendiente | en_progreso | implementado | deshabilitado)

        Returns:
            True si se actualizó correctamente, False si el sitio no existe
        """
        site = self.get_site(site_id)
        if not site:
            return False

        estados_validos = ["pendiente", "en_progreso", "implementado", "deshabilitado"]
        if nuevo_estado not in estados_validos:
            raise ValueError(f"Estado inválido: {nuevo_estado}. Debe ser uno de: {estados_validos}")

        site.estado_scraper = nuevo_estado
        self.save()

        return True

    # ========================================
    # VALIDACIÓN
    # ========================================

    def validate_catalog(self) -> List[str]:
        """
        Validar la integridad del catálogo.

        Returns:
            Lista de errores encontrados (vacía si todo está OK)
        """
        errores = []

        # Verificar IDs únicos
        site_ids = [site.site_id for site in self._sites]
        duplicados = set([x for x in site_ids if site_ids.count(x) > 1])
        if duplicados:
            errores.append(f"IDs duplicados: {duplicados}")

        # Verificar campos requeridos
        for site in self._sites:
            if not site.site_id:
                errores.append(f"Sitio sin ID: {site.nombre}")

            if not site.url_base:
                errores.append(f"Sitio sin URL base: {site.site_id}")

            if site.prioridad not in [1, 2, 3]:
                errores.append(f"Prioridad inválida en {site.site_id}: {site.prioridad}")

            if site.estado_scraper not in ["pendiente", "en_progreso", "implementado", "deshabilitado"]:
                errores.append(f"Estado inválido en {site.site_id}: {site.estado_scraper}")

        return errores


# ========================================
# FUNCIONES DE CONVENIENCIA
# ========================================

def load_catalog() -> CatalogManager:
    """
    Cargar el catálogo (función de conveniencia).

    Returns:
        Instancia de CatalogManager
    """
    return CatalogManager()


def get_site_info(site_id: str) -> Optional[SiteInfo]:
    """
    Obtener info de un sitio (función de conveniencia).

    Args:
        site_id: ID del sitio

    Returns:
        SiteInfo o None
    """
    catalog = load_catalog()
    return catalog.get_site(site_id)


def list_all_sites() -> List[SiteInfo]:
    """
    Listar todos los sitios (función de conveniencia).

    Returns:
        Lista de todos los sitios
    """
    catalog = load_catalog()
    return catalog.get_all_sites()


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    """Script de prueba del módulo."""

    print("=" * 60)
    print("PRUEBA DEL MÓDULO CATALOG")
    print("=" * 60)

    # Cargar catálogo
    print("\n1. Cargando catálogo...")
    catalog = load_catalog()
    print(f"   ✓ Catálogo cargado: {len(catalog.get_all_sites())} sitios")

    # Estadísticas
    print("\n2. Estadísticas generales:")
    stats = catalog.get_stats()
    print(f"   Total sitios: {stats['total_sitios']}")
    print(f"   Implementados: {stats['implementados']}")
    print(f"   Pendientes: {stats['pendientes']}")
    print(f"   Completado: {stats['porcentaje_completado']}%")
    print(f"   Por prioridad: {stats['por_prioridad']}")

    # Sitios Ola 1
    print("\n3. Sitios Ola 1 (MVP):")
    ola1 = catalog.get_ola1_sites()
    for site in ola1:
        print(f"   - {site.site_id:20s} | {site.nombre[:50]}")

    # Buscar un sitio específico
    print("\n4. Información de sitio específico (gaceta_oficial):")
    gaceta = catalog.get_site("gaceta_oficial")
    if gaceta:
        print(f"   Nombre: {gaceta.nombre}")
        print(f"   URL: {gaceta.url_base}")
        print(f"   Estado: {gaceta.estado_scraper}")
        print(f"   Documentos: {gaceta.documentos_totales}")

    # Validación
    print("\n5. Validación del catálogo:")
    errores = catalog.validate_catalog()
    if errores:
        print("   ✗ Errores encontrados:")
        for error in errores:
            print(f"     - {error}")
    else:
        print("   ✓ Catálogo válido")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
