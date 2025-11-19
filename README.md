# 🦉 BÚHO - Scraper Completo de Leyes Bolivianas

Sistema profesional de scraping, procesamiento, normalización y exportación de documentos legales del Estado Plurinacional de Bolivia.

## 📋 Características Principales

### ✨ Funcionalidades Completas

- **Scraping Multi-Sitio**: Scrapea simultáneamente +33 sitios del gobierno boliviano
- **Scraping con Selenium**: Scraper especializado para TCP Jurisprudencia con navegación dinámica
- **Procesamiento Inteligente**: PDF, DOC, DOCX e imágenes con OCR automático
- **Extracción de Metadatos**: Extrae automáticamente número de ley, área del derecho, fechas, etc.
- **División de PDFs**: Divide PDFs grandes en secciones manejables
- **Base de Datos SQLite**: Registro histórico completo con búsqueda y estadísticas
- **Exportación Múltiple**: CSV, JSON, Excel con todos los metadatos
- **Normalización**: Convierte todos los documentos a PDF con texto buscable
- **Interfaz Web**: Dashboard Streamlit para visualización y gestión

### 🎯 Sitios Gubernamentales Soportados

El sistema está configurado para scrapear 33+ sitios incluyendo:

- Gaceta Oficial de Bolivia
- Asamblea Legislativa Plurinacional
- **Tribunal Constitucional Plurinacional** (con Selenium para jurisprudencia completa)
- Ministerios (Justicia, Economía, Trabajo, Salud, etc.)
- Órgano Judicial
- Contraloría General del Estado
- Autoridades Regulatorias (ASFI, SIN, Aduana, etc.)
- Y muchos más...

## 🚀 Instalación

### Requisitos Previos

- Python 3.8+
- Tesseract OCR (para reconocimiento de texto en imágenes)
- LibreOffice (opcional, para convertir DOC a PDF)
- Chrome/Chromium (para scraping del TCP con Selenium)

### Instalación de Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki

### Instalación del Proyecto

1. Clonar el repositorio:
```bash
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 📖 Uso

### Modo CLI (Línea de Comandos)

El sistema ofrece múltiples comandos para diferentes operaciones:

#### 1. Scraping de Sitios Web

Scrapea todos los sitios configurados y descarga documentos:

```bash
python main.py --scrapear --workers 5
```

#### 1.1. Scraping del TCP (Tribunal Constitucional) con Selenium

Scrapea jurisprudencia del TCP usando Selenium para navegación dinámica:

```bash
# Solo scraping del TCP
python main.py --tcp

# Flujo completo del TCP (scrapear + procesar + exportar)
python main.py --tcp-completo --ocr
```

El scraper del TCP extrae:
- Número de resolución
- Tipo de jurisprudencia
- Tipo resolutivo
- Fecha
- Sumilla completa
- Magistrados
- Área/materia
- PDFs de sentencias

Ver documentación completa en: `scraper/sites/README_TCP.md`

#### 2. Procesamiento de Documentos

Procesa los documentos descargados, extrae texto y metadatos:

```bash
python main.py --procesar --ocr --dividir-pdfs
```

Opciones:
- `--ocr`: Aplica OCR a documentos escaneados
- `--dividir-pdfs`: Divide PDFs grandes en secciones

#### 3. Exportación de Datos

Exporta los datos a diferentes formatos:

```bash
python main.py --exportar --formato csv json excel
```

#### 4. Ver Estadísticas

Muestra estadísticas completas del sistema:

```bash
python main.py --stats
```

#### 5. Flujo Completo

Ejecuta todo el proceso (scrapear + procesar + exportar):

```bash
python main.py --completo --workers 5 --ocr --dividir-pdfs
```

### Modo Interfaz Web (Streamlit)

Lanza la interfaz web interactiva:

```bash
streamlit run app/streamlit_app.py
```

## 📊 Estructura de Datos

### Metadatos Extraídos

Para cada documento legal, el sistema extrae y almacena:

**Identificación:**
- Número de ley (ej: "Ley 1178")
- Tipo de norma (Ley, Decreto Supremo, Resolución, etc.)
- Título completo
- Código único (hash SHA256)

**Clasificación Jurídica:**
- Área del derecho (Constitucional, Penal, Laboral, etc.)
- Jerarquía normativa
- Materias y palabras clave

**Información Temporal:**
- Fecha de promulgación
- Fecha de publicación
- Fecha de vigencia
- Vigencia actual (sí/no)

**Origen y Fuente:**
- Órgano emisor
- Firmante
- URL de origen
- Sitio web fuente
- Fecha de scraping

**Documento:**
- Formato original (PDF, DOC, etc.)
- Tamaño en bytes
- Número de páginas
- Hashes MD5 y SHA256
- Rutas de archivos

**Procesamiento:**
- OCR aplicado (sí/no)
- Confianza del OCR (0-1)
- Idioma detectado
- Texto completo extraído
- Estado de procesamiento

**Contenido:**
- Artículos principales
- Total de artículos
- Total de palabras y caracteres
- Relaciones con otras leyes

## 🗂️ Estructura del Proyecto

```
bo-gov-scraper-buho/
├── config/
│   ├── sites_config.yaml          # Configuración de 33+ sitios
│   └── metadata_schema.yaml       # Esquema de metadatos
├── scraper/
│   ├── __init__.py
│   ├── multi_site_scraper.py      # Scraper principal
│   ├── sites/                     # Scrapers especializados
│   │   ├── __init__.py
│   │   ├── tcp_jurisprudencia_scraper.py  # Scraper TCP con Selenium
│   │   └── README_TCP.md          # Documentación del TCP scraper
│   ├── document_processor.py      # Procesador con OCR
│   ├── metadata.py                # Extractor de metadatos
│   ├── pdf_splitter.py            # Divisor de PDFs
│   └── database.py                # Gestor de BD SQLite
├── exporters/
│   ├── csv_exporter.py
│   ├── json_exporter.py
│   └── excel_exporter.py
├── data/
│   ├── raw/                       # Documentos originales
│   │   └── tcp_jurisprudencia/    # Sentencias del TCP
│   ├── processed/                 # Documentos procesados
│   └── laws.db                    # Base de datos SQLite
├── exports/                        # Exportaciones
├── app/
│   └── streamlit_app.py           # Interfaz web
├── main.py                         # Script principal
├── requirements.txt                # Dependencias
└── README.md                       # Este archivo
```

## 🔧 Configuración

### Configurar Sitios Web

Edita `config/sites_config.yaml` para:
- Habilitar/deshabilitar sitios
- Ajustar prioridades
- Configurar selectores CSS personalizados
- Modificar parámetros de scraping

### Configurar Metadatos

Edita `config/metadata_schema.yaml` para:
- Agregar nuevos campos de metadatos
- Modificar patrones de extracción
- Definir áreas del derecho adicionales

## 💾 Base de Datos

### Esquema de Tablas

**leyes**: Tabla principal con todos los metadatos
**historial_scraping**: Registro de cada sesión de scraping
**estadisticas_globales**: Estadísticas agregadas
**areas_derecho**: Catálogo de áreas del derecho

### Consultas de Ejemplo

```python
from scraper.database import LawDatabase

