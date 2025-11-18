# Formato de Documento Normalizado

## Objetivo

Definir el formato estándar JSON y TXT para todos los documentos legales procesados por el sistema, garantizando consistencia, trazabilidad y facilidad de consulta.

## Principios de Diseño

1. **JSON como fuente canónica**: El archivo JSON contiene TODA la información del documento
2. **TXT para lectura**: El archivo TXT contiene solo el texto limpio para búsquedas y lectura
3. **Autocontenido**: Cada JSON debe ser independiente y completo
4. **Versionado**: Incluye hashes y fechas para tracking de cambios
5. **Extensible**: Campo `metadata` permite agregar información sin romper estructura

## Estructura de Archivos

### Organización en Disco

```
data/normalized/{site_id}/
├── json/
│   ├── {id_documento}.json       # Documento completo estructurado
│   ├── {id_documento}.json
│   └── ...
└── text/
    ├── {id_documento}.txt        # Solo texto limpio
    ├── {id_documento}.txt
    └── ...
```

### Ejemplo Concreto

```
data/normalized/tcp/
├── json/
│   ├── tcp_sc_0001_2024.json
│   ├── tcp_sc_0002_2024.json
│   └── tcp_sc_0003_2024.json
└── text/
    ├── tcp_sc_0001_2024.txt
    ├── tcp_sc_0002_2024.txt
    └── tcp_sc_0003_2024.txt
```

## Formato JSON

### Esquema Completo

```json
{
  "id_documento": "tcp_sc_0001_2024",
  "site": "tcp",
  "tipo_documento": "Sentencia Constitucional",
  "numero_norma": "0001/2024",
  "fecha": "2024-01-01",
  "fecha_publicacion": "2024-01-05",
  "titulo": "Sentencia Constitucional 0001/2024-S1",
  "sumilla": "Acción de Amparo Constitucional contra actos de autoridad administrativa",
  "url_origen": "https://www.tcpbolivia.bo/sentencias/2024/sc-0001-2024.pdf",

  "ruta_pdf": "data/raw/tcp/tcp_sc_0001_2024.pdf",
  "ruta_txt": "data/normalized/tcp/text/tcp_sc_0001_2024.txt",
  "ruta_json": "data/normalized/tcp/json/tcp_sc_0001_2024.json",

  "texto_completo": "TRIBUNAL CONSTITUCIONAL PLURINACIONAL\\n\\nSENTENCIA CONSTITUCIONAL...",

  "articulos": [
    {
      "id_articulo": "tcp_sc_0001_2024_art_001",
      "id_documento": "tcp_sc_0001_2024",
      "numero": "I",
      "titulo": "ANTECEDENTES CON RELEVANCIA JURÍDICA",
      "contenido": "Contenido completo de la sección...",
      "tipo_unidad": "seccion",
      "metadata": {}
    },
    {
      "id_articulo": "tcp_sc_0001_2024_art_002",
      "id_documento": "tcp_sc_0001_2024",
      "numero": "II",
      "titulo": "CONCLUSIONES",
      "contenido": "Contenido de las conclusiones...",
      "tipo_unidad": "seccion",
      "metadata": {}
    },
    {
      "id_articulo": "tcp_sc_0001_2024_art_003",
      "id_documento": "tcp_sc_0001_2024",
      "numero": "III",
      "titulo": "FUNDAMENTOS JURÍDICOS DEL FALLO",
      "contenido": "Fundamentos legales...",
      "tipo_unidad": "seccion",
      "metadata": {}
    },
    {
      "id_articulo": "tcp_sc_0001_2024_art_004",
      "id_documento": "tcp_sc_0001_2024",
      "numero": "POR TANTO",
      "titulo": null,
      "contenido": "El Tribunal Constitucional Plurinacional, en virtud...",
      "tipo_unidad": "disposicion",
      "metadata": {}
    }
  ],

  "metadata": {
    "area_principal": "constitucional",
    "areas_derecho": ["constitucional", "administrativo"],
    "tipo_norma": "Sentencia Constitucional",
    "jerarquia": 1,
    "estado_vigencia": "vigente",
    "entidad_emisora": "Tribunal Constitucional Plurinacional",
    "modifica_normas": [],
    "deroga_normas": [],
    "palabras_clave": ["amparo", "constitucional", "derecho", "administrativo"],
    "estadisticas": {
      "total_caracteres": 45678,
      "total_palabras": 7890,
      "total_articulos": 4
    }
  },

  "hash_contenido": "a1b2c3d4e5f6g7h8",
  "fecha_scraping": "2024-01-15T10:30:00.123456",
  "fecha_ultima_actualizacion": "2024-01-15T10:30:00.123456"
}
```

