# 🦉 SISTEMA BÚHO - Pipeline de Procesamiento Legal

**Scraper completo de la Gaceta Oficial de Bolivia + OCR + Segmentación de Artículos**

Sistema end-to-end para descargar, procesar y estructurar documentos legales de la Gaceta Oficial de Bolivia.

---

## 📋 Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Pipeline](#-arquitectura-del-pipeline)
3. [Instalación](#-instalación)
4. [Uso Rápido](#-uso-rápido)
5. [Estructura de Datos](#-estructura-de-datos)
6. [Módulos del Sistema](#-módulos-del-sistema)
7. [Ejemplos](#-ejemplos)
8. [Solución de Problemas](#-solución-de-problemas)

---

## 🎯 Descripción General

El Sistema BÚHO procesa documentos legales bolivianos de forma automática:

- **Descarga** PDFs de la Gaceta Oficial de Bolivia
- **Extrae** metadatos (tipo de norma, número, fecha, entidad)
- **Procesa** texto usando extracción digital o OCR (para documentos escaneados)
- **Segmenta** el contenido en artículos, incisos y parágrafos
- **Genera** JSONs estructurados y CSVs para análisis

### Características

✅ Manejo automático de PDFs digitales y escaneados
✅ OCR en español con Tesseract
✅ Segmentación inteligente de artículos legales
✅ Base de datos CSV incremental (no pierde datos previos)
✅ Manejo robusto de errores
✅ Evita reprocesar documentos existentes

---

## 🏗️ Arquitectura del Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE END-TO-END                          │
└─────────────────────────────────────────────────────────────────┘

  URL Gaceta Oficial
         │
         ▼
  ┌─────────────────┐
  │  1. SCRAPER     │  → Descarga PDFs
  │  gaceta_scraper │     data/pdfs/*.pdf
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  2. METADATA    │  → Extrae tipo, número, fecha
  │  metadata_      │
  │  extractor      │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  3. TEXT        │  → Extrae texto (digital/OCR)
  │  EXTRACTION     │     data/text/*.txt
  │  text_extractor │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  4. PARSER      │  → Segmenta artículos
  │  legal_parser   │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  5. STORAGE     │  → Genera outputs finales
  │  csv_manager    │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────────────────────┐
  │  OUTPUTS                            │
  │  • data/csv/documentos.csv          │
  │  • data/csv/articulos.csv           │
  │  • data/parsed/*.json               │
  └─────────────────────────────────────┘
```

---

## 📦 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho
```

### 2. Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

### 3. Instalar Tesseract OCR (para PDFs escaneados)

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

### 4. Verificar Instalación

```bash
python -c "import pytesseract; print('Tesseract OK')"
```

---

## 🚀 Uso Rápido

### Ejecutar el Pipeline Completo

```bash
python main.py
```

Esto:
1. Descargará **3 documentos** de la Gaceta Oficial (configurable)
2. Procesará cada uno a través de todo el pipeline
3. Generará CSVs y JSONs con los resultados

### Configuración Personalizada

Edita las siguientes líneas en `main.py`:

```python
# URL de la página de la Gaceta con listado de normas
URL_INICIAL = "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar"

# Número de documentos a procesar
LIMITE_DOCUMENTOS = 3
```

### Uso Programático

```python
from main import run_full_pipeline

resultado = run_full_pipeline(
    url_inicial="https://www.gacetaoficialdebolivia.gob.bo/normas/buscar",
    limite_documentos=5,
    forzar_reprocesar=False  # True para reprocesar documentos existentes
)

print(f"Documentos procesados: {resultado['documentos_procesados']}")
print(f"Artículos extraídos: {resultado['total_articulos']}")
```

---

## 📊 Estructura de Datos

### CSVs Generados

#### 1. `data/csv/documentos.csv` - FUENTE DE VERDAD PRINCIPAL

Un registro por cada documento legal:

| Columna | Descripción |
|---------|-------------|
| `document_id` | ID único (ej: LEY-1234-2023-07-15) |
| `tipo_norma` | Tipo de norma (Ley, Decreto, etc.) |
| `numero_norma` | Número de la norma |
| `fecha_norma` | Fecha de emisión (YYYY-MM-DD) |
| `entidad_emisora` | Entidad que emitió el documento |
| `titulo_original` | Título completo del documento |
| `url_pdf` | URL original del PDF |
| `filename_pdf` | Nombre del archivo PDF |
| `filepath_pdf` | Ruta del PDF en disco |
| `size_bytes` | Tamaño del PDF en bytes |
| `download_date` | Fecha de descarga |
| `texto_extraido` | True/False si se extrajo texto |
| `metodo_extraccion` | 'digital' o 'ocr' |
| `filepath_txt` | Ruta del archivo .txt |
| `paginas` | Número de páginas |
| `caracteres_extraidos` | Número de caracteres |
| `total_articulos` | Número de artículos encontrados |
| `filepath_json` | Ruta del JSON parseado |
| `procesamiento_completo` | True/False |
| `error_mensaje` | Mensaje de error si lo hubo |
| `fecha_procesamiento` | Fecha de procesamiento |

#### 2. `data/csv/articulos.csv` - FUENTE DE VERDAD DE ARTÍCULOS

Un registro por cada artículo de cada documento:

| Columna | Descripción |
|---------|-------------|
| `articulo_id` | ID único (ej: LEY-1234-2023-07-15-ART-1) |
| `document_id` | ID del documento padre |
| `numero_articulo` | Número del artículo |
| `titulo_articulo` | Título del artículo |
| `contenido` | Contenido completo del artículo |
| `num_incisos` | Número de incisos |
| `num_paragrafos` | Número de parágrafos |
| `caracteres` | Longitud del contenido |
| `fecha_extraccion` | Fecha de extracción |

### JSONs Generados

Cada documento genera un JSON en `data/parsed/` con estructura completa:

```json
{
  "document_id": "LEY-1234-2023-07-15",
  "metadata": {
    "considerandos": "...",
    "tipo_accion": "DECRETA"
  },
  "articles": [
    {
      "numero": 1,
      "titulo": "OBJETO",
      "contenido": "La presente Ley...",
      "incisos": [
        {
          "numero": "I",
          "contenido": "..."
        }
      ],
      "paragrafos": [
        {
          "numero": "I",
          "contenido": "..."
        }
      ],
      "num_incisos": 3,
      "num_paragrafos": 1
    }
  ],
  "total_articles": 45,
  "texto_completo_length": 125000
}
```

---

## 🧩 Módulos del Sistema

### 1. `scraper/gaceta_scraper.py`
**Función:** Descarga PDFs de la Gaceta Oficial
**Entrada:** URL de listado de normas
**Salida:** PDFs en `data/pdfs/`

### 2. `scraper/metadata_extractor.py`
**Función:** Extrae metadatos de títulos y nombres
**Entrada:** Título del documento
**Salida:** Tipo, número, fecha, entidad

### 3. `scraper/text_extractor.py`
**Función:** Extrae texto de PDFs
**Métodos:**
- Extracción digital (PDFs con texto)
- OCR (PDFs escaneados con Tesseract)
**Salida:** Archivos .txt en `data/text/`

### 4. `scraper/legal_parser.py`
**Función:** Segmenta documentos en artículos
**Identifica:**
- Artículos
- Incisos (numeración romana)
- Parágrafos
**Salida:** Estructura jerárquica del documento

### 5. `scraper/csv_manager.py`
**Función:** Gestiona CSVs incrementales
**Características:**
- No pierde datos anteriores
- Evita duplicados por ID
- Actualiza registros existentes

### 6. `main.py`
**Función:** Orquesta el pipeline completo
**Función principal:** `run_full_pipeline()`

---

## 💡 Ejemplos

### Ejemplo 1: Procesar 10 documentos

```python
from main import run_full_pipeline

resultado = run_full_pipeline(
    url_inicial="https://www.gacetaoficialdebolivia.gob.bo/normas/buscar",
    limite_documentos=10
)
```

### Ejemplo 2: Reprocesar un documento

```python
resultado = run_full_pipeline(
    url_inicial="https://www.gacetaoficialdebolivia.gob.bo/normas/buscar",
    limite_documentos=1,
    forzar_reprocesar=True  # Reprocesa aunque ya exista
)
```

### Ejemplo 3: Leer resultados en pandas

```python
import pandas as pd

# Cargar documentos
docs = pd.read_csv('data/csv/documentos.csv')
print(f"Total documentos: {len(docs)}")

# Filtrar solo leyes
leyes = docs[docs['tipo_norma'] == 'LEY']
print(f"Total leyes: {len(leyes)}")

# Cargar artículos
arts = pd.read_csv('data/csv/articulos.csv')
print(f"Total artículos: {len(arts)}")
```

---

## 🔧 Solución de Problemas

### Error: "Tesseract not found"

**Solución:** Instala Tesseract OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang
```

### Error: "No se encontraron PDFs"

**Problema:** La URL de la Gaceta no contiene enlaces a PDFs.

**Solución:**
1. Verifica que la URL es correcta
2. Inspecciona la página para confirmar que tiene enlaces a PDFs
3. Ajusta el scraper si la estructura del sitio cambió

### PDFs sin artículos

**Problema:** El parser no encuentra artículos en el texto.

**Posibles causas:**
- OCR produjo texto de baja calidad
- El documento no tiene estructura de artículos (ej: resoluciones cortas)

**Solución:** Revisa el archivo .txt generado en `data/text/`

### Documentos duplicados

El sistema **automáticamente evita duplicados** usando `document_id`.
Si quieres reprocesar, usa `forzar_reprocesar=True`.

---

## 📝 Licencia

Este proyecto está bajo la licencia especificada en el archivo LICENSE.

---

## 👨‍💻 Autor

**Sistema BÚHO**
Desarrollado para el procesamiento automatizado de documentos legales bolivianos.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📞 Soporte

Si encuentras problemas o tienes preguntas:
1. Revisa la sección de [Solución de Problemas](#-solución-de-problemas)
2. Abre un Issue en GitHub
3. Proporciona logs completos del error

---

**¡Feliz procesamiento! 🦉**
