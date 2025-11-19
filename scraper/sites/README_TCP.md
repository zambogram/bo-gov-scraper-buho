# TCP Jurisprudencia Scraper

Scraper especializado para extraer jurisprudencia del Tribunal Constitucional Plurinacional de Bolivia usando Selenium.

## Características

- **Scraping con Selenium**: Navega por el HTML dinámico del TCP
- **Paginación automática**: Itera por todas las páginas de resultados
- **Extracción completa**: Obtiene datos de la tabla y de las fichas de detalle
- **Descarga de PDFs**: Descarga automáticamente los PDFs de las sentencias
- **Reintentos automáticos**: Manejo robusto de errores con reintentos
- **Exportación**: Genera archivos JSON y CSV con los resultados

## Sitios Cubiertos

1. **https://jurisprudencia.tcpbolivia.bo/**
2. **https://buscador.tcpbolivia.bo/busqueda-jurisprudencia**

## Datos Extraídos

Para cada sentencia, el scraper extrae:

- **Número de Resolución**: Identificador de la sentencia
- **Tipo de Jurisprudencia**: Clasificación del tipo de sentencia
- **Tipo Resolutivo**: Tipo de resolución dictada
- **Fecha**: Fecha de la sentencia
- **Sumilla**: Resumen de la sentencia
- **Magistrados**: Lista de magistrados que participaron
- **Área/Materia**: Área legal o materia constitucional
- **URL PDF**: Enlace al documento PDF
- **Archivo Local**: Ruta del PDF descargado

## Requisitos

```bash
pip install selenium webdriver-manager
```

El scraper instala automáticamente ChromeDriver usando `webdriver-manager`.

## Uso

### Opción 1: Uso Directo

```python
from scraper.sites.tcp_jurisprudencia_scraper import TCPJurisprudenciaScraper

# Crear scraper
scraper = TCPJurisprudenciaScraper(
    output_dir="data/raw/tcp_jurisprudencia",
    headless=True,
    timeout=30
)

# Ejecutar scraping
resultados = scraper.scrapear_todo()

# Exportar resultados
scraper.exportar_resultados(resultados['sentencias'], formato='json')
scraper.exportar_resultados(resultados['sentencias'], formato='csv')
```

### Opción 2: Desde main.py

```bash
# Solo scraping del TCP
python main.py --tcp

# Flujo completo: scrapear + procesar + exportar
python main.py --tcp-completo

# Con opciones adicionales
python main.py --tcp-completo --ocr --dividir-pdfs
```

### Opción 3: Ejecutar directamente

```bash
cd scraper/sites
python tcp_jurisprudencia_scraper.py
```

## Argumentos del Constructor

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `output_dir` | str | `"data/raw/tcp_jurisprudencia"` | Directorio para archivos descargados |
| `headless` | bool | `True` | Si se ejecuta Chrome sin interfaz gráfica |
| `timeout` | int | `30` | Timeout en segundos para esperar elementos |
| `retry_attempts` | int | `3` | Número de reintentos para operaciones fallidas |

## Arquitectura del Scraper

### Flujo Principal

```
1. Inicializar Driver de Selenium (Chrome)
   ↓
2. Navegar a la página del TCP
   ↓
3. Realizar búsqueda vacía (para listar todo)
   ↓
4. Iterar por todas las páginas
   ↓
5. Para cada página:
   - Extraer todas las filas de la tabla
   - Para cada fila:
     * Extraer datos visibles (número, tipo, fecha)
     * Click en "Ver Ficha"
     * Extraer detalles completos (sumilla, magistrados, etc.)
     * Descargar PDF
     * Volver a la tabla
   ↓
6. Exportar resultados a JSON y CSV
```

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `scrapear_todo()` | Ejecuta el scraping completo de todas las URLs |
| `_scrapear_sitio(url)` | Scrapea un sitio específico |
| `_realizar_busqueda_vacia()` | Hace búsqueda vacía para listar todo |
| `_extraer_sentencias_pagina()` | Extrae todas las sentencias de la página actual |
| `_extraer_datos_fila(fila)` | Extrae datos de una fila de la tabla |
| `_extraer_detalles_ficha(enlace)` | Click en "Ver Ficha" y extrae detalles |
| `_descargar_pdf(url)` | Descarga un PDF |
| `_ir_siguiente_pagina()` | Navega a la siguiente página |
| `exportar_resultados(sentencias, formato)` | Exporta a JSON o CSV |

## Manejo de Errores

El scraper implementa múltiples estrategias para manejar errores:

