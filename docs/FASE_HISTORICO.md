# Fase de Scraping Histórico Completo

## Objetivo

Implementar un sistema de scraping histórico que permita descargar y procesar el archivo completo de documentos legales de cada sitio gubernamental boliviano, de forma organizada y eficiente.

## Conceptos Clave

### Modo Full vs Delta

El sistema soporta dos modos de scraping:

1. **Modo Full (Histórico Completo)**
   - Descarga **todos** los documentos disponibles en el sitio
   - Recorre todas las páginas hasta agotar resultados
   - Útil para:
     - Primera carga del sistema
     - Recuperación después de fallas
     - Sincronización completa

2. **Modo Delta (Incremental)**
   - Descarga solo documentos nuevos o modificados
   - Utiliza índices para detectar cambios
   - Útil para:
     - Actualizaciones diarias
     - Mantenimiento continuo
     - Optimización de recursos

## Arquitectura

### 1. BaseScraper - Funcionalidad Base

Todos los scrapers heredan de `BaseScraper` que proporciona:

#### Método `listar_documentos()`
```python
def listar_documentos(
    self,
    limite: Optional[int] = None,
    modo: str = "delta",
    pagina: int = 1
) -> List[Dict[str, Any]]
```

**Responsabilidad**: Listar documentos de una página específica

**Parámetros**:
- `limite`: Número máximo de documentos a retornar
- `modo`: "full" o "delta" (indica intención del scraping)
- `pagina`: Número de página a consultar (1-indexed)

**Retorno**: Lista de diccionarios con metadata de documentos

**Comportamiento**:
- Retorna lista vacía cuando `pagina` excede el total disponible
- Retorna hasta `items_por_pagina` documentos (configurado en `sites_catalog.yaml`)

#### Método `listar_documentos_historico_completo()`
```python
def listar_documentos_historico_completo(
    self,
    limite_total: Optional[int] = None,
    progress_callback: Optional[Callable] = None
) -> List[Dict[str, Any]]
```

**Responsabilidad**: Coordinar el scraping de todas las páginas

**Parámetros**:
- `limite_total`: Límite total de documentos (para testing/debugging)
- `progress_callback`: Función para reportar progreso

**Comportamiento**:
1. Itera páginas secuencialmente (1, 2, 3, ...)
2. Llama a `listar_documentos()` para cada página
3. Detiene cuando:
   - Página retorna lista vacía
   - Página retorna menos de `items_por_pagina` documentos
   - Se alcanza `limite_total`
   - Se alcanza límite de seguridad (100 páginas)
4. Respeta delays configurados entre páginas
5. Reporta progreso vía callback

**Protecciones**:
- Máximo 100 páginas (configurable)
- Delay entre requests (configurable por sitio)
- Timeout por request

### 2. Pipeline - Flujo de Procesamiento

El pipeline (`scraper/pipeline.py`) coordina el flujo completo:

```python
def run_site_pipeline(
    site_id: str,
    mode: Literal["full", "delta"] = "delta",
    limit: Optional[int] = None,
    save_pdf: bool = False,
    save_txt: bool = True,
    save_json: bool = True,
    progress_callback: Optional[Callable] = None
) -> PipelineResult
```

#### Flujo en Modo Full

```
┌─────────────────────────────────────┐
│ 1. Inicialización                   │
│    - Cargar configuración            │
│    - Crear scrapers/extractors      │
│    - Inicializar índice              │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 2. Listado Histórico Completo       │
│    scraper.listar_documentos_       │
│    historico_completo()              │
│    - Itera todas las páginas        │
│    - Reporta progreso                │
│    - Retorna lista completa          │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 3. Procesamiento por Documento      │
│    FOR EACH documento:               │
│    ├─ Descargar PDF                 │
│    ├─ Extraer texto (+ OCR)         │
│    ├─ Parsear artículos             │
│    ├─ Extraer metadata extendida    │
│    ├─ Guardar JSON/TXT              │
│    ├─ Exportar a CSV/JSONL          │
│    └─ Actualizar índice             │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 4. Finalización                      │
│    - Guardar índice                  │
│    - Generar reporte                 │
│    - Exportar estadísticas           │
└─────────────────────────────────────┘
```

