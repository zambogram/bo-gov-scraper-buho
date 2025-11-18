"""
Scraper de Jurisprudencia del Tribunal Constitucional Plurinacional (TCP)

Este scraper está diseñado para obtener TODA la jurisprudencia del TCP
a través de sus APIs internas (SPA), NO mediante scraping HTML.

Sitios objetivo:
- https://buscador.tcpbolivia.bo/
- https://jurisprudencia.tcpbolivia.bo/

Características:
- Basado 100% en API REST
- Paginación automática
- Iteración por años/fechas/parámetros
- Validación de cobertura total
- Configuración externalizada en YAML
"""

import requests
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class TCPJurisprudenciaScraper:
    """
    Scraper especializado para jurisprudencia del TCP
    Diseñado para COBERTURA TOTAL mediante APIs
    """

    def __init__(self, config: Dict):
        """
        Inicializa el scraper con configuración desde YAML

        Args:
            config: Diccionario con configuración del sitio desde sites_catalog.yaml
        """
        self.config = config
        self.site_id = config['id']
        self.nombre = config['nombre']

        # URLs
        self.url_base = config['url_base']
        self.url_alternativa = config.get('url_alternativa', '')

        # Configuración de scraper
        self.scraper_config = config['scraper']
        self.endpoints = self.scraper_config['endpoints']
        self.mapeo_campos = self.scraper_config['mapeo_campos']
        self.paginacion_config = self.scraper_config['paginacion']

        # Configuración de descarga
        self.descarga_config = config['descarga']
        self.directorio_salida = Path(self.descarga_config['directorio'])
        self.directorio_salida.mkdir(parents=True, exist_ok=True)

        # Sesión HTTP
        self.session = requests.Session()
        self._configurar_session()

        # Estadísticas
        self.stats = {
            'total_documentos_encontrados': 0,
            'total_documentos_descargados': 0,
            'total_pdfs_descargados': 0,
            'total_errores': 0,
            'errores': [],
            'documentos': []
        }

    def _configurar_session(self):
        """Configura la sesión HTTP con headers apropiados"""
        # Obtener configuración global
        config_global = self.config.get('configuracion_global', {})

        self.session.headers.update({
            'User-Agent': config_global.get('user_agent',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
        })

        self.timeout = self.descarga_config.get('timeout', 60)
        self.reintentos = self.descarga_config.get('reintentos', 3)
        self.delay = self.descarga_config.get('delay_entre_requests', 1)

    def listar_documentos(self, limite: Optional[int] = None,
                         modo: str = "full",
                         pagina_inicial: int = 1,
                         endpoint: str = "busqueda_general",
                         parametros_extra: Dict = None) -> List[Dict]:
        """
        Lista TODOS los documentos disponibles en la API

        Args:
            limite: Límite de documentos (None = todos)
            modo: Modo de scraping:
                - "full": Iterar TODOS los años y páginas (cobertura total)
                - "incremental": Solo documentos nuevos desde última ejecución
                - "test": Solo primeras 100 páginas (testing)
            pagina_inicial: Página desde donde empezar
            endpoint: Nombre del endpoint a usar (ver config)
            parametros_extra: Parámetros adicionales para la API

        Returns:
            Lista de descriptores de documentos
        """
        logger.info(f"🚀 Iniciando scraping de {self.nombre}")
        logger.info(f"   Modo: {modo}")
        logger.info(f"   Endpoint: {endpoint}")

        documentos = []

        if modo == "full":
            # MODO COBERTURA TOTAL: iterar por años
            documentos = self._iterar_por_años(
                endpoint=endpoint,
                limite=limite,
                parametros_extra=parametros_extra
            )

        elif modo == "incremental":
            # MODO INCREMENTAL: solo últimos N días
            documentos = self._iterar_incremental(
                endpoint=endpoint,
                limite=limite,
                dias=30
            )

        elif modo == "test":
            # MODO TEST: solo primeras páginas
            documentos = self._iterar_paginas(
                endpoint=endpoint,
                max_paginas=5,
                parametros_base=parametros_extra or {}
            )

        else:
            raise ValueError(f"Modo '{modo}' no soportado")

        # Actualizar estadísticas
        self.stats['total_documentos_encontrados'] = len(documentos)
        self.stats['documentos'] = documentos

        logger.info(f"✅ Scraping completado: {len(documentos)} documentos encontrados")

        return documentos

    def _iterar_por_años(self, endpoint: str, limite: Optional[int] = None,
                        parametros_extra: Dict = None) -> List[Dict]:
        """
        Itera por todos los años desde inicio del TCP hasta hoy
        Para cada año, itera todas las páginas

        Esta es la estrategia de COBERTURA TOTAL
        """
        metadatos = self.config.get('metadatos', {})
        rango_años = metadatos.get('rango_años', {})

        año_inicio = rango_años.get('inicio', 1999)
        año_fin = rango_años.get('fin') or datetime.now().year

        logger.info(f"📅 Iterando años: {año_inicio} - {año_fin}")

        todos_documentos = []
        documentos_procesados = 0

        for año in range(año_inicio, año_fin + 1):
            logger.info(f"\n📆 Procesando año: {año}")

            # Parámetros para este año
            params = parametros_extra.copy() if parametros_extra else {}
            params['año'] = año

            # Obtener todos los documentos de este año
            documentos_año = self._iterar_paginas(
                endpoint=endpoint,
                parametros_base=params,
                max_paginas=self.paginacion_config['max_paginas']
            )

            logger.info(f"   ✅ {len(documentos_año)} documentos encontrados en {año}")

            todos_documentos.extend(documentos_año)
            documentos_procesados += len(documentos_año)

            # Verificar límite
            if limite and documentos_procesados >= limite:
                logger.info(f"⚠️  Límite de {limite} documentos alcanzado")
                break

            # Delay entre años
            time.sleep(self.delay * 2)

        return todos_documentos

    def _iterar_paginas(self, endpoint: str, parametros_base: Dict,
                       max_paginas: int = 10000) -> List[Dict]:
        """
        Itera todas las páginas de un endpoint específico

        Args:
            endpoint: Nombre del endpoint
            parametros_base: Parámetros base de la búsqueda
            max_paginas: Máximo de páginas a iterar (seguridad)

        Returns:
            Lista de todos los documentos encontrados
        """
        documentos = []
        pagina_actual = 1
        hay_mas_paginas = True

        # Tamaño de página
        tamaño_pagina = self.paginacion_config.get('tamaño_pagina_default', 50)

        # Crear barra de progreso
        pbar = tqdm(desc=f"   Paginando", unit="docs")

        while hay_mas_paginas and pagina_actual <= max_paginas:
            # Llamar a la API
            resultado = self._llamar_api_tcp(
                endpoint=endpoint,
                parametros={
                    **parametros_base,
                    self.paginacion_config['parametros']['pagina']: pagina_actual,
                    self.paginacion_config['parametros']['tamaño']: tamaño_pagina
                }
            )

            if not resultado:
                logger.warning(f"   ⚠️  Sin resultados en página {pagina_actual}")
                break

            # Extraer documentos del JSON
            docs_pagina = self._extraer_documentos_de_json(resultado)

            if not docs_pagina:
                logger.info(f"   ℹ️  No hay más documentos (página {pagina_actual})")
                break

            documentos.extend(docs_pagina)
            pbar.update(len(docs_pagina))

            # Verificar si hay más páginas
            hay_mas_paginas = self._hay_mas_paginas(resultado, len(docs_pagina), tamaño_pagina)

            pagina_actual += 1

            # Delay entre páginas
            time.sleep(self.delay)

        pbar.close()

        return documentos

    def _iterar_incremental(self, endpoint: str, limite: Optional[int],
                           dias: int = 30) -> List[Dict]:
        """
        Modo incremental: solo documentos de los últimos N días

        Args:
            endpoint: Endpoint a usar
            limite: Límite de documentos
            dias: Número de días hacia atrás

        Returns:
            Lista de documentos
        """
        from datetime import timedelta

        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)

        logger.info(f"📅 Modo incremental: {fecha_inicio.date()} a {fecha_fin.date()}")

        # Llamar con parámetros de fecha
        parametros = {
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
        }

        return self._iterar_paginas(
            endpoint=endpoint,
            parametros_base=parametros,
            max_paginas=100
        )

    def _llamar_api_tcp(self, endpoint: str, parametros: Dict) -> Optional[Dict]:
        """
        Realiza llamada a la API del TCP

        Args:
            endpoint: Nombre del endpoint (desde config)
            parametros: Parámetros de la request

        Returns:
            JSON parseado o None si falla
        """
        # Obtener configuración del endpoint
        if endpoint not in self.endpoints:
            logger.error(f"❌ Endpoint '{endpoint}' no configurado")
            return None

        endpoint_config = self.endpoints[endpoint]
        url = f"{self.url_base}{endpoint_config['url']}"
        metodo = endpoint_config.get('metodo', 'GET')
        headers = endpoint_config.get('headers', {})

        # Realizar request con reintentos
        for intento in range(self.reintentos):
            try:
                if metodo == 'POST':
                    response = self.session.post(
                        url,
                        json=parametros,
                        headers=headers,
                        timeout=self.timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        params=parametros,
                        headers=headers,
                        timeout=self.timeout
                    )

                response.raise_for_status()

                # Parsear JSON
                try:
                    data = response.json()
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parseando JSON: {e}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    return None

            except requests.RequestException as e:
                logger.warning(f"⚠️  Intento {intento + 1}/{self.reintentos} falló: {e}")

                if intento < self.reintentos - 1:
                    time.sleep(2 ** intento)  # Backoff exponencial
                else:
                    logger.error(f"❌ Falló después de {self.reintentos} intentos")
                    self.stats['total_errores'] += 1
                    self.stats['errores'].append({
                        'tipo': 'api_error',
                        'endpoint': endpoint,
                        'error': str(e)
                    })
                    return None

        return None

    def _extraer_documentos_de_json(self, json_data: Dict) -> List[Dict]:
        """
        Extrae documentos del JSON usando el mapeo configurado

        Args:
            json_data: JSON devuelto por la API

        Returns:
            Lista de descriptores de documentos
        """
        documentos = []

        try:
            # Obtener lista de resultados usando el campo configurado
            campo_resultados = self.mapeo_campos['campo_resultados']
            items = self._obtener_valor_anidado(json_data, campo_resultados)

            if not items:
                return []

            # Transformar cada item en un descriptor de documento
            for item in items:
                doc = self._transformar_item_a_documento(item)
                if doc:
                    documentos.append(doc)

        except Exception as e:
            logger.error(f"❌ Error extrayendo documentos del JSON: {e}")
            logger.debug(f"JSON structure: {list(json_data.keys())}")

        return documentos

    def _transformar_item_a_documento(self, item: Dict) -> Optional[Dict]:
        """
        Transforma un item del JSON de la API en un descriptor de documento

        Args:
            item: Item individual del JSON

        Returns:
            Descriptor de documento normalizado
        """
        try:
            # Mapear campos
            mapeo = self.mapeo_campos

            # ID único
            id_documento = item.get(mapeo.get('id', 'id'))
            if not id_documento:
                # Generar ID a partir de número de resolución
                numero = item.get(mapeo.get('numero_resolucion', 'numeroResolucion'))
                if numero:
                    id_documento = self._generar_id(numero)
                else:
                    # Último recurso: hash del item completo
                    id_documento = self._generar_id(json.dumps(item, sort_keys=True))

            # Extraer campos
            documento = {
                'id_documento': id_documento,
                'numero_resolucion': item.get(mapeo.get('numero_resolucion', 'numeroResolucion')),
                'tipo_documento': item.get(mapeo.get('tipo_documento', 'tipoDocumento')),
                'fecha_resolucion': item.get(mapeo.get('fecha_resolucion', 'fechaResolucion')),
                'fecha_ingreso': item.get(mapeo.get('fecha_ingreso', 'fechaIngreso')),
                'materia': item.get(mapeo.get('materia', 'materia')),
                'sumilla': item.get(mapeo.get('sumilla', 'sumilla')),
                'expediente': item.get(mapeo.get('expediente', 'expediente')),
                'partes': item.get(mapeo.get('partes', 'partes')),
                'magistrado': item.get(mapeo.get('magistrado', 'magistrado')),

                # URLs
                'url_pdf': self._obtener_url_pdf(item),
                'url_detalle': item.get(mapeo.get('url_detalle', 'urlDetalle')),

                # Metadatos adicionales
                'site_id': self.site_id,
                'area_derecho': self.config['metadatos']['area_derecho'],
                'fecha_scraping': datetime.now().isoformat(),

                # JSON raw (para debugging)
                'json_raw': item
            }

            return documento

        except Exception as e:
            logger.warning(f"⚠️  Error transformando item: {e}")
            logger.debug(f"Item: {item}")
            return None

    def _obtener_url_pdf(self, item: Dict) -> Optional[str]:
        """
        Obtiene la URL del PDF del documento

        Puede estar en el JSON directamente o necesitar construirse
        """
        mapeo = self.mapeo_campos

        # Intentar obtener del JSON
        url_pdf = item.get(mapeo.get('url_pdf', 'urlPdf'))
        if url_pdf:
            return url_pdf

        # Si no está, generarla según configuración
        extraccion_config = self.config.get('extraccion', {})
        if extraccion_config.get('generar_url_pdf'):
            patron = extraccion_config.get('patron_url_pdf', '')
            if patron:
                id_doc = item.get(mapeo.get('id', 'id'))
                if id_doc:
                    return patron.format(id=id_doc)

        return None

    def _hay_mas_paginas(self, json_data: Dict, items_actuales: int,
                        tamaño_pagina: int) -> bool:
        """
        Determina si hay más páginas disponibles

        Args:
            json_data: JSON de la respuesta
            items_actuales: Número de items en la página actual
            tamaño_pagina: Tamaño de página configurado

        Returns:
            True si hay más páginas
        """
        # Si la página actual tiene menos items que el tamaño de página,
        # probablemente es la última página
        if items_actuales < tamaño_pagina:
            return False

        # Intentar obtener el total de resultados del JSON
        try:
            campo_total = self.mapeo_campos.get('campo_total', 'data.total')
            total = self._obtener_valor_anidado(json_data, campo_total)
            if total:
                # Verificar si ya obtuvimos todos
                documentos_hasta_ahora = self.stats.get('total_documentos_encontrados', 0)
                return documentos_hasta_ahora < total
        except:
            pass

        # Por defecto, asumir que hay más páginas
        return True

    def descargar_pdfs(self, documentos: List[Dict]) -> List[Dict]:
        """
        Descarga los PDFs de los documentos

        Args:
            documentos: Lista de descriptores de documentos

        Returns:
            Lista de documentos con campo 'ruta_pdf' agregado
        """
        logger.info(f"📥 Descargando PDFs de {len(documentos)} documentos...")

        # Crear subdirectorio para PDFs
        pdf_dir = self.directorio_salida / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        documentos_con_pdf = []

        for doc in tqdm(documentos, desc="Descargando PDFs"):
            url_pdf = doc.get('url_pdf')
            if not url_pdf:
                logger.debug(f"Sin URL de PDF: {doc.get('id_documento')}")
                continue

            try:
                # Descargar PDF
                ruta_pdf = self._descargar_pdf(url_pdf, pdf_dir, doc)

                if ruta_pdf:
                    doc['ruta_pdf'] = str(ruta_pdf)
                    self.stats['total_pdfs_descargados'] += 1
                    documentos_con_pdf.append(doc)

                # Delay entre descargas
                time.sleep(self.delay)

            except Exception as e:
                logger.warning(f"⚠️  Error descargando PDF de {doc.get('id_documento')}: {e}")
                self.stats['total_errores'] += 1

        logger.info(f"✅ PDFs descargados: {self.stats['total_pdfs_descargados']}/{len(documentos)}")

        return documentos_con_pdf

    def _descargar_pdf(self, url: str, directorio: Path, doc: Dict) -> Optional[Path]:
        """
        Descarga un PDF individual

        Args:
            url: URL del PDF
            directorio: Directorio de destino
            doc: Descriptor del documento

        Returns:
            Path al archivo descargado o None
        """
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Generar nombre de archivo
            id_doc = doc.get('id_documento', 'unknown')
            numero = doc.get('numero_resolucion', '')
            tipo = doc.get('tipo_documento', '').replace(' ', '_')

            # Sanitizar nombre
            nombre_archivo = f"{tipo}_{numero}_{id_doc}.pdf"
            nombre_archivo = self._sanitizar_nombre_archivo(nombre_archivo)

            ruta_archivo = directorio / nombre_archivo

            # Guardar archivo
            with open(ruta_archivo, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return ruta_archivo

        except Exception as e:
            logger.debug(f"Error descargando {url}: {e}")
            return None

    def guardar_metadatos(self, documentos: List[Dict]) -> Path:
        """
        Guarda los metadatos de los documentos en JSON

        Args:
            documentos: Lista de documentos

        Returns:
            Path al archivo JSON
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_json = self.directorio_salida / f"documentos_{timestamp}.json"

        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(documentos, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Metadatos guardados: {archivo_json}")

        return archivo_json

    def validar_cobertura(self, total_esperado: Optional[int] = None) -> Dict:
        """
        Valida que se hayan obtenido todos los documentos

        Args:
            total_esperado: Total esperado de documentos (si se conoce)

        Returns:
            Diccionario con resultados de validación
        """
        total_encontrado = self.stats['total_documentos_encontrados']
        total_descargado = self.stats['total_pdfs_descargados']

        validacion = {
            'total_documentos_encontrados': total_encontrado,
            'total_pdfs_descargados': total_descargado,
            'porcentaje_exito_descarga': (total_descargado / total_encontrado * 100)
                if total_encontrado > 0 else 0,
            'errores': self.stats['total_errores']
        }

        if total_esperado:
            diferencia = abs(total_encontrado - total_esperado)
            porcentaje_diferencia = (diferencia / total_esperado * 100) if total_esperado > 0 else 0

            validacion['total_esperado'] = total_esperado
            validacion['diferencia'] = diferencia
            validacion['porcentaje_diferencia'] = porcentaje_diferencia

            # Verificar tolerancia
            tolerancia = self.config.get('validacion', {}).get('tolerancia_porcentaje', 5)
            validacion['cobertura_completa'] = porcentaje_diferencia <= tolerancia

        return validacion

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def _obtener_valor_anidado(self, data: Dict, campo: str) -> Any:
        """
        Obtiene valor de un campo anidado usando notación de punto

        Ejemplo: 'data.items' -> data['data']['items']
        """
        keys = campo.split('.')
        valor = data

        for key in keys:
            if isinstance(valor, dict):
                valor = valor.get(key)
            else:
                return None

        return valor

    def _generar_id(self, texto: str) -> str:
        """Genera un ID único a partir de un texto"""
        return hashlib.md5(texto.encode()).hexdigest()[:16]

    def _sanitizar_nombre_archivo(self, nombre: str) -> str:
        """Sanitiza un nombre de archivo"""
        import re
        # Eliminar caracteres no permitidos
        nombre = re.sub(r'[^\w\s.-]', '', nombre)
        # Reemplazar espacios
        nombre = re.sub(r'\s+', '_', nombre)
        # Limitar longitud
        return nombre[:200]

    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del scraping"""
        return self.stats


# =============================================================================
# FUNCIÓN HELPER PARA USO STANDALONE
# =============================================================================

def scrape_tcp_jurisprudencia(config_path: str = "config/sites_catalog.yaml",
                              modo: str = "test",
                              limite: int = None,
                              guardar_pdfs: bool = True) -> Dict:
    """
    Función helper para ejecutar el scraper directamente

    Args:
        config_path: Ruta al archivo de configuración
        modo: Modo de scraping (test, full, incremental)
        limite: Límite de documentos
        guardar_pdfs: Si se deben descargar los PDFs

    Returns:
        Diccionario con resultados
    """
    import yaml

    # Cargar configuración
    with open(config_path, 'r', encoding='utf-8') as f:
        catalogo = yaml.safe_load(f)

    config_sitio = catalogo['sites']['tcp_jurisprudencia']

    # Crear scraper
    scraper = TCPJurisprudenciaScraper(config_sitio)

    # Listar documentos
    documentos = scraper.listar_documentos(limite=limite, modo=modo)

    # Descargar PDFs si se solicita
    if guardar_pdfs and documentos:
        documentos = scraper.descargar_pdfs(documentos)

    # Guardar metadatos
    scraper.guardar_metadatos(documentos)

    # Validar cobertura
    validacion = scraper.validar_cobertura()

    return {
        'documentos': documentos,
        'estadisticas': scraper.obtener_estadisticas(),
        'validacion': validacion
    }


if __name__ == "__main__":
    # Ejemplo de uso standalone
    import sys

    modo = sys.argv[1] if len(sys.argv) > 1 else "test"

    print(f"🦉 BÚHO - Scraper TCP Jurisprudencia")
    print(f"Modo: {modo}")

    resultado = scrape_tcp_jurisprudencia(
        modo=modo,
        limite=100 if modo == "test" else None,
        guardar_pdfs=True
    )

    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    stats = resultado['estadisticas']
    print(f"Documentos encontrados: {stats['total_documentos_encontrados']}")
    print(f"PDFs descargados: {stats['total_pdfs_descargados']}")
    print(f"Errores: {stats['total_errores']}")
