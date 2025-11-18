"""
FASE 5: PARSER LEGAL POR ARTÍCULOS

Este módulo se encarga de tomar textos legales ya extraídos (documentos normativos bolivianos)
y segmentarlos en artículos individuales para facilitar su análisis posterior.

El módulo NO utiliza NLP avanzado, solo patrones simples con expresiones regulares.
"""

import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_metadata(csv_path: str) -> pd.DataFrame:
    """
    Carga los metadatos de los documentos desde un archivo CSV.

    Explicación para no técnicos:
    Esta función lee un archivo CSV (como una hoja de Excel pero en texto simple)
    que contiene información sobre los documentos legales: tipo de norma, número,
    fecha de publicación, etc.

    Args:
        csv_path: La ruta completa al archivo CSV que contiene los metadatos

    Returns:
        Una tabla (DataFrame) con todos los metadatos de los documentos

    Raises:
        FileNotFoundError: Si el archivo CSV no existe
        pd.errors.EmptyDataError: Si el archivo CSV está vacío
    """
    try:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"El archivo de metadatos no existe: {csv_path}")

        df = pd.read_csv(csv_path)
        logger.info(f"Metadatos cargados correctamente: {len(df)} documentos encontrados")
        return df

    except pd.errors.EmptyDataError:
        logger.error(f"El archivo CSV está vacío: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error al cargar metadatos desde {csv_path}: {str(e)}")
        raise


