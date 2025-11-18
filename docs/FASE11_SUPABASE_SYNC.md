# FASE 11: Sincronización Extendida con Supabase

## Descripción General

Sistema de sincronización idempotente entre el almacenamiento local (exports CSV y JSON normalizados) y Supabase PostgreSQL, incluyendo toda la metadata extendida: áreas del derecho, jerarquía normativa, estado de vigencia, palabras clave, etc.

## Arquitectura

```
exports/                          sync/                         Supabase PostgreSQL
  ├── tcp/                       ├── __init__.py               ├── sources
  │   └── 20250118_143025/      └── supabase_sync_extended.py ├── documents
  │       ├── documentos.csv         ↓                         ├── articles
  │       ├── articulos.csv          ↓                         └── extraction_logs
  │       └── registro_historico.jsonl
                                     ↓
data/normalized/                   SYNC
  ├── tcp/                          ↓
  │   └── json/                 Idempotent
  │       └── *.json            (hash check)
```

## Componentes

### 1. Módulo: `sync/supabase_sync_extended.py`

Sincronizador completo con las siguientes capacidades:

#### Clase Principal: `SupabaseSyncExtended`

```python
from sync import SupabaseSyncExtended

# Inicializar
syncer = SupabaseSyncExtended(
    exports_dir=Path("exports"),
    normalized_dir=Path("data/normalized"),
    log_dir=Path("logs/sync_supabase")
)

# Sincronizar un sitio
stats = syncer.sync_site("tcp")

# Sincronizar todos los sitios
stats_global = syncer.sync_all_sites()
```

#### Características Principales

1. **Lectura Multi-Fuente**
   - Lee desde `exports/{site}/{timestamp}/documentos.csv` y `articulos.csv`
   - Lee desde `data/normalized/{site}/json/*.json` como fallback
   - Combina información de múltiples fuentes

2. **Mapeo Completo a Schema**
   - Tabla `sources`: Información de sitios web
   - Tabla `documents`: Documentos con metadata extendida
   - Tabla `articles`: Artículos/secciones de documentos
   - Tabla `extraction_logs`: Logs de sesiones de scraping

3. **Sincronización Idempotente**
   - Verifica hash MD5 del contenido antes de actualizar
   - Solo actualiza si el contenido cambió
   - Evita duplicados y operaciones innecesarias

4. **Gestión de Metadata Extendida**
   - `tipo_norma`: Tipo normalizado (Ley, Decreto Supremo, etc.)
   - `jerarquia`: 1-99 (1=CPE, 2=Ley, 3=DS, etc.)
   - `area_principal`: Área del derecho principal
   - `areas_derecho`: Array de áreas detectadas
   - `estado_vigencia`: vigente | modificada | derogada
   - `entidad_emisora`: Entidad que emite la norma
   - `palabras_clave`: Array de palabras clave
   - `modifica_normas`: Array de normas modificadas
   - `deroga_normas`: Array de normas derogadas

5. **Logging Detallado**
   - Logs en `logs/sync_supabase/sync_TIMESTAMP.log`
   - Estadísticas completas por sesión
   - Seguimiento de errores

### 2. Schema de Supabase

**Archivo:** `db/schemas/supabase_schema.sql`

#### Tablas Principales

##### `sources` (Fuentes/Sitios)
```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    source_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255),
    tipo VARCHAR(100),
    categoria VARCHAR(100),
    url_base TEXT,
    prioridad INTEGER,
    activo BOOLEAN DEFAULT true
);
```