### Descripción de Campos

#### Campos Básicos de Identificación

| Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|-------|------|-------------|-------------|---------|
| `id_documento` | string | ✅ | ID único del documento | `"tcp_sc_0001_2024"` |
| `site` | string | ✅ | ID del sitio origen | `"tcp"`, `"tsj"`, `"sin"` |
| `tipo_documento` | string | ✅ | Tipo de norma/documento | `"Sentencia Constitucional"`, `"Ley"` |
| `numero_norma` | string | ❌ | Número oficial de la norma | `"843"`, `"0001/2024"` |
| `fecha` | string (ISO) | ❌ | Fecha del documento YYYY-MM-DD | `"2024-01-15"` |
| `fecha_publicacion` | string (ISO) | ❌ | Fecha de publicación | `"2024-01-20"` |
| `titulo` | string | ❌ | Título completo del documento | `"Ley 843 de Reforma Tributaria"` |
| `sumilla` | string | ❌ | Resumen breve del documento | `"Regula el sistema tributario..."` |
| `url_origen` | string (URL) | ❌ | URL del PDF original | `"https://..."` |

#### Campos de Rutas

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `ruta_pdf` | string | Ruta al PDF original | `"data/raw/tcp/tcp_sc_0001_2024.pdf"` |
| `ruta_txt` | string | Ruta al texto normalizado | `"data/normalized/tcp/text/tcp_sc_0001_2024.txt"` |
| `ruta_json` | string | Ruta a este JSON | `"data/normalized/tcp/json/tcp_sc_0001_2024.json"` |

**Nota**: Las rutas pueden ser `null` si no se guardó el archivo correspondiente.

#### Campos de Contenido

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `texto_completo` | string | Texto completo del documento extraído del PDF |
| `articulos` | array | Lista de artículos/secciones parseadas (ver estructura abajo) |

#### Campo metadata - Información Extendida

El campo `metadata` es un objeto JSON extensible con información legal:

```json
{
  "metadata": {
    // Clasificación legal
    "area_principal": "tributario",
    "areas_derecho": ["tributario", "financiero"],
    "tipo_norma": "Ley",
    "jerarquia": 2,

    // Estado y vigencia
    "estado_vigencia": "vigente",
    "entidad_emisora": "Asamblea Legislativa Plurinacional",

    // Relaciones con otras normas
    "modifica_normas": ["123", "456"],
    "deroga_normas": ["789"],

    // Indexación
    "palabras_clave": ["impuesto", "IVA", "tributario"],

    // Estadísticas
    "estadisticas": {
      "total_caracteres": 45678,
      "total_palabras": 7890,
      "total_articulos": 15
    }
  }
}
```

##### Campos de metadata

| Campo | Tipo | Valores Posibles | Descripción |
|-------|------|------------------|-------------|
| `area_principal` | string | Ver tabla de áreas | Área principal del derecho |
| `areas_derecho` | array[string] | Ver tabla de áreas | Todas las áreas que toca |
| `tipo_norma` | string | Ver tabla de tipos | Tipo de norma legal |
| `jerarquia` | integer | 1-99 | Jerarquía normativa (1=más alta) |
| `estado_vigencia` | string | vigente, modificada, derogada | Estado actual |
| `entidad_emisora` | string | Libre | Entidad que emitió la norma |
| `modifica_normas` | array[string] | - | Números de normas modificadas |
| `deroga_normas` | array[string] | - | Números de normas derogadas |
| `palabras_clave` | array[string] | - | Palabras clave extraídas |
| `estadisticas` | object | - | Estadísticas del documento |

