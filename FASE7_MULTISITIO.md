# Fase 7: Motor Multi-Sitio para Scraping Gubernamental

## Introducción

Este documento describe la arquitectura del motor multi-sitio implementado en la Fase 7 del proyecto. El objetivo es crear un sistema extensible y modular que permita agregar nuevos sitios gubernamentales sin modificar el código core.

## Arquitectura del Sistema

### Componentes Principales

```
bo-gov-scraper-buho/
├── config/
│   └── sites.json              # Configuración central de todos los sitios
├── scraper/
│   ├── base_site.py            # Clase base abstracta para scrapers
│   └── sites/
│       ├── __init__.py
│       └── gaceta.py           # Implementación específica de Gaceta
├── logs/                       # Logs de ejecución por sitio/fecha
├── outputs/                    # Salidas organizadas por sitio
│   ├── gaceta/
│   │   ├── pdfs/
│   │   ├── csv/
│   │   └── json/
│   ├── hermes/
│   └── ...
├── main.py                     # Punto de entrada CLI
└── requirements.txt            # Dependencias del proyecto
```

## 1. Configuración Central (`config/sites.json`)

### Estructura del Archivo

Cada sitio se configura en el archivo `config/sites.json`:

```json
{
  "sites": {
    "gaceta": {
      "id_sitio": "gaceta",
      "nombre": "Gaceta Oficial de Bolivia",
      "tipo": "gaceta",
      "descripcion": "Publicación oficial del Estado Plurinacional de Bolivia",
      "url_listado": "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar",
      "selectores_css": {
        "contenedor_resultados": ".tabla-resultados",
        "fila_documento": "tr.documento",
        "link_pdf": "a.btn-descargar",
        "titulo": ".titulo-norma",
        "fecha": ".fecha-publicacion",
        "numero_gaceta": ".numero-gaceta",
        "tipo_norma": ".tipo-norma"
      },
      "tipo_paginacion": "scroll_infinito",
      "requiere_selenium": true,
      "selenium_options": {
        "headless": true,
        "wait_time": 5,
        "scroll_pause": 2
      },
      "reglas_extraccion": {
        "formato_documento": "pdf",
        "extraer_texto": true,
        "extraer_articulos": true,
        "patron_articulos": "Art[ií]culo\\s+\\d+[°º]?",
        "encoding": "utf-8"
      },
      "rate_limit": {
        "requests_por_minuto": 10,
        "delay_entre_requests": 6
      },
      "output_folder": "outputs/gaceta",
      "campos_metadata": [
        "fecha_publicacion",
        "numero_gaceta",
        "tipo_norma",
        "titulo",
        "url_pdf",
        "fecha_descarga"
      ]
    }
  }
}
```

### Campos de Configuración

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_sitio` | string | Identificador único del sitio |
| `nombre` | string | Nombre completo del sitio |
| `tipo` | string | Categoría (gaceta, tribunal, impuestos, etc.) |
| `descripcion` | string | Descripción breve del sitio |
| `url_listado` | string | URL principal del listado de documentos |
| `selectores_css` | object | Selectores CSS para extraer elementos |
| `tipo_paginacion` | string | Tipo: scroll_infinito, paginado_numerico, boton_siguiente |
| `requiere_selenium` | boolean | Si necesita Selenium o requests es suficiente |
| `selenium_options` | object | Opciones de configuración de Selenium |
| `reglas_extraccion` | object | Reglas para extraer contenido de documentos |
| `rate_limit` | object | Configuración de límites de velocidad |
| `output_folder` | string | Carpeta de salida para este sitio |
| `campos_metadata` | array | Lista de campos de metadata a extraer |

## 2. Clase Base (`scraper/base_site.py`)

### Descripción

`BaseSiteScraper` es una clase abstracta que define la interfaz común para todos los scrapers. Proporciona:

- Carga automática de configuración
- Sistema de logging integrado
- Manejo de Selenium y requests
- Rate limiting automático
- Métodos para guardar en CSV/JSON
- Estadísticas de ejecución

### Métodos Abstractos (deben implementarse en clases hijas)

```python
@abstractmethod
def fetch_listing(self, limite: int = None) -> List[Dict[str, Any]]:
    """Obtiene el listado de documentos del sitio."""
    pass

