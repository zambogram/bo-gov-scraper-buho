# 🦉 BÚHO - Motor Multi-sitio de Scraping Jurídico Boliviano

**Sistema completo de captura, procesamiento y exportación de normativa y jurisprudencia de fuentes estatales bolivianas.**

---

## 📋 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Comandos CLI](#-comandos-cli)
- [Interfaz Web](#-interfaz-web)
- [Catálogo de Sitios](#-catálogo-de-sitios)
- [Arquitectura](#-arquitectura)
- [Documentación](#-documentación)
- [Roadmap](#-roadmap)

---

## 🎯 Descripción

BÚHO es un **motor multi-sitio de scraping jurídico** diseñado específicamente para el ecosistema legal boliviano. El sistema:

1. **Scrapea automáticamente** sitios estatales (Gaceta Oficial, TCP, TSJ, ASFI, SIN, etc.)
2. **Procesa documentos** (PDFs, HTMLs) extrayendo texto con OCR si es necesario
3. **Segmenta contenido** en unidades útiles (artículos, secciones, fundamentos, etc.)
4. **Exporta datos** en formato JSONL listo para Supabase/pgvector
5. **Actualiza incrementalmente** solo documentos nuevos o modificados (delta-update)

### Objetivo

Crear la **base de datos legal más completa de Bolivia** para alimentar aplicaciones LegalTech con búsqueda semántica, RAG, y análisis jurídico.

---

## ✨ Características

### Arquitectura Multi-sitio

- ✅ **Catálogo centralizado** de todos los sitios estatales bolivianos
- ✅ **Scrapers modulares** por sitio con configuración unificada
- ✅ **Sistema de prioridades** (Ola 1 MVP, Ola 2, Ola 3+)
- ✅ **Delta-update inteligente** (solo procesa lo nuevo)

### Procesamiento Avanzado

- 📄 **Extracción de PDFs** (texto digital + OCR para escaneados)
- 🔍 **Detección automática** de tipo de documento (ley, decreto, sentencia, etc.)
- ✂️ **Segmentación legal** en artículos, secciones, fundamentos, etc.
- 🏷️ **Metadatos ricos** (tipo_norma, número, fecha, fuente, etc.)

### Interfaces

- 💻 **CLI completo** con Rich (tablas, colores, progreso)
- 🌐 **UI web con Streamlit** (dashboard, filtros, stats, scraping)
- 📊 **Estadísticas en tiempo real** del catálogo

### Exportación

- 📤 **Formato Supabase** (JSONL + schema SQL)
- 🔌 **Listo para pgvector** (búsqueda semántica)
- 📈 **Métricas por sitio** (documentos, artículos, última actualización)

---

## 🚀 Instalación

### Requisitos

- Python 3.9+
- pip

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 3: Verificar instalación

```bash
python main.py --version
python main.py validate
```

---

## ⚡ Uso Rápido

### 1. Listar todos los sitios catalogados

```bash
python main.py list
```

### 2. Ver solo sitios de Ola 1 (MVP)

```bash
python main.py list --prioridad 1
```

### 3. Ver información detallada de un sitio

```bash
python main.py info gaceta_oficial
python main.py info tcp
python main.py info asfi
```

### 4. Ver estadísticas del catálogo

```bash
python main.py stats
```

### 5. Ejecutar scraping (cuando esté implementado)

```bash
python main.py scrape gaceta_oficial --limit 10
python main.py demo-ola1 --limit 5
```

### 6. Iniciar interfaz web

```bash
streamlit run app/streamlit_app.py
```

---

## 📋 Comandos CLI

### `list` - Listar sitios

```bash
# Todos los sitios
python main.py list

# Filtrar por prioridad
python main.py list --prioridad 1
python main.py list --prioridad 2

# Filtrar por estado
python main.py list --estado implementado
python main.py list --estado pendiente

# Filtrar por tipo
python main.py list --tipo normativa
python main.py list --tipo jurisprudencia
python main.py list --tipo regulador

# Filtrar por nivel
python main.py list --nivel nacional
python main.py list --nivel departamental

# Salida JSON
python main.py list --prioridad 1 --json
```

### `info` - Información detallada

```bash
# Ver detalles de un sitio
python main.py info gaceta_oficial

# Salida JSON
python main.py info tcp --json
```

### `stats` - Estadísticas

```bash
# Estadísticas del catálogo completo
python main.py stats

# Salida JSON
python main.py stats --json
```

### `validate` - Validar catálogo

```bash
# Verificar integridad del catálogo
python main.py validate
```

### `scrape` - Ejecutar scraping

```bash
# Scraping limitado
python main.py scrape gaceta_oficial --limit 10

# Scraping completo
python main.py scrape tcp --full

# Forzar re-scraping
python main.py scrape asfi --force
```

### `demo-ola1` - Demo sitios prioritarios

```bash
# Demo de scraping Ola 1
python main.py demo-ola1

# Con límite personalizado
python main.py demo-ola1 --limit 5
```

---

## 🌐 Interfaz Web

### Iniciar Streamlit

```bash
streamlit run app/streamlit_app.py
```

### Características de la UI

- **Dashboard**: Métricas generales, distribuciones, sitios Ola 1
- **Sitios**: Navegación con filtros (prioridad, estado, nivel, tipo)
- **Estadísticas**: Resumen completo, tabla exportable a CSV
- **Configuración**: Validación de catálogo, rutas del proyecto

### Pantallas

1. **🏠 Dashboard** - Vista general con métricas clave
2. **📋 Sitios** - Catálogo completo con filtros y tarjetas expandibles
3. **📊 Estadísticas** - Análisis detallado con exportación CSV
4. **⚙️ Configuración** - Validación y opciones del sistema

---

## 📚 Catálogo de Sitios

El archivo `config/sites_catalog.yaml` es la **fuente de verdad** del sistema.

### Sitios Ola 1 (MVP - Prioridad 1)

| Site ID | Nombre | Tipo | Estado |
|---------|--------|------|--------|
| `gaceta_oficial` | Gaceta Oficial del Estado Plurinacional | Normativa | ⏳ Pendiente |
| `tsj_genesis` | Tribunal Supremo de Justicia - GENESIS | Jurisprudencia | ⏳ Pendiente |
| `tcp` | Tribunal Constitucional Plurinacional | Jurisprudencia | ⏳ Pendiente |
| `asfi` | Autoridad de Supervisión del Sistema Financiero | Regulador | ⏳ Pendiente |
| `sin` | Servicio de Impuestos Nacionales | Regulador | ⏳ Pendiente |

### Sitios Ola 2 (Importante - Prioridad 2)

- **contraloria** - Contraloría General del Estado
- **silep** - Sistema de Información Legal
- **ait** - Autoridad de Impugnación Tributaria
- **aps** - Autoridad de Pensiones y Seguros
- **att** - Autoridad de Telecomunicaciones y Transportes

### Sitios Ola 3 (Complementario - Prioridad 3)

- **lexivox** - Compendio Normativo
- **anb** - Aduana Nacional
- **Gacetas departamentales** (9 departamentos)
- **Municipios principales** (La Paz, Santa Cruz, etc.)

**Total catalogados**: 15+ sitios
**Expansión potencial**: 30+ sitios

### Ver catálogo completo

- Archivo: [`config/sites_catalog.yaml`](config/sites_catalog.yaml)
- Documentación: [`docs/SITES_CATALOG.md`](docs/SITES_CATALOG.md)

---

## 🏗️ Arquitectura

### Estructura del Proyecto

```
bo-gov-scraper-buho/
├── config/
│   └── sites_catalog.yaml        # Catálogo central de sitios
├── scraper/
│   ├── __init__.py
│   ├── catalog.py                # Gestor del catálogo
│   ├── sites/                    # Scrapers individuales (futuros)
│   ├── extractors/               # Extracción texto/OCR (futuro)
│   ├── parsers/                  # Parsers legales (futuro)
│   └── exporters/                # Exportadores (futuro)
├── app/
│   └── streamlit_app.py          # UI web
├── data/                         # Datos descargados
├── exports/                      # Exportaciones JSONL
├── docs/                         # Documentación
├── main.py                       # CLI principal
└── requirements.txt              # Dependencias
```

### Flujo de Procesamiento

```
Sitio Web → Scraping → PDF Download → Texto/OCR → Parser Legal → Artículos + Metadatos → JSONL → Supabase
```

### Componentes

1. **Catalog Manager** (`scraper/catalog.py`)
   - Gestión del catálogo YAML
   - Búsquedas y filtros
   - Actualización de metadatos

2. **CLI** (`main.py`)
   - Comandos interactivos
   - Formateo con Rich
   - Gestión de scraping

3. **UI Streamlit** (`app/streamlit_app.py`)
   - Dashboard visual
   - Navegación y filtros
   - Estadísticas y exportación

4. **Scrapers** (próximamente)
   - Un módulo por sitio
   - Configuración desde catálogo
   - Delta-update automático

---

## 📖 Documentación

### Documentos Disponibles

- [**README.md**](README.md) - Este archivo (guía general)
- [**docs/SITES_CATALOG.md**](docs/SITES_CATALOG.md) - Guía del catálogo de sitios
- [**docs/USO_PRACTICO.md**](docs/USO_PRACTICO.md) - Tutorial paso a paso
- **docs/ARCHITECTURE.md** (próximamente) - Arquitectura técnica
- **docs/SCRAPERS.md** (próximamente) - Guía de desarrollo de scrapers

### Ejemplos de Uso

Ver [`docs/USO_PRACTICO.md`](docs/USO_PRACTICO.md) para:
- Instalación completa paso a paso
- Flujos de trabajo recomendados
- Casos de uso reales
- Troubleshooting

---

## 🗺️ Roadmap

### ✅ Fase 1: Fundación (COMPLETADO)

- [x] Catálogo central de sitios con URLs reales
- [x] Módulo de gestión del catálogo (catalog.py)
- [x] CLI completo con comandos básicos
- [x] UI Streamlit con dashboard y filtros
- [x] Documentación inicial

### 🔄 Fase 2: Scrapers Ola 1 (EN CURSO)

- [ ] Implementar scraper Gaceta Oficial
- [ ] Implementar scraper TSJ GENESIS
- [ ] Implementar scraper TCP
- [ ] Implementar scraper ASFI
- [ ] Implementar scraper SIN
- [ ] Implementar scraper Contraloría

### 📅 Fase 3: Procesamiento

- [ ] Módulo de extracción de texto (PyMuPDF + Tesseract)
- [ ] Detección de PDFs escaneados vs digitales
- [ ] Parsers legales (artículos, sentencias, etc.)
- [ ] Sistema de metadatos rico
- [ ] Delta-update con hashes

### 📅 Fase 4: Exportación

- [ ] Exportador a formato Supabase (JSONL)
- [ ] Schema SQL con pgvector
- [ ] Sync automático con Supabase
- [ ] Validación de datos exportados

### 📅 Fase 5: Ola 2 y 3

- [ ] Scrapers Ola 2 (SILEP, AIT, APS, ATT)
- [ ] Scrapers Ola 3 (Lexivox, ANB, departamentales)
- [ ] Scrapers municipales

### 📅 Fase 6: Producción

- [ ] Scheduler automático (cron/Airflow)
- [ ] Monitoreo y alertas
- [ ] Logs estructurados
- [ ] Tests completos (pytest)
- [ ] CI/CD
- [ ] Dockerización

---

## 🛠️ Tecnologías

### Core

- **Python 3.9+** - Lenguaje principal
- **PyYAML** - Gestión del catálogo
- **Click + Rich** - CLI interactivo
- **Streamlit** - UI web

### Scraping (futuro)

- **Requests** - HTTP requests
- **BeautifulSoup** - Parsing HTML
- **Selenium** - Sitios dinámicos
- **lxml** - Procesamiento XML/HTML rápido

### Procesamiento PDF (futuro)

- **PyMuPDF** - Extracción de texto
- **pdfplumber** - Análisis de estructura
- **Tesseract** - OCR para PDFs escaneados
- **pytesseract** - Wrapper Python

### Datos

- **Pandas** - Manipulación de datos
- **SQLAlchemy** - ORM (futuro)
- **Supabase** - Base de datos (externo)

---

## 🤝 Contribuir

Este es un proyecto interno de BÚHO LegalTech. Para consultas:
- Contacto: [tu-email]
- Documentación: ver carpeta `docs/`

---

## 📄 Licencia

Propietario - BÚHO LegalTech Bolivia © 2025

---

## 🦉 Sobre BÚHO

**BÚHO** es una LegalTech boliviana enfocada en democratizar el acceso a la información jurídica mediante tecnología de punta (IA, RAG, búsqueda semántica).

### Visión

Crear la **base de datos legal más completa de Bolivia** y hacerla accesible para abogados, empresas, ciudadanos y desarrolladores.

### Misión

Transformar la práctica legal boliviana mediante herramientas tecnológicas que reduzcan costos, aumenten eficiencia y mejoren el acceso a la justicia.

---

**Hecho con ❤️ en Bolivia 🇧🇴**
