# FASE 8: EXPORTACIONES PROFESIONALES PARA SUPABASE

## Memoria Legal Dinámica (MLD) de BÚHO

Esta fase implementa un pipeline completo de exportación de datos extraídos a formato JSONL listo para importar en Supabase, permitiendo alimentar el sistema de Memoria Legal Dinámica basado en pgvector.

---

## 📋 Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Estructura de Datos](#estructura-de-datos)
3. [Uso del Exportador](#uso-del-exportador)
4. [Importación en Supabase](#importación-en-supabase)
5. [Generación de Embeddings](#generación-de-embeddings)
6. [Consultas SQL Útiles](#consultas-sql-útiles)
7. [Integración con MLD](#integración-con-mld)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
bo-gov-scraper-buho/
│
├── schema/
│   └── supabase_schema.sql      # Schema completo de la base de datos
│
├── exporter/
│   ├── __init__.py              # Exports del módulo
│   ├── export_supabase.py       # Lógica principal de exportación
│   └── utils.py                 # Utilidades de limpieza y validación
│
├── data/                         # Datos JSON extraídos (input)
│   └── *.json
│
├── exports/                      # Archivos JSONL generados (output)
│   ├── documents_supabase_*.jsonl
│   ├── articles_supabase_*.jsonl
│   └── export_stats_*.json
│
└── main.py                       # CLI principal
```

### Flujo de Datos

```
┌─────────────────┐
│  Scraper/OCR    │
│  (Fases 1-7)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   data/*.json   │  ◄── Documentos extraídos en JSON
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Exportador    │  ◄── Procesa, limpia, valida
│  (FASE 8)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ exports/*.jsonl │  ◄── JSONL listo para Supabase
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase DB   │  ◄── PostgreSQL + pgvector
│   (MLD BÚHO)    │
└─────────────────┘
```

---

## 📊 Estructura de Datos

### Tabla: `documents`

Almacena documentos normativos completos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_documento` | TEXT (PK) | ID único: `{sitio}_{tipo}_{numero}_{fecha}` |
| `sitio` | TEXT | Nombre del sitio fuente (ej: gaceta, abi) |
| `tipo_norma` | TEXT | Tipo: ley, decreto_supremo, resolucion, etc. |
| `numero_norma` | TEXT | Número de la norma |
| `fecha_norma` | TEXT | Fecha de promulgación (YYYY-MM-DD) |
| `titulo` | TEXT | Título del documento |
| `url_fuente` | TEXT | URL de la página fuente |
| `url_pdf` | TEXT | URL del PDF (si existe) |
| `filename_pdf` | TEXT | Nombre del archivo PDF descargado |
| `metodo_extraccion` | TEXT | pdf_text, ocr, html, api |
| `paginas` | INTEGER | Número de páginas |
| `caracteres` | INTEGER | Total de caracteres extraídos |
| `total_articulos` | INTEGER | Número de artículos en el documento |
| `fecha_extraccion` | TIMESTAMP | Fecha de extracción |
| `estado` | TEXT | extraido, procesado, vectorizado, error |
| `raw_metadata` | JSONB | Metadatos originales en JSON |

### Tabla: `articles`

Almacena artículos individuales de cada documento.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_articulo` | TEXT (PK) | ID único: `{id_documento}_art{numero}` |
| `id_documento` | TEXT (FK) | Referencia a documents |
| `numero_articulo` | TEXT | Número del artículo |
| `titulo_articulo` | TEXT | Título del artículo (si existe) |
| `contenido` | TEXT | Texto completo del artículo |
| `tipo_norma` | TEXT | Heredado del documento |
| `fecha_norma` | TEXT | Heredado del documento |
| `sitio` | TEXT | Nombre del sitio fuente |
| `orden` | INTEGER | Orden dentro del documento |
| `raw` | TEXT | Texto sin procesar |

### Tabla: `embeddings`

Almacena vectores de embeddings para búsqueda semántica.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL (PK) | ID autoincrementable |
| `id_articulo` | TEXT (FK) | Referencia a articles |
| `embedding` | VECTOR(1536) | Vector de 1536 dimensiones (OpenAI) |
| `modelo` | TEXT | Modelo usado (ej: text-embedding-ada-002) |
| `created_at` | TIMESTAMP | Fecha de creación |

### Tabla: `sources`

Catálogo de sitios fuente de normativa.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sitio` | TEXT (PK) | Identificador del sitio |
| `nombre` | TEXT | Nombre completo |
| `url` | TEXT | URL del sitio |
| `descripcion` | TEXT | Descripción del sitio |
| `configuracion` | JSONB | Configuración del scraper |

---

## 🚀 Uso del Exportador

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### Comandos CLI

#### 1. Exportar Todos los Datos

Procesa todos los archivos JSON en `data/` y genera JSONL:

```bash
python main.py --export-supabase
```

Salida:
- `exports/documents_supabase_YYYYMMDD_HHMMSS.jsonl`
- `exports/articles_supabase_YYYYMMDD_HHMMSS.jsonl`
- `exports/export_stats_YYYYMMDD_HHMMSS.json`

#### 2. Exportar Solo un Sitio Específico

Filtra documentos por sitio fuente:

```bash
python main.py --export-supabase --sitio gaceta
```

```bash
python main.py --export-supabase --sitio abi
```

#### 3. Exportar un Documento Individual

Procesa un solo archivo JSON:

```bash
python main.py --export-documento data/mi_documento.json
```

Con sitio explícito:

```bash
python main.py --export-documento data/mi_documento.json --sitio gaceta
```

#### 4. Ver Información del Proyecto

Muestra estadísticas y archivos generados:

```bash
python main.py --info
```

### Uso Programático

También puedes usar el exportador desde código Python:

```python
from exporter import export_supabase_ready

# Exportar todos los datos
resultados = export_supabase_ready(
    data_dir='data',
    export_dir='exports',
    sitio=None  # o 'gaceta' para filtrar
)

print(resultados['documents'])  # Ruta al archivo de documentos
print(resultados['articles'])   # Ruta al archivo de artículos
print(resultados['stats'])      # Ruta al archivo de estadísticas
```

---

## 📥 Importación en Supabase

### Método 1: Dashboard de Supabase (GUI)

1. **Crear la Base de Datos**

   Ve a tu proyecto en Supabase → SQL Editor

2. **Ejecutar el Schema**

   Copia y pega el contenido de `schema/supabase_schema.sql` y ejecuta.

3. **Importar Documentos**

   ```sql
   -- Opción A: Desde interfaz gráfica
   -- Table Editor → documents → Import data → Upload JSONL

   -- Opción B: Desde SQL Editor
   COPY documents FROM '/path/to/documents_supabase.jsonl';
   ```

4. **Importar Artículos**

   ```sql
   COPY articles FROM '/path/to/articles_supabase.jsonl';
   ```

### Método 2: Cliente Supabase Python

```python
from supabase import create_client, Client
import json

# Configurar cliente
url = "https://tu-proyecto.supabase.co"
key = "tu-api-key"
supabase: Client = create_client(url, key)

# Leer JSONL
documents = []
with open('exports/documents_supabase_20231115_120000.jsonl', 'r') as f:
    for line in f:
        documents.append(json.loads(line))

# Insertar en batch
for doc in documents:
    supabase.table('documents').insert(doc).execute()
```

### Método 3: psycopg2 Directo

```python
import psycopg2
import json

# Conectar a Supabase
conn = psycopg2.connect(
    host="db.tu-proyecto.supabase.co",
    database="postgres",
    user="postgres",
    password="tu-password"
)

cursor = conn.cursor()

# Insertar documentos
with open('exports/documents_supabase.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        cursor.execute("""
            INSERT INTO documents (
                id_documento, sitio, tipo_norma, numero_norma,
                fecha_norma, titulo, url_fuente, url_pdf,
                metodo_extraccion, estado, raw_metadata
            ) VALUES (
                %(id_documento)s, %(sitio)s, %(tipo_norma)s, %(numero_norma)s,
                %(fecha_norma)s, %(titulo)s, %(url_fuente)s, %(url_pdf)s,
                %(metodo_extraccion)s, %(estado)s, %(raw_metadata)s
            ) ON CONFLICT (id_documento) DO NOTHING;
        """, doc)

conn.commit()
conn.close()
```

---

## 🤖 Generación de Embeddings

### Usando OpenAI API

```python
import openai
from supabase import create_client

# Configurar clientes
openai.api_key = "tu-openai-api-key"
supabase = create_client("url", "key")

# Obtener artículos sin embeddings
articulos = supabase.table('articles') \
    .select('id_articulo, contenido') \
    .execute()

for articulo in articulos.data:
    # Generar embedding
    response = openai.Embedding.create(
        input=articulo['contenido'],
        model="text-embedding-ada-002"
    )

    embedding = response['data'][0]['embedding']

    # Insertar en tabla embeddings
    supabase.table('embeddings').insert({
        'id_articulo': articulo['id_articulo'],
        'embedding': embedding,
        'modelo': 'text-embedding-ada-002'
    }).execute()
```

### Script Batch para Embeddings

```python
import json
from openai import OpenAI
from supabase import create_client
from tqdm import tqdm

client = OpenAI(api_key="tu-api-key")
supabase = create_client("url", "key")

# Obtener artículos sin embeddings
result = supabase.from_('view_articles_enriched') \
    .select('id_articulo, contenido') \
    .filter('tiene_embedding', 'eq', False) \
    .execute()

print(f"Procesando {len(result.data)} artículos...")

for articulo in tqdm(result.data):
    try:
        # Generar embedding
        response = client.embeddings.create(
            input=articulo['contenido'][:8000],  # Truncar si es muy largo
            model="text-embedding-ada-002"
        )

        embedding = response.data[0].embedding

        # Insertar
        supabase.table('embeddings').insert({
            'id_articulo': articulo['id_articulo'],
            'embedding': embedding,
            'modelo': 'text-embedding-ada-002'
        }).execute()

    except Exception as e:
        print(f"Error en {articulo['id_articulo']}: {e}")
        continue

print("✅ Embeddings generados exitosamente!")
```

---

## 🔍 Consultas SQL Útiles

### Búsqueda por Tipo de Norma

```sql
SELECT
    id_documento,
    tipo_norma,
    numero_norma,
    fecha_norma,
    titulo,
    total_articulos
FROM documents
WHERE tipo_norma = 'ley'
ORDER BY fecha_norma DESC
LIMIT 20;
```

### Artículos con Metadata del Documento

```sql
SELECT
    a.numero_articulo,
    a.contenido,
    d.tipo_norma,
    d.numero_norma,
    d.fecha_norma,
    d.titulo AS titulo_documento,
    d.sitio
FROM articles a
JOIN documents d ON a.id_documento = d.id_documento
WHERE d.tipo_norma = 'decreto_supremo'
AND d.fecha_norma >= '2023-01-01'
ORDER BY d.fecha_norma DESC, a.orden ASC;
```

### Búsqueda de Texto Completo

```sql
SELECT
    id_articulo,
    numero_articulo,
    contenido,
    ts_rank(to_tsvector('spanish', contenido), query) AS rank
FROM articles,
     to_tsquery('spanish', 'salud & educación') AS query
WHERE to_tsvector('spanish', contenido) @@ query
ORDER BY rank DESC
LIMIT 10;
```

### Búsqueda Semántica por Similitud

```sql
-- Primero obtener el embedding de la consulta desde tu app
-- Luego buscar artículos similares

SELECT
    id_articulo,
    numero_articulo,
    contenido,
    tipo_norma,
    fecha_norma,
    1 - (embedding <=> '[vector de consulta]'::vector) AS similarity
FROM embeddings e
JOIN articles a USING (id_articulo)
WHERE 1 - (embedding <=> '[vector de consulta]'::vector) > 0.7
ORDER BY embedding <=> '[vector de consulta]'::vector
LIMIT 10;
```

### Estadísticas por Sitio

```sql
SELECT
    sitio,
    COUNT(DISTINCT id_documento) AS total_documentos,
    COUNT(DISTINCT a.id_articulo) AS total_articulos,
    COUNT(DISTINCT e.id) AS total_embeddings
FROM documents d
LEFT JOIN articles a ON d.id_documento = a.id_documento
LEFT JOIN embeddings e ON a.id_articulo = e.id_articulo
GROUP BY sitio
ORDER BY total_documentos DESC;
```

### Documentos Pendientes de Vectorización

```sql
SELECT
    d.id_documento,
    d.tipo_norma,
    d.numero_norma,
    d.titulo,
    COUNT(a.id_articulo) AS articulos_totales,
    COUNT(e.id) AS articulos_vectorizados
FROM documents d
LEFT JOIN articles a ON d.id_documento = a.id_documento
LEFT JOIN embeddings e ON a.id_articulo = e.id_articulo
GROUP BY d.id_documento
HAVING COUNT(a.id_articulo) > COUNT(e.id);
```

---

## 🧠 Integración con MLD (Memoria Legal Dinámica)

### Arquitectura de Búsqueda Híbrida

La MLD de BÚHO combina:

1. **Búsqueda por Keywords** (PostgreSQL Full-Text Search)
2. **Búsqueda Semántica** (pgvector + OpenAI embeddings)
3. **Filtros Estructurados** (por tipo, fecha, sitio)

### Ejemplo de Consulta Híbrida

```python
def buscar_normativa(
    query: str,
    tipo_norma: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    usar_semantico: bool = True
) -> List[Dict]:

    if usar_semantico:
        # Generar embedding de la consulta
        embedding = openai.Embedding.create(
            input=query,
            model="text-embedding-ada-002"
        )['data'][0]['embedding']

        # Buscar por similitud vectorial
        query_sql = """
            SELECT
                a.id_articulo,
                a.numero_articulo,
                a.contenido,
                d.tipo_norma,
                d.numero_norma,
                d.fecha_norma,
                d.titulo,
                1 - (e.embedding <=> %s::vector) AS similarity
            FROM embeddings e
            JOIN articles a ON e.id_articulo = a.id_articulo
            JOIN documents d ON a.id_documento = d.id_documento
            WHERE 1 = 1
        """
        params = [embedding]

    else:
        # Búsqueda por texto completo
        query_sql = """
            SELECT
                a.id_articulo,
                a.numero_articulo,
                a.contenido,
                d.tipo_norma,
                d.numero_norma,
                d.fecha_norma,
                d.titulo,
                ts_rank(to_tsvector('spanish', a.contenido), query) AS similarity
            FROM articles a
            JOIN documents d ON a.id_documento = d.id_documento,
                 to_tsquery('spanish', %s) AS query
            WHERE to_tsvector('spanish', a.contenido) @@ query
        """
        params = [query]

    # Agregar filtros
    if tipo_norma:
        query_sql += " AND d.tipo_norma = %s"
        params.append(tipo_norma)

    if fecha_desde:
        query_sql += " AND d.fecha_norma >= %s"
        params.append(fecha_desde)

    if fecha_hasta:
        query_sql += " AND d.fecha_norma <= %s"
        params.append(fecha_hasta)

    query_sql += " ORDER BY similarity DESC LIMIT 20"

    # Ejecutar
    cursor.execute(query_sql, params)
    return cursor.fetchall()
```

---

## 🛠️ Troubleshooting

### Problema: Duplicados en la Importación

**Solución:** El exportador ya elimina duplicados automáticamente por ID. Si persisten:

```sql
-- Eliminar duplicados de documents
DELETE FROM documents a USING (
    SELECT MIN(ctid) as ctid, id_documento
    FROM documents
    GROUP BY id_documento HAVING COUNT(*) > 1
) b
WHERE a.id_documento = b.id_documento
AND a.ctid <> b.ctid;

-- Eliminar duplicados de articles
DELETE FROM articles a USING (
    SELECT MIN(ctid) as ctid, id_articulo
    FROM articles
    GROUP BY id_articulo HAVING COUNT(*) > 1
) b
WHERE a.id_articulo = b.id_articulo
AND a.ctid <> b.ctid;
```

### Problema: Encoding UTF-8

**Solución:** El exportador normaliza automáticamente a UTF-8. Si hay problemas:

```python
# En utils.py, la función limpiar_texto() ya maneja esto
# Pero si necesitas forzar:
import unicodedata

texto = unicodedata.normalize('NFKC', texto)
```

### Problema: Artículos sin ID de Documento

**Error:** `foreign key violation`

**Solución:** Importa primero los documentos, luego los artículos:

```bash
# 1. Importar documentos
psql -h db.supabase.co -d postgres -U postgres \
  -c "\COPY documents FROM 'documents.jsonl' CSV QUOTE E'\x01' DELIMITER E'\x02';"

# 2. Importar artículos
psql -h db.supabase.co -d postgres -U postgres \
  -c "\COPY articles FROM 'articles.jsonl' CSV QUOTE E'\x01' DELIMITER E'\x02';"
```

### Problema: Embeddings muy Lentos

**Solución:** Procesar en batch y usar rate limiting:

```python
import time
from tqdm import tqdm

BATCH_SIZE = 100
RATE_LIMIT_DELAY = 1  # segundos

articulos = obtener_articulos_sin_embeddings()

for i in tqdm(range(0, len(articulos), BATCH_SIZE)):
    batch = articulos[i:i+BATCH_SIZE]
    procesar_batch(batch)
    time.sleep(RATE_LIMIT_DELAY)
```

---

## 📚 Referencias

- [Supabase Docs](https://supabase.com/docs)
- [pgvector](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

---

## 🎯 Próximos Pasos

1. ✅ Implementar scrapers para sitios bolivianos (Fases 1-7)
2. ✅ Exportar datos a Supabase (FASE 8 - Completada)
3. 🔄 Generar embeddings para todos los artículos
4. 🔄 Implementar API de búsqueda híbrida
5. 🔄 Crear interfaz web con Streamlit
6. 🔄 Automatizar scraping periódico
7. 🔄 Implementar sistema de alertas

---

**Desarrollado para BÚHO - Memoria Legal Dinámica**

*FASE 8 - Noviembre 2025*