##### Tabla de Áreas del Derecho

| Área | Descripción |
|------|-------------|
| `constitucional` | Derecho Constitucional |
| `administrativo` | Derecho Administrativo |
| `tributario` | Derecho Tributario y Fiscal |
| `penal` | Derecho Penal |
| `civil` | Derecho Civil |
| `laboral` | Derecho Laboral |
| `comercial` | Derecho Comercial y Empresarial |
| `procesal` | Derecho Procesal |
| `financiero` | Derecho Financiero |
| `ambiental` | Derecho Ambiental |
| `minero` | Derecho Minero |
| `agrario` | Derecho Agrario |
| `familia` | Derecho de Familia |
| `internacional` | Derecho Internacional |
| `electoral` | Derecho Electoral |

##### Tabla de Tipos de Norma

| Tipo | Descripción |
|------|-------------|
| `Constitución Política del Estado` | CPE |
| `Ley` | Leyes ordinarias |
| `Decreto Supremo` | Decretos del ejecutivo |
| `Resolución Ministerial` | Resoluciones de ministerios |
| `Resolución Administrativa` | Resoluciones administrativas |
| `Sentencia Constitucional` | Sentencias del TCP |
| `Auto Supremo` | Autos del TSJ |
| `Resolución Normativa` | Resoluciones normativas (SIN, etc.) |
| `Ordenanza Municipal` | Ordenanzas municipales |
| `Reglamento` | Reglamentos |

##### Jerarquía Normativa

| Nivel | Tipo de Norma | Jerarquía |
|-------|---------------|-----------|
| 1 | Constitución Política del Estado | 1 |
| 2 | Leyes | 2 |
| 3 | Decretos Supremos | 3 |
| 4 | Resoluciones Supremas | 4 |
| 5 | Resoluciones Ministeriales | 5 |
| 6 | Resoluciones Administrativas | 6 |
| 99 | Otros documentos legales | 99 |

#### Campos de Control

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `hash_contenido` | string | Hash MD5 del contenido (para detectar cambios) |
| `fecha_scraping` | string (ISO datetime) | Cuándo se descargó por primera vez |
| `fecha_ultima_actualizacion` | string (ISO datetime) | Última actualización del documento |

### Estructura de Artículos

Cada artículo en el array `articulos` tiene la siguiente estructura:

```json
{
  "id_articulo": "tcp_sc_0001_2024_art_001",
  "id_documento": "tcp_sc_0001_2024",
  "numero": "1",
  "titulo": "ANTECEDENTES",
  "contenido": "Texto completo del artículo...",
  "tipo_unidad": "articulo",
  "metadata": {}
}
```

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id_articulo` | string | ID único del artículo | `"tcp_sc_0001_2024_art_001"` |
| `id_documento` | string | ID del documento padre | `"tcp_sc_0001_2024"` |
| `numero` | string | Número/identificador del artículo | `"1"`, `"Art. 5"`, `"I"` |
| `titulo` | string/null | Título del artículo (puede ser null) | `"ANTECEDENTES"` |
| `contenido` | string | Texto completo del artículo | `"Contenido..."` |
| `tipo_unidad` | string | Tipo de unidad textual | Ver tabla abajo |
| `metadata` | object | Metadata específica del artículo | `{}` |

#### Tipos de Unidad Textual

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `articulo` | Artículo numerado | "Artículo 1.-" |
| `seccion` | Sección del documento | "I. ANTECEDENTES" |
| `capitulo` | Capítulo | "CAPÍTULO I" |
| `titulo` | Título (mayor que capítulo) | "TÍTULO PRIMERO" |
| `disposicion` | Disposición final/transitoria | "DISPOSICIONES FINALES" |
| `considerando` | Considerando | "CONSIDERANDO:" |
| `visto` | Vistos | "VISTOS:" |
| `por_tanto` | Por tanto | "POR TANTO:" |

## Formato TXT

### Estructura

El archivo `.txt` contiene únicamente el texto limpio del documento, sin metadata:

```
TRIBUNAL CONSTITUCIONAL PLURINACIONAL

