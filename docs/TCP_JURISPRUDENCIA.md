# TCP Jurisprudencia Scraper

## 🎯 Objetivo

Scraper especializado para obtener **TODA la jurisprudencia** del Tribunal Constitucional Plurinacional (TCP) mediante sus APIs internas.

**IMPORTANTE**: Este NO es el scraper de gacetas TCP (tomos/guías). Este scraper obtiene sentencias, resoluciones y autos constitucionales.

## 🌐 Sitios objetivo

- https://buscador.tcpbolivia.bo/
  - `/busqueda-resolucion`
  - `/busqueda-unificacion`
  - `/busqueda-avocacion`
  - `/busqueda-jurisprudencia`
  - `/busqueda-fecha-ingreso`
  - `/busqueda-fecha-resolucion`

- https://jurisprudencia.tcpbolivia.bo/

## 🏗️ Arquitectura

### Diseño basado en API

Este scraper está **100% basado en APIs REST**, NO en scraping HTML.

**Características clave:**
- Configuración externalizada en `config/sites_catalog.yaml`
- Endpoints de API configurables
- Paginación automática con validación
- Iteración por años para cobertura total
- Mapeo de campos JSON personalizable

### Estructura de archivos

```
bo-gov-scraper-buho/
├── config/
│   └── sites_catalog.yaml         # Configuración del scraper
├── scraper/
│   └── sites/
│       ├── __init__.py
│       └── tcp_jurisprudencia_scraper.py  # Scraper principal
├── scripts/
│   └── validar_cobertura_tcp.py   # Script de validación
└── main.py                        # CLI actualizado
```

## 📋 Configuración

### 1. Inspeccionar la API real

⚠️ **IMPORTANTE**: Antes de usar el scraper, debes inspeccionar el sitio web con las herramientas de desarrollador del navegador.

**Pasos:**

1. Abre https://buscador.tcpbolivia.bo/ en Chrome/Firefox
2. Abre DevTools (F12) → pestaña **Network**
3. Filtra por **XHR** o **Fetch**
4. Realiza una búsqueda en el sitio
5. Identifica la request de la API

**Datos que necesitas obtener:**

- **URL del endpoint**: ej. `https://buscador.tcpbolivia.bo/api/buscar`
- **Método**: GET o POST
- **Parámetros**:
  - Nombre del parámetro de página: `page`, `pagina`, `offset`
  - Nombre del parámetro de tamaño: `size`, `limit`, `pageSize`
  - Otros parámetros: año, tipo, materia, etc.
- **Estructura del JSON de respuesta**:
  - Campo que contiene la lista de resultados: `data.items`, `results`, `documents`
  - Campo que contiene el total: `data.total`, `totalElements`, `pagination.total`

### 2. Actualizar config/sites_catalog.yaml

Edita `config/sites_catalog.yaml` y actualiza la sección `tcp_jurisprudencia`:

```yaml
sites:
  tcp_jurisprudencia:
    scraper:
      endpoints:
        busqueda_general:
          url: "/api/jurisprudencia/buscar"  # ← ACTUALIZAR con URL real
          metodo: "POST"  # ← ACTUALIZAR (GET o POST)

      paginacion:
        parametros:
          pagina: "page"      # ← ACTUALIZAR con nombre real del parámetro
          tamaño: "size"      # ← ACTUALIZAR con nombre real del parámetro

      mapeo_campos:
        campo_resultados: "data.items"  # ← ACTUALIZAR con path real en JSON
        campo_total: "data.total"       # ← ACTUALIZAR con path real en JSON

        # Campos de cada documento
        id: "id"                               # ← ACTUALIZAR
        numero_resolucion: "numeroResolucion"  # ← ACTUALIZAR
        tipo_documento: "tipoDocumento"        # ← ACTUALIZAR
        fecha_resolucion: "fechaResolucion"    # ← ACTUALIZAR
        # ... etc
```

### 3. Configurar URL de PDF

Si el JSON no incluye la URL del PDF directamente:

```yaml
extraccion:
  generar_url_pdf: true
  patron_url_pdf: "https://buscador.tcpbolivia.bo/documentos/{id}.pdf"  # ← ACTUALIZAR
```

Reemplaza `{id}` con el campo que contiene el ID del documento.

## 🚀 Uso

### Comandos básicos

```bash
# Modo TEST: solo 5 páginas (para probar configuración)
python main.py scrape tcp_jurisprudencia --mode test --limit 100

# Modo FULL: cobertura total (itera todos los años)
python main.py scrape tcp_jurisprudencia --mode full --save-pdf

# Modo INCREMENTAL: solo últimos 30 días
python main.py scrape tcp_jurisprudencia --mode incremental

# Sin descargar PDFs (solo metadatos)
python main.py scrape tcp_jurisprudencia --mode full --no-pdf

# Con límite específico
python main.py scrape tcp_jurisprudencia --mode full --limit 5000
```

### Modos de scraping

| Modo | Descripción | Uso |
|------|-------------|-----|
| `test` | Solo primeras 5 páginas | Probar configuración |
| `full` | Itera TODOS los años (1999-presente) | Cobertura total |
| `incremental` | Solo últimos 30 días | Actualización diaria |

## 📊 Validación de cobertura

### Durante el scraping

El scraper muestra automáticamente:

```
📋 VALIDACIÓN DE COBERTURA
----------------------------------------------------------
Total documentos encontrados: 15234
Total PDFs descargados: 14987
Porcentaje éxito descarga: 98.4%
```

### Después del scraping

Usa el script de validación:

```bash
# Validar desde JSON
python scripts/validar_cobertura_tcp.py \
  --json data/raw/tcp_jurisprudencia/documentos_20250118_123456.json

# Comparar con total esperado de la API
python scripts/validar_cobertura_tcp.py \
  --json data/raw/tcp_jurisprudencia/documentos_20250118_123456.json \
  --total-esperado 15500
```

