"""
Pipeline central de scraping → procesamiento → guardado local
"""
import json
import logging
from pathlib import Path
from typing import Optional, Callable, Literal, Dict, Any, List
from datetime import datetime
import tempfile
import shutil

from config import get_site_config, settings
from scraper.models import Documento, PipelineResult
from scraper.sites import get_scraper
from scraper.extractors import PDFExtractor
from scraper.parsers import LegalParser
from scraper.metadata_extractor import LegalMetadataExtractor
from scraper.exporter import DataExporter, HistoricalTracker

logger = logging.getLogger(__name__)


class IndexManager:
    """Gestor de índices para delta updates"""

    def __init__(self, index_path: Path):
        """
        Inicializar gestor de índices

        Args:
            index_path: Ruta al archivo de índice
        """
        self.index_path = index_path
        self.index_data = self._cargar_indice()

    def _cargar_indice(self) -> Dict[str, Any]:
        """Cargar índice desde archivo"""
        if not self.index_path.exists():
            return {
                'documentos': {},
                'last_update': None,
                'total_documentos': 0
            }

        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando índice: {e}")
            return {
                'documentos': {},
                'last_update': None,
                'total_documentos': 0
            }

    def guardar_indice(self) -> None:
        """Guardar índice a archivo"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index_data, f, ensure_ascii=False, indent=2)

    def documento_existe(self, id_documento: str) -> bool:
        """Verificar si un documento ya existe en el índice"""
        return id_documento in self.index_data['documentos']

    def documento_cambio(self, id_documento: str, hash_nuevo: str) -> bool:
        """
        Verificar si un documento cambió

        Returns:
            True si cambió o es nuevo
        """
        if not self.documento_existe(id_documento):
            return True

        hash_anterior = self.index_data['documentos'][id_documento].get('hash')
        return hash_anterior != hash_nuevo

    def actualizar_documento(self, documento: Documento) -> None:
        """Actualizar entrada de documento en índice"""
        self.index_data['documentos'][documento.id_documento] = {
            'hash': documento.hash_contenido,
            'fecha_actualizacion': documento.fecha_ultima_actualizacion,
            'ruta_pdf': str(documento.ruta_pdf) if documento.ruta_pdf else None,
            'ruta_txt': str(documento.ruta_txt) if documento.ruta_txt else None,
            'ruta_json': str(documento.ruta_json) if documento.ruta_json else None,
        }

        self.index_data['last_update'] = datetime.now().isoformat()
        self.index_data['total_documentos'] = len(self.index_data['documentos'])

    def get_documentos(self) -> List[Dict[str, Any]]:
        """Obtener lista de documentos en el índice"""
        return [
            {'id': id_doc, **data}
            for id_doc, data in self.index_data['documentos'].items()
        ]


def run_site_pipeline(
    site_id: str,
    mode: Literal["full", "delta"] = "delta",
    limit: Optional[int] = None,
    save_pdf: bool = False,
    save_txt: bool = True,
    save_json: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> PipelineResult:
    """
    Ejecutar pipeline completo para un sitio

    Args:
        site_id: ID del sitio (tcp, tsj, asfi, sin, contraloria)
        mode: Modo de scraping ("full" o "delta")
        limit: Límite de documentos a procesar
        save_pdf: Si guardar PDFs originales
        save_txt: Si guardar texto normalizado
        save_json: Si guardar JSON con artículos
        progress_callback: Función a llamar con mensajes de progreso

    Returns:
        PipelineResult con estadísticas y resultados
    """
    # Inicializar resultado
    result = PipelineResult(site_id=site_id, modo=mode)

    def _log(mensaje: str):
        """Log y callback de progreso"""
        logger.info(mensaje)
        result.agregar_mensaje(mensaje)
        if progress_callback:
            progress_callback(mensaje)

    try:
        # Obtener configuración del sitio
        site_config = get_site_config(site_id)
        if not site_config:
            raise ValueError(f"Sitio no encontrado: {site_id}")

        if not site_config.activo:
            raise ValueError(f"Sitio inactivo: {site_id}")

        _log(f"🚀 Iniciando pipeline para {site_config.nombre}")
        _log(f"   Modo: {mode}, Límite: {limit or 'sin límite'}")
        _log(f"   Guardar - PDF: {save_pdf}, TXT: {save_txt}, JSON: {save_json}")

        # Asegurar directorios
        site_config.ensure_directories()

        # Inicializar componentes
        scraper = get_scraper(site_id)
        extractor = PDFExtractor(usar_ocr=site_config.metadatos.get('requiere_ocr', False))
        parser = LegalParser()
        metadata_extractor = LegalMetadataExtractor()
        index_manager = IndexManager(site_config.index_file)

        # Inicializar exportador
        export_dir = settings.exports_dir
        exporter = DataExporter(export_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exporter.iniciar_sesion_exportacion(site_id, timestamp)

        # Tracker histórico
        tracker_file = settings.data_base_dir / "tracking_historico.json"
        tracker = HistoricalTracker(tracker_file)

        # Tracking de metadata agregada
        metadata_agregada = {
            'areas': [],
            'tipos': [],
            'jerarquias': []
        }

        _log(f"✓ Componentes inicializados (incluye exportación y metadata extendida)")

        # Listar documentos disponibles
        if mode == "full":
            _log(f"📋 Listando documentos disponibles (modo histórico completo)...")
            documentos_metadata = scraper.listar_documentos_historico_completo(
                limite_total=limit,
                progress_callback=_log
            )
        else:
            _log(f"📋 Listando documentos disponibles (modo delta)...")
            documentos_metadata = scraper.listar_documentos(
                limite=limit,
                modo="delta",
                pagina=1
            )

        result.total_encontrados = len(documentos_metadata)
        _log(f"✓ Encontrados {result.total_encontrados} documentos")

        # Procesar cada documento
        for idx, doc_meta in enumerate(documentos_metadata, 1):
            try:
                id_doc = doc_meta.get('id_documento', f"doc_{idx}")
                _log(f"\n📄 [{idx}/{result.total_encontrados}] Procesando: {id_doc}")

                # Crear objeto Documento
                documento = scraper.crear_documento_desde_metadata(doc_meta)

                # Verificar si ya existe (modo delta)
                if mode == "delta" and index_manager.documento_existe(id_doc):
                    _log(f"⊙ Documento ya existe, saltando: {id_doc}")
                    continue

                # === PASO 1: Descargar PDF ===
                pdf_path = None
                usar_temp = not save_pdf

                if usar_temp:
                    # Usar archivo temporal
                    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                    pdf_path = Path(temp_file.name)
                else:
                    # Guardar en data/raw
                    pdf_path = site_config.raw_pdf_dir / f"{id_doc}.pdf"

                _log(f"  ⬇ Descargando PDF...")
                url_pdf = doc_meta.get('url', '')
                if scraper.descargar_pdf(url_pdf, pdf_path):
                    result.total_descargados += 1
                    if save_pdf:
                        documento.ruta_pdf = str(pdf_path)
                    _log(f"  ✓ PDF descargado")
                else:
                    result.agregar_error(f"Error descargando PDF: {id_doc}", url_pdf)
                    continue

                # === PASO 2: Extraer texto ===
                _log(f"  📝 Extrayendo texto...")
                try:
                    texto = extractor.extraer_texto(pdf_path)

                    if save_txt:
                        txt_path = site_config.normalized_text_dir / f"{id_doc}.txt"
                        extractor.guardar_texto(texto, txt_path)
                        documento.ruta_txt = str(txt_path)
                        _log(f"  ✓ Texto guardado ({len(texto)} caracteres)")

                    documento.texto_completo = texto

                except Exception as e:
                    result.agregar_error(f"Error extrayendo texto: {id_doc}", str(e))
                    if usar_temp and pdf_path and pdf_path.exists():
                        pdf_path.unlink()
                    continue

                # === PASO 3: Parsear y dividir en artículos ===
                _log(f"  🔍 Parseando artículos...")
                try:
                    # Parsear con contexto site-aware (tipo de documento y sitio)
                    articulos = parser.parsear_documento(
                        id_doc,
                        texto,
                        tipo_documento=documento.tipo_documento,
                        site_id=site_id
                    )
                    documento.articulos = articulos
                    _log(f"  ✓ Parseados {len(articulos)} artículos/secciones")

                except Exception as e:
                    result.agregar_error(f"Error parseando: {id_doc}", str(e))
                    # Continuar sin artículos

                # === PASO 3.5: Extraer metadata extendida ===
                _log(f"  📊 Extrayendo metadata extendida...")
                try:
                    metadata_ext = metadata_extractor.extraer_metadata_completa(
                        texto=texto,
                        titulo=documento.titulo,
                        tipo_documento=documento.tipo_documento,
                        sumilla=documento.sumilla
                    )

                    # Agregar metadata al documento
                    documento.metadata.update(metadata_ext)

                    # Extraer metadata SITE-AWARE específica del sitio
                    metadata_sitio = metadata_extractor.extraer_metadata_sitio_especifico(
                        site_id=site_id,
                        texto=texto,
                        titulo=documento.titulo,
                        documento_base=documento.metadata
                    )
                    documento.metadata.update(metadata_sitio)

                    # Tracking para reporte
                    if metadata_ext.get('area_principal'):
                        metadata_agregada['areas'].append(metadata_ext['area_principal'])
                    if metadata_ext.get('tipo_norma'):
                        metadata_agregada['tipos'].append(metadata_ext['tipo_norma'])
                    if metadata_ext.get('jerarquia'):
                        metadata_agregada['jerarquias'].append(metadata_ext['jerarquia'])

                    _log(f"  ✓ Metadata: Área={metadata_ext.get('area_principal', 'N/A')}, "
                         f"Tipo={metadata_ext.get('tipo_norma', 'N/A')}, "
                         f"Jerarquía={metadata_ext.get('jerarquia', 'N/A')}")

                except Exception as e:
                    result.agregar_error(f"Error extrayendo metadata: {id_doc}", str(e))
                    metadata_ext = {}

                # === PASO 4: Guardar JSON ===
                if save_json:
                    _log(f"  💾 Guardando JSON...")
                    try:
                        json_path = site_config.normalized_json_dir / f"{id_doc}.json"
                        documento.ruta_json = str(json_path)
                        documento.actualizar_hash()
                        documento.guardar_json(json_path)
                        _log(f"  ✓ JSON guardado")

                    except Exception as e:
                        result.agregar_error(f"Error guardando JSON: {id_doc}", str(e))

                # === PASO 5: Exportar documento ===
                _log(f"  📤 Exportando datos...")
                try:
                    exporter.exportar_documento(documento, metadata_ext)
                    _log(f"  ✓ Documento exportado")
                except Exception as e:
                    result.agregar_error(f"Error exportando: {id_doc}", str(e))

                # === PASO 6: Actualizar índice ===
                documento.actualizar_hash()
                index_manager.actualizar_documento(documento)
                result.total_parseados += 1
                result.documentos_procesados.append(id_doc)

                _log(f"✅ Documento completado: {id_doc}")

                # Limpiar PDF temporal si corresponde
                if usar_temp and pdf_path and pdf_path.exists():
                    pdf_path.unlink()

            except Exception as e:
                result.agregar_error(f"Error procesando documento {idx}", str(e))
                logger.exception(e)
                continue

        # Guardar índice actualizado
        _log(f"\n💾 Guardando índice...")
        index_manager.guardar_indice()

        # Finalizar exportación
        _log(f"📤 Finalizando exportación...")
        rutas_exportadas = exporter.finalizar_sesion_exportacion()

        # Generar reporte completo
        estadisticas_reporte = {
            'total_encontrados': result.total_encontrados,
            'total_descargados': result.total_descargados,
            'total_parseados': result.total_parseados,
            'total_errores': result.total_errores,
            'duracion_segundos': result.duracion_segundos,
            'areas_procesadas': metadata_agregada['areas'],
            'tipos_procesados': metadata_agregada['tipos'],
            'jerarquias': metadata_agregada['jerarquias']
        }
        reporte_path = exporter.generar_reporte_completo(site_id, timestamp, estadisticas_reporte)

        # Registrar en tracker histórico
        tracker.registrar_sesion(site_id, result, metadata_agregada)

        # Finalizar
        result.finalizar()

        _log(f"\n✅ Pipeline completado")
        _log(f"   Total encontrados: {result.total_encontrados}")
        _log(f"   Total descargados: {result.total_descargados}")
        _log(f"   Total parseados: {result.total_parseados}")
        _log(f"   Total errores: {result.total_errores}")
        _log(f"   Duración: {result.duracion_segundos:.2f}s")
        _log(f"\n📁 Exportaciones:")
        for nombre, ruta in rutas_exportadas.items():
            _log(f"   {nombre}: {ruta}")
        _log(f"📊 Reporte: {reporte_path}")

        return result

    except Exception as e:
        result.agregar_error("Error fatal en pipeline", str(e))
        result.finalizar()
        logger.exception(e)
        return result


def run_all_sites_pipeline(
    mode: Literal["full", "delta"] = "delta",
    limit: Optional[int] = None,
    save_pdf: bool = False,
    save_txt: bool = True,
    save_json: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, PipelineResult]:
    """
    Ejecutar pipeline para todos los sitios activos

    Args:
        mode: Modo de scraping
        limit: Límite de documentos por sitio
        save_pdf: Si guardar PDFs
        save_txt: Si guardar TXT
        save_json: Si guardar JSON
        progress_callback: Callback de progreso

    Returns:
        Diccionario con resultados por sitio
    """
    from config import list_active_sites

    results = {}
    sites = list_active_sites()

    logger.info(f"🚀 Ejecutando pipeline para {len(sites)} sitios")

    for site_config in sites:
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando sitio: {site_config.nombre}")
        logger.info(f"{'='*60}")

        try:
            result = run_site_pipeline(
                site_id=site_config.id,
                mode=mode,
                limit=limit,
                save_pdf=save_pdf,
                save_txt=save_txt,
                save_json=save_json,
                progress_callback=progress_callback
            )
            results[site_config.id] = result

        except Exception as e:
            logger.error(f"Error en sitio {site_config.id}: {e}")
            results[site_config.id] = PipelineResult(
                site_id=site_config.id,
                modo=mode
            )
            results[site_config.id].agregar_error("Error fatal", str(e))
            results[site_config.id].finalizar()

    return results