#### Flujo en Modo Delta

Similar al modo full, pero:
- Solo procesa primera página (o hasta encontrar documento existente)
- Salta documentos que ya existen en índice
- Más rápido para actualizaciones diarias

### 3. IndexManager - Control de Cambios

Gestiona el índice de documentos procesados:

**Archivo**: `data/{site_id}/index.json`

**Estructura**:
```json
{
  "documentos": {
    "tcp_sc_0001_2024": {
      "hash": "abc123...",
      "fecha_actualizacion": "2024-01-15T10:30:00",
      "ruta_pdf": "data/raw/tcp/tcp_sc_0001_2024.pdf",
      "ruta_txt": "data/normalized/tcp/text/tcp_sc_0001_2024.txt",
      "ruta_json": "data/normalized/tcp/json/tcp_sc_0001_2024.json"
    }
  },
  "last_update": "2024-01-15T10:30:00",
  "total_documentos": 100
}
```

**Funciones**:
- `documento_existe()`: Verificar si documento ya fue procesado
- `documento_cambio()`: Detectar cambios por hash
- `actualizar_documento()`: Registrar nuevo documento o actualización

## Configuración por Sitio

### Archivo: `config/sites_catalog.yaml`

Parámetros relevantes para scraping histórico:

```yaml
tcp:
  nombre: "Tribunal Constitucional Plurinacional"
  scraper:
    items_por_pagina: 20           # Documentos por página
    delay_entre_requests: 2        # Segundos entre requests
    max_paginas: 100               # Límite de seguridad
    requiere_ocr: false            # Si PDFs son escaneados
```

## Scrapers Implementados

### Estado Actual (Datos de Ejemplo)

Todos los scrapers actualmente usan **datos de ejemplo** para demostración:

| Sitio | Scraper | Estado | Documentos Ejemplo | Páginas |
|-------|---------|--------|-------------------|---------|
| TCP   | `tcp_scraper.py` | ✅ Listo | 100 | 5 |
| TSJ   | `tsj_scraper.py` | ✅ Listo | 150 | 8 |
| ASFI  | `asfi_scraper.py` | ✅ Listo | 80 | 4 |
| SIN   | `sin_scraper.py` | ✅ Listo | 120 | 6 |
| Contraloría | `contraloria_scraper.py` | ✅ Listo | 60 | 3 |
| Gaceta | - | ⏳ Pendiente | - | - |

### Migración a Scraping Real

Para migrar un scraper de ejemplo a scraping real:

#### 1. Implementar `listar_documentos()`

**Antes (ejemplo)**:
```python
def listar_documentos(self, limite=None, modo="delta", pagina=1):
    # Datos de ejemplo
    documentos = [...]
    return documentos[:limite] if limite else documentos
```

**Después (real)**:
```python
def listar_documentos(self, limite=None, modo="delta", pagina=1):
    # 1. Construir URL con paginación
    url = f"{self.config.url_search}?page={pagina}"

    # 2. Hacer request HTTP
    response = self.session.get(url, timeout=30)
    response.raise_for_status()

    # 3. Parsear HTML
    soup = BeautifulSoup(response.text, 'lxml')

    # 4. Extraer documentos
    documentos = []
    for item in soup.select('.documento-item'):  # Selector específico del sitio
        doc = {
            'id_documento': item.select_one('.id').text.strip(),
            'titulo': item.select_one('.titulo').text.strip(),
            'fecha': item.select_one('.fecha').text.strip(),
            'url': urljoin(self.config.url_base, item.select_one('a')['href']),
            # ... más campos
        }
        documentos.append(doc)

    # 5. Aplicar límite
    return documentos[:limite] if limite else documentos
```

#### 2. Implementar `descargar_pdf()`

**Antes (ejemplo)**:
```python
def descargar_pdf(self, url, ruta_destino):
    # Crear PDF de prueba
    with open(ruta_destino, 'wb') as f:
        f.write(b'%PDF-1.4\nEjemplo')
    return True
```

**Después (real)**:
```python
def descargar_pdf(self, url, ruta_destino):
    return self._download_file(url, ruta_destino)  # Método heredado de BaseScraper
```

#### 3. Ajustar Selectores CSS/XPath

