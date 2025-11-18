# Guía de Uso Práctico - Scraper Gubernamental Bolivia

## Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Comandos Básicos](#comandos-básicos)
3. [Ejemplos de Uso](#ejemplos-de-uso)
4. [Interfaz Web](#interfaz-web)
5. [Interpretación de Resultados](#interpretación-de-resultados)
6. [Solución de Problemas](#solución-de-problemas)

---

## Inicio Rápido

### Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd bo-gov-scraper-buho

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar instalación
python main.py --help
```

### Primer Scraping

```bash
# Ejecutar demo de un sitio
python main.py scrape gaceta_oficial --limit 5 --demo

# Ver resultados
python main.py stats
```

---

## Comandos Básicos

### 1. Listar Sitios (`list`)

```bash
# Ver todos los sitios
python main.py list

# Solo sitios de prioridad 1 (Ola 1)
python main.py list --prioridad 1

# Solo sitios judiciales
python main.py list --categoria judicial

# Solo scrapers implementados
python main.py list --estado implementado
```

**Salida esperada:**
```
================================================================================
CATÁLOGO DE SITIOS GUBERNAMENTALES
================================================================================

ID: gaceta_oficial
  Nombre: Gaceta Oficial de Bolivia
  Categoría: legislativo
  Prioridad: 1
  Estado Scraper: implementado
  URL: http://www.gacetaoficialdebolivia.gob.bo
  Tipos: Leyes, Decretos Supremos, Resoluciones Ministeriales...
  Notas: Sitio principal para normativa nacional...
```

### 2. Ejecutar Scraping (`scrape`)

```bash
# Scraping básico con límite
python main.py scrape gaceta_oficial --limit 10 --demo

# Sin límite (todos los documentos disponibles)
python main.py scrape tcp --demo

# Solo documentos nuevos o modificados
python main.py scrape asfi --limit 20 --solo-nuevos --demo
```

**Parámetros:**
- `site_id`: ID del sitio a scrapear (requerido)
- `--limit N`: Limitar a N documentos (opcional)
- `--solo-nuevos`: Solo procesar documentos nuevos o modificados (default: True)
- `--demo`: Modo demostración (genera datos de prueba)

**Salida esperada:**
```
================================================================================
SCRAPING: Gaceta Oficial de Bolivia
================================================================================
Site ID: gaceta_oficial
URL: http://www.gacetaoficialdebolivia.gob.bo/normas/buscar
Modo: DEMO
Límite: 10
Solo nuevos: Sí
================================================================================

2025-01-18 10:30:15 - scraper.gaceta_oficial - INFO - Iniciando scraping...
2025-01-18 10:30:15 - scraper.gaceta_oficial - INFO - Generando datos demo...
2025-01-18 10:30:15 - scraper.gaceta_oficial - INFO - Scraping completado. 10 documentos procesados.

================================================================================
RESUMEN DE SCRAPING
================================================================================
Sitio: gaceta_oficial
Total encontrados: 10
  - Nuevos: 10
  - Modificados: 0
  - Sin cambios: 0
  - Con PDF: 10
Fecha: 2025-01-18T10:30:15
================================================================================

Ejemplos de documentos:
  - [NUEVO] Ley 1400 - Ley de modificación al Código Tributario Boliviano
    Fecha: 2025-01-15 | ID: GACETA_OFICIAL-LEY-1400-20250115
  - [NUEVO] Decreto Supremo 1401 - Reglamentación de la Ley de Empresas
    Fecha: 2025-01-12 | ID: GACETA_OFICIAL-DECRETO-SUPREMO-1401-20250112
  ... y 8 más

Datos guardados en: data/raw/gaceta_oficial/
Índice guardado en: data/index/gaceta_oficial.json
```

### 3. Demo de la Ola 1 (`demo-ola1`)

Ejecuta scraping de todos los sitios de prioridad 1:

```bash
# Demo de todos los sitios Ola 1 con 5 documentos cada uno
python main.py demo-ola1 --limit 5
```

**Salida esperada:**
```
================================================================================
DEMO - OLA 1 (SCRAPERS DE PRIORIDAD MÁXIMA)
================================================================================

Sitios a procesar: gaceta_oficial, tsj_genesis, tcp, asfi, sin

▶️  Procesando gaceta_oficial...
   ✅ 5 documentos | 5 nuevos | 5 con PDF

▶️  Procesando tsj_genesis...
   ✅ 5 documentos | 5 nuevos | 5 con PDF

▶️  Procesando tcp...
   ✅ 5 documentos | 5 nuevos | 5 con PDF

▶️  Procesando asfi...
   ✅ 5 documentos | 5 nuevos | 5 con PDF

▶️  Procesando sin...
   ✅ 5 documentos | 5 nuevos | 5 con PDF


================================================================================
RESUMEN FINAL - OLA 1
================================================================================

Sitios procesados: 5/5
Total documentos: 25
Nuevos: 25

================================================================================
```

### 4. Ver Estadísticas (`stats`)

```bash
python main.py stats
```

**Salida esperada:**
```
================================================================================
ESTADÍSTICAS DE SCRAPERS
================================================================================

Gaceta Oficial de Bolivia (gaceta_oficial)
  Total documentos: 10
  Última actualización: 2025-01-18 10:30:15

Tribunal Supremo de Justicia - GENESIS (tsj_genesis)
  Total documentos: 5
  Última actualización: 2025-01-18 10:32:20

================================================================================
```

---

## Ejemplos de Uso

### Caso 1: Recolección Inicial de Datos

**Objetivo:** Recolectar las primeras 50 normas de cada sitio de la Ola 1.

```bash
# Opción 1: Uno por uno
python main.py scrape gaceta_oficial --limit 50 --demo
python main.py scrape tsj_genesis --limit 50 --demo
python main.py scrape tcp --limit 50 --demo
python main.py scrape asfi --limit 50 --demo
python main.py scrape sin --limit 50 --demo

# Opción 2: Demo rápido
python main.py demo-ola1 --limit 50

# Ver estadísticas
python main.py stats
```

### Caso 2: Actualización Diaria

**Objetivo:** Actualizar solo documentos nuevos o modificados.

```bash
# Ejecutar sin límite, solo nuevos (default)
python main.py scrape gaceta_oficial --demo

# O especificar explícitamente
python main.py scrape tcp --solo-nuevos --demo
```

### Caso 3: Exploración de un Sitio Específico

**Objetivo:** Ver qué documentos tiene un sitio antes de scrapear todo.

```bash
# Ver info del sitio
python main.py list --estado implementado | grep -A 10 "tcp"

# Scrapear muestra pequeña
python main.py scrape tcp --limit 5 --demo

# Ver los datos generados
cat data/raw/tcp/documentos.json | python -m json.tool

# Ver el índice
cat data/index/tcp.json | python -m json.tool
```

### Caso 4: Monitoreo y Validación

**Objetivo:** Verificar que los scrapers están funcionando correctamente.

```bash
# 1. Ejecutar demo completo
python main.py demo-ola1 --limit 10

# 2. Ver estadísticas
python main.py stats

# 3. Verificar archivos generados
ls -lh data/raw/*/
ls -lh data/index/

# 4. Revisar logs
tail -f scraper.log
```

---

## Interfaz Web

### Iniciar la Interfaz

```bash
streamlit run app/streamlit_app.py
```

Se abrirá automáticamente en `http://localhost:8501`

### Páginas Disponibles

#### 1. Dashboard
- Vista general de todos los sitios
- Métricas de documentos totales
- Estado de scrapers de la Ola 1
- Última actualización por sitio

#### 2. Catálogo de Sitios
- Lista completa de sitios con filtros:
  - Por prioridad (1, 2, ...)
  - Por categoría (legislativo, judicial, regulatorio)
  - Por estado (implementado, pendiente)
- Detalles de cada sitio

#### 3. Ejecutar Scraping
- Selector de sitio
- Configuración de parámetros:
  - Límite de documentos
  - Solo nuevos
  - Modo demo
- Botón de ejecución
- Resultados en tiempo real
- Vista previa de documentos

#### 4. Estadísticas
- Estadísticas por sitio:
  - Total de documentos
  - Última actualización
  - Distribución por estado (nuevo, modificado, sin cambios)
  - Distribución por tipo de norma

#### 5. Ayuda
- Documentación integrada
- Ejemplos de comandos CLI
- Estructura de datos

### Flujo de Trabajo en la UI

1. **Explorar el catálogo:**
   - Ir a "Catálogo de Sitios"
   - Filtrar por prioridad 1
   - Revisar sitios disponibles

2. **Ejecutar scraping:**
   - Ir a "Ejecutar Scraping"
   - Seleccionar sitio (ej: "Gaceta Oficial")
   - Configurar límite: 10
   - Marcar "Modo demo"
   - Click en "🚀 Ejecutar Scraping"
   - Ver resultados

3. **Ver estadísticas:**
   - Ir a "Estadísticas"
   - Expandir sitios de interés
   - Analizar distribución de documentos

---

## Interpretación de Resultados

### Estados de Documentos

Los documentos pueden tener tres estados:

- **`nuevo`**: Documento visto por primera vez
- **`modificado`**: Documento existente con cambios en el contenido
- **`sin_cambios`**: Documento ya visto sin cambios

### Estructura de Datos

#### Archivo de Documentos (`data/raw/<site_id>/documentos.json`)

```json
[
  {
    "site_id": "gaceta_oficial",
    "document_id": "GACETA_OFICIAL-LEY-1400-20250115",
    "titulo": "Ley 1400 - Ley de modificación al Código Tributario",
    "tipo_norma": "Ley",
    "numero_norma": "1400",
    "fecha_publicacion": "2025-01-15",
    "url_detalle": "http://...",
    "url_pdf": "http://.../gaceta_1400.pdf",
    "path_pdf": null,
    "hash_contenido": "a1b2c3d4e5f6...",
    "estado": "nuevo",
    "metadata_extra": {"modo": "demo", "indice": 0},
    "fecha_scraping": "2025-01-18T10:30:15.123456"
  }
]
```

#### Archivo de Índice (`data/index/<site_id>.json`)

```json
{
  "GACETA_OFICIAL-LEY-1400-20250115": {
    "hash": "a1b2c3d4e5f6...",
    "titulo": "Ley 1400...",
    "fecha_publicacion": "2025-01-15",
    "fecha_ultima_vez_visto": "2025-01-18T10:30:15",
    "estado": "nuevo",
    "url_pdf": "http://..."
  }
}
```

### Cómo Usar los Datos

#### En Python:

```python
import json
from pathlib import Path

# Leer documentos
with open('data/raw/gaceta_oficial/documentos.json', 'r') as f:
    documentos = json.load(f)

# Filtrar leyes
leyes = [d for d in documentos if d['tipo_norma'] == 'Ley']
print(f"Total leyes: {len(leyes)}")

# Documentos recientes
from datetime import datetime, timedelta
fecha_limite = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
recientes = [d for d in documentos if d['fecha_publicacion'] >= fecha_limite]
print(f"Documentos últimos 30 días: {len(recientes)}")
```

#### En la Terminal:

```bash
# Contar documentos
cat data/raw/gaceta_oficial/documentos.json | python -m json.tool | grep "document_id" | wc -l

# Ver solo nuevos
cat data/raw/gaceta_oficial/documentos.json | python -m json.tool | grep -A 5 '"estado": "nuevo"'

# Listar tipos de normas
cat data/raw/gaceta_oficial/documentos.json | python -m json.tool | grep "tipo_norma" | sort | uniq
```

---

## Solución de Problemas

### Error: "No se encontró el catálogo"

**Problema:** El archivo `config/sites_catalog.yaml` no existe.

**Solución:**
```bash
# Verificar que existe
ls config/sites_catalog.yaml

# Si no existe, verificar que estás en el directorio correcto
pwd  # Debe ser /path/to/bo-gov-scraper-buho
```

### Error: "No hay scraper implementado"

**Problema:** Intentaste scrapear un sitio de la Ola 2 u otro no implementado.

**Solución:**
```bash
# Ver solo sitios implementados
python main.py list --estado implementado

# Usar solo site_ids de la Ola 1:
# - gaceta_oficial
# - tsj_genesis
# - tcp
# - asfi
# - sin
```

### Error: ImportError con módulos

**Problema:** Falta instalar dependencias.

**Solución:**
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "pyyaml|requests|beautifulsoup4|streamlit"
```

### Sin Datos en Estadísticas

**Problema:** `python main.py stats` dice "No hay datos".

**Solución:**
```bash
# Primero ejecuta algún scraper
python main.py demo-ola1 --limit 5

# Ahora verifica
python main.py stats

# Verifica manualmente
ls -lh data/index/
```

### Logs para Debugging

```bash
# Ver logs en tiempo real
tail -f scraper.log

# Buscar errores
grep ERROR scraper.log

# Logs de un sitio específico
grep "gaceta_oficial" scraper.log
```

### Limpiar Datos y Empezar de Nuevo

```bash
# CUIDADO: Esto borra todos los datos scrapeados
rm -rf data/raw/*
rm -rf data/index/*
rm scraper.log

# Verificar limpieza
python main.py stats
# Debe decir "No hay datos de scraping todavía"
```

---

## Próximos Pasos

Una vez dominado el uso básico:

1. **Fase 3 (Próxima):** Procesamiento de texto y OCR
2. **Fase 4 (Futura):** Integración con Supabase
3. **Fase 5 (Futura):** API REST y sistema de notificaciones

---

**Fecha:** 2025-01-18
**Versión:** Fase 2 - Ola 1
**Autor:** Sistema Scraper Gubernamental Bolivia
