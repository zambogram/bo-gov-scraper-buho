"""
Sincronizador extendido con Supabase
Lee datos de exports/ y data/normalized/, sincroniza con Supabase
Incluye toda la metadata extendida: áreas del derecho, jerarquía, estado de vigencia, etc.
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Importar cliente de Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase no está instalado. Instalar con: pip install supabase")

logger = logging.getLogger(__name__)


class SupabaseSyncExtended:
    """Sincronizador extendido con Supabase con metadata completa"""

    def __init__(
        self,
        exports_dir: Optional[Path] = None,
        normalized_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None
    ):
        """
        Inicializar sincronizador

        Args:
            exports_dir: Directorio de exportaciones CSV
            normalized_dir: Directorio de JSON normalizados
            log_dir: Directorio para logs de sincronización
        """
        # Cargar variables de entorno
        load_dotenv()

        # Verificar disponibilidad
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase no está disponible. Instalar con: pip install supabase")

        # Configurar directorios
        self.exports_dir = exports_dir or Path("exports")
        self.normalized_dir = normalized_dir or Path("data/normalized")
        self.log_dir = log_dir or Path("logs/sync_supabase")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Cliente de Supabase
        self.supabase: Optional[Client] = None
        self._init_supabase()

        # Configurar logging
        self._setup_logging()

        # Estadísticas de sincronización
        self.stats = {
            'sources_insertados': 0,
            'sources_actualizados': 0,
            'documents_insertados': 0,
            'documents_actualizados': 0,
            'articles_insertados': 0,
            'extraction_logs_insertados': 0,
            'errores': []
        }

    def _init_supabase(self) -> None:
        """Inicializar cliente de Supabase"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "Faltan credenciales de Supabase. "
                "Definir SUPABASE_URL y SUPABASE_KEY en .env"
            )

        self.supabase = create_client(url, key)
        logger.info("✓ Cliente de Supabase inicializado")

    def _setup_logging(self) -> None:
        """Configurar logging para sincronización"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"sync_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"✓ Logging configurado: {log_file}")

    def sync_site(self, site_id: str, session_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Sincronizar un sitio específico

        Args:
            site_id: ID del sitio (tcp, tsj, asfi, etc.)
            session_timestamp: Timestamp de sesión específica (opcional)

        Returns:
            Diccionario con estadísticas de sincronización
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Sincronizando sitio: {site_id}")
        logger.info(f"{'='*60}")

        # Resetear estadísticas
        self.stats = {
            'sources_insertados': 0,
            'sources_actualizados': 0,
            'documents_insertados': 0,
            'documents_actualizados': 0,
            'articles_insertados': 0,
            'extraction_logs_insertados': 0,
            'errores': []
        }

        try:
            # 1. Sincronizar source
            self._sync_source(site_id)

            # 2. Leer datos de exports y/o normalized
            documentos = self._read_site_data(site_id, session_timestamp)

            if not documentos:
                logger.warning(f"No se encontraron documentos para {site_id}")
                return self.stats

            logger.info(f"Total documentos a sincronizar: {len(documentos)}")

            # 3. Sincronizar cada documento
            for i, doc_data in enumerate(documentos, 1):
                logger.info(f"[{i}/{len(documentos)}] Procesando: {doc_data.get('id_documento')}")
                self._sync_document(doc_data)

            # 4. Registrar log de extracción
            self._sync_extraction_log(site_id, session_timestamp)

            logger.info(f"\n✓ Sincronización completada para {site_id}")
            self._print_stats()

        except Exception as e:
            logger.error(f"Error sincronizando {site_id}: {e}", exc_info=True)
            self.stats['errores'].append({
                'tipo': 'error_general',
                'mensaje': str(e)
            })

        return self.stats

    def sync_all_sites(self) -> Dict[str, Any]:
        """
        Sincronizar todos los sitios disponibles

        Returns:
            Diccionario con estadísticas globales
        """
        logger.info(f"\n{'='*60}")
        logger.info("SINCRONIZACIÓN MASIVA - TODOS LOS SITIOS")
        logger.info(f"{'='*60}\n")

        stats_global = {
            'sitios_procesados': 0,
            'sitios_exitosos': 0,
            'sitios_con_errores': 0,
            'stats_por_sitio': {}
        }

        # Obtener lista de sitios desde exports/
        sitios = self._get_available_sites()

        if not sitios:
            logger.warning("No se encontraron sitios para sincronizar")
            return stats_global

        logger.info(f"Sitios encontrados: {len(sitios)}")
        logger.info(f"Sitios: {', '.join(sitios)}\n")

        # Procesar cada sitio
        for i, site_id in enumerate(sitios, 1):
            logger.info(f"\n[{i}/{len(sitios)}] Procesando sitio: {site_id}")
            logger.info("-" * 60)

            try:
                stats_sitio = self.sync_site(site_id)
                stats_global['sitios_procesados'] += 1

                if not stats_sitio['errores']:
                    stats_global['sitios_exitosos'] += 1
                else:
                    stats_global['sitios_con_errores'] += 1

                stats_global['stats_por_sitio'][site_id] = stats_sitio

            except Exception as e:
                logger.error(f"Error procesando sitio {site_id}: {e}")
                stats_global['sitios_con_errores'] += 1
                stats_global['stats_por_sitio'][site_id] = {'errores': [str(e)]}

        # Resumen final
        logger.info(f"\n{'='*60}")
        logger.info("RESUMEN DE SINCRONIZACIÓN MASIVA")
        logger.info(f"{'='*60}")
        logger.info(f"Sitios procesados: {stats_global['sitios_procesados']}")
        logger.info(f"Sitios exitosos: {stats_global['sitios_exitosos']}")
        logger.info(f"Sitios con errores: {stats_global['sitios_con_errores']}")

        return stats_global

    def _get_available_sites(self) -> List[str]:
        """Obtener lista de sitios disponibles en exports/"""
        sitios = []

        if self.exports_dir.exists():
            for site_dir in self.exports_dir.iterdir():
                if site_dir.is_dir():
                    sitios.append(site_dir.name)

        return sorted(sitios)

    def _read_site_data(
        self,
        site_id: str,
        session_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Leer datos del sitio desde exports y/o normalized

        Args:
            site_id: ID del sitio
            session_timestamp: Timestamp de sesión (opcional)

        Returns:
            Lista de documentos con metadata completa
        """
        documentos = []

        # Opción 1: Leer desde exports CSV (más reciente)
        documentos_csv = self._read_from_exports(site_id, session_timestamp)
        if documentos_csv:
            logger.info(f"Leídos {len(documentos_csv)} documentos desde exports CSV")
            documentos.extend(documentos_csv)

        # Opción 2: Leer desde normalized JSON (completo)
        if not documentos:
            documentos_json = self._read_from_normalized(site_id)
            if documentos_json:
                logger.info(f"Leídos {len(documentos_json)} documentos desde normalized JSON")
                documentos.extend(documentos_json)

        return documentos

    def _read_from_exports(
        self,
        site_id: str,
        session_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Leer documentos desde exports CSV"""
        site_exports = self.exports_dir / site_id

        if not site_exports.exists():
            return []

        # Buscar sesión más reciente o específica
        sesiones = sorted(site_exports.iterdir(), key=lambda x: x.name, reverse=True)

        if session_timestamp:
            # Buscar sesión específica
            sesiones = [s for s in sesiones if s.name == session_timestamp]

        if not sesiones:
            return []

        session_dir = sesiones[0]
        csv_docs_path = session_dir / "documentos.csv"
        csv_arts_path = session_dir / "articulos.csv"

        if not csv_docs_path.exists():
            return []

        documentos = []

        # Leer documentos
        with open(csv_docs_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            docs_dict = {row['id_documento']: row for row in reader}

        # Leer artículos
        articulos_por_doc = {}
        if csv_arts_path.exists():
            with open(csv_arts_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    id_doc = row['id_documento']
                    if id_doc not in articulos_por_doc:
                        articulos_por_doc[id_doc] = []
                    articulos_por_doc[id_doc].append(row)

        # Combinar documentos con artículos
        for id_doc, doc_row in docs_dict.items():
            doc_data = self._map_csv_to_document(doc_row)
            doc_data['articulos'] = articulos_por_doc.get(id_doc, [])
            documentos.append(doc_data)

        return documentos

    def _read_from_normalized(self, site_id: str) -> List[Dict[str, Any]]:
        """Leer documentos desde normalized JSON"""
        json_dir = self.normalized_dir / site_id / "json"

        if not json_dir.exists():
            return []

        documentos = []

        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documentos.append(doc_data)
            except Exception as e:
                logger.error(f"Error leyendo {json_file}: {e}")

        return documentos

    def _map_csv_to_document(self, csv_row: Dict[str, str]) -> Dict[str, Any]:
        """Mapear fila CSV a documento con metadata completa"""
        return {
            'id_documento': csv_row['id_documento'],
            'site': csv_row['site'],
            'tipo_documento': csv_row['tipo_documento'],
            'numero_norma': csv_row.get('numero_norma') or None,
            'fecha': csv_row.get('fecha') or None,
            'titulo': csv_row.get('titulo') or None,
            'sumilla': csv_row.get('sumilla') or None,
            'url_origen': csv_row.get('url_origen') or None,
            'ruta_pdf': csv_row.get('ruta_pdf') or None,
            'ruta_txt': csv_row.get('ruta_txt') or None,
            'ruta_json': csv_row.get('ruta_json') or None,
            'hash_contenido': csv_row.get('hash_contenido') or None,
            'fecha_scraping': csv_row.get('fecha_scraping') or None,
            'metadata': {
                'tipo_norma': csv_row.get('tipo_norma'),
                'jerarquia': int(csv_row['jerarquia']) if csv_row.get('jerarquia') else 99,
                'area_principal': csv_row.get('area_principal', 'otros'),
                'areas_derecho': csv_row.get('areas_derecho', '').split(',') if csv_row.get('areas_derecho') else [],
                'estado_vigencia': csv_row.get('estado_vigencia', 'vigente'),
                'entidad_emisora': csv_row.get('entidad_emisora') or None,
                'palabras_clave': [],
                'modifica_normas': [],
                'deroga_normas': []
            },
            'total_articulos': int(csv_row.get('total_articulos', 0)),
            'articulos': []
        }

    def _sync_source(self, site_id: str) -> None:
        """Sincronizar source (sitio)"""
        try:
            # Verificar si existe
            response = self.supabase.table('sources').select('*').eq('source_id', site_id).execute()

            source_data = {
                'source_id': site_id,
                'nombre': self._get_site_nombre(site_id),
                'tipo': self._get_site_tipo(site_id),
                'categoria': self._get_site_categoria(site_id),
                'activo': True,
                'updated_at': datetime.now().isoformat()
            }

            if response.data:
                # Actualizar
                self.supabase.table('sources').update(source_data).eq('source_id', site_id).execute()
                self.stats['sources_actualizados'] += 1
                logger.debug(f"Source actualizado: {site_id}")
            else:
                # Insertar
                self.supabase.table('sources').insert(source_data).execute()
                self.stats['sources_insertados'] += 1
                logger.debug(f"Source insertado: {site_id}")

        except Exception as e:
            logger.error(f"Error sincronizando source {site_id}: {e}")
            self.stats['errores'].append({
                'tipo': 'source',
                'id': site_id,
                'mensaje': str(e)
            })

    def _sync_document(self, doc_data: Dict[str, Any]) -> None:
        """Sincronizar documento con metadata extendida"""
        id_documento = doc_data['id_documento']

        try:
            # Verificar si existe (por hash)
            hash_contenido = doc_data.get('hash_contenido')

            if hash_contenido:
                response = self.supabase.table('documents')\
                    .select('id_documento, hash_contenido')\
                    .eq('id_documento', id_documento)\
                    .execute()

                # Si existe y el hash es igual, skip
                if response.data and response.data[0].get('hash_contenido') == hash_contenido:
                    logger.debug(f"Documento sin cambios (mismo hash): {id_documento}")
                    return

            # Mapear a schema de Supabase
            document_row = self._map_to_supabase_document(doc_data)

            # Insertar o actualizar
            if response.data:
                self.supabase.table('documents').update(document_row).eq('id_documento', id_documento).execute()
                self.stats['documents_actualizados'] += 1
                logger.debug(f"Documento actualizado: {id_documento}")
            else:
                self.supabase.table('documents').insert(document_row).execute()
                self.stats['documents_insertados'] += 1
                logger.debug(f"Documento insertado: {id_documento}")

            # Sincronizar artículos
            if doc_data.get('articulos'):
                self._sync_articles(doc_data['articulos'], id_documento)

        except Exception as e:
            logger.error(f"Error sincronizando documento {id_documento}: {e}")
            self.stats['errores'].append({
                'tipo': 'document',
                'id': id_documento,
                'mensaje': str(e)
            })

    def _map_to_supabase_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mapear documento a schema de Supabase"""
        metadata = doc_data.get('metadata', {})

        # Extraer arrays
        areas_derecho = metadata.get('areas_derecho', [])
        if isinstance(areas_derecho, str):
            areas_derecho = [a.strip() for a in areas_derecho.split(',') if a.strip()]

        palabras_clave = metadata.get('palabras_clave', [])
        modifica_normas = metadata.get('modifica_normas', [])
        deroga_normas = metadata.get('deroga_normas', [])

        return {
            'id_documento': doc_data['id_documento'],
            'source_id': doc_data.get('site'),
            'tipo_documento': doc_data.get('tipo_documento'),
            'numero_norma': doc_data.get('numero_norma'),
            'fecha': doc_data.get('fecha'),
            'fecha_publicacion': doc_data.get('fecha_publicacion'),
            'titulo': doc_data.get('titulo'),
            'sumilla': doc_data.get('sumilla'),
            'url_origen': doc_data.get('url_origen'),
            # Metadata extendida
            'tipo_norma': metadata.get('tipo_norma'),
            'jerarquia': metadata.get('jerarquia', 99),
            'area_principal': metadata.get('area_principal', 'otros'),
            'areas_derecho': areas_derecho,
            'estado_vigencia': metadata.get('estado_vigencia', 'vigente'),
            'entidad_emisora': metadata.get('entidad_emisora'),
            'palabras_clave': palabras_clave,
            'modifica_normas': modifica_normas,
            'deroga_normas': deroga_normas,
            # Archivos
            'ruta_pdf': doc_data.get('ruta_pdf'),
            'ruta_txt': doc_data.get('ruta_txt'),
            'ruta_json': doc_data.get('ruta_json'),
            # Control
            'hash_contenido': doc_data.get('hash_contenido'),
            'fecha_scraping': doc_data.get('fecha_scraping'),
            'fecha_ultima_actualizacion': datetime.now().isoformat(),
            # Estadísticas
            'total_articulos': doc_data.get('total_articulos', len(doc_data.get('articulos', []))),
            'total_caracteres': metadata.get('estadisticas', {}).get('total_caracteres', 0),
            'total_palabras': metadata.get('estadisticas', {}).get('total_palabras', 0),
            'paginas_estimadas': metadata.get('estadisticas', {}).get('estimado_paginas', 0),
            # Metadata adicional (JSON)
            'metadata': metadata
        }

    def _sync_articles(self, articulos: List[Dict[str, Any]], id_documento: str) -> None:
        """Sincronizar artículos de un documento"""
        # Eliminar artículos anteriores
        try:
            self.supabase.table('articles').delete().eq('id_documento', id_documento).execute()
        except:
            pass  # Puede que no existan

        # Insertar artículos
        for i, articulo in enumerate(articulos):
            try:
                article_row = {
                    'id_articulo': articulo.get('id_articulo', f"{id_documento}_art_{i+1}"),
                    'id_documento': id_documento,
                    'numero': articulo.get('numero'),
                    'titulo': articulo.get('titulo'),
                    'contenido': articulo.get('contenido', articulo.get('contenido_preview', '')),
                    'tipo_unidad': articulo.get('tipo_unidad', 'articulo'),
                    'orden': i + 1,
                    'metadata': articulo.get('metadata', {})
                }

                self.supabase.table('articles').insert(article_row).execute()
                self.stats['articles_insertados'] += 1

            except Exception as e:
                logger.error(f"Error sincronizando artículo {i+1} de {id_documento}: {e}")

    def _sync_extraction_log(self, site_id: str, session_timestamp: Optional[str]) -> None:
        """Registrar log de extracción"""
        try:
            log_data = {
                'source_id': site_id,
                'session_id': session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S"),
                'modo': 'full',
                'exito': len(self.stats['errores']) == 0,
                'total_encontrados': self.stats['documents_insertados'] + self.stats['documents_actualizados'],
                'total_descargados': self.stats['documents_insertados'] + self.stats['documents_actualizados'],
                'total_parseados': self.stats['documents_insertados'] + self.stats['documents_actualizados'],
                'total_errores': len(self.stats['errores']),
                'errores': self.stats['errores'] if self.stats['errores'] else None,
                'created_at': datetime.now().isoformat()
            }

            self.supabase.table('extraction_logs').insert(log_data).execute()
            self.stats['extraction_logs_insertados'] += 1

        except Exception as e:
            logger.error(f"Error registrando extraction_log: {e}")

    def _print_stats(self) -> None:
        """Imprimir estadísticas de sincronización"""
        logger.info(f"\n{'='*60}")
        logger.info("ESTADÍSTICAS DE SINCRONIZACIÓN")
        logger.info(f"{'='*60}")
        logger.info(f"Sources insertados: {self.stats['sources_insertados']}")
        logger.info(f"Sources actualizados: {self.stats['sources_actualizados']}")
        logger.info(f"Documents insertados: {self.stats['documents_insertados']}")
        logger.info(f"Documents actualizados: {self.stats['documents_actualizados']}")
        logger.info(f"Articles insertados: {self.stats['articles_insertados']}")
        logger.info(f"Extraction logs: {self.stats['extraction_logs_insertados']}")
        logger.info(f"Errores: {len(self.stats['errores'])}")
        logger.info(f"{'='*60}\n")

    # Métodos auxiliares para obtener información de sitios
    def _get_site_nombre(self, site_id: str) -> str:
        """Obtener nombre del sitio"""
        nombres = {
            'tcp': 'Tribunal Constitucional Plurinacional',
            'tsj': 'Tribunal Supremo de Justicia',
            'asfi': 'Autoridad de Supervisión del Sistema Financiero',
            'sin': 'Servicio de Impuestos Nacionales',
            'contraloria': 'Contraloría General del Estado'
        }
        return nombres.get(site_id, site_id.upper())

    def _get_site_tipo(self, site_id: str) -> str:
        """Obtener tipo del sitio"""
        tipos = {
            'tcp': 'Tribunal',
            'tsj': 'Tribunal',
            'asfi': 'Entidad Reguladora',
            'sin': 'Entidad Reguladora',
            'contraloria': 'Órgano de Control'
        }
        return tipos.get(site_id, 'Entidad Pública')

    def _get_site_categoria(self, site_id: str) -> str:
        """Obtener categoría del sitio"""
        categorias = {
            'tcp': 'Judicial',
            'tsj': 'Judicial',
            'asfi': 'Financiero',
            'sin': 'Tributario',
            'contraloria': 'Control'
        }
        return categorias.get(site_id, 'General')
