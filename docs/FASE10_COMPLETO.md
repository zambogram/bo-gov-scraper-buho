# FASE 10 - Documentación Técnica Completa

## 🎯 Visión General

FASE 10 representa la implementación completa del sistema BÚHO (Bolivian Government Document Scraper), integrando todas las capacidades de scraping, parsing, exportación y sincronización en una plataforma unificada.

## 📐 Arquitectura General

### Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────┐
│                        BÚHO System                            │
│                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐       │
│  │     CLI     │   │  Streamlit  │   │   Scheduler  │       │
│  │   main.py   │   │     UI      │   │  run_daily   │       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬───────┘       │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                  │
│              ┌─────────────▼─────────────┐                   │
│              │    Scraper Module         │                   │
│              ├───────────────────────────┤                   │
│              │ • BaseScraper             │                   │
│              │ • TCPScraper              │                   │
│              │ • TSJScraper              │                   │
│              │ • ASFIScraper             │                   │
│              │ • SINScraper              │                   │
│              │ • ContraloriaScraper      │                   │
│              │ • LegalParser             │                   │
│              │ • MetadataExtractor       │                   │
│              └─────────────┬─────────────┘                   │
│                            │                                  │
│              ┌─────────────▼─────────────┐                   │
│              │    Storage Layer          │                   │
│              ├───────────────────────────┤                   │
│              │ • JSON Index              │                   │
│              │ • JSON Articles           │                   │
│              │ • JSONL Exports           │                   │
│              │ • Sync Logs               │                   │
│              └─────────────┬─────────────┘                   │
│                            │                                  │
│              ┌─────────────▼─────────────┐                   │
│              │    Sync Module            │                   │
│              ├───────────────────────────┤                   │
│              │ • SupabaseSync            │                   │
│              │ • Duplicate Detection     │                   │
│              │ • Stats Aggregation       │                   │
│              └─────────────┬─────────────┘                   │
│                            │                                  │
│                            ▼                                  │
│                   ┌────────────────┐                         │
│                   │   Supabase DB  │                         │
│                   └────────────────┘                         │
└──────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes Principales

### 1. Scraper Module

#### BaseScraper

Clase base abstracta que proporciona funcionalidad común a todos los scrapers.

**Responsabilidades:**
- Gestión de sesiones HTTP
- Almacenamiento de índices y artículos
- Cálculo de MD5 para detección de cambios
- Exportación a JSONL
- Estadísticas

**Métodos Principales:**
```python
class BaseScraper:
    def scrape(limit, only_new) -> Dict
    def load_index() -> List[Dict]
    def save_index(documents)
    def load_articles() -> List[Dict]
    def save_articles(articles)
    def compute_md5(content) -> str
    def export_jsonl() -> Dict
    def get_stats() -> Dict
```

#### Scrapers Específicos

Cada scraper hereda de `BaseScraper` e implementa la lógica específica del sitio:

1. **TCPScraper**: Tribunal Constitucional Plurinacional
   - Sentencias constitucionales
   - Formato: SC-XXXX/YYYY

2. **TSJScraper**: Tribunal Supremo de Justicia
   - Autos supremos
   - Múltiples salas

3. **ASFIScraper**: Autoridad de Supervisión del Sistema Financiero
   - Resoluciones financieras
   - Normativa bancaria

4. **SINScraper**: Servicio de Impuestos Nacionales
   - Resoluciones normativas tributarias
   - Circulares

5. **ContraloriaScraper**: Contraloría General del Estado
   - Informes de auditoría
   - Resoluciones administrativas

### 2. Legal Parser

#### LegalParser

Parser especializado para documentos legales bolivianos.

**Funcionalidades:**
- Detección automática de artículos
- Extracción de estructura legal
- Soporte para múltiples formatos
- Preservación de contexto

**Patrones Soportados:**
```regex
Artículo \d+[°º]?
Art\. \d+[°º]?
ARTÍCULO \d+[°º]?
```

**Ejemplo de Parsing:**
```python
from scraper.parser import LegalParser

document = {
    'id': 'tcp-000001',
    'content': 'Artículo 1.- Contenido...\nArtículo 2.- Más contenido...'
}

articles = LegalParser.parse_document(document)
# [
#   {'id': 'tcp-000001-art-001', 'article_number': 1, 'content': '...'},
#   {'id': 'tcp-000001-art-002', 'article_number': 2, 'content': '...'}
# ]
```

### 3. Metadata Extractor

#### MetadataExtractor

Extractor inteligente de metadatos de documentos legales.

**Capacidades:**
- Extracción de fechas (múltiples formatos)
- Extracción de números de documento
- Detección de tipo de documento
- Enriquecimiento automático