##### `documents` (Documentos Legales con Metadata Extendida)
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    id_documento VARCHAR(255) UNIQUE NOT NULL,
    source_id VARCHAR(50) REFERENCES sources(source_id),

    -- Clasificación básica
    tipo_documento VARCHAR(100),
    numero_norma VARCHAR(100),
    fecha DATE,
    titulo TEXT,

    -- METADATA EXTENDIDA
    tipo_norma VARCHAR(100),
    jerarquia INTEGER,                    -- 1-99
    area_principal VARCHAR(100),          -- constitucional, penal, tributario, etc.
    areas_derecho TEXT[],                 -- Array de áreas
    estado_vigencia VARCHAR(50),          -- vigente, modificada, derogada
    entidad_emisora VARCHAR(255),
    palabras_clave TEXT[],
    modifica_normas TEXT[],
    deroga_normas TEXT[],

    -- Archivos y control
    ruta_pdf TEXT,
    ruta_txt TEXT,
    ruta_json TEXT,
    hash_contenido VARCHAR(32),

    -- Estadísticas
    total_articulos INTEGER,
    total_caracteres INTEGER,
    total_palabras INTEGER,
    paginas_estimadas INTEGER
);
```

**Índices para Performance:**
- GIN indexes para arrays (`areas_derecho`, `palabras_clave`)
- Full-text search para español (`to_tsvector('spanish', titulo)`)
- Índices en campos clave (área, jerarquía, estado)

##### `articles` (Artículos/Secciones)
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY,
    id_articulo VARCHAR(255) UNIQUE NOT NULL,
    id_documento VARCHAR(255) REFERENCES documents(id_documento) ON DELETE CASCADE,
    numero VARCHAR(50),
    titulo TEXT,
    contenido TEXT NOT NULL,
    tipo_unidad VARCHAR(50),              -- articulo, seccion, capitulo
    orden INTEGER
);
```

##### `extraction_logs` (Logs de Scraping)
```sql
CREATE TABLE extraction_logs (
    id UUID PRIMARY KEY,
    source_id VARCHAR(50) REFERENCES sources(source_id),
    session_id VARCHAR(100),
    modo VARCHAR(20),                     -- full, delta
    total_encontrados INTEGER,
    total_descargados INTEGER,
    total_parseados INTEGER,
    total_errores INTEGER,
    errores JSONB
);
```

#### Vistas Útiles

##### `vw_stats_por_area`
Estadísticas agrupadas por área del derecho:
```sql
SELECT area_principal, COUNT(*) as total_documentos, ...
FROM documents
GROUP BY area_principal;
```

##### `vw_stats_por_jerarquia`
Estadísticas por nivel jerárquico:
```sql
SELECT jerarquia, tipo_norma, COUNT(*) as total_documentos
FROM documents
GROUP BY jerarquia, tipo_norma;
```

### 3. Comandos CLI

#### Sincronizar un Sitio Específico

```bash
# Sincronizar TCP (Tribunal Constitucional)
python main.py sync-supabase tcp

# Sincronizar una sesión específica
python main.py sync-supabase tcp --session 20250118_143025
```

#### Sincronizar Todos los Sitios

```bash
# Sincronizar todos los sitios disponibles
python main.py sync-supabase --all
```

**Salida esperada:**
```
🔄 Sincronización con Supabase
--------------------------------------------------------------------------------

📋 Sincronizando TODOS los sitios...

============================================================
Sincronizando sitio: tcp
============================================================
Leídos 45 documentos desde exports CSV
[1/45] Procesando: tcp_ley_123_2024
[2/45] Procesando: tcp_ds_456_2024
...

============================================================
ESTADÍSTICAS DE SINCRONIZACIÓN
============================================================
Sources insertados: 1
Sources actualizados: 0
Documents insertados: 30
Documents actualizados: 15
Articles insertados: 450
Extraction logs: 1
Errores: 0
============================================================

...

============================================================
RESUMEN DE SINCRONIZACIÓN MASIVA
============================================================
Sitios procesados: 5
Sitios exitosos: 5
Sitios con errores: 0

✅ Sincronización completada
Ver logs en: logs/sync_supabase/
```

## Configuración

### 1. Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave_de_servicio_aqui
```

**Obtener credenciales:**
1. Ir a tu proyecto en Supabase
2. Settings → API
3. Copiar "Project URL" y "service_role key"

### 2. Instalar Dependencias

```bash
pip install supabase python-dotenv
```

### 3. Crear Schema en Supabase

```bash
# Opción 1: SQL Editor en Supabase Dashboard
# Copiar y ejecutar db/schemas/supabase_schema.sql

# Opción 2: psql (si tienes acceso directo)
psql -h db.tu-proyecto.supabase.co -U postgres -d postgres -f db/schemas/supabase_schema.sql
```

## Flujo de Trabajo

### Flujo Normal: Scraping → Sync

```bash
# 1. Hacer scraping de un sitio
python main.py scrape tcp --mode delta --limit 50 --save-txt --save-json

