# FASE 4: OCR y Extracción de Texto - Documentación Técnica

## 📋 Resumen

La FASE 4 implementa un sistema completo de extracción de texto de documentos PDF, capaz de procesar tanto PDFs digitales como escaneados usando técnicas de OCR.

## 🎯 Objetivos Cumplidos

- ✅ Detección automática de tipo de PDF (escaneado vs. digital)
- ✅ Extracción de texto de PDFs digitales
- ✅ OCR para PDFs escaneados usando Tesseract
- ✅ Limpieza y normalización de texto
- ✅ Almacenamiento estructurado de textos extraídos
- ✅ Generación/actualización de CSV con metadatos
- ✅ Sistema de logging detallado

## 🔍 Método de Detección de PDFs Escaneados

### Estrategia Principal

La función `is_scanned_pdf()` utiliza un enfoque pragmático basado en la cantidad de texto extraíble:

```python
def is_scanned_pdf(pdf_path: str, threshold: int = 100) -> bool:
    """
    Detecta si un PDF es escaneado o digital mediante análisis de contenido de texto.
    """
```

### Proceso de Detección (Paso a Paso)

1. **Apertura del PDF con PyMuPDF (fitz)**
   - Se utiliza PyMuPDF por su velocidad y eficiencia
   - Se verifica que el PDF no esté vacío

2. **Extracción de Texto de la Primera Página**
   - Se extrae el texto de solo la primera página para eficiencia
   - Se usa `page.get_text()` que obtiene todo el texto visible

3. **Limpieza y Conteo**
   - Se eliminan todos los espacios en blanco: `re.sub(r'\s+', '', text)`
   - Se cuentan los caracteres restantes

4. **Comparación con Umbral**
   - **Umbral por defecto: 100 caracteres**
   - Si `caracteres < 100` → PDF escaneado (imagen)
   - Si `caracteres >= 100` → PDF digital (texto)

### Justificación del Método

**¿Por qué este enfoque?**

- **Simplicidad**: Un solo análisis rápido vs. análisis complejo de imágenes
- **Eficiencia**: Solo lee la primera página, no todo el documento
- **Precisión**: PDFs escaneados típicamente tienen 0 caracteres o muy pocos (metadatos)
- **Velocidad**: PyMuPDF es una de las librerías más rápidas para este análisis

**¿Por qué umbral de 100 caracteres?**

- PDFs digitales típicamente tienen >500 caracteres en la primera página
- PDFs escaneados suelen tener 0-20 caracteres (solo metadatos)
- 100 caracteres es un punto medio seguro que minimiza falsos positivos/negativos

### Casos Especiales

- **PDFs híbridos**: Se tratan como digitales si tienen suficiente texto
- **PDFs corruptos**: Se asume escaneado y se aplica OCR (fallback seguro)
- **PDFs con imágenes y texto**: Si tienen >100 caracteres → digital

## 🛠️ Funciones Principales

### 1. `is_scanned_pdf(pdf_path, threshold=100)`
Detecta tipo de PDF.

**Parámetros:**
- `pdf_path`: Ruta al archivo PDF
- `threshold`: Umbral de caracteres (default: 100)

**Retorna:** `bool` - True si es escaneado, False si es digital

### 2. `extract_text_scanned(pdf_path, lang='spa')`
Extrae texto usando OCR con Tesseract.

**Proceso:**
1. Convierte cada página del PDF a imagen (pdf2image)
2. Aplica OCR con Tesseract en español
3. Concatena textos de todas las páginas

**Parámetros:**
- `pdf_path`: Ruta al PDF escaneado
- `lang`: Idioma para OCR (default: español)

**Retorna:** `str` - Texto extraído

### 3. `extract_text_digital(pdf_path)`
Extrae texto de PDF digital.

**Proceso:**
1. Abre PDF con PyMuPDF
2. Itera por cada página extrayendo texto
3. Fallback a pdfminer.six si PyMuPDF falla

**Retorna:** `str` - Texto extraído

### 4. `clean_text(raw_text)`
Limpia y normaliza texto extraído.

**Operaciones:**
- Elimina caracteres de control
- Normaliza espacios múltiples
- Limita saltos de línea consecutivos (máx 2)
- Elimina espacios al inicio/final de líneas

**Retorna:** `str` - Texto limpio

### 5. `save_text(pdf_path, text, output_dir)`
Guarda texto en archivo .txt.

**Retorna:** `str` - Ruta del archivo creado

### 6. `process_pdf(pdf_path, output_dir)`
**Función principal** que orquesta todo el pipeline.

**Pipeline:**
```
PDF → Detectar tipo → Extraer texto → Limpiar → Guardar → Metadatos
```

**Retorna:** `dict` con resultados completos

### 7. `process_multiple_pdfs(pdf_list, output_dir)`
Procesa múltiples PDFs con logging detallado.

### 8. `print_summary(results)`
Imprime resumen formateado de resultados.

