"""
SCRAPER DE LA GACETA OFICIAL DE BOLIVIA
========================================

Este módulo se encarga de descargar automáticamente documentos (PDFs)
desde la Gaceta Oficial de Bolivia.

¿Qué hace este scraper?
- Visita la página web de la Gaceta Oficial
- Extrae los enlaces a los documentos PDF de normas y decretos
- Descarga los PDFs y los guarda en la carpeta 'data/'
- Registra toda la información en un archivo CSV para llevar control

Funciones principales:
1. fetch_page: Descarga el contenido HTML de una página web
2. parse_list_page: Analiza el HTML y extrae los enlaces a PDFs
3. download_pdf: Descarga un PDF y lo guarda en disco
4. run_gaceta_scraper: Coordina todo el proceso completo
"""

import requests
from bs4 import BeautifulSoup
import os
import csv
from datetime import datetime
import time
import re
from urllib.parse import urljoin, urlparse


def fetch_page(url, timeout=30):
    """
    Descarga el contenido HTML de una página web.

    Esta función envía una solicitud al servidor web y obtiene el código HTML
    de la página. Es como abrir la página en un navegador pero de forma automática.

    Parámetros:
    -----------
    url : str
        La dirección web (URL) de la página que queremos descargar
    timeout : int
        Tiempo máximo de espera en segundos (por defecto 30 segundos)

    Retorna:
    --------
    str
        El contenido HTML de la página como texto

    None
        Si hubo algún error al descargar la página

    Ejemplo:
    --------
    html = fetch_page("http://www.gacetaoficialdebolivia.gob.bo")
    """
    try:
        # Headers que simulan ser un navegador web normal
        # Esto ayuda a que el servidor no rechace nuestra solicitud
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Connection': 'keep-alive',
        }

        print(f"📥 Descargando página: {url}")

        # Hacemos la solicitud HTTP GET
        response = requests.get(url, headers=headers, timeout=timeout)

        # Verificamos que la solicitud fue exitosa (código 200 = OK)
        response.raise_for_status()

        print(f"✅ Página descargada exitosamente ({len(response.text)} caracteres)")
        return response.text

    except requests.exceptions.Timeout:
        print(f"❌ Error: La página tardó demasiado en responder (más de {timeout} segundos)")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: No se pudo conectar al servidor. Verifica tu conexión a internet.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