1. **Reintentos con Backoff Exponencial**: Reintenta operaciones fallidas con espera creciente (2s, 4s, 8s...)
2. **Selectores Múltiples**: Prueba varios selectores CSS/XPath para encontrar elementos
3. **Timeouts Configurables**: Permite ajustar el tiempo de espera
4. **Logging Detallado**: Registra todos los errores y advertencias
5. **Ventanas Emergentes**: Maneja ventanas emergentes y navegación hacia atrás

## Integración con el Pipeline

Una vez scrapeado, los datos se integran con el pipeline completo:

```python
# 1. Scraping
buho.ejecutar_scraping_tcp()

# 2. Procesamiento de PDFs (extracción de texto + OCR si es necesario)
buho.procesar_documentos(
    directorio="data/raw/tcp_jurisprudencia",
    aplicar_ocr=True
)

# 3. Exportación (CSV, JSON, Excel)
buho.exportar_datos(formatos=['csv', 'json', 'excel'])
```

### Metadatos Extraídos Automáticamente

El `MetadataExtractor` procesa cada sentencia y extrae:

- **Identificación**: Número de sentencia, tipo, código único
- **Clasificación**: Área del derecho, materia constitucional
- **Temporales**: Fechas de publicación, vigencia
- **Fuente**: URL origen, magistrados, TCP
- **Documento**: Hash MD5/SHA256, número de páginas
- **Procesamiento**: OCR aplicado, confianza, texto extraído

## Estructura de Archivos Generados

```
data/raw/tcp_jurisprudencia/
├── tcp_sentencia_a1b2c3d4.pdf
├── tcp_sentencia_e5f6g7h8.pdf
├── tcp_sentencias_20250119_143022.json
└── tcp_sentencias_20250119_143022.csv
```

## Ejemplo de Salida JSON

```json
[
  {
    "numero_resolucion": "SCP 0001/2024",
    "tipo_jurisprudencia": "Sentencia Constitucional Plurinacional",
    "tipo_resolutivo": "CONCEDE",
    "fecha": "10/01/2024",
    "url_ficha": "https://jurisprudencia.tcpbolivia.bo/ficha/12345",
    "sumilla": "Acción de amparo constitucional...",
    "magistrados": [
      "Magistrado 1",
      "Magistrado 2"
    ],
    "area_materia": "Derecho al debido proceso",
    "url_pdf": "https://jurisprudencia.tcpbolivia.bo/pdf/12345.pdf",
    "archivo_local": "data/raw/tcp_jurisprudencia/tcp_sentencia_a1b2c3d4.pdf"
  }
]
```

## Ejemplo de Salida CSV

```csv
numero_resolucion,tipo_jurisprudencia,tipo_resolutivo,fecha,sumilla,magistrados,area_materia,url_pdf,archivo_local
SCP 0001/2024,Sentencia Constitucional Plurinacional,CONCEDE,10/01/2024,Acción de amparo constitucional...,"Magistrado 1, Magistrado 2",Derecho al debido proceso,https://jurisprudencia.tcpbolivia.bo/pdf/12345.pdf,data/raw/tcp_jurisprudencia/tcp_sentencia_a1b2c3d4.pdf
```

## Troubleshooting

### Error: ChromeDriver no encontrado

```bash
# Reinstalar webdriver-manager
pip install --upgrade webdriver-manager
```

### Error: Timeout esperando elemento

Aumenta el timeout:

```python
scraper = TCPJurisprudenciaScraper(timeout=60)
```

### Error: No se encontraron filas en la tabla

El sitio puede haber cambiado su estructura HTML. Verifica los selectores en el código.

### Chrome no se ejecuta en modo headless

Desactiva el modo headless:

```python
scraper = TCPJurisprudenciaScraper(headless=False)
```

## Optimización

Para scraping más rápido:

```python
# Reducir delay entre páginas (USAR CON PRECAUCIÓN)
scraper = TCPJurisprudenciaScraper()
# En el código, time.sleep(2) se puede reducir
```

Para scraping más robusto:

```python
# Aumentar reintentos y timeouts
scraper = TCPJurisprudenciaScraper(
    timeout=60,
    retry_attempts=5
)
```

## Notas Importantes

1. **Respeto a los Servidores**: El scraper incluye delays entre peticiones para no sobrecargar los servidores del TCP
2. **Términos de Servicio**: Asegúrate de cumplir con los términos de servicio del TCP
3. **Uso Responsable**: Este scraper es para fines educativos y de investigación legal
4. **Actualizaciones**: Si el sitio web cambia, puede que necesites actualizar los selectores

## Contribución

Para agregar nuevos campos o mejorar el scraper:

1. Modifica `tcp_jurisprudencia_scraper.py`
2. Actualiza los selectores en los métodos `_extraer_*`
3. Actualiza esta documentación
4. Prueba el scraper con diferentes páginas

## Licencia

Este scraper es parte del proyecto BÚHO y está disponible bajo la misma licencia.
