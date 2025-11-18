# Directorio de Exportaciones

Este directorio contiene los archivos JSONL generados por el exportador de Supabase (FASE 8).

## Archivos Generados

### Documentos
- `documents_supabase_YYYYMMDD_HHMMSS.jsonl` - Documentos normativos completos

### Artículos
- `articles_supabase_YYYYMMDD_HHMMSS.jsonl` - Artículos individuales de cada documento

### Estadísticas
- `export_stats_YYYYMMDD_HHMMSS.json` - Estadísticas del proceso de exportación

## Formato JSONL

Cada archivo `.jsonl` contiene una línea por registro en formato JSON:

```
{"id_documento": "gaceta_ley_1234_20231115", "sitio": "gaceta", ...}
{"id_documento": "gaceta_ley_5678_20231120", "sitio": "gaceta", ...}
```

## Importar en Supabase

Ver `FASE8_SUPABASE.md` para instrucciones detalladas de importación.

### Opción 1: GUI de Supabase
1. Ir a Table Editor
2. Seleccionar tabla (documents o articles)
3. Import data → Upload JSONL

### Opción 2: SQL
```sql
\COPY documents FROM 'documents_supabase.jsonl' CSV;
\COPY articles FROM 'articles_supabase.jsonl' CSV;
```

### Opción 3: Cliente Python
```python
from supabase import create_client
import json

supabase = create_client(url, key)

with open('documents_supabase.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        supabase.table('documents').insert(doc).execute()
```