## 📊 Estructura de Datos

### Resultado de `process_pdf()`

```python
{
    'pdf_path': str,              # Ruta original del PDF
    'is_scanned': bool,           # True si es escaneado
    'ocr_usado': bool,            # True si se usó OCR
    'paginas': int,               # Número de páginas
    'caracteres_extraidos': int,  # Total de caracteres
    'texto_extraido': bool,       # True si hubo éxito
    'txt_path': str,              # Ruta del .txt generado
    'error': str                  # Mensaje de error (si hay)
}
```

### CSV de Metadatos

Columnas generadas/actualizadas:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `pdf_filename` | str | Nombre del archivo PDF |
| `pdf_path` | str | Ruta completa al PDF |
| `texto_extraido` | str | 'sí' o 'no' |
| `ocr_usado` | str | 'sí' o 'no' |
| `paginas` | int | Cantidad de páginas |
| `caracteres_extraidos` | int | Total de caracteres |
| `ruta_texto` | str | Ruta al .txt generado |
| `tipo_pdf` | str | 'escaneado' o 'digital' |
| `error` | str | Mensaje de error (vacío si OK) |

## 📁 Estructura de Directorios

```
data/
├── pdfs/           # PDFs originales a procesar
├── text/           # Textos extraídos (.txt)
└── csv/            # CSVs con metadatos
    └── documentos_metadata.csv
```

## 🚀 Uso del Sistema

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

**Nota importante:** Tesseract OCR debe estar instalado en el sistema:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang

# Windows
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```

### Ejecución

```bash
# Colocar PDFs en data/pdfs/
python main.py
```

### Ejemplo de Salida

```
======================================================================
FASE 4: OCR Y EXTRACCIÓN DE TEXTO DE PDFs
Sistema de procesamiento de documentos del Estado Boliviano
======================================================================

Buscando PDFs en: data/pdfs
✅ Encontrados 3 PDFs para procesar

============================================================
Procesando PDF 1/3: decreto_123.pdf
============================================================
INFO:__main__:PDF: decreto_123.pdf - Caracteres: 1543 - Tipo: DIGITAL
INFO:__main__:Extrayendo texto digital de: decreto_123.pdf
INFO:__main__:Extracción digital completada: 15234 caracteres
INFO:__main__:Texto guardado en: data/text/decreto_123.txt

...

======================================================================
RESUMEN DE EXTRACCIÓN DE TEXTO
======================================================================

1. decreto_123.pdf
   Tipo: DIGITAL
   OCR usado: NO
   Páginas: 5
   Caracteres extraídos: 15,234
   Texto extraído: SÍ
   Archivo generado: data/text/decreto_123.txt

...

Estadísticas:
  Total PDFs procesados: 3
  PDFs digitales: 2
  PDFs escaneados: 1
  OCR aplicado: 1
  Extracciones exitosas: 3/3
======================================================================
```

## 🔧 Configuración Avanzada

### Ajustar Umbral de Detección

Editar en `text_extractor.py`:

```python
# Para PDFs con poco texto legítimo
is_scanned = is_scanned_pdf(pdf_path, threshold=50)

# Para ser más estricto
is_scanned = is_scanned_pdf(pdf_path, threshold=200)
```

### Cambiar Idioma de OCR

```python
# Para documentos en inglés
text = extract_text_scanned(pdf_path, lang='eng')

# Para documentos multiidioma
text = extract_text_scanned(pdf_path, lang='spa+eng+que')
```

## 🎨 Integración con Pipeline Completo

Este módulo está diseñado para integrarse fácilmente:

```python
from scraper.text_extractor import process_pdf

# Procesar un PDF del scraper
result = process_pdf('data/pdfs/documento.pdf', 'data/text')

# Usar resultados en análisis posterior (FASE 5)
if result['texto_extraido']:
    with open(result['txt_path'], 'r') as f:
        texto = f.read()
        # Aplicar análisis jurídico, NLP, etc.
```

## 📈 Mejoras Futuras (Preparación FASE 5)

- ✅ Textos limpios y normalizados listos para NLP
- ✅ Metadatos estructurados en CSV
- ✅ Identificación de tipo de documento
- 🔜 Análisis jurídico de contenido
- 🔜 Extracción de entidades (fechas, números de ley, etc.)
- 🔜 Clasificación automática de documentos
- 🔜 Búsqueda semántica en corpus

## ⚠️ Limitaciones Conocidas

1. **OCR de calidad variable**: Depende de la calidad del escaneo
2. **Lento para PDFs grandes**: OCR puede tomar minutos por documento
3. **Requiere Tesseract instalado**: Dependencia del sistema
4. **Memoria**: PDFs muy grandes pueden consumir mucha RAM

## 🤝 Contribución

Este módulo es parte del proyecto BÚHO de análisis de documentos del Estado Boliviano.

---

**Autor:** Sistema BÚHO
**Fecha:** Noviembre 2025
**Versión:** 1.0.0
