# bo-gov-scraper-buho
Scraper completo de páginas del Estado boliviano + OCR + metadatos para BÚHO

## FASE 2: Scraper de la Gaceta Oficial de Bolivia ✅

### Descripción
Este proyecto implementa un scraper automatizado para descargar documentos (normas, decretos, leyes) desde la Gaceta Oficial de Bolivia.

### Características
- ✅ Descarga automática de PDFs desde la Gaceta Oficial
- ✅ Extracción de enlaces dinámicos (`/normas/descargarPdf/[ID]`)
- ✅ Registro detallado en CSV con información de cada descarga
- ✅ Manejo robusto de errores y timeouts
- ✅ Nombres de archivo únicos (evita sobrescribir)
- ✅ Comentarios explicativos para usuarios no técnicos

### Estructura del Proyecto
```
bo-gov-scraper-buho/
├── scraper/                  # Módulo del scraper
│   ├── __init__.py
│   └── gaceta_scraper.py    # Scraper principal de la Gaceta Oficial
├── data/                     # PDFs descargados
├── exports/                  # Archivos de log (CSV)
├── main.py                   # Punto de entrada del programa
└── requirements.txt          # Dependencias del proyecto
```

### Instalación
```bash
pip install -r requirements.txt
```

### Uso
```bash
python main.py
```

### Dependencias
- `requests`: Para hacer solicitudes HTTP
- `beautifulsoup4`: Para analizar HTML
- `lxml`: Parser rápido de HTML/XML
- `pandas`: Para manipulación de datos (futuro)
- `streamlit`: Para interfaz web (futuro)

### Funcionalidades Implementadas (Fase 2)

#### 1. `fetch_page(url)`
Descarga el contenido HTML de una página web con manejo de errores.

#### 2. `parse_list_page(html, base_url)`
Analiza el HTML y extrae información de documentos:
- Busca enlaces directos a PDFs (`.pdf`)
- Busca enlaces dinámicos (`/normas/descargarPdf/[ID]`)
- Extrae títulos y fechas cuando están disponibles

#### 3. `download_pdf(url_pdf, ruta_destino)`
Descarga un archivo PDF desde una URL:
- Verifica que el archivo sea realmente un PDF
- Muestra el tamaño del archivo descargado
- Maneja timeouts y errores de conexión

#### 4. `run_gaceta_scraper(url_inicial, limite=10)`
Función principal que coordina todo el proceso:
- Descarga la página de listado
- Extrae enlaces a documentos
- Descarga los PDFs (hasta el límite especificado)
- Genera un registro en CSV

### Resultados de la Última Ejecución
- **Documentos encontrados**: 48
- **PDFs descargados exitosamente**: 7
- **Ubicación**: `data/`
- **Log**: `exports/gaceta_log.csv`

### Formato del CSV de Log
```csv
titulo,url_pdf,archivo_descargado,fecha_documento,fecha_extraccion,estado
```

### Próximas Fases
- **Fase 3**: Mejorar extracción de metadatos (títulos, fechas, tipos de norma)
- **Fase 4**: Implementar OCR para extraer texto de los PDFs
- **Fase 5**: Crear base de datos con metadatos estructurados
- **Fase 6**: Interfaz web con Streamlit para explorar documentos

### Notas Técnicas
- El servidor de la Gaceta Oficial puede tener problemas de disponibilidad (errores 503)
- Algunos PDFs pueden estar vacíos o ser páginas HTML de error
- El scraper incluye pausas entre descargas para no sobrecargar el servidor
- Los títulos se extraen del contexto HTML (trabajo en progreso)