with LawDatabase() as db:
    # Buscar leyes por área
    leyes_laborales = db.buscar_ley(area_derecho="Laboral")

    # Buscar leyes vigentes
    leyes_vigentes = db.buscar_ley(vigente=True)

    # Obtener estadísticas
    stats = db.obtener_estadisticas()

    # Exportar a CSV
    db.exportar_a_csv("exports/leyes.csv")
```

## 📤 Formatos de Exportación

### CSV
Archivo plano compatible con Excel, ideal para análisis de datos

### JSON
Formato estructurado con todos los metadatos, ideal para APIs

### Excel
Archivo .xlsx con formato, ideal para reportes

## 🔍 Ejemplos de Uso

### Ejemplo 1: Scrapear solo sitios específicos

```python
from scraper.multi_site_scraper import MultiSiteScraper

scraper = MultiSiteScraper()
# Modificar config para habilitar solo ciertos sitios
resultados = scraper.scrapear_todos_los_sitios(max_workers=3)
```

### Ejemplo 2: Procesar un documento específico

```python
from scraper.document_processor import DocumentProcessor
from scraper.metadata import MetadataExtractor

processor = DocumentProcessor()
extractor = MetadataExtractor()

# Procesar documento
resultado = processor.procesar_documento("mi_ley.pdf")

# Extraer metadatos
metadatos = extractor.extraer_metadatos(
    resultado['texto'],
    archivo_path="mi_ley.pdf",
    sitio_web="Gaceta Oficial",
    url_origen="https://..."
)
```

### Ejemplo 3: Dividir un PDF grande

```python
from scraper.pdf_splitter import PDFSplitter

splitter = PDFSplitter()

# Dividir PDF
archivos = splitter.dividir_pdf(
    "ley_grande.pdf",
    max_paginas_por_seccion=30,
    dividir_por_estructura=True
)

# Agregar metadatos a cada sección
for archivo in archivos:
    splitter.agregar_metadatos_a_seccion(archivo, metadatos)
```

## 📈 Flujo de Trabajo Recomendado

### Para Scraping Completo (Primera Vez)

```bash
# 1. Scrapear todos los sitios (puede tardar horas)
python main.py --scrapear --workers 5

# 2. Scrapear el TCP con Selenium (puede tardar varias horas)
python main.py --tcp

# 3. Procesar documentos con OCR y división
python main.py --procesar --ocr --dividir-pdfs

# 4. Exportar a todos los formatos
python main.py --exportar --formato csv json excel

# 5. Ver estadísticas
python main.py --stats
```

### Para Scraping Solo del TCP

```bash
# Flujo completo del TCP en un solo comando
python main.py --tcp-completo --ocr --dividir-pdfs
```

### Para Actualizaciones Periódicas

```bash
# Flujo completo con menos hilos (más respetuoso)
python main.py --completo --workers 3 --ocr
```

## ⚙️ Optimización y Rendimiento

### Scraping
- **Concurrent workers**: Ajusta `--workers` según tu conexión (3-10)
- **Delay entre requests**: Configurado en 2 segundos por defecto
- **Retry attempts**: 3 intentos automáticos por defecto

### Procesamiento
- OCR puede ser lento: desactiva con `--ocr` si no es necesario
- División de PDFs: solo para documentos >50 páginas por defecto

### Base de Datos
- Índices automáticos en campos clave
- Consultas optimizadas
- Backups automáticos recomendados

## 🐛 Solución de Problemas

### Error: "Tesseract not found"
Instala Tesseract OCR y agrega al PATH del sistema

### Error: "LibreOffice not found"
La conversión DOC→PDF requiere LibreOffice (opcional)

### PDFs sin texto extraído
Activa `--ocr` para aplicar OCR a documentos escaneados

### Sitio web no responde
Algunos sitios pueden estar temporalmente caídos o bloquear bots

## 📜 Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

Para preguntas, sugerencias o reportar problemas, abre un issue en GitHub.

## 🙏 Agradecimientos

- A todos los sitios gubernamentales bolivianos por hacer pública la información legal
- A la comunidad de código abierto por las excelentes bibliotecas utilizadas

---

**🦉 BÚHO** - Scraper Profesional de Leyes Bolivianas | 2024
