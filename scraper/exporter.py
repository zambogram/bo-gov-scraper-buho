"""
Sistema de exportación simultánea mientras se procesa
Exporta a CSV, Excel, Base de datos, etc.
"""
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from scraper.models import Documento, Articulo

logger = logging.getLogger(__name__)


class DataExporter:
    """Exportador de datos procesados"""

    def __init__(self, export_dir: Path):
        """
        Inicializar exportador

        Args:
            export_dir: Directorio base para exportaciones
        """
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de exportación continua
        self.csv_documentos = None
        self.csv_articulos = None
        self.registro_historico = None

    def iniciar_sesion_exportacion(self, site_id: str, timestamp: str) -> None:
        """
        Iniciar sesión de exportación para un sitio

        Args:
            site_id: ID del sitio
            timestamp: Timestamp de la sesión
        """
        # Crear directorio para esta sesión
        session_dir = self.export_dir / site_id / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)

        # Archivo CSV para documentos
        csv_docs_path = session_dir / "documentos.csv"
        self.csv_documentos = open(csv_docs_path, 'w', encoding='utf-8', newline='')
        self.csv_docs_writer = csv.DictWriter(
            self.csv_documentos,
            fieldnames=[
                'id_documento', 'site', 'tipo_documento', 'numero_norma',
                'fecha', 'titulo', 'area_principal', 'areas_derecho',
                'jerarquia', 'estado_vigencia', 'entidad_emisora',
                'total_articulos', 'ruta_pdf', 'ruta_txt', 'ruta_json',
                'hash_contenido', 'fecha_scraping'
            ]
        )
        self.csv_docs_writer.writeheader()

        # Archivo CSV para artículos
        csv_arts_path = session_dir / "articulos.csv"
        self.csv_articulos = open(csv_arts_path, 'w', encoding='utf-8', newline='')
        self.csv_arts_writer = csv.DictWriter(
            self.csv_articulos,
            fieldnames=[
                'id_articulo', 'id_documento', 'numero', 'titulo',
                'tipo_unidad', 'contenido_preview'
            ]
        )
        self.csv_arts_writer.writeheader()

        # Archivo de registro histórico
        registro_path = session_dir / "registro_historico.jsonl"
        self.registro_historico = open(registro_path, 'w', encoding='utf-8')

        logger.info(f"✓ Sesión de exportación iniciada: {session_dir}")

    def exportar_documento(self, documento: Documento, metadata_extendida: Dict[str, Any]) -> None:
        """
        Exportar un documento procesado

        Args:
            documento: Documento procesado
            metadata_extendida: Metadata extendida del documento
        """
        if not self.csv_documentos:
            logger.warning("Sesión de exportación no iniciada")
            return

        try:
            # Exportar a CSV documentos
            row_doc = {
                'id_documento': documento.id_documento,
                'site': documento.site,
                'tipo_documento': documento.tipo_documento,
                'numero_norma': documento.numero_norma or metadata_extendida.get('numero_norma'),
                'fecha': documento.fecha or metadata_extendida.get('fecha_promulgacion'),
                'titulo': documento.titulo,
                'area_principal': metadata_extendida.get('area_principal', 'otros'),
                'areas_derecho': ','.join(metadata_extendida.get('areas_derecho', [])),
                'jerarquia': metadata_extendida.get('jerarquia', 99),
                'estado_vigencia': metadata_extendida.get('estado_vigencia', 'vigente'),
                'entidad_emisora': metadata_extendida.get('entidad_emisora', ''),
                'total_articulos': len(documento.articulos),
                'ruta_pdf': documento.ruta_pdf or '',
                'ruta_txt': documento.ruta_txt or '',
                'ruta_json': documento.ruta_json or '',
                'hash_contenido': documento.hash_contenido,
                'fecha_scraping': documento.fecha_scraping
            }
            self.csv_docs_writer.writerow(row_doc)

            # Exportar artículos a CSV
            for articulo in documento.articulos:
                row_art = {
                    'id_articulo': articulo.id_articulo,
                    'id_documento': articulo.id_documento,
                    'numero': articulo.numero or '',
                    'titulo': articulo.titulo or '',
                    'tipo_unidad': articulo.tipo_unidad,
                    'contenido_preview': articulo.contenido[:200] if articulo.contenido else ''
                }
                self.csv_arts_writer.writerow(row_art)

            # Registro histórico (JSONL)
            registro_entry = {
                'timestamp': datetime.now().isoformat(),
                'id_documento': documento.id_documento,
                'tipo_documento': documento.tipo_documento,
                'numero_norma': row_doc['numero_norma'],
                'area_principal': row_doc['area_principal'],
                'jerarquia': row_doc['jerarquia'],
                'total_articulos': len(documento.articulos),
                'metadata_completa': metadata_extendida
            }
            self.registro_historico.write(json.dumps(registro_entry, ensure_ascii=False) + '\n')

            # Flush para asegurar escritura inmediata
            self.csv_documentos.flush()
            self.csv_articulos.flush()
            self.registro_historico.flush()

        except Exception as e:
            logger.error(f"Error exportando documento {documento.id_documento}: {e}")

    def finalizar_sesion_exportacion(self) -> Dict[str, str]:
        """
        Finalizar sesión de exportación

        Returns:
            Diccionario con rutas de archivos exportados
        """
        rutas = {}

        if self.csv_documentos:
            rutas['csv_documentos'] = self.csv_documentos.name
            self.csv_documentos.close()
            self.csv_documentos = None

        if self.csv_articulos:
            rutas['csv_articulos'] = self.csv_articulos.name
            self.csv_articulos.close()
            self.csv_articulos = None

        if self.registro_historico:
            rutas['registro_historico'] = self.registro_historico.name
            self.registro_historico.close()
            self.registro_historico = None

        logger.info(f"✓ Sesión de exportación finalizada")
        return rutas

    def generar_reporte_completo(
        self,
        site_id: str,
        timestamp: str,
        estadisticas: Dict[str, Any]
    ) -> Path:
        """
        Generar reporte completo de la sesión de scraping

        Args:
            site_id: ID del sitio
            timestamp: Timestamp de la sesión
            estadisticas: Estadísticas de la sesión

        Returns:
            Path del archivo de reporte
        """
        session_dir = self.export_dir / site_id / timestamp
        reporte_path = session_dir / "reporte_scraping.json"

        reporte = {
            'site_id': site_id,
            'timestamp': timestamp,
            'fecha_generacion': datetime.now().isoformat(),
            'estadisticas': estadisticas,
            'archivos_generados': {
                'csv_documentos': str(session_dir / "documentos.csv"),
                'csv_articulos': str(session_dir / "articulos.csv"),
                'registro_historico': str(session_dir / "registro_historico.jsonl"),
                'reporte': str(reporte_path)
            }
        }

        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Reporte completo generado: {reporte_path}")
        return reporte_path