Cada sitio tiene estructura HTML diferente. Investigar:

1. **Inspeccionar página de búsqueda**:
   - ¿Cómo se listan los documentos?
   - ¿Qué selectores CSS identifican cada elemento?
   - ¿Cómo funciona la paginación?

2. **Identificar patrones de URL**:
   - URL de búsqueda: `/busqueda`, `/normativa`, etc.
   - Parámetros de paginación: `?page=N`, `?offset=N`, etc.
   - URL de PDFs: `/pdfs/{año}/{id}.pdf`, etc.

3. **Probar extracción**:
   ```python
   # Test en consola/notebook
   from bs4 import BeautifulSoup
   import requests

   url = "https://www.tcpbolivia.bo/tcp/busqueda?page=1"
   response = requests.get(url)
   soup = BeautifulSoup(response.text, 'lxml')

   # Encontrar selectores correctos
   items = soup.select('.resultado-sentencia')  # Ajustar
   for item in items:
       print(item.select_one('.numero').text)
   ```

## Uso del Sistema

### CLI

#### Scraping histórico completo de un sitio

```bash
# TCP - histórico completo
python main.py scrape tcp --mode full

# Con límite (para testing)
python main.py scrape tcp --mode full --limit 50

# Guardar PDFs originales
python main.py scrape tcp --mode full --save-pdf
```

#### Scraping delta (incremental)

```bash
# Solo documentos nuevos
python main.py scrape tcp --mode delta

# Todos los sitios en modo delta
python main.py scrape all --mode delta
```

#### Opciones de guardado

```bash
# Solo JSON y TXT (sin PDFs)
python main.py scrape tcp --mode full --no-save-pdf

# Solo JSON
python main.py scrape tcp --mode full --no-save-pdf --no-save-txt

# Todo
python main.py scrape tcp --mode full --save-pdf --save-txt --save-json
```

### Programático (Python)

```python
from scraper.pipeline import run_site_pipeline

# Scraping histórico con progreso
def mostrar_progreso(mensaje):
    print(f"[PROGRESO] {mensaje}")

resultado = run_site_pipeline(
    site_id='tcp',
    mode='full',
    limit=None,  # Sin límite
    save_pdf=False,
    save_txt=True,
    save_json=True,
    progress_callback=mostrar_progreso
)

print(f"Procesados: {resultado.total_parseados}")
print(f"Errores: {resultado.total_errores}")
print(f"Duración: {resultado.duracion_segundos}s")
```

## Estructura de Datos Generados

### Durante Scraping Histórico

```
data/
├── raw/                          # PDFs originales (si save_pdf=True)
│   └── tcp/
│       ├── tcp_sc_0001_2024.pdf
│       ├── tcp_sc_0002_2024.pdf
│       └── ...
│
├── normalized/                   # Datos normalizados
│   └── tcp/
│       ├── text/                 # Texto extraído
│       │   ├── tcp_sc_0001_2024.txt
│       │   └── ...
│       └── json/                 # Documentos estructurados
│           ├── tcp_sc_0001_2024.json
│           └── ...
│
├── exports/                      # Exportaciones por sesión
│   └── tcp/
│       └── 20240115_103000/
│           ├── documentos.csv    # Todos los documentos
│           ├── articulos.csv     # Todos los artículos
│           ├── registro_historico.jsonl
│           └── reporte.json      # Estadísticas de sesión
│
└── tcp/
    └── index.json                # Índice de control
```

## Monitoreo y Debugging

### Logs

El sistema genera logs detallados:

```bash
# Ver logs en tiempo real
tail -f logs/scraper.log

# Filtrar por sitio
grep "tcp" logs/scraper.log

# Ver solo errores
grep "ERROR" logs/scraper.log
```

### Reportes de Sesión

Cada sesión de scraping genera un reporte:

**Archivo**: `data/exports/{site_id}/{timestamp}/reporte.json`

```json
{
  "site_id": "tcp",
  "timestamp": "20240115_103000",
  "modo": "full",
  "estadisticas": {
    "total_encontrados": 100,
    "total_descargados": 100,
    "total_parseados": 98,
    "total_errores": 2,
    "duracion_segundos": 245.6
  },
  "errores": [
    {
      "documento": "tcp_sc_0042_2024",
      "tipo": "Error descargando PDF",
      "detalle": "Connection timeout"
    }
  ]
}
```