def load_text(text_path: str) -> str:
    """
    Carga el contenido de un documento de texto.

    Explicación para no técnicos:
    Esta función lee el contenido completo de un archivo de texto (.txt)
    que contiene el texto extraído de un documento legal (PDF convertido a texto).

    Args:
        text_path: La ruta completa al archivo de texto

    Returns:
        El contenido completo del archivo como una cadena de texto

    Raises:
        FileNotFoundError: Si el archivo de texto no existe
    """
    try:
        if not os.path.exists(text_path):
            raise FileNotFoundError(f"El archivo de texto no existe: {text_path}")

        with open(text_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Texto cargado correctamente: {len(content)} caracteres desde {text_path}")
        return content

    except UnicodeDecodeError:
        # Intentar con otra codificación si UTF-8 falla
        try:
            with open(text_path, 'r', encoding='latin-1') as f:
                content = f.read()
            logger.warning(f"Texto cargado con codificación latin-1: {text_path}")
            return content
        except Exception as e:
            logger.error(f"Error al cargar texto con codificación alternativa: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error al cargar texto desde {text_path}: {str(e)}")
        raise


def segment_articles(text: str) -> List[Dict[str, Any]]:
    """
    Segmenta un texto legal en artículos individuales usando patrones comunes.

    Explicación para no técnicos:
    Esta función toma el texto completo de una ley o decreto y lo divide en
    artículos separados. Por ejemplo, si el texto dice "Artículo 1.- El Estado..."
    y luego "Artículo 2.- Los ciudadanos...", la función identificará que son
    dos artículos diferentes y los separará.

    Patrones soportados (mayúsculas y minúsculas):
    - "Artículo 1.-"
    - "Artículo 1."
    - "Artículo 1°"
    - "Artículo 1º"
    - "Art. 1.-"
    - "Art. 1."
    - "ARTÍCULO 1.-"
    - Y variaciones similares

    Args:
        text: El texto completo del documento legal

    Returns:
        Una lista de diccionarios, donde cada diccionario representa un artículo con:
        - articulo_numero: El número del artículo (ej. "1", "2", "3")
        - titulo_articulo: El título del artículo si se detecta (puede estar vacío)
        - texto: El contenido completo del artículo

    Notas:
    - Si no se detecta ningún patrón de artículo, devuelve todo el texto como
      un solo "artículo" sin número.
    - Los artículos pueden tener números del 1 al 999 o más.
    """

    # Patrones para detectar artículos en documentos legales bolivianos
    # Estos patrones buscan: "Artículo" o "Art." seguido de un número
    patterns = [
        # Artículo 1.- (con guión)
        r'(?:ARTÍCULO|Artículo|artículo|ARTICULO|Articulo|articulo|ART\.|Art\.|art\.)\s+(\d+)\s*\.-',
        # Artículo 1. (con punto)
        r'(?:ARTÍCULO|Artículo|artículo|ARTICULO|Articulo|articulo|ART\.|Art\.|art\.)\s+(\d+)\s*\.',
        # Artículo 1° o Artículo 1º (con símbolo de grado)
        r'(?:ARTÍCULO|Artículo|artículo|ARTICULO|Articulo|articulo|ART\.|Art\.|art\.)\s+(\d+)\s*[°º]',
        # Artículo 1 (sin puntuación, solo espacio)
        r'(?:ARTÍCULO|Artículo|artículo|ARTICULO|Articulo|articulo|ART\.|Art\.|art\.)\s+(\d+)\s+',
    ]

    # Combinar todos los patrones en uno solo con alternativas (|)
    combined_pattern = '|'.join(f'({p})' for p in patterns)

    # Buscar todas las ocurrencias de artículos en el texto
    matches = []
    for match in re.finditer(combined_pattern, text, re.MULTILINE):
        # Obtener la posición donde se encontró el patrón
        start_pos = match.start()
        # Obtener el número del artículo (está en uno de los grupos de captura)
        article_num = None
        for group in match.groups():
            if group and group.isdigit():
                article_num = group
                break

        if article_num:
            matches.append({
                'numero': article_num,
                'posicion': start_pos,
                'match_text': match.group()
            })

    # Si no se encontraron artículos, devolver todo el texto como un solo bloque
    if not matches:
        logger.warning("No se detectaron patrones de artículos en el texto")
        return [{
            'articulo_numero': '',
            'titulo_articulo': '',
            'texto': text.strip()
        }]

    # Segmentar el texto en artículos
    articles = []
    for i, match in enumerate(matches):
        # Determinar dónde empieza este artículo
        start = match['posicion']

        # Determinar dónde termina (empieza el siguiente artículo, o fin del texto)
        if i < len(matches) - 1:
            end = matches[i + 1]['posicion']
        else:
            end = len(text)

        # Extraer el texto del artículo
        article_text = text[start:end].strip()

        # Intentar extraer el título del artículo (primera línea después del número)
        # Por ejemplo: "Artículo 1.- Objeto\n El presente decreto..."
        # El título sería "Objeto"
        titulo = ''
        lines = article_text.split('\n', 2)
        if len(lines) >= 2:
            # La primera línea contiene "Artículo X.-"
            # La segunda línea podría ser el título (si es corta, < 100 caracteres)
            potential_title = lines[1].strip()
            if len(potential_title) < 100 and not potential_title.endswith('.'):
                titulo = potential_title

        articles.append({
            'articulo_numero': match['numero'],
            'titulo_articulo': titulo,
            'texto': article_text
        })

    logger.info(f"Segmentación completada: {len(articles)} artículos detectados")
    return articles


def build_document_structure(metadata_row: pd.Series, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Construye la estructura completa de un documento legal con sus metadatos y artículos.

    Explicación para no técnicos:
    Esta función toma la información general de un documento (tipo de norma, número, fecha)
    y la combina con sus artículos segmentados para crear una estructura organizada
    que contiene todo junto.

    Args:
        metadata_row: Una fila de la tabla de metadatos con información del documento
        articles: La lista de artículos segmentados del documento

    Returns:
        Un diccionario con la estructura completa:
        - metadata: Información general del documento (tipo, número, fecha, etc.)
        - articles: Lista de todos los artículos con su contenido
        - statistics: Estadísticas básicas (total de artículos, caracteres, etc.)
    """

    # Construir la estructura del documento
    doc_structure = {
        'metadata': {
            'id_documento': metadata_row.get('id_documento', ''),
            'tipo_norma': metadata_row.get('tipo_norma', ''),
            'numero_norma': metadata_row.get('numero_norma', ''),
            'fecha_publicacion': metadata_row.get('fecha_publicacion_aproximada', ''),
            'titulo': metadata_row.get('titulo', ''),
            'descripcion': metadata_row.get('descripcion', ''),
        },
        'articles': articles,
        'statistics': {
            'total_articles': len(articles),
            'total_characters': sum(len(art['texto']) for art in articles),
            'articles_with_title': sum(1 for art in articles if art['titulo_articulo'])
        }
    }

    logger.info(f"Estructura del documento construida: {doc_structure['statistics']['total_articles']} artículos")
    return doc_structure


def save_document_json(doc_structure: Dict[str, Any], output_dir: str) -> str:
    """
    Guarda la estructura de un documento en formato JSON.

    Explicación para no técnicos:
    Esta función toma la estructura completa de un documento (metadatos + artículos)
    y la guarda en un archivo JSON (un formato de texto estructurado que las
    computadoras pueden leer fácilmente).

    Args:
        doc_structure: La estructura completa del documento
        output_dir: La carpeta donde se guardará el archivo JSON

    Returns:
        La ruta completa del archivo JSON creado

    Raises:
        OSError: Si no se puede crear la carpeta o escribir el archivo
    """

    # Crear la carpeta de salida si no existe
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generar el nombre del archivo basado en el ID del documento
    id_documento = doc_structure['metadata'].get('id_documento', 'unknown')
    filename = f"{id_documento}.json"
    filepath = os.path.join(output_dir, filename)

    try:
        # Guardar el JSON con formato bonito (indentado)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_structure, f, ensure_ascii=False, indent=2)

        logger.info(f"Documento JSON guardado: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error al guardar JSON en {filepath}: {str(e)}")
        raise


def append_articles_to_csv(doc_structure: Dict[str, Any], csv_articulos_path: str) -> None:
    """
    Agrega los artículos de un documento al CSV de artículos.

    Explicación para no técnicos:
    Esta función toma todos los artículos de un documento y los agrega a un
    archivo CSV (como una hoja de Excel) donde cada fila representa un artículo.
    Esto facilita buscar y analizar artículos específicos de múltiples documentos.

    El CSV tendrá columnas como:
    - id_documento: Identificador del documento
    - tipo_norma: Tipo de norma (ley, decreto, resolución, etc.)
    - numero_norma: Número de la norma
    - fecha_publicacion_aproximada: Fecha aproximada de publicación
    - articulo_numero: Número del artículo
    - titulo_articulo: Título del artículo (si existe)
    - texto_articulo: Contenido completo del artículo

    Args:
        doc_structure: La estructura completa del documento con sus artículos
        csv_articulos_path: La ruta al archivo CSV donde se guardarán los artículos

    Raises:
        OSError: Si no se puede escribir en el archivo CSV
    """

    # Preparar las filas para el CSV
    rows = []
    metadata = doc_structure['metadata']

    for article in doc_structure['articles']:
        row = {
            'id_documento': metadata.get('id_documento', ''),
            'tipo_norma': metadata.get('tipo_norma', ''),
            'numero_norma': metadata.get('numero_norma', ''),
            'fecha_publicacion_aproximada': metadata.get('fecha_publicacion', ''),
            'articulo_numero': article['articulo_numero'],
            'titulo_articulo': article['titulo_articulo'],
            'texto_articulo': article['texto']
        }
        rows.append(row)

    # Crear DataFrame con las filas
    df_new = pd.DataFrame(rows)

    try:
        # Si el archivo ya existe, agregar las filas; si no, crear uno nuevo
        if os.path.exists(csv_articulos_path):
            df_existing = pd.read_csv(csv_articulos_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(csv_articulos_path, index=False)
            logger.info(f"Se agregaron {len(rows)} artículos al CSV existente: {csv_articulos_path}")
        else:
            # Crear la carpeta padre si no existe
            Path(csv_articulos_path).parent.mkdir(parents=True, exist_ok=True)
            df_new.to_csv(csv_articulos_path, index=False)
            logger.info(f"CSV de artículos creado con {len(rows)} artículos: {csv_articulos_path}")

    except Exception as e:
        logger.error(f"Error al guardar artículos en CSV {csv_articulos_path}: {str(e)}")
        raise


def process_document(text_path: str, metadata_row: pd.Series,
                     output_json_dir: str, csv_articulos_path: str) -> Optional[Dict[str, Any]]:
    """
    Procesa un documento completo: carga el texto, segmenta artículos y guarda resultados.

    Explicación para no técnicos:
    Esta es la función principal que coordina todo el proceso:
    1. Lee el texto del documento
    2. Lo divide en artículos
    3. Combina todo con los metadatos
    4. Guarda el resultado en JSON y CSV

    Args:
        text_path: Ruta al archivo de texto del documento
        metadata_row: Fila con los metadatos del documento
        output_json_dir: Carpeta donde guardar los JSONs
        csv_articulos_path: Ruta al CSV de artículos

    Returns:
        La estructura del documento procesado, o None si hubo error
    """

    try:
        # 1. Cargar el texto
        text = load_text(text_path)

        # 2. Segmentar en artículos
        articles = segment_articles(text)

        # 3. Construir estructura del documento
        doc_structure = build_document_structure(metadata_row, articles)

        # 4. Guardar JSON
        save_document_json(doc_structure, output_json_dir)

        # 5. Agregar artículos al CSV
        append_articles_to_csv(doc_structure, csv_articulos_path)

        logger.info(f"Documento procesado exitosamente: {metadata_row.get('id_documento', 'unknown')}")
        return doc_structure

    except Exception as e:
        logger.error(f"Error al procesar documento {text_path}: {str(e)}")
        return None