# 2. Sincronizar con Supabase
python main.py sync-supabase tcp

# 3. Verificar en Supabase Dashboard
# → Ver tabla documents con metadata extendida
```

### Flujo Histórico: Full Scraping → Sync All

```bash
# 1. Scraping histórico completo
./scripts/scrape_historico_completo.sh

# 2. Sincronizar todos los sitios
python main.py sync-supabase --all

# 3. Consultar estadísticas
python main.py stats
```

## Características de Sincronización

### 1. Idempotencia

El sistema verifica el hash MD5 del contenido antes de actualizar:

```python
# En _sync_document()
if hash_contenido:
    response = supabase.table('documents')\
        .select('hash_contenido')\
        .eq('id_documento', id_documento)\
        .execute()

    # Si existe y el hash es igual, skip
    if response.data and response.data[0]['hash_contenido'] == hash_contenido:
        logger.debug("Documento sin cambios (mismo hash)")
        return
```

**Beneficios:**
- No duplica datos
- Solo actualiza cuando hay cambios reales
- Optimiza uso de recursos

### 2. Manejo de Errores

```python
# Errores por tipo
self.stats['errores'].append({
    'tipo': 'document',
    'id': id_documento,
    'mensaje': str(e)
})
```

**Logs detallados:**
- Cada error se registra con contexto
- Logs guardados en `logs/sync_supabase/`
- No interrumpe la sincronización completa

### 3. Estadísticas en Tiempo Real

```python
stats = {
    'sources_insertados': 0,
    'sources_actualizados': 0,
    'documents_insertados': 0,
    'documents_actualizados': 0,
    'articles_insertados': 0,
    'extraction_logs_insertados': 0,
    'errores': []
}
```

## Consultas Útiles en Supabase

### Ver Documentos por Área

```sql
SELECT area_principal, COUNT(*) as total
FROM documents
GROUP BY area_principal
ORDER BY total DESC;
```

### Documentos por Jerarquía

```sql
SELECT jerarquia, tipo_norma, COUNT(*) as total
FROM documents
GROUP BY jerarquia, tipo_norma
ORDER BY jerarquia;
```

### Búsqueda Full-Text

```sql
SELECT titulo, area_principal, fecha
FROM documents
WHERE to_tsvector('spanish', titulo) @@ to_tsquery('spanish', 'tributario');
```

### Ver Logs de Scraping

```sql
SELECT source_id, session_id, modo, total_parseados, total_errores, created_at
FROM extraction_logs
ORDER BY created_at DESC
LIMIT 20;
```

## Resolución de Problemas

### Error: "Supabase no está instalado"

```bash
pip install supabase
```

### Error: "Faltan credenciales de Supabase"

Verificar archivo `.env`:
```bash
cat .env
# Debe contener SUPABASE_URL y SUPABASE_KEY
```

### Error: "Permission denied" al insertar

Verificar que estás usando `service_role` key (no `anon` key).

### Documentos no se sincronizan

```bash
# Ver logs detallados
cat logs/sync_supabase/sync_*.log | grep ERROR
```

## Próximos Pasos

1. **Embeddings para Búsqueda Semántica**
   - Tabla `embeddings` ya está en el schema
   - Generar vectores con OpenAI o alternativas
   - Búsqueda semántica con pgvector

2. **API REST / GraphQL**
   - Supabase auto-genera APIs
   - Consultas desde frontend/aplicaciones

3. **Row Level Security (RLS)**
   - Políticas de acceso por tipo de usuario
   - Auditoría de cambios

4. **Webhooks y Triggers**
   - Notificaciones en cambios
   - Validaciones automáticas

## Resumen

BLOQUE 1 implementa:
- ✅ Módulo `sync/supabase_sync_extended.py`
- ✅ Schema completo en `db/schemas/supabase_schema.sql`
- ✅ Comandos CLI: `sync-supabase <site>` y `sync-supabase --all`
- ✅ Sincronización idempotente con verificación de hash
- ✅ Mapeo completo de metadata extendida
- ✅ Logging detallado y manejo de errores
- ✅ Documentación completa

**Siguiente:** BLOQUE 2 - Interfaz QA Legal en Streamlit
