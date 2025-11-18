"""
Exportador de datos a formato JSONL para Supabase
FASE 8 - Exportaciones Profesionales para BÚHO MLD

Este módulo procesa documentos extraídos y genera archivos JSONL
listos para importar en Supabase.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .utils import (
    limpiar_campos,
    generar_id_documento,
    generar_id_articulo,
    normalizar_tipo_norma,
    normalizar_fecha,
    normalizar_sitio,
    validar_documento,
    validar_articulo,
    extraer_numero_articulo
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseExporter:
    """
    Clase para exportar datos a formato JSONL para Supabase.
    """

    def __init__(self, data_dir: str = "data", export_dir: str = "exports"):
        """
        Inicializa el exportador.

        Args:
            data_dir: Directorio con los datos extraídos
            export_dir: Directorio donde guardar las exportaciones
        """
        self.data_dir = Path(data_dir)
        self.export_dir = Path(export_dir)

        # Crear directorio de exports si no existe
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Contadores
        self.stats = {
            'documentos_procesados': 0,
            'documentos_validos': 0,
            'documentos_invalidos': 0,
            'articulos_procesados': 0,
            'articulos_validos': 0,
            'articulos_invalidos': 0,
            'errores': []
        }

    def procesar_documento(self, data: Dict[str, Any], sitio: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Procesa un documento y lo convierte al formato Supabase.

        Args:
            data: Datos del documento
            sitio: Nombre del sitio fuente (si no está en data)

        Returns:
            Documento procesado o None si es inválido
        """
        try:
            # Extraer campos básicos
            sitio_doc = sitio or data.get('sitio') or data.get('source') or 'desconocido'
            sitio_doc = normalizar_sitio(sitio_doc)

            tipo_norma = normalizar_tipo_norma(data.get('tipo_norma') or data.get('tipo'))
            numero_norma = data.get('numero_norma') or data.get('numero')
            fecha_norma = normalizar_fecha(data.get('fecha_norma') or data.get('fecha'))

            # Generar ID del documento
            id_documento = data.get('id_documento')
            if not id_documento:
                id_documento = generar_id_documento(
                    sitio=sitio_doc,
                    tipo_norma=tipo_norma,
                    numero_norma=numero_norma,
                    fecha_norma=fecha_norma
                )

            # Construir documento para Supabase
            documento = {
                'id_documento': id_documento,
                'sitio': sitio_doc,
                'tipo_norma': tipo_norma,
                'numero_norma': str(numero_norma) if numero_norma else None,
                'fecha_norma': fecha_norma,
                'titulo': data.get('titulo') or data.get('title'),
                'url_fuente': data.get('url_fuente') or data.get('url') or data.get('source_url'),
                'url_pdf': data.get('url_pdf') or data.get('pdf_url'),
                'filename_pdf': data.get('filename_pdf') or data.get('pdf_filename'),
                'metodo_extraccion': data.get('metodo_extraccion') or data.get('extraction_method') or 'unknown',
                'paginas': data.get('paginas') or data.get('pages'),
                'caracteres': data.get('caracteres') or data.get('characters') or len(data.get('contenido', '')),
                'total_articulos': data.get('total_articulos') or len(data.get('articulos', [])),
                'fecha_extraccion': data.get('fecha_extraccion') or datetime.now().isoformat(),
                'estado': data.get('estado') or 'extraido',
                'raw_metadata': data.get('metadata') or {}
            }

            # Limpiar campos
            documento = limpiar_campos(documento)

            # Validar
            es_valido, error = validar_documento(documento)
            if not es_valido:
                logger.warning(f"Documento inválido: {error} - {id_documento}")
                self.stats['documentos_invalidos'] += 1
                self.stats['errores'].append({
                    'tipo': 'documento_invalido',
                    'id': id_documento,
                    'error': error
                })
                return None

            self.stats['documentos_validos'] += 1
            return documento

        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            self.stats['documentos_invalidos'] += 1
            self.stats['errores'].append({
                'tipo': 'error_procesamiento_documento',
                'error': str(e),
                'data': str(data)[:200]
            })
            return None

    def procesar_articulo(
        self,
        articulo: Dict[str, Any],
        id_documento: str,
        sitio: str,
        tipo_norma: Optional[str] = None,
        fecha_norma: Optional[str] = None,
        orden: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa un artículo y lo convierte al formato Supabase.

        Args:
            articulo: Datos del artículo
            id_documento: ID del documento padre
            sitio: Nombre del sitio fuente
            tipo_norma: Tipo de norma del documento
            fecha_norma: Fecha de la norma
            orden: Orden del artículo en el documento

        Returns:
            Artículo procesado o None si es inválido
        """
        try:
            # Extraer número de artículo
            numero_articulo = articulo.get('numero') or articulo.get('numero_articulo')
            if not numero_articulo and 'titulo' in articulo:
                numero_articulo = extraer_numero_articulo(articulo['titulo'])

            # Generar ID del artículo
            id_articulo = articulo.get('id_articulo')
            if not id_articulo:
                id_articulo = generar_id_articulo(
                    id_documento=id_documento,
                    numero_articulo=numero_articulo,
                    orden=orden
                )

            # Construir artículo para Supabase
            articulo_procesado = {
                'id_articulo': id_articulo,
                'id_documento': id_documento,
                'numero_articulo': str(numero_articulo) if numero_articulo else None,
                'titulo_articulo': articulo.get('titulo') or articulo.get('titulo_articulo'),
                'contenido': articulo.get('contenido') or articulo.get('texto') or articulo.get('content'),
                'tipo_norma': tipo_norma,
                'fecha_norma': fecha_norma,
                'sitio': normalizar_sitio(sitio),
                'orden': orden,
                'raw': articulo.get('raw') or articulo.get('texto_original')
            }

            # Limpiar campos
            articulo_procesado = limpiar_campos(articulo_procesado)

            # Validar
            es_valido, error = validar_articulo(articulo_procesado)
            if not es_valido:
                logger.warning(f"Artículo inválido: {error} - {id_articulo}")
                self.stats['articulos_invalidos'] += 1
                self.stats['errores'].append({
                    'tipo': 'articulo_invalido',
                    'id': id_articulo,
                    'error': error
                })
                return None

            self.stats['articulos_validos'] += 1
            return articulo_procesado

        except Exception as e:
            logger.error(f"Error procesando artículo: {str(e)}")
            self.stats['articulos_invalidos'] += 1
            self.stats['errores'].append({
                'tipo': 'error_procesamiento_articulo',
                'id_documento': id_documento,
                'error': str(e)
            })
            return None

    def procesar_archivo_json(self, filepath: Path, sitio: Optional[str] = None) -> tuple[List[Dict], List[Dict]]:
        """
        Procesa un archivo JSON con uno o múltiples documentos.

        Args:
            filepath: Ruta al archivo JSON
            sitio: Nombre del sitio fuente (opcional)

        Returns:
            Tupla (lista_documentos, lista_articulos)
        """
        documentos = []
        articulos = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determinar si es un documento único o una lista
            if isinstance(data, list):
                documentos_raw = data
            elif isinstance(data, dict):
                # Puede ser un documento único o contener una lista
                if 'documentos' in data:
                    documentos_raw = data['documentos']
                elif 'documents' in data:
                    documentos_raw = data['documents']
                else:
                    documentos_raw = [data]
            else:
                logger.warning(f"Formato no reconocido en {filepath}")
                return [], []

            # Procesar cada documento
            for doc_data in documentos_raw:
                self.stats['documentos_procesados'] += 1

                # Procesar documento
                documento = self.procesar_documento(doc_data, sitio)
                if not documento:
                    continue

                documentos.append(documento)

                # Procesar artículos
                articulos_raw = doc_data.get('articulos') or doc_data.get('articles') or []
                for idx, art_data in enumerate(articulos_raw):
                    self.stats['articulos_procesados'] += 1

                    articulo = self.procesar_articulo(
                        articulo=art_data,
                        id_documento=documento['id_documento'],
                        sitio=documento['sitio'],
                        tipo_norma=documento['tipo_norma'],
                        fecha_norma=documento['fecha_norma'],
                        orden=idx
                    )

                    if articulo:
                        articulos.append(articulo)

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON en {filepath}: {str(e)}")
            self.stats['errores'].append({
                'tipo': 'json_decode_error',
                'archivo': str(filepath),
                'error': str(e)
            })
        except Exception as e:
            logger.error(f"Error procesando archivo {filepath}: {str(e)}")
            self.stats['errores'].append({
                'tipo': 'error_procesamiento_archivo',
                'archivo': str(filepath),
                'error': str(e)
            })

        return documentos, articulos

    def export_documents_jsonl(self, documentos: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
        """
        Exporta documentos a formato JSONL.

        Args:
            documentos: Lista de documentos procesados
            output_file: Nombre del archivo de salida (opcional)

        Returns:
            Ruta al archivo generado
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"documents_supabase_{timestamp}.jsonl"

        output_path = self.export_dir / output_file

        # Eliminar duplicados por ID
        docs_unicos = {}
        for doc in documentos:
            id_doc = doc['id_documento']
            if id_doc not in docs_unicos:
                docs_unicos[id_doc] = doc
            else:
                logger.warning(f"Documento duplicado encontrado: {id_doc}")

        # Escribir JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in docs_unicos.values():
                json_line = json.dumps(doc, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(f"Exportados {len(docs_unicos)} documentos a {output_path}")
        return str(output_path)

    def export_articles_jsonl(self, articulos: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
        """
        Exporta artículos a formato JSONL.

        Args:
            articulos: Lista de artículos procesados
            output_file: Nombre del archivo de salida (opcional)

        Returns:
            Ruta al archivo generado
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"articles_supabase_{timestamp}.jsonl"

        output_path = self.export_dir / output_file

        # Eliminar duplicados por ID
        arts_unicos = {}
        for art in articulos:
            id_art = art['id_articulo']
            if id_art not in arts_unicos:
                arts_unicos[id_art] = art
            else:
                logger.warning(f"Artículo duplicado encontrado: {id_art}")

        # Escribir JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for art in arts_unicos.values():
                json_line = json.dumps(art, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(f"Exportados {len(arts_unicos)} artículos a {output_path}")
        return str(output_path)

    def export_supabase_ready(self, sitio: Optional[str] = None) -> Dict[str, str]:
        """
        Procesa todos los archivos JSON del directorio data y genera exportaciones JSONL.

        Args:
            sitio: Filtrar solo archivos de un sitio específico (opcional)

        Returns:
            Diccionario con rutas de archivos generados
        """
        logger.info(f"Iniciando exportación Supabase desde {self.data_dir}")

        # Resetear estadísticas
        self.stats = {
            'documentos_procesados': 0,
            'documentos_validos': 0,
            'documentos_invalidos': 0,
            'articulos_procesados': 0,
            'articulos_validos': 0,
            'articulos_invalidos': 0,
            'errores': []
        }

        documentos_totales = []
        articulos_totales = []

        # Buscar archivos JSON
        if sitio:
            pattern = f"*{sitio}*.json"
        else:
            pattern = "*.json"

        archivos_json = list(self.data_dir.glob(pattern))
        logger.info(f"Encontrados {len(archivos_json)} archivos JSON")

        # Procesar cada archivo
        for filepath in archivos_json:
            logger.info(f"Procesando {filepath.name}...")
            docs, arts = self.procesar_archivo_json(filepath, sitio)
            documentos_totales.extend(docs)
            articulos_totales.extend(arts)

        # Exportar a JSONL
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sufijo = f"_{sitio}" if sitio else ""

        docs_file = self.export_documents_jsonl(
            documentos_totales,
            f"documents_supabase{sufijo}_{timestamp}.jsonl"
        )
        arts_file = self.export_articles_jsonl(
            articulos_totales,
            f"articles_supabase{sufijo}_{timestamp}.jsonl"
        )

        # Guardar estadísticas
        stats_file = self.export_dir / f"export_stats{sufijo}_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE EXPORTACIÓN")
        logger.info("="*60)
        logger.info(f"Documentos procesados: {self.stats['documentos_procesados']}")
        logger.info(f"Documentos válidos: {self.stats['documentos_validos']}")
        logger.info(f"Documentos inválidos: {self.stats['documentos_invalidos']}")
        logger.info(f"Artículos procesados: {self.stats['articulos_procesados']}")
        logger.info(f"Artículos válidos: {self.stats['articulos_validos']}")
        logger.info(f"Artículos inválidos: {self.stats['articulos_invalidos']}")
        logger.info(f"Errores totales: {len(self.stats['errores'])}")
        logger.info("="*60)

        return {
            'documents': docs_file,
            'articles': arts_file,
            'stats': str(stats_file)
        }


# Funciones de conveniencia para importar

def export_documents_jsonl(documentos: List[Dict], output_file: str = "documents_supabase.jsonl") -> str:
    """
    Exporta lista de documentos a JSONL.

    Args:
        documentos: Lista de documentos
        output_file: Nombre del archivo de salida

    Returns:
        Ruta al archivo generado
    """
    exporter = SupabaseExporter()
    return exporter.export_documents_jsonl(documentos, output_file)


def export_articles_jsonl(articulos: List[Dict], output_file: str = "articles_supabase.jsonl") -> str:
    """
    Exporta lista de artículos a JSONL.

    Args:
        articulos: Lista de artículos
        output_file: Nombre del archivo de salida

    Returns:
        Ruta al archivo generado
    """
    exporter = SupabaseExporter()
    return exporter.export_articles_jsonl(articulos, output_file)


def export_supabase_ready(data_dir: str = "data", export_dir: str = "exports", sitio: Optional[str] = None) -> Dict[str, str]:
    """
    Procesa todos los archivos JSON y genera exportaciones JSONL listas para Supabase.

    Args:
        data_dir: Directorio con datos JSON
        export_dir: Directorio de salida
        sitio: Filtrar por sitio específico (opcional)

    Returns:
        Diccionario con rutas de archivos generados
    """
    exporter = SupabaseExporter(data_dir, export_dir)
    return exporter.export_supabase_ready(sitio)


def procesar_documento_individual(filepath: str, sitio: Optional[str] = None) -> Dict[str, str]:
    """
    Procesa un documento individual y genera exportaciones JSONL.

    Args:
        filepath: Ruta al archivo JSON del documento
        sitio: Nombre del sitio fuente (opcional)

    Returns:
        Diccionario con rutas de archivos generados
    """
    exporter = SupabaseExporter()
    docs, arts = exporter.procesar_archivo_json(Path(filepath), sitio)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    docs_file = exporter.export_documents_jsonl(docs, f"document_{timestamp}.jsonl")
    arts_file = exporter.export_articles_jsonl(arts, f"articles_{timestamp}.jsonl")

    return {
        'documents': docs_file,
        'articles': arts_file,
        'stats': {
            'documentos': len(docs),
            'articulos': len(arts)
        }
    }