SENTENCIA CONSTITUCIONAL 0001/2024-S1

Sucre, 1 de enero de 2024

ACCIÓN DE AMPARO CONSTITUCIONAL

[Texto completo del documento...]
```

### Características

- **Encoding**: UTF-8
- **Line endings**: `\n` (Unix)
- **Sin metadatos**: Solo texto puro
- **Normalizado**: Espacios en blanco normalizados
- **Uso**: Búsquedas de texto completo, indexación, lectura humana

## Ejemplos por Tipo de Documento

### Ejemplo 1: Sentencia Constitucional (TCP)

```json
{
  "id_documento": "tcp_sc_0042_2024",
  "site": "tcp",
  "tipo_documento": "Sentencia Constitucional",
  "numero_norma": "0042/2024",
  "fecha": "2024-02-15",
  "titulo": "Sentencia Constitucional 0042/2024-S2",
  "sumilla": "Acción de Libertad por detención preventiva sin fundamentación",
  "url_origen": "https://www.tcpbolivia.bo/sentencias/2024/sc-0042-2024.pdf",
  "texto_completo": "...",
  "articulos": [...],
  "metadata": {
    "area_principal": "constitucional",
    "areas_derecho": ["constitucional", "penal", "procesal"],
    "tipo_norma": "Sentencia Constitucional",
    "jerarquia": 1,
    "estado_vigencia": "vigente",
    "entidad_emisora": "Tribunal Constitucional Plurinacional"
  },
  "hash_contenido": "xyz789",
  "fecha_scraping": "2024-02-16T10:00:00",
  "fecha_ultima_actualizacion": "2024-02-16T10:00:00"
}
```

### Ejemplo 2: Auto Supremo (TSJ)

```json
{
  "id_documento": "tsj_as_0123_2024",
  "site": "tsj",
  "tipo_documento": "Auto Supremo",
  "numero_norma": "0123/2024",
  "fecha": "2024-03-10",
  "titulo": "Auto Supremo 0123/2024 - Materia Civil",
  "sumilla": "Recurso de casación sobre contratos civiles",
  "url_origen": "https://tsj.bo/autos/2024/as-0123-2024.pdf",
  "texto_completo": "...",
  "articulos": [...],
  "metadata": {
    "area_principal": "civil",
    "areas_derecho": ["civil", "procesal"],
    "tipo_norma": "Auto Supremo",
    "jerarquia": 2,
    "estado_vigencia": "vigente",
    "entidad_emisora": "Tribunal Supremo de Justicia"
  },
  "hash_contenido": "abc456",
  "fecha_scraping": "2024-03-11T14:30:00",
  "fecha_ultima_actualizacion": "2024-03-11T14:30:00"
}
```

### Ejemplo 3: Resolución Normativa (SIN)

```json
{
  "id_documento": "sin_rn_0015_2024",
  "site": "sin",
  "tipo_documento": "Resolución Normativa de Directorio",
  "numero_norma": "102400000015",
  "fecha": "2024-04-05",
  "titulo": "Resolución Normativa de Directorio 102400000015",
  "sumilla": "Normativa sobre IVA - actualización de procedimientos",
  "url_origen": "https://www.impuestos.gob.bo/normativa/rnd-0015-2024.pdf",
  "texto_completo": "...",
  "articulos": [...],
  "metadata": {
    "area_principal": "tributario",
    "areas_derecho": ["tributario", "administrativo"],
    "tipo_norma": "Resolución Normativa",
    "jerarquia": 5,
    "estado_vigencia": "vigente",
    "entidad_emisora": "Servicio de Impuestos Nacionales",
    "modifica_normas": ["102400000010"],
    "palabras_clave": ["IVA", "impuesto", "valor agregado", "facturación"]
  },
  "hash_contenido": "def789",
  "fecha_scraping": "2024-04-06T09:00:00",
  "fecha_ultima_actualizacion": "2024-04-06T09:00:00"
}
```

## Uso del Formato

### Cargar un Documento

```python
from scraper.models import Documento
from pathlib import Path

