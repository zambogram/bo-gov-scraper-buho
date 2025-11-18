# FASE 9 - SITES REALES + PARSERS AVANZADOS + DELTA-UPDATE

## 📋 Descripción General

La FASE 9 del proyecto BÚHO implementa un sistema completo de scraping de sitios gubernamentales bolivianos con las siguientes capacidades:

- **Scraping de sitios reales** de 5 instituciones del Estado
- **Parsing avanzado de PDFs** con detección automática de OCR
- **Sistema de actualización incremental** (Delta-Update) para evitar procesamiento duplicado
- **CLI completo** con múltiples comandos y opciones
- **Arquitectura multisite** extensible y modular

## 🏛️ Sitios Implementados

### 1. Tribunal Constitucional Plurinacional (TCP)
- **Código**: `tcp`
- **URL**: https://buscador.tcpbolivia.bo
- **Documentos**: Sentencias Constitucionales (SC, SCP, SCA)
- **Secciones parseadas**:
  - VISTOS
  - ANTECEDENTES
  - PROBLEMÁTICA
  - CONSIDERANDO
  - FUNDAMENTOS JURÍDICOS
  - POR TANTO

### 2. Tribunal Supremo de Justicia (TSJ)
- **Código**: `tsj`
- **URL**: https://tsj.bo
- **Documentos**: Autos Supremos de diferentes salas
- **Salas**: Penal, Civil, Social, Contencioso Administrativa
- **Secciones parseadas**:
  - RESULTANDOS
  - CONSIDERANDOS
  - PARTE RESOLUTIVA

### 3. Contraloría General del Estado
- **Código**: `contraloria`
- **URL**: https://www.contraloria.gob.bo
- **Documentos**: Resoluciones de Contraloría
- **Parsing**: Estructura por numerales romanos (I, II, III, etc.)

### 4. ASFI (Autoridad de Supervisión del Sistema Financiero)
- **Código**: `asfi`
- **URL**: https://www.asfi.gob.bo
- **Documentos**:
  - Resoluciones Administrativas
  - Circulares
  - Comunicados
- **Parsing**: Articulado y estructura formal

### 5. SIN (Servicio de Impuestos Nacionales)
- **Código**: `sin`
- **URL**: https://www.impuestos.gob.bo
- **Documentos**:
  - RND (Normas de Directorio)
  - RA (Resoluciones Administrativas)
  - RM (Resoluciones Ministeriales)
- **Parsing**: Articulado específico de normativa tributaria

## 🏗️ Arquitectura del Sistema

```
bo-gov-scraper-buho/
├── scraper/
│   ├── core/                    # Módulos base
│   │   ├── __init__.py
│   │   ├── base_scraper.py     # Clase base abstracta
│   │   ├── pdf_parser.py       # Parser avanzado con OCR
│   │   ├── delta_manager.py    # Sistema delta-update
│   │   └── utils.py            # Utilidades comunes
│   │
│   ├── sites/                   # Scrapers específicos
│   │   ├── __init__.py
│   │   ├── tcp_scraper.py      # Tribunal Constitucional
│   │   ├── tsj_scraper.py      # Tribunal Supremo
│   │   ├── contraloria_scraper.py
│   │   ├── asfi_scraper.py
│   │   └── sin_scraper.py
│   │
│   └── __init__.py             # API pública del paquete
│
├── outputs/                     # Salidas por sitio
│   ├── tcp/
│   │   ├── index.json          # Índice delta-update
│   │   ├── pdfs/               # PDFs descargados
│   │   └── json/               # Documentos parseados
│   ├── tsj/
│   ├── contraloria/
│   ├── asfi/
│   └── sin/
│
├── docs/                        # Documentación
│   └── FASE9_SITES_REALES.md   # Este archivo
│
├── main.py                      # CLI principal
└── requirements.txt             # Dependencias
```

## 🔧 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Tesseract OCR (para PDFs escaneados)

### Instalación de Dependencias

```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Instalar Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Instalar Tesseract OCR (macOS)
brew install tesseract tesseract-lang

# Instalar Tesseract OCR (Windows)
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```

## 🚀 Uso del Sistema

### Comandos Principales

#### 1. Listar sitios disponibles

```bash
python main.py listar
```

#### 2. Ejecutar scraper de un sitio específico

```bash
# Scraping completo
python main.py scrape tcp

# Solo documentos nuevos
python main.py scrape tcp --solo-nuevos

# Solo documentos modificados
python main.py scrape tsj --solo-modificados

# Limitar cantidad de documentos
python main.py scrape asfi --limit 10
```