**Formatos de Fecha Soportados:**
- "15 de enero de 2024"
- "15/01/2024"
- "2024-01-15"

### 4. Supabase Sync Module

#### SupabaseSync

Gestor de sincronización bidireccional con Supabase.

**Características:**
- Detección de duplicados por MD5
- Inserción de nuevos documentos
- Actualización de modificados
- Logging detallado
- Manejo de errores

**Flujo de Sincronización:**

```
┌─────────────┐
│  Local JSON │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Check MD5       │
│ in Supabase     │
└──────┬──────────┘
       │
       ├─── Exists + Same MD5 ──→ Skip
       │
       ├─── Exists + Diff MD5 ──→ Update
       │
       └─── Not Exists ─────────→ Insert
```

**Funciones Públicas:**
```python
sync_documents_to_supabase(site, only_new)
sync_articles_to_supabase(site, only_new)
sync_all_sites(only_new)
verify_duplicates(site)
get_stats_from_supabase(site)
```

### 5. Streamlit UI

#### Interfaz Completa

**Componentes:**

1. **Sidebar**
   - Selector de sitio
   - Estadísticas en tiempo real
   - Controles de scraping
   - Botones de exportación
   - Botones de sincronización

2. **Pestaña Documents**
   - Tabla interactiva
   - Visor de documentos
   - Filtros
   - Métricas

3. **Pestaña Articles**
   - Tabla de artículos
   - Visor de contenido
   - Metadatos expandibles

4. **Pestaña Statistics**
   - Gráficas de volumen
   - Comparación entre sitios
   - Distribución (pie chart)
   - Métricas agregadas

5. **Pestaña Logs**
   - Visualización de logs de sync
   - Historial de operaciones

### 6. Scheduler

#### Scheduler Automático

Sistema de tareas programadas para scraping automático.

**Características:**
- Scraping diario a las 2 AM
- Sincronización automática con Supabase
- Logging detallado
- Exportación automática
- Soporte para ejecución inmediata

**Modos de Ejecución:**

1. **Inmediato**: `python scheduler/run_daily.py --now`
2. **Daemon**: `python scheduler/run_daily.py --daemon`
3. **Systemd**: Integración con systemd para ejecución persistente

## 📊 Flujos de Datos

### Flujo de Scraping

```
1. Iniciar Scraper
   ↓
2. Cargar Índice Existente
   ↓
3. Hacer Request HTTP
   ↓
4. Parsear HTML
   ↓
5. Extraer Contenido
   ↓
6. Calcular MD5
   ↓
7. Comparar con Existente
   ↓
8. Clasificar (Nuevo/Modificado/Sin Cambios)
   ↓
9. Actualizar Índice
   ↓
10. Guardar JSON
```

### Flujo de Parsing

```
1. Cargar Documentos
   ↓
2. Para cada documento:
   ├─ Aplicar RegEx de Artículos
   ├─ Extraer Números
   ├─ Extraer Contenido
   └─ Crear Objeto Article
   ↓
3. Guardar Articles JSON
```

### Flujo de Exportación

```
1. Cargar JSON
   ↓
2. Para cada documento/artículo:
   └─ Escribir línea JSONL
   ↓
3. Guardar exports/{site}/documents.jsonl
4. Guardar exports/{site}/articles.jsonl
```

### Flujo de Sincronización

```
1. Cargar JSON Local
   ↓
2. Conectar a Supabase
   ↓
3. Para cada documento:
   ├─ Query por MD5
   ├─ Si existe y MD5 igual → Skip
   ├─ Si existe y MD5 diferente → Update
   └─ Si no existe → Insert
   ↓
4. Log Results
   ↓
5. Guardar logs/sync/{timestamp}.json
```

## 🗄️ Esquemas de Datos

### Document Schema

```json
{
  "id": "tcp-000001",
  "site": "tcp",
  "url": "https://www.tcpbolivia.bo/...",
  "title": "Sentencia Constitucional SC-0001/2024",
  "content": "Texto completo del documento...",
  "md5": "a1b2c3d4e5f6...",
  "status": "new",
  "scraped_at": "2024-01-15T10:30:00",
  "metadata": {
    "tipo": "Sentencia Constitucional",
    "numero": "SC-0001/2024",
    "fecha": "2024-01-15"
  }
}
```

### Article Schema

```json
{
  "id": "tcp-000001-art-001",
  "document_id": "tcp-000001",
  "site": "tcp",
  "article_number": 1,
  "content": "Contenido del artículo...",
  "metadata": {
    "document_title": "Sentencia Constitucional SC-0001/2024",
    "document_url": "https://...",
    "document_type": "Sentencia Constitucional",
    "parsed_at": "2024-01-15T10:30:00"
  }
}
```