### Cómo obtener el total esperado

1. Inspecciona la primera llamada a la API en Network tab
2. Busca en el JSON de respuesta el campo que indica el total
3. Ejemplo de JSON:
   ```json
   {
     "data": {
       "total": 15500,  ← Este es el total esperado
       "items": [...]
     }
   }
   ```

### Verificar cobertura manualmente

```python
import json
import pandas as pd

# Cargar datos
with open('data/raw/tcp_jurisprudencia/documentos_TIMESTAMP.json') as f:
    docs = json.load(f)

# Convertir a DataFrame
df = pd.DataFrame(docs)

# Análisis
print(f"Total documentos: {len(df)}")
print(f"\nDocumentos por año:")
df['año'] = pd.to_datetime(df['fecha_resolucion']).dt.year
print(df['año'].value_counts().sort_index())

# Verificar duplicados
print(f"\nDuplicados: {df.duplicated(subset=['id_documento']).sum()}")

# Verificar PDFs
print(f"\nCon PDF: {df['ruta_pdf'].notna().sum()} / {len(df)}")
```

### Indicadores de cobertura completa

✅ **Buenas señales:**
- Diferencia < 5% entre total obtenido y total esperado
- Distribución uniforme por años (no hay años con 0-5 documentos)
- Sin duplicados de ID
- > 95% de PDFs descargados

⚠️ **Señales de alerta:**
- Diferencia > 10% con total esperado → revisar paginación
- Varios años con < 5 documentos → paginación cortada
- Muchos duplicados → revisar lógica de ID único
- < 80% PDFs descargados → revisar URLs de PDF

## 🔧 Troubleshooting

### Error: "No se pudo obtener la página principal"

**Causa**: URL del endpoint incorrecta o API cambió.

**Solución**:
1. Inspecciona Network tab del navegador
2. Actualiza `endpoints.busqueda_general.url` en config

### Error: "Error parseando JSON"

**Causa**: La API devuelve HTML en lugar de JSON, o estructura cambió.

**Solución**:
1. Verifica que el método (GET/POST) sea correcto
2. Verifica headers (Content-Type: application/json)
3. Inspecciona la respuesta real en Network tab

### Cobertura incompleta (diferencia > 10%)

**Causas posibles:**
1. Paginación cortada prematuramente
2. Parámetros incorrectos (ej: usando `page` cuando debería ser `offset`)
3. Tamaño de página limitado por la API

**Solución**:
1. Verifica parámetros de paginación en config
2. Reduce `tamaño_pagina_default` (ej: de 100 a 50)
3. Verifica que `campo_resultados` apunte al array correcto

### Muchos campos vacíos en CSV

**Causa**: Mapeo de campos incorrecto.

**Solución**:
1. Inspecciona el JSON de un documento en Network tab
2. Actualiza `mapeo_campos` en config con los nombres reales
3. Usa notación de punto para campos anidados: `data.documento.numero`

## 📁 Archivos generados

Después del scraping, encontrarás en `data/raw/tcp_jurisprudencia/`:

```
data/raw/tcp_jurisprudencia/
├── documentos_20250118_123456.json    # Metadatos completos
├── documentos_20250118_123456.csv     # CSV para análisis
└── pdfs/                              # PDFs descargados
    ├── Sentencia_Constitucional_0001-2024_abc123.pdf
    ├── Auto_Constitucional_0002-2024_def456.pdf
    └── ...
```

### Estructura del JSON

```json
[
  {
    "id_documento": "abc123",
    "numero_resolucion": "0001/2024",
    "tipo_documento": "Sentencia Constitucional",
    "fecha_resolucion": "2024-01-15",
    "fecha_ingreso": "2024-01-10",
    "materia": "Amparo Constitucional",
    "sumilla": "Resumen del caso...",
    "expediente": "EXP-2024-001",
    "partes": "Juan Pérez vs. Estado",
    "magistrado": "Dr. Magistrado Nombre",
    "url_pdf": "https://...",
    "ruta_pdf": "/path/to/pdf",
    "site_id": "tcp_jurisprudencia",
    "area_derecho": "Constitucional",
    "fecha_scraping": "2025-01-18T12:34:56",
    "json_raw": { ... }
  },
  ...
]
```

## 🔄 Actualización continua

Para mantener la base de datos actualizada:

```bash
# Ejecutar diariamente (cron)
0 2 * * * cd /path/to/buho && python main.py scrape tcp_jurisprudencia --mode incremental
```

Esto descargará solo documentos de los últimos 30 días.

## 🆚 Diferencias con tcp_gaceta

| Característica | tcp_gaceta | tcp_jurisprudencia |
|----------------|------------|-------------------|
| Fuente | Gacetas TCP (tomos, guías) | Buscador de jurisprudencia |
| Tipo | PDF simple (listados) | Sentencias individuales |
| Tecnología | Scraping HTML | API REST |
| Cobertura | Gacetas publicadas | Toda la jurisprudencia |
| Scraper | (otro scraper) | `tcp_jurisprudencia_scraper.py` |

**NO mezcles los dos scrapers. Son completamente independientes.**

## 🐛 Debugging

Habilitar logs detallados:

```python
# En tcp_jurisprudencia_scraper.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Ver requests:

```python
# Agregar al scraper
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

## 📚 Referencias

- Sitios TCP:
  - https://buscador.tcpbolivia.bo/
  - https://jurisprudencia.tcpbolivia.bo/

- Documentación del proyecto:
  - `README.md`: Documentación general
  - `config/sites_catalog.yaml`: Configuración completa
  - `scraper/sites/tcp_jurisprudencia_scraper.py`: Código fuente
