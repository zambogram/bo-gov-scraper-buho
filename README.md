# 🦉 BO-GOV-SCRAPER-BUHO

**Scraper completo de páginas del Estado boliviano + OCR + metadatos para BÚHO**

Sistema integral de scraping, procesamiento y almacenamiento local de normativa legal boliviana, con interfaz web interactiva y CLI potente.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Interfaz Web (Streamlit)](#-interfaz-web-streamlit)
- [CLI](#-cli)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Configuración](#-configuración)
- [Pipeline de Procesamiento](#-pipeline-de-procesamiento)
- [Sitios Soportados](#-sitios-soportados)
- [Desarrollo](#-desarrollo)

---

## ✨ Características

### Pipeline Completo
- **Scraping automatizado** de sitios gubernamentales bolivianos
- **Extracción de texto** desde PDFs con soporte para OCR
- **Parsing legal** inteligente: división automática en artículos, secciones, capítulos
- **Delta updates**: procesamiento incremental (solo documentos nuevos)
- **Modo histórico**: scraping completo de archivos históricos

### Almacenamiento Local Controlable
- PDFs originales (opcional)
- Texto normalizado (.txt)
- Estructura JSON con metadatos y artículos
- Sistema de índices para actualizaciones incrementales

### Interfaz Web (Streamlit)
- Control total del pipeline desde la UI
- Visualización de documentos y artículos
- Estadísticas en tiempo real
- Logs de proceso

### CLI Potente
- Scraping por sitio o todos los sitios
- Modo delta o histórico completo
- Control granular de qué guardar
- Estadísticas globales

---

## 🚀 Instalación

### Requisitos
- Python 3.12+
- Tesseract OCR (opcional, para PDFs escaneados)

### Pasos

1. **Clonar repositorio**
   ```bash
   git clone https://github.com/zambogram/bo-gov-scraper-buho.git
   cd bo-gov-scraper-buho
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar (opcional)**
   ```bash
   cp .env.example .env
   # Editar .env según necesidades
   ```

---

## 💡 Uso Rápido

### Interfaz Web (Streamlit)

```bash
streamlit run app/streamlit_app.py
```

Abre tu navegador en `http://localhost:8501`

### CLI - Ejemplos Básicos

```bash
# Listar sitios disponibles
python main.py listar

# Scraping rápido de TCP (solo nuevos, 3 documentos)
python main.py scrape tcp --mode delta --limit 3

# Scraping completo de TSJ guardando PDFs
python main.py scrape tsj --mode full --limit 10 --save-pdf

# Ver estadísticas
python main.py stats
```

---

## 🌐 Interfaz Web (Streamlit)

La interfaz web proporciona control total sobre el pipeline de scraping.

### Sidebar: Configuración

**1. Sitio**
- Seleccionar sitio a procesar
- Ver información: tipo, categoría, prioridad, última actualización

**2. Modo de Scraping**
- **Delta**: Solo documentos nuevos (recomendado)
- **Histórico completo**: Procesar todo el archivo
- **Límite por corrida**: Cuántos documentos procesar (default: 50)

**3. Qué Guardar**
- [ ] Guardar PDF original
- [x] Guardar texto normalizado (.txt)
- [x] Guardar estructura JSON (.json)

**4. Acciones**
- **Raspar sitio seleccionado**: Ejecutar pipeline para un sitio
- **Raspar TODOS los sitios**: Ejecutar pipeline para todos

### Pestañas Principales

**📄 Documentos**
- Tabla de documentos procesados
- Vista previa de texto
- Metadata completa

**📑 Artículos**
- Todos los artículos parseados
- Filtros por tipo y documento
- Vista detallada

**📊 Estadísticas**
- Métricas globales
- Estadísticas por sitio
- Gráficos interactivos

**📝 Logs**
- Logs de sesión actual en tiempo real
- Logs históricos por sitio

---

## 🖥️ CLI

### Comandos Disponibles

#### `listar` (aliases: `list`, `ls`)
Listar todos los sitios disponibles

```bash
python main.py listar
```

#### `scrape`
Ejecutar scraping de uno o todos los sitios

```bash
# Sintaxis
python main.py scrape [SITIO] [OPCIONES]

# Sitios disponibles
tcp, tsj, asfi, sin, contraloria, all
```

**Opciones:**

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--mode {full,delta}` | Modo de scraping | `delta` |
| `--limit N` | Límite de documentos | Sin límite |
| `--save-pdf` | Guardar PDFs originales | No guardar |
| `--no-txt` | NO guardar texto | Guardar |
| `--no-json` | NO guardar JSON | Guardar |

**Ejemplos:**

```bash
# Delta update de TCP (solo nuevos, 50 docs)
python main.py scrape tcp --mode delta --limit 50

# Histórico completo de TSJ con PDFs (20 docs)
python main.py scrape tsj --mode full --limit 20 --save-pdf

# Todos los sitios, delta, 10 docs cada uno
python main.py scrape all --mode delta --limit 10

# Solo JSON, sin texto ni PDFs
python main.py scrape asfi --no-txt
```

#### `stats`
Ver estadísticas globales

```bash
python main.py stats
```

---

## 📁 Estructura del Proyecto

```
bo-gov-scraper-buho/
├── app/
│   └── streamlit_app.py          # Interfaz web Streamlit
├── config/
│   ├── __init__.py
│   ├── settings.py                # Configuración global
│   └── sites_catalog.yaml         # Catálogo de sitios
├── scraper/
│   ├── __init__.py
│   ├── models.py                  # Modelos de datos
│   ├── pipeline.py                # Pipeline central
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── pdf_extractor.py       # Extracción de texto/OCR
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── legal_parser.py        # Parser legal (artículos)
│   └── sites/
│       ├── __init__.py
│       ├── base_scraper.py        # Scraper base
│       ├── tcp_scraper.py
│       ├── tsj_scraper.py
│       ├── asfi_scraper.py
│       ├── sin_scraper.py
│       └── contraloria_scraper.py
├── data/                          # Datos locales (gitignored)
│   ├── raw/{site}/pdfs/           # PDFs sin procesar
│   ├── normalized/{site}/text/    # Texto normalizado
│   ├── normalized/{site}/json/    # JSON estructurado
│   └── index/{site}/index.json    # Índices delta
├── logs/                          # Logs por sitio
├── docs/
│   └── PIPELINE_LOCAL.md          # Doc del pipeline
├── main.py                        # CLI principal
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Directorios base
DATA_BASE_DIR=data
LOGS_DIR=logs
EXPORTS_DIR=exports

# Scraping
MAX_CONCURRENT_DOWNLOADS=3
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3

# OCR (opcional)
TESSERACT_PATH=/usr/bin/tesseract
TESSERACT_LANG=spa

# Supabase (opcional)
SUPABASE_URL=
SUPABASE_KEY=
```

### Catálogo de Sitios

Los sitios se configuran en `config/sites_catalog.yaml`:

```yaml
sites:
  tcp:
    id: tcp
    nombre: "Tribunal Constitucional Plurinacional"
    tipo: "Tribunal"
    url_base: "https://www.tcpbolivia.bo"
    prioridad: 1
    activo: true
    # ... más configuración
```

---

## 🔄 Pipeline de Procesamiento

Ver [docs/PIPELINE_LOCAL.md](docs/PIPELINE_LOCAL.md) para documentación detallada.

### Flujo General

Para cada documento:

1. **Descarga de PDF**
   - Guardar en `data/raw/{site}/pdfs/` (opcional)
   - O usar archivo temporal

2. **Extracción de Texto**
   - PyPDF2 para PDFs digitales
   - Tesseract OCR para PDFs escaneados
   - Guardar en `data/normalized/{site}/text/{id}.txt`

3. **Parsing Legal**
   - Dividir en artículos, secciones, capítulos
   - Extraer metadata (número, título, contenido)

4. **Guardado JSON**
   - Estructura completa del documento
   - Array de artículos con metadata
   - Guardar en `data/normalized/{site}/json/{id}.json`

5. **Actualización de Índice**
   - Actualizar `data/index/{site}/index.json`
   - Hash MD5 para delta updates
   - Rutas a archivos generados

---

## 🏛️ Sitios Soportados

| Sitio | ID | Tipo | Prioridad | Estado |
|-------|----|----- |-----------|--------|
| TCP | `tcp` | Tribunal | 1 | ✅ Activo |
| TSJ | `tsj` | Tribunal | 1 | ✅ Activo |
| ASFI | `asfi` | Ente Regulador | 2 | ✅ Activo |
| SIN | `sin` | Ente Tributario | 2 | ✅ Activo |
| Contraloría | `contraloria` | Control | 2 | ✅ Activo |
| Gaceta Oficial | `gaceta_oficial` | Gaceta | 1 | 🔜 Próximamente |

**Nota:** Los scrapers actuales retornan datos de ejemplo. Se debe implementar la lógica de scraping real para cada sitio según su estructura web.

---

## 🛠️ Desarrollo

### Agregar Nuevo Sitio

1. **Agregar entrada en `config/sites_catalog.yaml`**
2. **Crear scraper en `scraper/sites/{sitio}_scraper.py`**
3. **Heredar de `BaseScraper`**
4. **Implementar métodos:**
   - `listar_documentos(limite)`
   - `descargar_pdf(url, ruta_destino)`
5. **Registrar en `scraper/sites/__init__.py`**

### Testing

```bash
# Probar CLI
python main.py listar
python main.py scrape tcp --limit 1

# Probar UI
streamlit run app/streamlit_app.py
```

### Logging

Los logs se guardan en:
- `logs/{site}/scrape_{timestamp}.log`
- Stdout/stderr durante ejecución

---

## 📜 Licencia

[Especificar licencia]

---

## 👥 Contribuidores

Proyecto BÚHO - Sistema de información legal boliviano

---

## 📞 Contacto

[Información de contacto]

---

## 🗺️ Roadmap

- [x] Pipeline completo de scraping local
- [x] Interfaz Streamlit con control total
- [x] CLI robusto
- [x] Sistema de delta updates
- [ ] Scrapers reales para cada sitio
- [ ] Scraper de Gaceta Oficial
- [ ] Sincronización con Supabase
- [ ] API REST
- [ ] Tests automatizados
- [ ] Docker containerization

---

**Última actualización:** 2025-11-18