### Sync Log Schema

```json
{
  "site": "tcp",
  "timestamp": "2024-01-15T10:30:00",
  "inserted": 5,
  "updated": 2,
  "skipped": 10,
  "errors": 0
}
```

## 🔧 Instalación y Configuración

### Requisitos

- Python 3.8+
- pip
- Conexión a Internet
- (Opcional) Cuenta de Supabase

### Pasos de Instalación

1. **Clonar Repositorio**
   ```bash
   git clone https://github.com/zambogram/bo-gov-scraper-buho.git
   cd bo-gov-scraper-buho
   ```

2. **Crear Entorno Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Supabase** (Opcional)
   ```bash
   cp .env.example .env
   # Editar .env con credenciales
   ```

5. **Crear Tablas en Supabase**
   - Ejecutar SQL schema (ver README.md)

## 🧪 Testing

### Tests Manuales

```bash
# Test 1: Listar sitios
python main.py listar

# Test 2: Scrape individual
python main.py scrape tcp --limit 2

# Test 3: Scrape todos
python main.py actualizar-todos --limit 2

# Test 4: Export
python main.py export-jsonl tcp

# Test 5: UI
streamlit run app/streamlit_app.py

# Test 6: Scheduler
python scheduler/run_daily.py --now
```

### Validación de Datos

```python
# Verificar índice
import json
with open('data/index/tcp_index.json') as f:
    docs = json.load(f)
    print(f"Total documents: {len(docs)}")
    print(f"First doc: {docs[0]}")

# Verificar artículos
with open('data/articles/tcp_articles.json') as f:
    arts = json.load(f)
    print(f"Total articles: {len(arts)}")

# Verificar export
with open('exports/tcp/documents.jsonl') as f:
    lines = f.readlines()
    print(f"JSONL lines: {len(lines)}")
```

## 📈 Métricas y Monitoreo

### Métricas Clave

1. **Scraping**
   - Documentos nuevos por día
   - Documentos modificados por día
   - Tasa de error
   - Tiempo de ejecución

2. **Parsing**
   - Artículos extraídos por documento
   - Tasa de éxito de parsing

3. **Sincronización**
   - Documentos sincronizados
   - Duplicados detectados
   - Fallos de sincronización

### Logs

```
logs/
├── sync/
│   ├── sync_tcp_20240115_103000.json
│   ├── sync_tsj_20240115_103100.json
│   └── ...
└── auto/
    ├── scraping_20240115_020000.json
    └── ...
```

## 🚀 Deployment

### Producción

1. **Configurar Servidor**
   - Ubuntu 20.04+ / Debian 11+
   - Python 3.8+
   - Nginx (para UI)

2. **Setup Systemd**
   ```bash
   sudo cp buho-scraper.service /etc/systemd/system/
   sudo systemctl enable buho-scraper
   sudo systemctl start buho-scraper
   ```

3. **Setup Nginx para Streamlit**
   ```nginx
   location / {
       proxy_pass http://localhost:8501;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

## 🔒 Seguridad

### Mejores Prácticas

1. **Credenciales**
   - Nunca commitear .env
   - Usar variables de entorno
   - Rotar keys regularmente

2. **Rate Limiting**
   - Respetar robots.txt
   - Implementar delays entre requests
   - No sobrecargar servidores

3. **Validación**
   - Validar datos antes de insertar
   - Sanitizar contenido
   - Escapar SQL (Supabase lo hace automáticamente)

## 🎓 Extensibilidad

### Agregar Nuevo Scraper

1. Crear `scraper/nuevo_scraper.py`:
   ```python
   from scraper.base_scraper import BaseScraper

   class NuevoScraper(BaseScraper):
       def __init__(self):
           super().__init__(name='nuevo', base_url='https://...')

       def scrape(self, limit=None, only_new=False):
           # Implementar lógica
           pass
   ```

2. Registrar en `scraper/__init__.py`:
   ```python
   from scraper.nuevo_scraper import NuevoScraper

   SCRAPERS = {
       # ...
       'nuevo': NuevoScraper
   }
   ```

## 📚 Referencias

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Schedule Library](https://schedule.readthedocs.io/)

## 🤝 Soporte

Para preguntas o problemas:
- GitHub Issues: https://github.com/zambogram/bo-gov-scraper-buho/issues
- Email: [contacto]

---

**Versión**: FASE 10
**Fecha**: 2025-01-15
**Autor**: Zambogram