### Tracking Histórico

**Archivo**: `data/tracking_historico.json`

Registra todas las sesiones de scraping:

```json
{
  "sesiones": {
    "tcp": [
      {
        "timestamp": "2024-01-15T10:30:00",
        "modo": "full",
        "documentos_procesados": 98,
        "errores": 2,
        "duracion_segundos": 245.6,
        "metadata_agregada": {
          "areas_procesadas": ["constitucional", "penal", "civil"],
          "tipos_procesados": ["Sentencia Constitucional"],
          "jerarquias": [1, 2]
        }
      }
    ]
  }
}
```

## Mejores Prácticas

### 1. Primera Ejecución (Histórico Completo)

```bash
# Empezar con límite pequeño para verificar
python main.py scrape tcp --mode full --limit 10

# Si funciona bien, aumentar gradualmente
python main.py scrape tcp --mode full --limit 50
python main.py scrape tcp --mode full --limit 100

# Finalmente, sin límite
python main.py scrape tcp --mode full
```

### 2. Actualizaciones Diarias (Delta)

```bash
# Cron job para ejecutar diariamente
# 0 2 * * * cd /path/to/bo-gov-scraper-buho && python main.py scrape all --mode delta
```

### 3. Recuperación de Errores

```bash
# Si una sesión falla a mitad, los documentos procesados quedan en índice
# Reejecutar en modo full saltará documentos ya procesados
python main.py scrape tcp --mode full
```

### 4. Limpieza de Datos

```bash
# Limpiar y recomenzar (CUIDADO: borra todo)
rm -rf data/tcp/
rm -rf data/raw/tcp/
rm -rf data/normalized/tcp/
python main.py scrape tcp --mode full
```

## Consideraciones de Rendimiento

### Tiempos Estimados

Para **TCP** (100 documentos de ejemplo):
- Listado: ~10s (con delays)
- Descarga: ~2s por documento (200s total)
- Extracción de texto: ~1s por documento (100s)
- Parsing: ~0.5s por documento (50s)
- Metadata extendida: ~0.5s por documento (50s)
- **Total**: ~7 minutos

Para sitios reales con 10,000 documentos:
- Estimado: ~12 horas (con delays de 2s)

### Optimizaciones Posibles

1. **Paralelización** (no implementado):
   - Descargar múltiples PDFs en paralelo
   - Procesar múltiples documentos en paralelo
   - Riesgo: puede ser bloqueado por sitio

2. **Caché de PDFs** (ya implementado):
   - PDFs no se redescargan si ya existen

3. **Reinicio desde checkpoint**:
   - Índice permite saber qué documentos ya fueron procesados

## Troubleshooting

### Problema: "Página X excede máximo"
**Causa**: El scraper detectó que no hay más páginas
**Solución**: Normal, indica fin de scraping

### Problema: "Connection timeout"
**Causa**: Sitio no responde
**Solución**:
- Verificar conectividad
- Aumentar timeout en BaseScraper
- Intentar más tarde

### Problema: "Error 403 Forbidden"
**Causa**: Sitio bloqueó el scraper
**Solución**:
- Aumentar delays
- Agregar User-Agent más realista
- Revisar robots.txt del sitio

### Problema: PDFs corruptos
**Causa**: Descarga incompleta
**Solución**:
- Verificar hash antes de guardar
- Implementar reintentos
- Validar PDF con PyPDF2

## Próximos Pasos

1. ✅ **Scrapers con paginación** (COMPLETADO)
2. ⏳ **Implementar scraping real** (por hacer):
   - Investigar estructura HTML de cada sitio
   - Implementar selectores CSS
   - Probar con sitios reales
3. ⏳ **Gaceta Oficial** (pendiente):
   - Activar en catálogo
   - Implementar scraper específico
4. ⏳ **Más sitios** (~30 sitios eventualmente)

## Referencias

- `scraper/sites/base_scraper.py`: Clase base con método histórico
- `scraper/pipeline.py`: Orquestación del flujo
- `config/sites_catalog.yaml`: Configuración de sitios
- `scraper/models.py`: Modelos de datos