class HistoricalTracker:
    """Tracker de progreso histórico de scraping"""

    def __init__(self, tracker_file: Path):
        """
        Inicializar tracker

        Args:
            tracker_file: Archivo de tracking histórico
        """
        self.tracker_file = tracker_file
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_tracker()

    def _load_tracker(self) -> Dict[str, Any]:
        """Cargar datos de tracking"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            'inicio_proyecto': datetime.now().isoformat(),
            'sitios': {},
            'estadisticas_globales': {
                'total_documentos': 0,
                'total_articulos': 0,
                'total_sesiones': 0
            }
        }

    def registrar_sesion(
        self,
        site_id: str,
        resultado: 'PipelineResult',
        metadata_agregada: Dict[str, List[str]]
    ) -> None:
        """
        Registrar sesión de scraping

        Args:
            site_id: ID del sitio
            resultado: Resultado del pipeline
            metadata_agregada: Metadata agregada (áreas, tipos, etc.)
        """
        if site_id not in self.data['sitios']:
            self.data['sitios'][site_id] = {
                'primera_sesion': datetime.now().isoformat(),
                'ultima_sesion': None,
                'total_sesiones': 0,
                'total_documentos': 0,
                'total_articulos': 0,
                'sesiones': []
            }

        site_data = self.data['sitios'][site_id]

        # Registrar sesión
        sesion = {
            'timestamp': datetime.now().isoformat(),
            'modo': resultado.modo,
            'total_encontrados': resultado.total_encontrados,
            'total_descargados': resultado.total_descargados,
            'total_parseados': resultado.total_parseados,
            'total_errores': resultado.total_errores,
            'duracion_segundos': resultado.duracion_segundos,
            'areas_procesadas': metadata_agregada.get('areas', []),
            'tipos_documento': metadata_agregada.get('tipos', [])
        }

        site_data['sesiones'].append(sesion)
        site_data['ultima_sesion'] = sesion['timestamp']
        site_data['total_sesiones'] += 1
        site_data['total_documentos'] += resultado.total_parseados
        site_data['total_articulos'] += sum(
            1 for _ in range(resultado.total_parseados)
        )  # Aproximado

        # Actualizar estadísticas globales
        self.data['estadisticas_globales']['total_documentos'] += resultado.total_parseados
        self.data['estadisticas_globales']['total_sesiones'] += 1

        # Guardar
        self._save_tracker()

        logger.info(f"✓ Sesión registrada en tracking histórico")

    def _save_tracker(self) -> None:
        """Guardar datos de tracking"""
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_progreso_historico(self, site_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener progreso histórico

        Args:
            site_id: ID del sitio (None para global)

        Returns:
            Diccionario con progreso
        """
        if site_id:
            return self.data['sitios'].get(site_id, {})
        else:
            return self.data