@abstractmethod
def extract_links(self, html_content: str) -> List[str]:
    """Extrae los enlaces a documentos del HTML."""
    pass

@abstractmethod
def download_document(self, url: str, metadata: Dict[str, Any]) -> Optional[str]:
    """Descarga un documento específico."""
    pass

@abstractmethod
def normalize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza la metadata extraída del sitio."""
    pass
```

### Métodos Útiles Heredados

- `extract_text_from_pdf(pdf_path)`: Extrae texto de PDFs
- `extract_articles(text)`: Extrae artículos usando regex
- `save_to_csv(datos, filename)`: Guarda datos en CSV
- `save_to_json(datos, filename)`: Guarda datos en JSON
- `log_stats()`: Muestra estadísticas de ejecución
- `run(limite, reprocesar)`: Ejecuta el proceso completo

## 3. Implementación Específica: Gaceta

### Archivo: `scraper/sites/gaceta.py`

La clase `GacetaScraper` hereda de `BaseSiteScraper` e implementa la lógica específica para la Gaceta Oficial de Bolivia.

#### Ejemplo de Uso

```python
from scraper.sites.gaceta import GacetaScraper

# Crear instancia del scraper
scraper = GacetaScraper()

# Ejecutar scraping con límite de 10 documentos
scraper.run(limite=10, reprocesar=False)
```

#### Características Específicas

- Manejo de scroll infinito con Selenium
- Parseo de fechas en formato boliviano (DD/MM/YYYY)
- Extracción de metadatos específicos de gacetas:
  - Número de gaceta
  - Tipo de norma
  - Fecha de publicación
  - URL del PDF
- Descarga automática de PDFs
- Extracción de artículos del texto

## 4. Interfaz de Línea de Comandos (`main.py`)

### Comandos Disponibles

#### Listar todos los sitios configurados

```bash
python main.py --listar-sitios
```

**Salida esperada:**
```
======================================================================
SITIOS GUBERNAMENTALES DISPONIBLES
======================================================================

ID: gaceta
   Nombre: Gaceta Oficial de Bolivia
   Tipo: gaceta
   Descripción: Publicación oficial del Estado Plurinacional de Bolivia
   URL: https://www.gacetaoficialdebolivia.gob.bo/normas/buscar

ID: hermes
   Nombre: Sistema Hermes - Contratos Públicos
   Tipo: contratos
   ...

======================================================================
Total de sitios disponibles: 5
======================================================================
```

#### Ejecutar scraping de un sitio

```bash
# Scraping básico con límite
python main.py --sitio gaceta --limite 10

# Scraping sin límite
python main.py --sitio gaceta

# Reprocesar documentos existentes
python main.py --sitio gaceta --limite 50 --reprocesar

# Usar configuración personalizada
python main.py --sitio hermes --config config/mi_config.json
```

### Argumentos del CLI

| Argumento | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--sitio` | ID del sitio a scrapear | `--sitio gaceta` |
| `--limite` | Número máximo de documentos | `--limite 10` |
| `--reprocesar` | Reprocesar documentos existentes | `--reprocesar` |
| `--config` | Archivo de configuración personalizado | `--config config/custom.json` |
| `--listar-sitios` | Mostrar sitios disponibles | `--listar-sitios` |
| `--version` | Mostrar versión del programa | `--version` |

## 5. Sistema de Logs

### Ubicación

Los logs se guardan en `logs/` con el formato:
```
logs/{sitio}_{fecha}_{hora}.log
```

Ejemplo: `logs/gaceta_20250118_143052.log`

### Información Registrada

Cada log incluye:

1. **Inicio de ejecución**
   - Sitio objetivo
   - URL
   - Límite de documentos
   - Configuración de Selenium

2. **Progreso**
   - Documentos encontrados
   - Documentos procesados
   - Descargas completadas
   - Errores encontrados

3. **Estadísticas finales**
   - Total de documentos encontrados
   - Total de documentos descargados
   - Total de artículos extraídos
   - Cantidad de errores
   - Tiempo total de ejecución

### Ejemplo de Log

```
2025-01-18 14:30:52 - gaceta_scraper - INFO - GacetaScraper inicializado
2025-01-18 14:30:52 - gaceta_scraper - INFO - Iniciando scraping de Gaceta Oficial de Bolivia
2025-01-18 14:30:52 - gaceta_scraper - INFO - URL: https://www.gacetaoficialdebolivia.gob.bo/normas/buscar
2025-01-18 14:30:52 - gaceta_scraper - INFO - Límite: 10
2025-01-18 14:30:53 - gaceta_scraper - INFO - Selenium WebDriver inicializado correctamente
2025-01-18 14:30:58 - gaceta_scraper - INFO - Encontradas 50 filas en el HTML
2025-01-18 14:31:00 - gaceta_scraper - INFO - Se obtuvieron 10 documentos del listado
2025-01-18 14:31:00 - gaceta_scraper - INFO - Procesando documento 1/10
2025-01-18 14:31:05 - gaceta_scraper - INFO - Descargando: https://...
2025-01-18 14:31:08 - gaceta_scraper - INFO - Descargado: outputs/gaceta/pdfs/gaceta_1234_2025-01-15_20250118_143108.pdf
...
2025-01-18 14:35:00 - gaceta_scraper - INFO - ============================================================
2025-01-18 14:35:00 - gaceta_scraper - INFO - ESTADÍSTICAS DE SCRAPING - Gaceta Oficial de Bolivia
2025-01-18 14:35:00 - gaceta_scraper - INFO - ============================================================
2025-01-18 14:35:00 - gaceta_scraper - INFO - Documentos encontrados: 10
2025-01-18 14:35:00 - gaceta_scraper - INFO - Documentos descargados: 10
2025-01-18 14:35:00 - gaceta_scraper - INFO - Artículos extraídos: 247
2025-01-18 14:35:00 - gaceta_scraper - INFO - Errores: 0
2025-01-18 14:35:00 - gaceta_scraper - INFO - Duración: 0:04:08
```

## 6. Cómo Agregar un Nuevo Sitio

### Paso 1: Agregar Configuración

Edita `config/sites.json` y agrega un nuevo sitio:

```json
{
  "sites": {
    "mi_nuevo_sitio": {
      "id_sitio": "mi_nuevo_sitio",
      "nombre": "Mi Nuevo Sitio Gubernamental",
      "tipo": "tribunal",
      "descripcion": "Descripción del sitio",
      "url_listado": "https://www.ejemplo.gob.bo/documentos",
      "selectores_css": {
        "fila_documento": "div.documento",
        "link_pdf": "a.descargar",
        "titulo": "h3.titulo",
        "fecha": "span.fecha"
      },
      "tipo_paginacion": "paginado_numerico",
      "requiere_selenium": false,
      "reglas_extraccion": {
        "formato_documento": "pdf",
        "extraer_texto": true
      },
      "rate_limit": {
        "delay_entre_requests": 3
      },
      "output_folder": "outputs/mi_nuevo_sitio"
    }
  }
}
```

### Paso 2: Crear Clase del Scraper

Crea `scraper/sites/mi_nuevo_sitio.py`:

```python
"""
Scraper para Mi Nuevo Sitio Gubernamental.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import requests