#### 3. Actualizar todos los sitios

```bash
# Actualizar todos
python main.py actualizar-todos

# Actualizar solo algunos sitios
python main.py actualizar-todos --sitios tcp,tsj,asfi

# Solo documentos nuevos de todos los sitios
python main.py actualizar-todos --solo-nuevos

# Con límite por sitio
python main.py actualizar-todos --limit 5
```

#### 4. Ver estadísticas

```bash
# Estadísticas de un sitio
python main.py estadisticas tcp

# Resumen de todos los sitios
python main.py resumen
```

#### 5. Limpiar índice

```bash
# Eliminar del índice documentos cuyos archivos no existen
python main.py limpiar-index tcp
```

## 📊 Sistema de Actualización Incremental (Delta-Update)

### Funcionamiento

El sistema mantiene un archivo `index.json` por cada sitio que registra:

- **ID de documentos** procesados
- **Hash MD5** de cada PDF para detectar modificaciones
- **Metadata** (fecha, URL, título, etc.)
- **Estadísticas** de ejecuciones

### Estructura del index.json

```json
{
  "site": "tcp",
  "created_at": "2024-01-15 10:30:00",
  "last_updated": "2024-01-15 14:25:30",
  "total_documents": 150,
  "documents": {
    "SCP_0001_2024": {
      "id": "SCP_0001_2024",
      "title": "SCP 0001/2024 - Amparo Constitucional",
      "date": "2024-01-15",
      "url": "https://...",
      "hash": "a1b2c3d4e5f6...",
      "pdf_path": "outputs/tcp/pdfs/SCP_0001_2024.pdf",
      "json_path": "outputs/tcp/json/SCP_0001_2024.json",
      "registered_at": "2024-01-15 10:35:12",
      "status": "processed"
    }
  },
  "statistics": {
    "total_processed": 15,
    "total_new": 5,
    "total_modified": 2,
    "total_skipped": 8,
    "last_run": "2024-01-15 14:25:30"
  }
}
```

### Ventajas

1. **Evita descargas duplicadas**: Solo descarga documentos nuevos o modificados
2. **Detección de cambios**: Compara hash MD5 para detectar modificaciones
3. **Estadísticas precisas**: Mantiene registro de todas las ejecuciones
4. **Eficiencia**: Reduce tiempo y ancho de banda

## 📄 Parsing Avanzado de PDFs

### Detección Automática de OCR

El sistema detecta automáticamente si un PDF es:
- **Digital**: Extrae texto directamente
- **Escaneado**: Aplica OCR con Tesseract

```python
from scraper.core.pdf_parser import PDFParser

parser = PDFParser("documento.pdf")
texto = parser.extract_text()  # Detecta automáticamente
```

### Parsers Específicos por Tipo de Documento

Cada tipo de documento tiene un parser especializado:

```python
# Tribunal Constitucional
parsed = parser.parse_tribunal_constitucional()
# Retorna: vistos, antecedentes, problemática, considerando, fundamentos, por_tanto

# Tribunal Supremo
parsed = parser.parse_tribunal_supremo()
# Retorna: resultandos, considerandos, parte_resolutiva

# Contraloría
parsed = parser.parse_contraloria()
# Retorna: estructura por numerales romanos

# Parser genérico
parsed = parser.parse_generic()
# Retorna: metadata + texto completo
```

### Estructura de Salida

Cada documento parseado se guarda en formato JSON:

```json
{
  "id": "SCP_0001_2024",
  "title": "SCP 0001/2024 - Amparo Constitucional",
  "url": "https://...",
  "date": "2024-01-15",
  "tipo": "SCP",
  "parsed_data": {
    "tipo": "tribunal_constitucional",
    "metadata": {
      "filename": "SCP_0001_2024.pdf",
      "file_size": 524288,
      "is_scanned": false,
      "pages": 45
    },
    "secciones": {
      "vistos": "La presente acción de amparo...",
      "antecedentes": "El accionante señala que...",
      "problematica": "Se debe determinar si...",
      "considerando": "El Tribunal considera...",
      "fundamentos": "Conforme a los artículos...",
      "por_tanto": "RESUELVE: 1° CONCEDER..."
    },
    "info_adicional": {
      "magistrado_relator": "Dr. Juan Pérez",
      "sala": "SALA PRIMERA",
      "tipo_accion": "AMPARO CONSTITUCIONAL"
    }
  },
  "processed_at": "2024-01-15 10:35:12"
}
```

## 🔌 API Programática

### Uso desde Python

