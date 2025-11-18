# 🇧🇴 Scraper de Sitios Gubernamentales de Bolivia

Sistema integral de scraping y gestión de documentos legales y normativos de sitios web gubernamentales de Bolivia.

## 🎯 Descripción

Este proyecto permite recolectar, organizar y gestionar documentación oficial del Estado Plurinacional de Bolivia, incluyendo leyes, decretos, resoluciones, sentencias y normativa regulatoria de diferentes instituciones.

## 🚀 Estado del Proyecto

### FASE 2 - OLA 1: SCRAPERS IMPLEMENTADOS ✅

Los siguientes sitios de prioridad máxima están completamente implementados:

- ✅ **Gaceta Oficial de Bolivia** - Leyes, decretos y resoluciones
- ✅ **TSJ GENESIS** - Jurisprudencia del Tribunal Supremo
- ✅ **TCP** - Sentencias del Tribunal Constitucional Plurinacional
- ✅ **ASFI** - Normativa del sistema financiero
- ✅ **SIN** - Normativa tributaria

## 📋 Características

- **Catálogo centralizado** de sitios gubernamentales con configuración YAML
- **Scrapers modulares** con interfaz común y fácil extensión
- **Sistema de índices** para evitar duplicados y tracking de cambios
- **CLI completo** para operaciones desde línea de comandos
- **Interfaz web** con Streamlit para uso visual
- **Modo demo** para pruebas sin conexión a sitios reales
- **Logging detallado** de todas las operaciones

## 📦 Instalación

### Requisitos

- Python 3.8 o superior
- pip

### Pasos

```bash
# Clonar el repositorio
git clone <repo-url>
cd bo-gov-scraper-buho

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🎮 Uso

### Interfaz de Línea de Comandos (CLI)

#### Listar sitios del catálogo

```bash
# Listar todos los sitios
python main.py list

# Filtrar por prioridad
python main.py list --prioridad 1

# Filtrar por categoría
python main.py list --categoria judicial

# Filtrar por estado del scraper
python main.py list --estado implementado
```

#### Ejecutar scraping de un sitio

```bash
# Scraping básico (modo demo)
python main.py scrape gaceta_oficial --limit 10 --demo

# Scraping con límite
python main.py scrape tcp --limit 5

# Scraping sin límite, solo nuevos
python main.py scrape asfi --solo-nuevos

# Scraping sin filtro de nuevos
python main.py scrape sin --limit 20
```

#### Demo de la Ola 1 completa

```bash
# Ejecutar demo de todos los sitios de la Ola 1
python main.py demo-ola1 --limit 5
```

#### Ver estadísticas

```bash
# Mostrar estadísticas de todos los sitios scrapeados
python main.py stats
```

### Interfaz Web (Streamlit)

```bash
# Iniciar la aplicación web
streamlit run app/streamlit_app.py
```

La interfaz web incluye:
- **Dashboard**: Vista general de scrapers y estadísticas
- **Catálogo de Sitios**: Exploración con filtros
- **Ejecutar Scraping**: Interfaz visual para ejecutar scrapers
- **Estadísticas**: Análisis detallado de documentos recolectados
- **Ayuda**: Documentación integrada

## 📁 Estructura del Proyecto

```
bo-gov-scraper-buho/
├── config/
│   └── sites_catalog.yaml          # Catálogo de sitios
├── scraper/
│   ├── __init__.py
│   ├── catalog.py                  # Gestor del catálogo
│   ├── base.py                     # Clase base de scrapers
│   └── sites/                      # Scrapers por sitio
│       ├── __init__.py
│       ├── gaceta_oficial.py
│       ├── tsj_genesis.py
│       ├── tcp.py
│       ├── asfi.py
│       └── sin.py
├── data/
│   ├── raw/                        # Documentos scrapeados
│   │   └── <site_id>/
│   │       ├── documentos.json     # Datos de documentos
│   │       └── pdfs/               # PDFs descargados
│   └── index/                      # Índices de tracking
│       └── <site_id>.json
├── app/
│   └── streamlit_app.py            # Interfaz web
├── docs/
│   └── USO_PRACTICO.md             # Guía de uso detallada
├── main.py                         # CLI principal
├── requirements.txt
└── README.md
```

## 🔧 Configuración

### Catálogo de Sitios

El archivo `config/sites_catalog.yaml` contiene la configuración de todos los sitios:

```yaml
sitios:
  gaceta_oficial:
    nombre: "Gaceta Oficial de Bolivia"
    prioridad: 1
    url_base: "http://www.gacetaoficialdebolivia.gob.bo"
    estado_scraper: "implementado"
    # ... más configuración
```

### Agregar un Nuevo Sitio

1. Agregar configuración en `config/sites_catalog.yaml`
2. Crear scraper en `scraper/sites/nuevo_sitio.py` heredando de `BaseSiteScraper`
3. Registrar en `scraper/sites/__init__.py`
4. Implementar método `scrape()`

## 📊 Datos Generados

### Documentos Scrapeados

Cada documento tiene la siguiente estructura:

```json
{
  "site_id": "gaceta_oficial",
  "document_id": "GACETA_OFICIAL-LEY-1234-20250115",
  "titulo": "Ley 1234 - Ley de ...",
  "tipo_norma": "Ley",
  "numero_norma": "1234",
  "fecha_publicacion": "2025-01-15",
  "url_detalle": "http://...",
  "url_pdf": "http://.../pdf",
  "path_pdf": "data/raw/gaceta_oficial/pdfs/...",
  "hash_contenido": "md5hash...",
  "estado": "nuevo",
  "fecha_scraping": "2025-01-18T10:30:00"
}
```

### Índices

Los índices en `data/index/<site_id>.json` rastrean documentos para evitar duplicados:

```json
{
  "GACETA_OFICIAL-LEY-1234-20250115": {
    "hash": "md5hash...",
    "titulo": "Ley 1234...",
    "fecha_publicacion": "2025-01-15",
    "fecha_ultima_vez_visto": "2025-01-18T10:30:00",
    "estado": "nuevo",
    "url_pdf": "http://..."
  }
}
```

## 🧪 Modo Demo

Todos los scrapers soportan un modo demo que genera datos realistas sin conectarse a sitios reales:

```bash
# CLI
python main.py scrape gaceta_oficial --limit 10 --demo

# En código
scraper = GacetaOficialScraper(site_config, modo_demo=True)
```

Útil para:
- Desarrollo y pruebas
- Demos y presentaciones
- Entornos sin conexión a internet

## 🛣️ Próximas Fases

### Fase 3: Procesamiento de Texto
- Extracción de texto de PDFs
- OCR para documentos escaneados
- Parsers legales especializados
- Extracción de metadatos avanzados

### Fase 4: Integración con Supabase
- Sync automático con base de datos
- API REST para consultas
- Sistema de notificaciones
- Dashboard analytics

## 📝 Logs

Los logs se guardan en `scraper.log` y también se muestran en consola.

Nivel de logging configurable en `main.py`:

```python
logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contribuir

Para agregar un nuevo sitio o mejorar scrapers existentes:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa cambios siguiendo la estructura existente
4. Prueba con modo demo
5. Envía un pull request

## 📄 Licencia

[Especificar licencia]

## 🆘 Soporte

Para problemas o preguntas:
- Revisa `docs/USO_PRACTICO.md`
- Consulta los logs en `scraper.log`
- Abre un issue en el repositorio

---

**Versión**: Fase 2 - Ola 1
**Última actualización**: 2025-01-18
**Estado**: Producción