def parse_list_page(html, base_url):
    """
    Analiza el HTML de una página de listado y extrae información de las normas/decretos.

    Esta función lee el código HTML de la página y busca todos los enlaces
    a documentos PDF, junto con sus títulos y otra información relevante.

    Parámetros:
    -----------
    html : str
        El contenido HTML de la página
    base_url : str
        La URL base del sitio (para construir URLs completas)

    Retorna:
    --------
    list
        Una lista de diccionarios, cada uno con información de un documento:
        - titulo: El título o nombre del documento
        - url_pdf: La URL completa del PDF
        - fecha: La fecha del documento (si está disponible)

    Ejemplo:
    --------
    documentos = parse_list_page(html, "http://www.gacetaoficialdebolivia.gob.bo")
    # Retorna: [{'titulo': 'Decreto Supremo 123', 'url_pdf': 'http://...', 'fecha': '2024-01-15'}, ...]
    """

    print("🔍 Analizando la página en busca de documentos PDF...")

    # BeautifulSoup nos ayuda a analizar el HTML de forma fácil
    soup = BeautifulSoup(html, 'lxml')

    documentos = []

    # Estrategia 1: Buscar enlaces directos a PDFs
    # Buscamos todos los enlaces (<a>) que apuntan a archivos .pdf
    enlaces_pdf = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))

    for enlace in enlaces_pdf:
        # Extraemos la URL del PDF
        url_pdf = enlace.get('href', '')

        # Si la URL es relativa (no empieza con http), la convertimos a URL completa
        if url_pdf and not url_pdf.startswith('http'):
            url_pdf = urljoin(base_url, url_pdf)

        # Extraemos el título del enlace
        titulo = enlace.get_text(strip=True)

        # Si no hay título en el enlace, usamos el nombre del archivo
        if not titulo:
            titulo = os.path.basename(urlparse(url_pdf).path)

        # Intentamos extraer la fecha del contexto del enlace
        fecha = extraer_fecha_contexto(enlace)

        documentos.append({
            'titulo': titulo,
            'url_pdf': url_pdf,
            'fecha': fecha
        })

    # Estrategia 2: Buscar enlaces dinámicos a PDFs (descargarPdf)
    # La Gaceta Oficial de Bolivia usa enlaces como /normas/descargarPdf/12345
    enlaces_descargar = soup.find_all('a', href=re.compile(r'/normas/descargarPdf/\d+', re.IGNORECASE))

    for enlace in enlaces_descargar:
        href = enlace.get('href', '')
        url_completa = urljoin(base_url, href)

        # Buscamos el título en el contexto del enlace
        # Usualmente está en un <td> o <div> cercano
        titulo = "Documento sin título"

        # Intentamos encontrar el título en la fila de la tabla
        fila = enlace.find_parent('tr')
        if fila:
            # Buscamos todos los <td> de la fila
            celdas = fila.find_all('td')
            for celda in celdas:
                texto_celda = celda.get_text(strip=True)
                # Si la celda tiene texto sustancial y no es solo "Ver" o "Descargar"
                if len(texto_celda) > 15 and 'descargar' not in texto_celda.lower() and 'ver norma' not in texto_celda.lower():
                    titulo = texto_celda
                    break

            # Si no encontramos título en las celdas, usamos el texto de toda la fila
            if titulo == "Documento sin título":
                texto_fila = fila.get_text(strip=True)
                # Limpiamos el texto eliminando "Ver Norma", "Descargar", etc.
                texto_limpio = re.sub(r'(Ver Norma|Descargar Word|Descargar PDF|Ver|Descargar)', '', texto_fila)
                texto_limpio = texto_limpio.strip()
                if len(texto_limpio) > 10:
                    titulo = texto_limpio[:200]  # Limitamos a 200 caracteres

        # Evitamos duplicados
        if not any(doc['url_pdf'] == url_completa for doc in documentos):
            documentos.append({
                'titulo': titulo,
                'url_pdf': url_completa,
                'fecha': extraer_fecha_contexto(enlace) if fila else None
            })

    # Estrategia 3: Buscar en divs o tablas comunes en la Gaceta Oficial
    # Muchas veces los documentos están en tablas o divs con clases específicas

    # Buscamos tablas que puedan contener listados de normas
    tablas = soup.find_all('table')
    for tabla in tablas:
        filas = tabla.find_all('tr')
        for fila in filas:
            # Buscamos enlaces dentro de cada fila
            enlaces = fila.find_all('a')
            for enlace in enlaces:
                href = enlace.get('href', '')

                # Solo procesamos si es un PDF directo
                if '.pdf' in href.lower() and href.lower().endswith('.pdf'):
                    url_completa = urljoin(base_url, href)

                    # Extraemos todo el texto de la fila para obtener más contexto
                    texto_fila = fila.get_text(strip=True)
                    titulo_enlace = enlace.get_text(strip=True)

                    # Evitamos duplicados
                    if not any(doc['url_pdf'] == url_completa for doc in documentos):
                        documentos.append({
                            'titulo': titulo_enlace or texto_fila[:100],  # Limitamos a 100 caracteres
                            'url_pdf': url_completa,
                            'fecha': extraer_fecha_contexto(fila)
                        })

    print(f"✅ Se encontraron {len(documentos)} documentos")

    return documentos


def extraer_fecha_contexto(elemento):
    """
    Intenta extraer una fecha del texto cercano a un elemento HTML.

    Esta función busca patrones de fecha comunes en el texto.

    Parámetros:
    -----------
    elemento : BeautifulSoup element
        El elemento HTML donde buscar fechas

    Retorna:
    --------
    str
        La fecha encontrada en formato "YYYY-MM-DD" o None si no se encuentra
    """

    # Obtenemos el texto del elemento y sus padres cercanos
    texto = elemento.get_text()

    # Patrón para fechas en formato DD/MM/YYYY o DD-MM-YYYY
    patron_fecha = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'
    match = re.search(patron_fecha, texto)

    if match:
        dia, mes, anio = match.groups()
        return f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"

    # Patrón para fechas en formato YYYY-MM-DD
    patron_fecha_iso = r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b'
    match = re.search(patron_fecha_iso, texto)

    if match:
        anio, mes, dia = match.groups()
        return f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"

    return None