```python
from scraper import get_scraper, SCRAPERS

# Obtener un scraper
scraper = get_scraper('tcp')

# Ejecutar scraping
stats = scraper.run(only_new=True, limit=10)

# Ver resultados
print(f"Nuevos: {stats['total_new']}")
print(f"Modificados: {stats['total_modified']}")

# Acceder al delta manager
delta = scraper.delta_manager
print(f"Total documentos: {delta.index['total_documents']}")
```

### Crear un Scraper Personalizado

```python
from scraper.core import BaseScraper, PDFParser

class MiScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name="mi_sitio",
            base_url="https://ejemplo.gob.bo"
        )

    def fetch_document_list(self):
        # Implementar lógica de scraping
        return [
            {
                'id': 'DOC_001',
                'title': 'Documento 1',
                'url': 'https://...',
                'date': '2024-01-15'
            }
        ]

    def parse_document(self, pdf_path):
        parser = PDFParser(pdf_path)
        return parser.parse_generic()
```

## 🐛 Troubleshooting

### Problema: Error de OCR

**Síntoma**: `Error en extracción OCR`

**Solución**:
```bash
# Verificar instalación de Tesseract
tesseract --version

# Verificar idioma español instalado
tesseract --list-langs | grep spa

# Reinstalar si es necesario
sudo apt-get install --reinstall tesseract-ocr-spa
```

### Problema: PDF no se descarga

**Síntoma**: `Error descargando PDF: 403 Forbidden`

**Solución**:
- Verificar que el sitio web esté accesible
- Algunos sitios requieren autenticación o cookies
- Modificar headers en el scraper específico

### Problema: Secciones no se extraen

**Síntoma**: Las secciones del PDF están vacías

**Solución**:
- El formato del PDF puede haber cambiado
- Ajustar los patrones regex en el parser específico
- Usar modo debug para ver el texto extraído:

```python
parser = PDFParser("documento.pdf")
texto = parser.extract_text()
print(texto)  # Ver texto raw para ajustar patrones
```

### Problema: Documentos duplicados

**Síntoma**: Se procesan documentos ya existentes

**Solución**:
```bash
# Verificar índice
python main.py estadisticas tcp

# Limpiar índice si es necesario
python main.py limpiar-index tcp

# Usar flag --solo-nuevos
python main.py scrape tcp --solo-nuevos
```

## 📈 Consideraciones de Rendimiento

### Optimizaciones Implementadas

1. **Delta-Update**: Evita procesamiento innecesario
2. **Streaming de descarga**: No carga archivos completos en memoria
3. **Cache de índices**: Mantiene índices en memoria durante ejecución
4. **Límites configurables**: Permite procesar en lotes

### Recomendaciones

```bash
# Para primera ejecución completa
python main.py actualizar-todos --limit 50

# Para actualizaciones diarias
python main.py actualizar-todos --solo-nuevos

# Para verificar cambios
python main.py actualizar-todos --solo-modificados

# Para sitio específico con mucho volumen
python main.py scrape tcp --solo-nuevos --limit 100
```

## 🔒 Consideraciones de Seguridad

1. **Validación de URLs**: El sistema valida URLs antes de descargar
2. **Tamaño de archivos**: Límites en tamaño de descarga
3. **Sanitización de nombres**: Limpia nombres de archivos
4. **Manejo de errores**: No expone información sensible en errores

## 🚦 Roadmap Futuro

### Posibles Mejoras

- [ ] Soporte para más sitios gubernamentales
- [ ] Búsqueda full-text en documentos parseados
- [ ] API REST para consultas
- [ ] Dashboard web con Streamlit
- [ ] Exportación a formatos adicionales (XML, CSV)
- [ ] Notificaciones de nuevos documentos
- [ ] Integración con bases de datos
- [ ] Análisis de texto con NLP
- [ ] Extracción de entidades (personas, leyes citadas)
- [ ] Clasificación automática de documentos

## 📝 Licencia

Este proyecto es parte del sistema BÚHO de scraping gubernamental.

## 👥 Contribuciones

Para contribuir:
1. Crear un nuevo scraper en `scraper/sites/`
2. Heredar de `BaseScraper`
3. Implementar `fetch_document_list()` y `parse_document()`
4. Agregar a `SCRAPERS` en `scraper/__init__.py`
5. Documentar el nuevo sitio en este archivo

## 📞 Soporte

Para reportar problemas o sugerencias, abrir un issue en el repositorio del proyecto.

---

**BÚHO FASE 9** - Sistema Completo de Scraping Gubernamental de Bolivia
Versión 9.0.0 - Enero 2025