from ..base_site import BaseSiteScraper


class MiNuevoSitioScraper(BaseSiteScraper):
    """Scraper para Mi Nuevo Sitio."""

    def __init__(self, config_path: str = "config/sites.json"):
        super().__init__(config_path=config_path, site_id='mi_nuevo_sitio')
        self.logger.info("MiNuevoSitioScraper inicializado")

    def fetch_listing(self, limite: int = None) -> List[Dict[str, Any]]:
        """Obtiene el listado de documentos."""
        try:
            response = self.session.get(self.url_listado, timeout=30)
            response.raise_for_status()

            documentos = self._parse_html(response.text, limite)
            return documentos

        except Exception as e:
            self.logger.error(f"Error al obtener listado: {e}")
            return []

    def _parse_html(self, html: str, limite: int = None) -> List[Dict[str, Any]]:
        """Parsea el HTML y extrae documentos."""
        soup = BeautifulSoup(html, 'html.parser')
        documentos = []

        filas = soup.select(self.selectores.get('fila_documento', 'div.item'))

        for i, fila in enumerate(filas):
            if limite and i >= limite:
                break

            doc = {
                'titulo': self._extract_text(fila, self.selectores.get('titulo', 'h3')),
                'fecha': self._extract_text(fila, self.selectores.get('fecha', '.fecha')),
                'url_pdf': self._extract_link(fila, self.selectores.get('link_pdf', 'a')),
            }

            if doc['url_pdf']:
                documentos.append(doc)

        return documentos

    def _extract_text(self, element, selector: str) -> str:
        """Extrae texto usando selector CSS."""
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else ''
        except:
            return ''

    def _extract_link(self, element, selector: str) -> str:
        """Extrae URL usando selector CSS."""
        try:
            found = element.select_one(selector)
            if found:
                url = found.get('href', '')
                if not url.startswith('http'):
                    from urllib.parse import urljoin
                    url = urljoin(self.url_listado, url)
                return url
        except:
            return ''

    def extract_links(self, html_content: str) -> List[str]:
        """Extrae enlaces del HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        for link in soup.select(self.selectores.get('link_pdf', 'a[href$=".pdf"]')):
            url = link.get('href', '')
            if url:
                links.append(url)

        return links

    def download_document(self, url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Descarga un documento."""
        import os

        try:
            filename = f"{self.site_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.output_folder, 'pdfs', filename)

            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Descargado: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error descargando {url}: {e}")
            return None

    def normalize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza metadata."""
        return {
            'sitio': self.site_id,
            'nombre_sitio': self.nombre,
            'titulo': raw_metadata.get('titulo', ''),
            'fecha': raw_metadata.get('fecha', ''),
            'url_pdf': raw_metadata.get('url_pdf', ''),
            'fecha_scraping': datetime.now().isoformat(),
            **raw_metadata
        }
```

### Paso 3: Registrar el Scraper

Edita `main.py` en la función `obtener_scraper()`:

```python
def obtener_scraper(site_id: str, config_path: str = "config/sites.json"):
    from scraper.sites.gaceta import GacetaScraper
    from scraper.sites.mi_nuevo_sitio import MiNuevoSitioScraper  # Nueva importación

    scrapers_map = {
        'gaceta': GacetaScraper,
        'mi_nuevo_sitio': MiNuevoSitioScraper,  # Nuevo registro
    }

    # ... resto del código
```

### Paso 4: Probar el Nuevo Scraper

```bash
# Ver si está disponible
python main.py --listar-sitios

# Ejecutar prueba con límite pequeño
python main.py --sitio mi_nuevo_sitio --limite 5

# Ejecutar scraping completo
python main.py --sitio mi_nuevo_sitio
```

## 7. Estructura de Salidas

### Organización de Archivos

```
outputs/
├── gaceta/
│   ├── pdfs/
│   │   ├── gaceta_1234_2025-01-15_20250118_143108.pdf
│   │   └── gaceta_1235_2025-01-16_20250118_143120.pdf
│   ├── csv/
│   │   └── gaceta_20250118_143052.csv
│   └── json/
│       └── gaceta_20250118_143052.json
├── hermes/
│   ├── pdfs/
│   ├── csv/
│   └── json/
└── mi_nuevo_sitio/
    ├── pdfs/
    ├── csv/
    └── json/
```

### Formato de CSV

El archivo CSV incluye todas las columnas de metadata:

```csv
sitio,nombre_sitio,tipo,titulo,fecha_publicacion,numero_gaceta,tipo_norma,url_pdf,archivo_local,fecha_scraping
gaceta,Gaceta Oficial de Bolivia,gaceta,Decreto Supremo 1234,15/01/2025,Nº 4567,Decreto Supremo,https://...,outputs/gaceta/pdfs/gaceta_4567_15-01-2025_20250118_143108.pdf,2025-01-18T14:31:08
```

### Formato de JSON

```json
[
  {
    "sitio": "gaceta",
    "nombre_sitio": "Gaceta Oficial de Bolivia",
    "tipo": "gaceta",
    "titulo": "Decreto Supremo 1234",
    "fecha_publicacion": "15/01/2025",
    "fecha_publicacion_iso": "2025-01-15",
    "numero_gaceta": "Nº 4567",
    "tipo_norma": "Decreto Supremo",
    "url_pdf": "https://...",
    "archivo_local": "outputs/gaceta/pdfs/gaceta_4567_15-01-2025_20250118_143108.pdf",
    "fecha_scraping": "2025-01-18T14:31:08.123456"
  }
]
```

## 8. Tipos de Paginación Soportados

### scroll_infinito

Para sitios que cargan contenido dinámicamente al hacer scroll:

```python
def _scroll_infinito(self, limite: int = None):
    """Maneja sitios con scroll infinito."""
    # Implementado en base_site.py
    # Se usa en GacetaScraper
```

### paginado_numerico

Para sitios con páginas numeradas (1, 2, 3...):

```python
def _paginacion_numerica(self, limite: int = None):
    """Maneja sitios con paginación numérica."""
    # Busca botones "siguiente" o "next"
    # Hace clic y espera carga de nueva página
```

### boton_siguiente

Para sitios con botón "Siguiente" simple:

```python
def _boton_siguiente(self, limite: int = None):
    """Maneja sitios con botón 'Siguiente'."""
    # Similar a paginación numérica
```

## 9. Manejo de Errores

### Errores Comunes y Soluciones

1. **Timeout en Selenium**
   - Aumenta `wait_time` en la configuración
   - Verifica que los selectores CSS sean correctos

2. **Error 403/404 al descargar**
   - Verifica que las URLs estén correctas
   - Ajusta `User-Agent` en headers
   - Respeta `rate_limit`

3. **Selectores CSS no encuentran elementos**
   - Inspecciona el HTML del sitio
   - Actualiza los selectores en `config/sites.json`
   - Usa selectores más genéricos como fallback

4. **Rate limiting del servidor**
   - Aumenta `delay_entre_requests`
   - Reduce `requests_por_minuto`

### Logs de Errores

Todos los errores se registran en el log con traceback completo:

```
2025-01-18 14:31:15 - gaceta_scraper - ERROR - Error descargando https://...: HTTPError 404
2025-01-18 14:31:15 - gaceta_scraper - ERROR - Error procesando documento 5: 'NoneType' object has no attribute 'get'
```

## 10. Mejores Prácticas

### 1. Respetar Rate Limits

Siempre configura delays apropiados:

```json
"rate_limit": {
  "requests_por_minuto": 10,
  "delay_entre_requests": 6
}
```

### 2. Usar Selectores CSS Robustos

Prefiere selectores por clase o ID en lugar de estructura:

```json
"selectores_css": {
  "link_pdf": "a.btn-descargar",  // ✓ Bueno
  "link_pdf": "div > table > tr > td > a"  // ✗ Frágil
}
```

### 3. Manejar Fechas Correctamente

Implementa `_normalizar_fecha()` para cada formato de sitio:

```python
def _normalizar_fecha(self, fecha_str: str) -> Optional[str]:
    """Convierte DD/MM/YYYY a YYYY-MM-DD."""
    # Implementación específica del sitio
```

### 4. Validar Datos Antes de Guardar

```python
if doc and doc.get('url_pdf') and doc.get('titulo'):
    documentos.append(doc)
```

### 5. Usar Logging Apropiado

```python
self.logger.info("Operación exitosa")    # Información general
self.logger.warning("Posible problema")  # Advertencias
self.logger.error("Error recuperable")   # Errores
```

## 11. Pruebas y Validación

### Probar un Nuevo Scraper

```bash
# 1. Verificar configuración
python main.py --listar-sitios

# 2. Prueba con 1 documento
python main.py --sitio mi_sitio --limite 1

# 3. Prueba con 10 documentos
python main.py --sitio mi_sitio --limite 10

# 4. Verificar outputs
ls -la outputs/mi_sitio/pdfs/
ls -la outputs/mi_sitio/csv/

# 5. Revisar logs
tail -f logs/mi_sitio_*.log
```

### Validación de Salidas

1. **CSV**: Debe tener headers y datos correctos
2. **JSON**: Debe ser válido y parseable
3. **PDFs**: Deben abrirse correctamente
4. **Logs**: No deben tener errores críticos

## 12. Instalación y Setup

### Requisitos

- Python 3.8+
- Google Chrome (para Selenium)
- ChromeDriver (se instala automáticamente con webdriver-manager)

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar instalación
python main.py --version
python main.py --listar-sitios
```

### Configuración Inicial

1. Edita `config/sites.json` según tus necesidades
2. Crea carpetas de salida: `mkdir -p outputs logs`
3. Ejecuta una prueba: `python main.py --sitio gaceta --limite 1`

## 13. Roadmap y Extensiones Futuras

### Funcionalidades Planeadas

- [ ] Cache de documentos ya descargados
- [ ] Base de datos SQLite para metadata
- [ ] API REST para consultar datos
- [ ] Dashboard web con Streamlit
- [ ] Notificaciones por email/Telegram
- [ ] Ejecución programada (cron/scheduler)
- [ ] Docker containerization
- [ ] Tests unitarios y de integración
- [ ] CI/CD pipeline
- [ ] Documentación API con Swagger

### Sitios por Implementar

- [ ] Hermes (Contratos Públicos)
- [ ] ICOES (Comercio Exterior)
- [ ] Derechos Reales
- [ ] SIN (Impuestos Nacionales)
- [ ] Tribunal Constitucional
- [ ] Tribunal Supremo de Justicia
- [ ] Ministerio de Economía

## 14. Contribuir

### Cómo Contribuir

1. Fork el repositorio
2. Crea una branch para tu feature: `git checkout -b feature/nuevo-sitio`
3. Implementa tu scraper siguiendo esta guía
4. Agrega tests si es posible
5. Actualiza la documentación
6. Crea un Pull Request

### Guía de Estilo

- Usa PEP 8 para Python
- Documenta todas las funciones con docstrings
- Añade type hints donde sea posible
- Escribe logs descriptivos
- Mantén los scrapers simples y enfocados

## 15. Soporte y Contacto

### Problemas Comunes

Consulta los issues en GitHub: [Issues](https://github.com/tu-usuario/bo-gov-scraper-buho/issues)

### Documentación Adicional

- [README.md](README.md): Introducción general
- [requirements.txt](requirements.txt): Dependencias
- [config/sites.json](config/sites.json): Configuración de sitios

### Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

**Última actualización:** 18 de Enero, 2025
**Versión:** 1.0.0 - Fase 7: Motor Multi-Sitio