def download_pdf(url_pdf, ruta_destino, timeout=60):
    """
    Descarga un archivo PDF desde una URL y lo guarda en disco.

    Esta función descarga el archivo PDF byte por byte y lo guarda
    en la ubicación especificada.

    Parámetros:
    -----------
    url_pdf : str
        La URL del archivo PDF a descargar
    ruta_destino : str
        La ruta completa donde guardar el archivo (incluyendo nombre y extensión)
    timeout : int
        Tiempo máximo de espera en segundos (por defecto 60 segundos)

    Retorna:
    --------
    bool
        True si la descarga fue exitosa, False en caso contrario

    Ejemplo:
    --------
    exito = download_pdf("http://ejemplo.com/documento.pdf", "data/documento.pdf")
    """

    try:
        print(f"📥 Descargando PDF: {os.path.basename(ruta_destino)}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        # Descargamos el PDF con stream=True para manejar archivos grandes
        response = requests.get(url_pdf, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # Verificamos que realmente sea un PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not url_pdf.lower().endswith('.pdf'):
            print(f"⚠️  Advertencia: El archivo puede no ser un PDF (tipo: {content_type})")

        # Creamos el directorio si no existe
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

        # Guardamos el archivo en disco
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verificamos el tamaño del archivo
        tamanio = os.path.getsize(ruta_destino)
        tamanio_mb = tamanio / (1024 * 1024)

        print(f"✅ PDF descargado: {os.path.basename(ruta_destino)} ({tamanio_mb:.2f} MB)")
        return True

    except requests.exceptions.Timeout:
        print(f"❌ Error: El PDF tardó demasiado en descargarse (más de {timeout} segundos)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Falló la conexión durante la descarga")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP al descargar PDF: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado al descargar PDF: {e}")
        return False


def sanitizar_nombre_archivo(titulo, max_length=100):
    """
    Convierte un título en un nombre de archivo válido.

    Esta función elimina caracteres especiales y espacios que podrían
    causar problemas en nombres de archivo.

    Parámetros:
    -----------
    titulo : str
        El título original
    max_length : int
        Longitud máxima del nombre (por defecto 100 caracteres)

    Retorna:
    --------
    str
        Un nombre de archivo válido
    """

    # Eliminamos caracteres especiales y los reemplazamos por guiones bajos
    nombre = re.sub(r'[^\w\s-]', '', titulo)

    # Reemplazamos espacios por guiones bajos
    nombre = re.sub(r'[\s]+', '_', nombre)

    # Eliminamos guiones bajos múltiples
    nombre = re.sub(r'_+', '_', nombre)

    # Limitamos la longitud
    nombre = nombre[:max_length].strip('_')

    # Si el nombre quedó vacío, usamos un nombre por defecto
    if not nombre:
        nombre = f"documento_{int(time.time())}"

    return nombre


def run_gaceta_scraper(url_inicial, limite=10, carpeta_destino='data', archivo_log='exports/gaceta_log.csv'):
    """
    Ejecuta el scraper completo de la Gaceta Oficial.

    Esta es la función principal que coordina todo el proceso:
    1. Descarga la página de listado
    2. Extrae los enlaces a PDFs
    3. Descarga los PDFs (hasta el límite especificado)
    4. Guarda un registro en CSV

    Parámetros:
    -----------
    url_inicial : str
        La URL de la página de listado de normas/decretos
    limite : int
        Número máximo de PDFs a descargar (por defecto 10)
    carpeta_destino : str
        Carpeta donde guardar los PDFs (por defecto 'data')
    archivo_log : str
        Ruta del archivo CSV para el log (por defecto 'exports/gaceta_log.csv')

    Retorna:
    --------
    dict
        Un diccionario con estadísticas del proceso:
        - total_encontrados: Número de documentos encontrados
        - total_descargados: Número de PDFs descargados exitosamente
        - archivos: Lista de archivos descargados
    """

    print("=" * 70)
    print("🇧🇴  SCRAPER DE LA GACETA OFICIAL DE BOLIVIA")
    print("=" * 70)
    print(f"URL inicial: {url_inicial}")
    print(f"Límite de descargas: {limite}")
    print(f"Carpeta de destino: {carpeta_destino}")
    print("=" * 70)
    print()

    # Paso 1: Descargar la página de listado
    html = fetch_page(url_inicial)

    if not html:
        print("❌ No se pudo descargar la página inicial. Abortando.")
        return {
            'total_encontrados': 0,
            'total_descargados': 0,
            'archivos': []
        }

    print()

    # Paso 2: Analizar la página y extraer documentos
    documentos = parse_list_page(html, url_inicial)

    if not documentos:
        print("⚠️  No se encontraron documentos en la página.")
        return {
            'total_encontrados': 0,
            'total_descargados': 0,
            'archivos': []
        }

    print()
    print(f"📋 Total de documentos encontrados: {len(documentos)}")
    print(f"📥 Se descargarán hasta {limite} documentos")
    print()

    # Limitamos al número especificado
    documentos = documentos[:limite]

    # Paso 3: Descargar los PDFs
    archivos_descargados = []
    resultados_log = []

    for i, doc in enumerate(documentos, 1):
        print(f"\n--- Documento {i}/{len(documentos)} ---")
        print(f"Título: {doc['titulo']}")
        print(f"URL: {doc['url_pdf']}")

        # Generamos un nombre de archivo único
        nombre_base = sanitizar_nombre_archivo(doc['titulo'])
        nombre_archivo = f"{nombre_base}.pdf"

        # Si el archivo ya existe, agregamos un número
        contador = 1
        ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
        while os.path.exists(ruta_completa):
            nombre_archivo = f"{nombre_base}_{contador}.pdf"
            ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
            contador += 1

        # Descargamos el PDF
        exito = download_pdf(doc['url_pdf'], ruta_completa)

        # Registramos el resultado
        if exito:
            archivos_descargados.append(nombre_archivo)

            resultados_log.append({
                'titulo': doc['titulo'],
                'url_pdf': doc['url_pdf'],
                'archivo_descargado': nombre_archivo,
                'fecha_documento': doc.get('fecha', 'N/A'),
                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'estado': 'exitoso'
            })
        else:
            resultados_log.append({
                'titulo': doc['titulo'],
                'url_pdf': doc['url_pdf'],
                'archivo_descargado': 'N/A',
                'fecha_documento': doc.get('fecha', 'N/A'),
                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'estado': 'fallido'
            })

        # Pausa breve entre descargas para no sobrecargar el servidor
        if i < len(documentos):
            time.sleep(1)

    # Paso 4: Guardar el log en CSV
    print(f"\n\n💾 Guardando registro en {archivo_log}...")

    try:
        # Creamos el directorio si no existe
        os.makedirs(os.path.dirname(archivo_log), exist_ok=True)

        # Escribimos el CSV
        with open(archivo_log, 'w', newline='', encoding='utf-8') as f:
            if resultados_log:
                writer = csv.DictWriter(f, fieldnames=resultados_log[0].keys())
                writer.writeheader()
                writer.writerows(resultados_log)

        print(f"✅ Log guardado exitosamente")

    except Exception as e:
        print(f"❌ Error al guardar el log: {e}")

    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE LA EJECUCIÓN")
    print("=" * 70)
    print(f"✅ Documentos encontrados: {len(documentos)}")
    print(f"✅ PDFs descargados exitosamente: {len(archivos_descargados)}")
    print(f"✅ Archivos guardados en: {carpeta_destino}/")
    print(f"✅ Log guardado en: {archivo_log}")
    print("=" * 70)

    return {
        'total_encontrados': len(documentos),
        'total_descargados': len(archivos_descargados),
        'archivos': archivos_descargados
    }


if __name__ == "__main__":
    # Si ejecutamos este archivo directamente, hacemos una prueba
    print("Este módulo está diseñado para ser importado.")
    print("Usa main.py para ejecutar el scraper.")