# Cargar desde JSON
doc = Documento.cargar_json(Path("data/normalized/tcp/json/tcp_sc_0001_2024.json"))

# Acceder a campos
print(doc.titulo)
print(doc.tipo_documento)
print(doc.metadata['area_principal'])

# Iterar artículos
for articulo in doc.articulos:
    print(f"{articulo.numero}: {articulo.titulo}")
```

### Crear un Documento

```python
from scraper.models import Documento, Articulo

# Crear documento
doc = Documento(
    id_documento="tcp_sc_0001_2024",
    site="tcp",
    tipo_documento="Sentencia Constitucional",
    numero_norma="0001/2024",
    titulo="Sentencia Constitucional 0001/2024-S1",
    texto_completo="..."
)

# Agregar metadata extendida
doc.metadata = {
    "area_principal": "constitucional",
    "areas_derecho": ["constitucional"],
    "jerarquia": 1,
    "estado_vigencia": "vigente"
}

# Agregar artículos
art1 = Articulo(
    id_articulo="tcp_sc_0001_2024_art_001",
    id_documento="tcp_sc_0001_2024",
    numero="I",
    titulo="ANTECEDENTES",
    contenido="...",
    tipo_unidad="seccion"
)
doc.agregar_articulo(art1)

# Actualizar hash
doc.actualizar_hash()

# Guardar
doc.guardar_json(Path("data/normalized/tcp/json/tcp_sc_0001_2024.json"))
```

### Leer Texto Normalizado

```python
from pathlib import Path

# Leer TXT
txt_path = Path("data/normalized/tcp/text/tcp_sc_0001_2024.txt")
with open(txt_path, 'r', encoding='utf-8') as f:
    texto = f.read()

# Buscar en texto
if "amparo constitucional" in texto.lower():
    print("Documento contiene 'amparo constitucional'")
```

## Validación del Formato

### Campos Obligatorios

Un documento válido debe tener al mínimo:

```python
required_fields = [
    'id_documento',
    'site',
    'tipo_documento'
]
```

### Validación Programática

```python
def validar_documento(doc_dict):
    """Validar que un documento tenga estructura correcta"""
    required = ['id_documento', 'site', 'tipo_documento']

    for field in required:
        if field not in doc_dict or not doc_dict[field]:
            raise ValueError(f"Campo obligatorio faltante: {field}")

    # Validar artículos si existen
    if 'articulos' in doc_dict:
        for art in doc_dict['articulos']:
            if 'id_articulo' not in art:
                raise ValueError("Artículo sin id_articulo")

    return True
```

## Migración y Versionado

### Versión Actual: 1.0

Este es el formato inicial. Cambios futuros mantendrán compatibilidad hacia atrás agregando campos opcionales.

### Changelog

- **v1.0** (2024-01-15): Formato inicial con campos básicos y metadata extendida

## Referencias

- Implementación en: `scraper/models.py` (clases `Documento` y `Articulo`)
- Guardado en: `scraper/pipeline.py` (líneas 236-241 para TXT, 292-299 para JSON)
- Extractor de metadata: `scraper/metadata_extractor.py`
- Tests: `tests/test_models.py`, `tests/test_metadata_extractor.py`
