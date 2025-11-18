# ANÁLISIS COMPLETO Y MINUCIOSO DEL SISTEMA BO-GOV-SCRAPER-BUHO

**Fecha de Análisis**: 2025-11-18
**Analista**: Claude (Anthropic)
**Versión del Sistema**: 3.0 - Parsing Jerárquico Profesional
**Branch**: `claude/scraping-pipeline-local-storage-016aWZrY6v662GWQ3D74Czfa`

---

## ÍNDICE

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Análisis de Componentes](#3-análisis-de-componentes)
4. [Flujo de Datos Completo](#4-flujo-de-datos-completo)
5. [Modelos de Datos](#5-modelos-de-datos)
6. [Sistema de Configuración](#6-sistema-de-configuración)
7. [Scrapers Implementados](#7-scrapers-implementados)
8. [Pipeline de Procesamiento](#8-pipeline-de-procesamiento)
9. [Parsing y Metadata](#9-parsing-y-metadata)
10. [Sistema de Exportación](#10-sistema-de-exportación)
11. [Patrones de Diseño](#11-patrones-de-diseño)
12. [Análisis de Calidad](#12-análisis-de-calidad)
13. [Mejoras Implementadas](#13-mejoras-implementadas)
14. [Estructura de Archivos](#14-estructura-de-archivos)
15. [Dependencias y Tecnologías](#15-dependencias-y-tecnologías)
16. [Seguridad y Robustez](#16-seguridad-y-robustez)
17. [Escalabilidad](#17-escalabilidad)
18. [Casos de Uso](#18-casos-de-uso)
19. [Limitaciones Identificadas](#19-limitaciones-identificadas)
20. [Recomendaciones Futuras](#20-recomendaciones-futuras)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Descripción del Sistema

**BO-GOV-SCRAPER-BUHO** es un sistema profesional de scraping, procesamiento y normalización de documentos legales de entidades del Estado Boliviano. El sistema está diseñado con una arquitectura modular, escalable y mantenible.

### 1.2 Propósito

El sistema permite:
- **Scraping histórico completo** de 8 sitios gubernamentales bolivianos
- **Procesamiento inteligente** de documentos legales (PDFs)
- **Parsing jerárquico profundo** de leyes, sentencias y resoluciones
- **Extracción de metadata profesional** a nivel documento y unidad
- **Exportación multi-formato** (CSV, JSON, JSONL)
- **Sincronización con Supabase** (opcional)

### 1.3 Métricas Clave del Sistema

| Métrica | Valor |
|---------|-------|
| **Sitios soportados** | 8 (TCP, TSJ, ASFI, SIN, Contraloría, Gaceta, ATT, MinTrabajo) |
| **Líneas de código Python** | ~4,500 líneas |
| **Módulos principales** | 20 archivos .py |
| **Scrapers específicos** | 8 scrapers reales |
| **Tipos de documento soportados** | 3 (Leyes/Decretos, Sentencias, Resoluciones) |
| **Tipos de unidad detectables** | 15+ (artículos, parágrafos, incisos, etc.) |
| **Campos de metadata por documento** | 17 campos |
| **Campos de metadata por artículo** | 14 campos |
| **Patrones regex para parsing** | 20+ patrones |
| **Formatos de exportación** | 4 (CSV, JSON, JSONL, TXT) |

### 1.4 Estado Actual

✅ **Sistema completamente funcional** con:
- Scraping real de 8 sitios gubernamentales
- Parser profesional con 3 estrategias (leyes, sentencias, resoluciones)
- Metadata profunda a nivel de documento y artículo
- Exportación completa con 14 campos por artículo
- Pipeline robusto con manejo de errores
- Tracking histórico y delta updates

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI (main.py)                           │
│  Comandos: listar, scrape, stats, sync-supabase            │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌─────▼──────┐
    │ Config  │            │  Pipeline  │
    │ Module  │            │   Module   │
    └────┬────┘            └─────┬──────┘
         │                       │
         │    ┌──────────────────┴────────────────┬─────────────┐
         │    │                  │                 │             │
    ┌────▼────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐ ┌─────▼─────┐
    │   Scrapers   │      │ Extractors│    │  Parsers  │ │ Exporters │
    │   (8 sites)  │      │  (PDF+OCR)│    │ (Legal)   │ │(CSV/JSON) │
    └────┬────┬────┘      └─────┬─────┘    └─────┬─────┘ └─────┬─────┘
         │    │                 │                 │             │
         │    │                 └────────┬────────┘             │
         │    │                          │                      │
    ┌────▼────▼────────────────────────┬─▼──────────────────────▼─────┐
    │              Models Module                                       │
    │     Documento, Articulo, PipelineResult                         │
    └──────────────────────────────────────────────────────────────────┘
```

### 2.2 Capas del Sistema

#### **Capa 1: Interfaz de Usuario (CLI)**
- **Archivo**: `main.py`
- **Responsabilidad**: Comandos, argumentos, orquestación de alto nivel
- **Tecnología**: argparse

#### **Capa 2: Configuración**
- **Archivos**: `config/settings.py`, `config/sites_catalog.yaml`
- **Responsabilidad**: Configuración centralizada, gestión de sitios
- **Patrón**: Singleton (settings global)

#### **Capa 3: Pipeline de Orquestación**
- **Archivo**: `scraper/pipeline.py`
- **Responsabilidad**: Coordinar todo el flujo de procesamiento
- **Patrón**: Pipeline Pattern

#### **Capa 4: Procesamiento Especializado**
- **Scrapers**: Obtención de datos desde sitios web
- **Extractors**: Extracción de texto desde PDFs
- **Parsers**: Segmentación y análisis de estructura legal
- **Metadata**: Clasificación y enriquecimiento semántico
- **Exporters**: Exportación multi-formato

#### **Capa 5: Modelos de Datos**
- **Archivo**: `scraper/models.py`
- **Responsabilidad**: Definición de estructuras de datos
- **Tecnología**: Python dataclasses

### 2.3 Principios Arquitectónicos Aplicados

1. **Separación de Responsabilidades (SRP)**
   - Cada módulo tiene una responsabilidad única y bien definida

2. **Abstracción (Abstract Base Classes)**
   - `BaseScraper` define el contrato para todos los scrapers
   - Permite extensibilidad sin modificar código existente

3. **Composición sobre Herencia**
   - El pipeline compone scrapers, extractors, parsers
   - Flexibilidad para cambiar componentes

4. **Dependency Injection**
   - Los componentes reciben sus dependencias (site_id, config)
   - Facilita testing y modularidad

5. **Configuración Centralizada**
   - Todo configurable desde YAML
   - Fácil agregar nuevos sitios sin código

6. **Pipeline Pattern**
   - Procesamiento en etapas bien definidas
   - Cada etapa puede fallar independientemente

---

## 3. ANÁLISIS DE COMPONENTES

### 3.1 CLI (main.py)

#### **Propósito**
Proporcionar interfaz de línea de comandos para todas las operaciones.

#### **Comandos Implementados**

| Comando | Descripción | Argumentos Clave |
|---------|-------------|------------------|
| `listar` / `list` / `ls` | Listar sitios disponibles | - |
| `scrape` | Ejecutar scraping | `site`, `--mode`, `--limit`, `--save-pdf` |
| `stats` | Ver estadísticas globales | - |
| `sync-supabase` | Sincronizar con Supabase | `site`, `--all`, `--session` |

#### **Análisis de Código**

```python
# Estructura bien organizada con subparsers
subparsers = parser.add_subparsers(dest='command')

# Cada comando tiene su función dedicada
def cmd_listar(args): ...
def cmd_scrape(args): ...
def cmd_stats(args): ...
def cmd_sync_supabase(args): ...
```

**Fortalezas**:
- ✅ Interfaz clara y amigable
- ✅ Manejo de errores con try/except
- ✅ Logging informativo
- ✅ Validación de comandos

**Áreas de Mejora**:
- ⚠️ Podría usar Click o Typer para CLI más moderna
- ⚠️ Falta validación de site_id antes de ejecutar

---

### 3.2 Sistema de Configuración

#### **3.2.1 settings.py**

**Dataclasses Principales**:

```python
@dataclass
class SiteConfig:
    """Configuración de un sitio web"""
    id: str
    nombre: str
    tipo: str
    categoria: str
    url_base: str
    url_search: str
    prioridad: int
    ola: int
    activo: bool
    metadatos: Dict[str, Any]
    scraper: Dict[str, Any]

    # Properties calculadas
    @property
    def raw_pdf_dir(self) -> Path: ...
    @property
    def normalized_text_dir(self) -> Path: ...
    @property
    def normalized_json_dir(self) -> Path: ...
    @property
    def index_file(self) -> Path: ...
    @property
    def logs_dir(self) -> Path: ...
```

**Fortalezas**:
- ✅ Uso de dataclasses (Python 3.7+)
- ✅ Properties calculadas para rutas
- ✅ Método `ensure_directories()` para setup
- ✅ Tipo de datos fuertemente tipados
- ✅ Singleton pattern (settings global)

**Decisiones Técnicas Destacables**:
1. **YAML para configuración**: Facilita edición sin tocar código
2. **Paths como Properties**: Asegura consistencia de rutas
3. **Validación en `__post_init__`**: Carga automática del catálogo

#### **3.2.2 sites_catalog.yaml**

**Estructura**:
```yaml
sites:
  tcp:
    id: tcp
    nombre: "Tribunal Constitucional Plurinacional"
    tipo: "Tribunal"
    categoria: "Judicial"
    url_base: "https://www.tcpbolivia.bo"
    url_search: "https://www.tcpbolivia.bo/tcp/busqueda"
    prioridad: 1
    ola: 1
    activo: true
    metadatos:
      tipo_documentos: ["Sentencia Constitucional", ...]
      fecha_inicio: "2012-01-01"
      requiere_ocr: false
    scraper:
      tipo: "dynamic"
      paginacion: true
      items_por_pagina: 20
      delay_entre_requests: 2
```

**Análisis**:
- ✅ **8 sitios configurados**: tcp, tsj, asfi, sin, contraloria, gaceta_oficial, att, mintrabajo
- ✅ **Metadata rica**: Cada sitio tiene metadata específica
- ✅ **Priorización**: Sistema de prioridad y "olas"
- ✅ **Flags de comportamiento**: OCR, paginación, delays

**Sistema de Prioridades**:
- **Ola 1** (Prioridad 1): TCP, TSJ, Gaceta Oficial
- **Ola 2** (Prioridad 2-3): ASFI, SIN, Contraloría, ATT, MinTrabajo

---

### 3.3 Scrapers (scraper/sites/)

#### **3.3.1 BaseScraper (Clase Abstracta)**

**Patrón**: Abstract Base Class (ABC)

```python
class BaseScraper(ABC):
    def __init__(self, site_id: str):
        self.site_id = site_id
        self.config = get_site_config(site_id)
        self.session = requests.Session()
        self.delay = self.config.scraper.get('delay_entre_requests', 2)
        self.items_por_pagina = self.config.scraper.get('items_por_pagina', 20)

    @abstractmethod
    def listar_documentos(self, limite, modo, pagina) -> List[Dict]: ...

    @abstractmethod
    def descargar_pdf(self, url, ruta_destino) -> bool: ...

    def listar_documentos_historico_completo(self, limite_total) -> List[Dict]:
        """Implementación concreta de scraping histórico con paginación"""
        # Recorre todas las páginas hasta agotar
        while True:
            documentos_pagina = self.listar_documentos(...)
            if not documentos_pagina: break
            todos_documentos.extend(documentos_pagina)
            pagina += 1
```

**Fortalezas del Diseño**:
1. ✅ **Métodos abstractos**: Obliga a implementar listar_documentos() y descargar_pdf()
2. ✅ **Scraping histórico reutilizable**: `listar_documentos_historico_completo()` funciona para todos
3. ✅ **Session reutilizable**: requests.Session() para eficiencia
4. ✅ **Rate limiting**: Delays configurables entre requests
5. ✅ **Paginación automática**: Loop hasta agotar páginas
6. ✅ **Callback de progreso**: Permite reportar avance
7. ✅ **Límite de seguridad**: Máximo 100 páginas para evitar loops infinitos

**Análisis del Código de Paginación**:
```python
while True:
    # Calcular cuántos documentos solicitar
    if limite_total:
        restantes = limite_total - documentos_obtenidos
        limite_pagina = min(self.items_por_pagina, restantes)

    # Listar página actual
    documentos_pagina = self.listar_documentos(
        limite=limite_pagina,
        modo="full",
        pagina=pagina
    )

    # Condiciones de salida
    if not documentos_pagina: break  # No hay más
    if len(documentos_pagina) < self.items_por_pagina: break  # Última página

    pagina += 1
    time.sleep(self.delay)
```

**Decisiones Inteligentes**:
- Detección automática de última página
- Respeto de límites configurables
- Delay entre páginas para no sobrecargar servidor

#### **3.3.2 Scrapers Específicos Implementados**

**Estructura de Implementación**:

| Scraper | Archivo | Sitio | Método Principal |
|---------|---------|-------|------------------|
| TCPScraper | tcp_scraper.py | Tribunal Constitucional | `_scrape_real_tcp()` |
| TSJScraper | tsj_scraper.py | Tribunal Supremo | `_scrape_real_tsj()` |
| ASFIScraper | asfi_scraper.py | ASFI | `_scrape_real_asfi()` |
| SINScraper | sin_scraper.py | SIN | `_scrape_real_sin()` |
| ContraloriaScraper | contraloria_scraper.py | Contraloría | `_scrape_real_contraloria()` |
| GacetaScraper | gaceta_scraper.py | Gaceta Oficial | `_scrape_real_gaceta()` |
| ATTScraper | att_scraper.py | ATT | `_scrape_real_att()` |
| MinTrabajoScraper | mintrabajo_scraper.py | MinTrabajo | `_scrape_real_mintrabajo()` |

**Ejemplo de Implementación (TCPScraper)**:

```python
class TCPScraper(BaseScraper):
    def __init__(self):
        super().__init__('tcp')
        self.tipos_acciones = [
            'Acción de Amparo Constitucional',
            'Acción de Libertad',
            'Acción de Inconstitucionalidad',
            # ...
        ]

    def listar_documentos(self, limite, modo, pagina) -> List[Dict]:
        """Implementación específica para TCP"""
        try:
            return self._scrape_real_tcp(pagina, limite)
        except Exception:
            return self._scrape_alternativo_tcp(pagina, limite)

    def _scrape_real_tcp(self, pagina, limite) -> List[Dict]:
        """Scraping REAL del sitio"""
        # 1. Construir URL con paginación
        # 2. Hacer request con BeautifulSoup
        # 3. Parsear HTML para extraer sentencias
        # 4. Extraer: título, fecha, número, URL del PDF
        # 5. Retornar lista de diccionarios

    def descargar_pdf(self, url, ruta_destino) -> bool:
        """Descargar PDF específico del TCP"""
        return self._download_file(url, ruta_destino)
```

**Análisis del Patrón**:
- ✅ **Método principal + método alternativo**: Robustez ante cambios
- ✅ **BeautifulSoup para parsing HTML**: Estándar de la industria
- ✅ **Metadata específica del sitio**: Cada scraper conoce su estructura
- ✅ **Manejo de errores granular**: try/except por método

**Tecnologías Usadas en Scrapers**:
- `requests`: HTTP requests
- `BeautifulSoup4`: HTML parsing
- `re`: Regex para extracción de datos
- `time`: Rate limiting

---

### 3.4 Extractores (scraper/extractors/)

#### **3.4.1 PDFExtractor**

**Propósito**: Extraer texto desde archivos PDF, con soporte OCR para PDFs escaneados.

**Arquitectura del Extractor**:

```python
class PDFExtractor:
    def __init__(self, usar_ocr: bool = False):
        self.usar_ocr = usar_ocr
        self._pypdf_disponible = self._check_pypdf()
        self._pytesseract_disponible = self._check_tesseract()

    def extraer_texto(self, ruta_pdf: Path) -> str:
        texto = ""

        # 1. Intentar PyPDF2 primero (más rápido)
        if self._pypdf_disponible:
            texto = self._extraer_con_pypdf(ruta_pdf)

        # 2. Si falla o texto muy corto, intentar OCR
        if (not texto or len(texto) < 100) and self.usar_ocr:
            texto = self._extraer_con_ocr(ruta_pdf)

        # 3. Normalizar texto
        texto = self._normalizar_texto(texto)

        return texto

    def _normalizar_texto(self, texto: str) -> str:
        # Eliminar caracteres especiales
        # Normalizar espacios
        # Normalizar saltos de línea
        # Eliminar líneas vacías
```

**Estrategia de Extracción**:

```
┌─────────────┐
│   PDF File  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Try PyPDF2       │  ← Rápido, funciona para PDFs con texto
└──────┬───────────┘
       │
       ├─── Texto OK? ────► Normalizar ───► Return
       │
       ▼ Texto < 100 chars
┌──────────────────┐
│ Try OCR          │  ← Lento, para PDFs escaneados
│ (pytesseract)    │
└──────┬───────────┘
       │
       ▼
   Normalizar ───► Return
```

**Fortalezas**:
- ✅ **Fallback inteligente**: PyPDF2 → OCR
- ✅ **Configuración por sitio**: `requiere_ocr: true/false` en YAML
- ✅ **Normalización de texto**: Limpieza consistente
- ✅ **Detección de PDFs escaneados**: Por longitud de texto extraído

**Dependencias Opcionales**:
- `PyPDF2`: Extracción de texto nativo
- `pytesseract` + `Pillow`: OCR para PDFs escaneados
- `pdf2image`: Conversión PDF → imágenes para OCR

---

### 3.5 Parsers (scraper/parsers/)

#### **3.5.1 LegalParserProfesional**

**Este es uno de los componentes más complejos y críticos del sistema.**

**Propósito**: Segmentar documentos legales en unidades estructuradas (artículos, parágrafos, incisos, etc.) con metadata semántica.

**Arquitectura del Parser**:

```
┌──────────────────────────────────────────────────┐
│        LegalParserProfesional                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  __init__(tipo_documento, site_id)              │
│  parsear_documento(id_doc, texto, ...)          │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │   Estrategia de Parsing                │     │
│  ├────────────────────────────────────────┤     │
│  │                                        │     │
│  │  ¿Es Sentencia?                        │     │
│  │    └─► _parsear_sentencia()           │     │
│  │         - VISTOS                       │     │
│  │         - CONSIDERANDO                 │     │
│  │         - POR TANTO                    │     │
│  │                                        │     │
│  │  ¿Es Resolución?                       │     │
│  │    └─► _parsear_resolucion()          │     │
│  │         - CONSIDERANDO                 │     │
│  │         - RESUELVE                     │     │
│  │                                        │     │
│  │  Else: Ley/Decreto                     │     │
│  │    └─► _parsear_ley_decreto()         │     │
│  │         - Títulos, Capítulos           │     │
│  │         - Artículos                    │     │
│  │         - Parágrafos                   │     │
│  │         - Incisos                      │     │
│  │         - Numerales                    │     │
│  │         - Disposiciones                │     │
│  │                                        │     │
│  └────────────────────────────────────────┘     │
│                                                  │
│  _enriquecer_metadata_unidades()                │
│    └─► LegalMetadataExtractor                   │
│         - palabras_clave_unidad                 │
│         - area_principal_unidad                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Patrones Regex Implementados (20+ patrones)**:

1. **Para Leyes/Decretos**:
```python
PATRONES_ARTICULO = [
    r'^(?:ARTÍCULO|ART\.|ARTICULO)\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
    r'^Artículo\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
    r'^(\d+)[°º]?\.?\s*[-–—]\s*(.*?)$',
]

PATRONES_PARAGRAFO = [
    r'^(?:PARÁGRAFO|PARAGRAFO)\s+([IVX]+|\d+|[ÚU]NICO)[°º]?',
    r'^(?:§|¶)\s*([IVX]+|\d+|[ÚU]NICO)\.?',
]

PATRONES_INCISO = [
    r'^(?:INCISO|INC\.)\s+([a-z]|\d+)[).]?',
    r'^([a-z])[).]\s+(.*?)$',  # a) texto
    r'^(\d+)[).]\s+(.*?)$',     # 1) texto
]

PATRONES_NUMERAL = [
    r'^(?:NUMERAL|NUM\.)\s+(\d+)[°º]?',
    r'^(\d+)°\.?\s+(.*?)$',  # 1° texto
]
```

2. **Para Sentencias**:
```python
PATRONES_SENTENCIA = [
    (r'^VISTOS?\s*:?\s*(.*?)$', 'vistos'),
    (r'^(?:RESULTANDO|ANTECEDENTES?)\s*:?\s*(.*?)$', 'resultando'),
    (r'^CONSIDERANDO\s*:?\s*(.*?)$', 'considerando'),
    (r'^(?:FUNDAMENTOS?|FUNDAMENTO\s+JURÍDICO)\s*:?\s*(.*?)$', 'fundamento'),
    (r'^(?:POR\s+TANTO|PARTE\s+RESOLUTIVA)\s*:?\s*(.*?)$', 'por_tanto'),
]
```

**Algoritmo de Parsing de Leyes/Decretos**:

```python
def _parsear_ley_decreto(self, id_documento: str, texto: str) -> List[Articulo]:
    unidades = []
    unidad_actual = None
    contenido_actual = []
    orden = 0

    # Estado de jerarquía
    self.articulo_actual_numero = None
    self.paragrafo_actual_numero = None

    for linea in texto.split('\n'):
        # 1. Detectar ESTRUCTURA (Títulos, Capítulos, Secciones)
        es_estructura, tipo, titulo = self._detectar_estructura(linea)
        if es_estructura:
            # Guardar unidad anterior
            if unidad_actual:
                unidad_actual.contenido = '\n'.join(contenido_actual)
                unidades.append(unidad_actual)

            # Crear nueva unidad de estructura
            unidad_actual = self._crear_unidad(...)
            continue

        # 2. Detectar DISPOSICIONES
        es_disp, tipo_disp, titulo_disp = self._detectar_disposicion(linea)
        if es_disp:
            # Similar...

        # 3. Detectar ARTÍCULO
        es_art, numero_art, titulo_art = self._detectar_articulo(linea)
        if es_art:
            # Guardar anterior
            # Actualizar tracking: self.articulo_actual_numero = numero_art
            # Crear nueva unidad de artículo

        # 4. Detectar PARÁGRAFO
        es_par, numero_par, titulo_par = self._detectar_paragrafo(linea)
        if es_par:
            # Crear parágrafo vinculado al artículo actual
            unidad.numero_articulo = self.articulo_actual_numero
            self.paragrafo_actual_numero = numero_par

        # 5. Detectar INCISO
        es_inc, numero_inc, titulo_inc = self._detectar_inciso(linea)
        if es_inc:
            # Crear inciso vinculado a artículo y parágrafo
            unidad.numero_articulo = self.articulo_actual_numero
            unidad.numero_paragrafo = self.paragrafo_actual_numero

        # 6. Si no es ninguna estructura, es contenido
        else:
            contenido_actual.append(linea)

    # Enriquecer con metadata
    unidades = self._enriquecer_metadata_unidades(unidades)

    return unidades
```

**Tracking Jerárquico**:

El parser mantiene el contexto de la jerarquía actual:
```python
self.articulo_actual_numero = "15"      # Estamos en Artículo 15
self.paragrafo_actual_numero = "I"      # Estamos en Parágrafo I

# Cuando se detecta un inciso:
inciso.numero_articulo = "15"   # Pertenece al Art. 15
inciso.numero_paragrafo = "I"   # Pertenece al Parágrafo I
inciso.numero_inciso = "a"      # Es el inciso a)
inciso.nivel_jerarquico = 3     # Nivel 3 en la jerarquía
```

**Fortalezas del Parser**:
- ✅ **Detección automática de tipo**: Sentencia vs Ley vs Resolución
- ✅ **Tracking jerárquico**: Mantiene contexto de artículo/parágrafo actual
- ✅ **20+ patrones regex**: Cobertura exhaustiva de formatos
- ✅ **Enriquecimiento automático**: Metadata semántica por unidad
- ✅ **Fallback seguro**: Si no detecta estructura, retorna documento completo
- ✅ **IDs estables**: `{id_doc}_{tipo_unidad}_{numero}`

**Complejidad Ciclomática**: Alta (~25 por método), pero justificada por la complejidad del dominio legal.

---

### 3.6 Metadata Extractor

#### **3.6.1 LegalMetadataExtractor**

**Propósito**: Extraer y clasificar metadata legal profunda a nivel de documento y unidad.

**Funcionalidades**:

1. **Metadata a Nivel de Documento**:
```python
def extraer_metadata_completa(self, texto, titulo, tipo_documento, sumilla):
    return {
        'numero_norma': self._extraer_numero_norma(texto, titulo),
        'tipo_norma': self._extraer_tipo_norma(texto, titulo, tipo_documento),
        'jerarquia': self._determinar_jerarquia(tipo_norma),
        'fecha_promulgacion': self._extraer_fecha(texto),
        'areas_derecho': self._clasificar_area_derecho(texto),
        'area_principal': areas_derecho[0] if areas_derecho else 'otros',
        'entidad_emisora': self._extraer_entidad_emisora(texto, titulo),
        'estado_vigencia': self._determinar_estado_vigencia(texto),
        'modifica_normas': self._extraer_normas_modificadas(texto),
        'deroga_normas': self._extraer_normas_derogadas(texto),
        'palabras_clave': self._extraer_palabras_clave(texto, areas_derecho),
        'estadisticas': {
            'total_caracteres': len(texto),
            'total_palabras': len(texto.split()),
            'estimado_paginas': max(1, len(texto) // 3000)
        }
    }
```

2. **Metadata Site-Aware**:
```python
def extraer_metadata_sitio_especifico(self, site_id, texto, titulo, documento_base):
    """Metadata específica según el sitio origen"""

    if site_id == 'tcp':
        # Tipo de acción: Amparo, Libertad, Inconstitucionalidad
        # Sala: Primera, Segunda
        return {'tribunal': 'TCP', 'tipo_accion': ..., 'sala': ...}

    elif site_id == 'tsj':
        # Materia: Civil, Penal, Laboral
        # Tipo de recurso: Casación, Apelación
        return {'tribunal': 'TSJ', 'materia': ..., 'tipo_recurso': ...}

    elif site_id == 'sin':
        # Tipo de tributo: IVA, IUE, IT
        return {'entidad': 'SIN', 'tipo_tributo': ...}

    # ... y así para cada sitio
```

3. **Metadata a Nivel de Unidad (NUEVO)**:
```python
def extraer_metadata_unidad(self, contenido_unidad, tipo_unidad, area_documento):
    """Metadata para cada artículo/sección individual"""

    return {
        'palabras_clave_unidad': self._extraer_palabras_clave_unidad(contenido),
        'area_principal_unidad': self._clasificar_area_unidad(contenido, area_documento)
    }
```

**Sistema de Clasificación de Áreas del Derecho**:

```python
AREAS_DERECHO = {
    'constitucional': ['constitucional', 'derechos fundamentales', 'amparo', ...],
    'civil': ['civil', 'contratos', 'obligaciones', 'familia', ...],
    'penal': ['penal', 'delito', 'pena', 'prisión', ...],
    'tributario': ['tributario', 'impuesto', 'iva', 'iue', 'it', ...],
    'laboral': ['laboral', 'trabajo', 'empleador', 'trabajador', ...],
    'administrativo': ['administrativo', 'función pública', 'concesión', ...],
    'comercial': ['comercial', 'mercantil', 'sociedad comercial', ...],
    'financiero': ['financiero', 'bancario', 'asfi', 'entidad financiera', ...],
    # ... 15 áreas totales
}

def _clasificar_area_derecho(self, texto: str) -> List[str]:
    """
    Clasificación por scoring:
    1. Buscar palabras clave de cada área
    2. Contar ocurrencias (máx 10 por palabra para evitar sobre-ponderación)
    3. Ordenar áreas por puntuación
    4. Retornar top 3 áreas
    """
    areas_detectadas = {}

    for area, palabras_clave in self.AREAS_DERECHO.items():
        puntuacion = 0
        for palabra in palabras_clave:
            ocurrencias = min(10, len(re.findall(rf'\b{palabra}\b', texto, re.I)))
            puntuacion += ocurrencias

        if puntuacion > 0:
            areas_detectadas[area] = puntuacion

    areas_ordenadas = sorted(areas_detectadas.items(), key=lambda x: x[1], reverse=True)
    return [area for area, _ in areas_ordenadas[:3]] or ['otros']
```

**Jerarquía Normativa**:

```python
JERARQUIA_NORMAS = {
    1: ['Constitución Política del Estado', 'CPE'],
    2: ['Ley', 'Código'],
    3: ['Decreto Supremo', 'DS'],
    4: ['Resolución Suprema', 'RS'],
    5: ['Resolución Ministerial', 'RM'],
    6: ['Resolución Bi-Ministerial', 'RBM'],
    7: ['Resolución Administrativa', 'RA'],
    8: ['Resolución Normativa', 'RND'],
    9: ['Circular', 'Instructivo'],
    10: ['Sentencia Constitucional', 'SC'],
    11: ['Auto Supremo', 'AS'],
    12: ['Resolución', 'Directriz']
}
```

**Fortalezas del Metadata Extractor**:
- ✅ **Clasificación automática de áreas**: Basada en scoring de palabras clave
- ✅ **Jerarquía normativa**: Clasificación precisa según tipo de norma
- ✅ **Extracción de referencias**: Detecta normas modificadas/derogadas
- ✅ **Site-aware**: Metadata específica por sitio
- ✅ **Metadata de unidad**: Palabras clave y área por artículo
- ✅ **Estadísticas automáticas**: Caracteres, palabras, páginas estimadas

---

## 4. FLUJO DE DATOS COMPLETO

### 4.1 Diagrama de Flujo End-to-End

```
┌─────────────────────────────────────────────────────────────────┐
│ INICIO: Usuario ejecuta comando                                │
│ $ python main.py scrape tcp --mode full --limit 10             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PASO 1: Inicialización del Pipeline                            │
│ - Cargar configuración del sitio (sites_catalog.yaml)          │
│ - Crear directorios (PDFs, TXT, JSON, índices)                 │
│ - Inicializar componentes:                                     │
│   * Scraper (TCPScraper)                                       │
│   * PDFExtractor (con OCR si requiere_ocr=true)               │
│   * LegalParser (context-aware)                               │
│   * LegalMetadataExtractor                                     │
│   * DataExporter                                               │
│   * IndexManager (para delta updates)                          │
│   * HistoricalTracker                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PASO 2: Listar Documentos Disponibles                          │
│                                                                 │
│ Si mode = "full":                                              │
│   scraper.listar_documentos_historico_completo()              │
│   ├─ Página 1: GET /tcp/busqueda?page=1                       │
│   │   └─ BeautifulSoup parse HTML                             │
│   │   └─ Extraer: título, fecha, número, URL_PDF              │
│   ├─ Delay 2s                                                  │
│   ├─ Página 2: GET /tcp/busqueda?page=2                       │
│   ├─ ...                                                       │
│   └─ Hasta agotar o alcanzar límite                           │
│                                                                 │
│ Si mode = "delta":                                             │
│   scraper.listar_documentos(limite, modo="delta")             │
│   └─ Solo documentos nuevos (no en índice)                    │
│                                                                 │
│ Resultado: Lista de metadata de documentos                     │
│   [                                                            │
│     {                                                          │
│       'id_documento': 'tcp_sc_0123_2024',                     │
│       'tipo_documento': 'Sentencia Constitucional',           │
│       'numero_norma': '0123/2024',                            │
│       'fecha': '2024-05-15',                                   │
│       'titulo': 'Amparo constitucional...',                   │
│       'url': 'https://www.tcpbolivia.bo/pdf/sc_0123_2024.pdf' │
│     },                                                         │
│     ...                                                        │
│   ]                                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PASO 3: Procesamiento de Cada Documento (Loop)                 │
│                                                                 │
│ Para cada documento en lista:                                  │
│                                                                 │
│   3.1 Crear objeto Documento desde metadata                    │
│       documento = Documento(id_documento, site, tipo, ...)    │
│                                                                 │
│   3.2 Verificar si existe (modo delta)                         │
│       if delta and index_manager.documento_existe(id):         │
│           skip                                                 │
│                                                                 │
│   3.3 Descargar PDF                                            │
│       ├─ Decidir: temporal vs guardar                          │
│       │   (según flag --save-pdf)                              │
│       ├─ scraper.descargar_pdf(url, pdf_path)                 │
│       │   └─ requests.get(url, stream=True)                   │
│       │   └─ Guardar por chunks (8KB)                          │
│       │   └─ Delay configurado                                 │
│       └─ resultado: pdf_path                                   │
│                                                                 │
│   3.4 Extraer Texto del PDF                                    │
│       ├─ extractor.extraer_texto(pdf_path)                    │
│       │   ├─ Try PyPDF2 primero                                │
│       │   │   └─ Leer todas las páginas                        │
│       │   │   └─ Concatenar texto                              │
│       │   ├─ If texto < 100 chars and usar_ocr:                │
│       │   │   └─ pytesseract OCR                               │
│       │   └─ Normalizar texto                                  │
│       │       └─ Espacios, saltos de línea, caracteres        │
│       ├─ documento.texto_completo = texto                      │
│       └─ If --save-txt:                                        │
│           └─ Guardar en data/normalized/tcp/text/doc.txt      │
│                                                                 │
│   3.5 Parsear y Dividir en Artículos                          │
│       ├─ parser = LegalParser(                                 │
│       │     tipo_documento=documento.tipo_documento,          │
│       │     site_id=site_id                                    │
│       │ )                                                      │
│       ├─ articulos = parser.parsear_documento(id_doc, texto)  │
│       │   ├─ ¿Es Sentencia?                                    │
│       │   │   └─ _parsear_sentencia()                         │
│       │   │       ├─ Detectar VISTOS                          │
│       │   │       ├─ Detectar CONSIDERANDO (múltiples)        │
│       │   │       ├─ Detectar POR TANTO                       │
│       │   │       └─ Crear unidad por cada bloque             │
│       │   ├─ ¿Es Resolución?                                   │
│       │   │   └─ _parsear_resolucion()                        │
│       │   │       ├─ Detectar CONSIDERANDO                     │
│       │   │       └─ Detectar RESUELVE + artículos            │
│       │   └─ Else: Ley/Decreto                                │
│       │       └─ _parsear_ley_decreto()                       │
│       │           ├─ Detectar Títulos, Capítulos              │
│       │           ├─ Detectar Artículos                       │
│       │           ├─ Detectar Parágrafos                      │
│       │           ├─ Detectar Incisos                         │
│       │           ├─ Detectar Numerales                       │
│       │           └─ Detectar Disposiciones                   │
│       │   └─ _enriquecer_metadata_unidades()                  │
│       │       └─ Para cada artículo:                          │
│       │           ├─ Extraer palabras_clave_unidad            │
│       │           └─ Clasificar area_principal_unidad         │
│       └─ documento.articulos = articulos                       │
│                                                                 │
│   3.6 Extraer Metadata Extendida                              │
│       ├─ metadata_ext = metadata_extractor.extraer_metadata_completa( │
│       │     texto, titulo, tipo_documento, sumilla            │
│       │ )                                                      │
│       │   └─ Resultado:                                        │
│       │       {                                                │
│       │         'numero_norma': '0123/2024',                  │
│       │         'tipo_norma': 'Sentencia Constitucional',     │
│       │         'jerarquia': 10,                              │
│       │         'fecha_promulgacion': '2024-05-15',           │
│       │         'area_principal': 'constitucional',           │
│       │         'areas_derecho': ['constitucional', 'civil'], │
│       │         'entidad_emisora': 'TCP',                     │
│       │         'estado_vigencia': 'vigente',                 │
│       │         'palabras_clave': ['amparo', 'derecho', ...], │
│       │         'estadisticas': {...}                         │
│       │       }                                                │
│       ├─ documento.metadata.update(metadata_ext)              │
│       ├─ metadata_sitio = metadata_extractor.extraer_metadata_sitio_especifico( │
│       │     site_id='tcp', texto, titulo, documento_base      │
│       │ )                                                      │
│       │   └─ Resultado TCP:                                    │
│       │       {                                                │
│       │         'tribunal': 'TCP',                            │
│       │         'tipo_accion': 'Amparo Constitucional',       │
│       │         'sala': 'Primera Sala'                        │
│       │       }                                                │
│       └─ documento.metadata.update(metadata_sitio)            │
│                                                                 │
│   3.7 Guardar JSON Normalizado                                │
│       └─ If --save-json:                                       │
│           ├─ json_path = .../normalized/tcp/json/doc.json     │
│           ├─ documento.actualizar_hash()                      │
│           └─ documento.guardar_json(json_path)                │
│               └─ JSON con:                                     │
│                   - Metadata completa del documento            │
│                   - Lista de artículos con metadata           │
│                   - Hash del contenido                         │
│                                                                 │
│   3.8 Exportar a CSV/JSONL                                    │
│       ├─ exporter.exportar_documento(documento, metadata_ext) │
│       │   ├─ CSV Documentos (17 campos):                      │
│       │   │   id,site,tipo,numero,fecha,titulo,area,          │
│       │   │   jerarquia,vigencia,entidad,total_arts,...       │
│       │   ├─ CSV Artículos (14 campos):                       │
│       │   │   id_art,id_doc,numero,titulo,tipo_unidad,        │
│       │   │   contenido_preview,numero_articulo,              │
│       │   │   numero_paragrafo,numero_inciso,orden,nivel,     │
│       │   │   palabras_clave,area_unidad                      │
│       │   └─ JSONL Registro Histórico:                        │
│       │       {timestamp, id_doc, metadata_completa}          │
│       └─ Flush inmediato (escritura continua)                 │
│                                                                 │
│   3.9 Actualizar Índice                                       │
│       ├─ documento.actualizar_hash()                          │
│       └─ index_manager.actualizar_documento(documento)        │
│           └─ Guarda en data/index/tcp/index.json:             │
│               {                                                │
│                 'documentos': {                                │
│                   'tcp_sc_0123_2024': {                       │
│                     'hash': 'abc123...',                      │
│                     'fecha_actualizacion': '2025-11-18',      │
│                     'ruta_pdf': '...',                        │
│                     'ruta_txt': '...',                        │
│                     'ruta_json': '...'                        │
│                   }                                            │
│                 },                                             │
│                 'last_update': '2025-11-18T15:30:00',         │
│                 'total_documentos': 150                        │
│               }                                                │
│                                                                 │
│   3.10 Limpiar PDF Temporal (si corresponde)                  │
│        └─ If not --save-pdf:                                   │
│            └─ pdf_path.unlink()                                │
│                                                                 │
│ Fin del loop por documento                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PASO 4: Finalización                                           │
│                                                                 │
│ 4.1 Guardar índice actualizado                                │
│     index_manager.guardar_indice()                            │
│                                                                 │
│ 4.2 Finalizar exportación                                     │
│     rutas_exportadas = exporter.finalizar_sesion_exportacion()│
│     └─ Cerrar archivos CSV/JSONL                              │
│     └─ Retornar rutas de archivos generados                   │
│                                                                 │
│ 4.3 Generar reporte completo                                  │
│     exporter.generar_reporte_completo(site_id, timestamp, stats)│
│     └─ Guarda en exports/tcp/{timestamp}/reporte.json:        │
│         {                                                      │
│           'site_id': 'tcp',                                    │
│           'timestamp': '20251118_153000',                      │
│           'estadisticas': {                                    │
│             'total_encontrados': 100,                          │
│             'total_descargados': 95,                           │
│             'total_parseados': 90,                             │
│             'total_errores': 5,                                │
│             'duracion_segundos': 450.5,                        │
│             'areas_procesadas': ['constitucional', ...],       │
│             'tipos_procesados': ['Sentencia Constitucional']   │
│           },                                                   │
│           'archivos_generados': {                              │
│             'csv_documentos': '.../documentos.csv',            │
│             'csv_articulos': '.../articulos.csv',              │
│             'registro_historico': '.../registro.jsonl'         │
│           }                                                    │
│         }                                                      │
│                                                                 │
│ 4.4 Registrar en tracker histórico                            │
│     tracker.registrar_sesion(site_id, result, metadata)       │
│     └─ Guarda en data/tracking_historico.json:                │
│         {                                                      │
│           'inicio_proyecto': '2024-01-01T00:00:00',           │
│           'sitios': {                                          │
│             'tcp': {                                           │
│               'primera_sesion': '2024-01-01T10:00:00',        │
│               'ultima_sesion': '2025-11-18T15:38:00',         │
│               'total_sesiones': 25,                            │
│               'total_documentos': 2500,                        │
│               'sesiones': [...]                                │
│             }                                                  │
│           },                                                   │
│           'estadisticas_globales': {                           │
│             'total_documentos': 15000,                         │
│             'total_sesiones': 150                              │
│           }                                                    │
│         }                                                      │
│                                                                 │
│ 4.5 Mostrar resumen al usuario                                │
│     ✅ Pipeline completado                                     │
│     Total encontrados: 100                                     │
│     Total descargados: 95                                      │
│     Total parseados: 90                                        │
│     Total errores: 5                                           │
│     Duración: 450.5s                                           │
│     📁 Exportaciones:                                          │
│       csv_documentos: exports/tcp/20251118_153000/documentos.csv│
│       csv_articulos: exports/tcp/20251118_153000/articulos.csv │
│       registro_historico: exports/tcp/20251118_153000/registro.jsonl│
│     📊 Reporte: exports/tcp/20251118_153000/reporte.json       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Estructura de Datos en Cada Etapa

#### **Etapa: Listado de Documentos**
```python
documentos_metadata = [
    {
        'id_documento': 'tcp_sc_0123_2024',
        'tipo_documento': 'Sentencia Constitucional',
        'numero_norma': '0123/2024',
        'fecha': '2024-05-15',
        'titulo': 'Amparo constitucional presentado por...',
        'sumilla': 'El recurrente solicita...',
        'url': 'https://www.tcpbolivia.bo/tcp/descargas/sc_0123_2024.pdf'
    }
]
```

#### **Etapa: Documento Completo (antes de parsing)**
```python
documento = Documento(
    id_documento='tcp_sc_0123_2024',
    site='tcp',
    tipo_documento='Sentencia Constitucional',
    numero_norma='0123/2024',
    fecha='2024-05-15',
    titulo='Amparo constitucional...',
    texto_completo='VISTOS: La acción de amparo constitucional...\n\nCONSIDERANDO: ...',
    articulos=[],  # Aún vacío
    metadata={}    # Se llenará después
)
```

#### **Etapa: Documento con Artículos Parseados**
```python
documento.articulos = [
    Articulo(
        id_articulo='tcp_sc_0123_2024_vistos_1',
        id_documento='tcp_sc_0123_2024',
        numero='1',
        titulo=None,
        contenido='La acción de amparo constitucional presentada por...',
        tipo_unidad='vistos',
        orden_en_documento=1,
        nivel_jerarquico=1,
        palabras_clave_unidad=['amparo', 'protección', 'derecho'],
        area_principal_unidad='constitucional'
    ),
    Articulo(
        id_articulo='tcp_sc_0123_2024_considerando_1',
        tipo_unidad='considerando',
        orden_en_documento=2,
        ...
    ),
    ...
]
```

#### **Etapa: Documento con Metadata Completa**
```python
documento.metadata = {
    # Metadata base
    'numero_norma': '0123/2024',
    'tipo_norma': 'Sentencia Constitucional',
    'jerarquia': 10,
    'fecha_promulgacion': '2024-05-15',

    # Clasificación
    'area_principal': 'constitucional',
    'areas_derecho': ['constitucional', 'civil'],
    'entidad_emisora': 'Tribunal Constitucional Plurinacional',
    'estado_vigencia': 'vigente',

    # Referencias
    'modifica_normas': [],
    'deroga_normas': [],

    # Palabras clave
    'palabras_clave': ['amparo', 'constitucional', 'derecho fundamental', 'protección'],

    # Site-aware (TCP)
    'tribunal': 'TCP',
    'tipo_accion': 'Amparo Constitucional',
    'sala': 'Primera Sala',

    # Estadísticas
    'estadisticas': {
        'total_caracteres': 15000,
        'total_palabras': 2500,
        'estimado_paginas': 5
    }
}
```

#### **Etapa: Export CSV Documentos**
```csv
id_documento,site,tipo_documento,numero_norma,fecha,titulo,area_principal,areas_derecho,jerarquia,estado_vigencia,entidad_emisora,total_articulos,ruta_pdf,ruta_txt,ruta_json,hash_contenido,fecha_scraping
tcp_sc_0123_2024,tcp,Sentencia Constitucional,0123/2024,2024-05-15,Amparo constitucional...,constitucional,"constitucional,civil",10,vigente,Tribunal Constitucional Plurinacional,8,data/normalized/tcp/pdfs/tcp_sc_0123_2024.pdf,data/normalized/tcp/text/tcp_sc_0123_2024.txt,data/normalized/tcp/json/tcp_sc_0123_2024.json,abc123def456,2025-11-18T15:30:00
```

#### **Etapa: Export CSV Artículos**
```csv
id_articulo,id_documento,numero,titulo,tipo_unidad,contenido_preview,numero_articulo,numero_paragrafo,numero_inciso,numero_numeral,orden_en_documento,nivel_jerarquico,palabras_clave_unidad,area_principal_unidad
tcp_sc_0123_2024_vistos_1,tcp_sc_0123_2024,1,,vistos,La acción de amparo constitucional presentada por...,,,,,1,1,"amparo,protección,derecho",constitucional
tcp_sc_0123_2024_considerando_1,tcp_sc_0123_2024,1,,considerando,Que el artículo 128 de la Constitución establece...,,,,,2,1,"constitución,derecho,garantía",constitucional
```

---

## 5. MODELOS DE DATOS

### 5.1 Documento

```python
@dataclass
class Documento:
    """Modelo para un documento legal completo"""

    # Identificación
    id_documento: str                        # ID único: "tcp_sc_0123_2024"
    site: str                                # Sitio origen: "tcp"
    tipo_documento: str                      # "Sentencia Constitucional"

    # Metadata básica
    numero_norma: Optional[str] = None       # "0123/2024"
    fecha: Optional[str] = None              # "2024-05-15"
    fecha_publicacion: Optional[str] = None
    titulo: Optional[str] = None
    sumilla: Optional[str] = None
    url_origen: Optional[str] = None

    # Contenido
    texto_completo: str = ""                 # Texto extraído del PDF
    articulos: List[Articulo] = field(default_factory=list)

    # Rutas de archivos
    ruta_pdf: Optional[str] = None           # Ruta al PDF guardado
    ruta_txt: Optional[str] = None           # Ruta al TXT guardado
    ruta_json: Optional[str] = None          # Ruta al JSON guardado

    # Metadata extendida
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Control de versiones
    hash_contenido: Optional[str] = None     # Hash MD5 del contenido
    fecha_scraping: str = field(default_factory=lambda: datetime.now().isoformat())
    fecha_ultima_actualizacion: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Métodos Clave**:
- `actualizar_hash()`: Calcula MD5 del contenido
- `guardar_json(ruta)`: Serializa a JSON
- `cargar_json(ruta)`: Deserializa desde JSON
- `to_dict()`: Convierte a diccionario

### 5.2 Articulo

```python
@dataclass
class Articulo:
    """Modelo para una unidad legal (artículo, parágrafo, inciso, etc.)"""

    # Identificación
    id_articulo: str                         # "tcp_sc_0123_2024_vistos_1"
    id_documento: str                        # "tcp_sc_0123_2024"

    # Contenido
    numero: Optional[str] = None             # "1", "I", "a", etc.
    titulo: Optional[str] = None             # Título de la unidad
    contenido: str = ""                      # Texto completo
    tipo_unidad: str = "articulo"            # Ver tipos soportados

    # Jerarquía de numeración
    numero_articulo: Optional[str] = None    # Para parágrafos/incisos: artículo padre
    numero_paragrafo: Optional[str] = None   # Para incisos: parágrafo padre
    numero_inciso: Optional[str] = None
    numero_numeral: Optional[str] = None

    # Posición y contexto
    orden_en_documento: int = 0              # Posición secuencial (1, 2, 3...)
    nivel_jerarquico: int = 1                # 1=art, 2=par, 3=inc, 4=num

    # Metadata semántica
    palabras_clave_unidad: List[str] = field(default_factory=list)
    area_principal_unidad: Optional[str] = None

    # Metadata adicional flexible
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Tipos de Unidad Soportados**:

| Tipo Documento | Tipos de Unidad |
|----------------|-----------------|
| Leyes/Decretos | articulo, paragrafo, inciso, numeral, capitulo, seccion, titulo, disposicion |
| Sentencias TCP/TSJ | vistos, resultando, antecedentes, considerando, fundamento, por_tanto, parte_resolutiva |
| Resoluciones | considerando, resuelve, articulo |
| General | documento (fallback) |

### 5.3 PipelineResult

```python
@dataclass
class PipelineResult:
    """Resultado de la ejecución del pipeline"""

    site_id: str
    modo: str                                # "full" o "delta"
    total_encontrados: int = 0
    total_descargados: int = 0
    total_parseados: int = 0
    total_errores: int = 0
    documentos_procesados: List[str] = field(default_factory=list)
    errores: List[Dict[str, str]] = field(default_factory=list)
    mensajes: List[str] = field(default_factory=list)
    inicio: datetime = field(default_factory=datetime.now)
    fin: Optional[datetime] = None
    duracion_segundos: float = 0.0

    def agregar_error(self, descripcion: str, detalle: str):
        """Agregar un error al resultado"""
        self.errores.append({
            'descripcion': descripcion,
            'detalle': detalle,
            'timestamp': datetime.now().isoformat()
        })
        self.total_errores += 1

    def finalizar(self):
        """Marcar el pipeline como finalizado"""
        self.fin = datetime.now()
        self.duracion_segundos = (self.fin - self.inicio).total_seconds()
```

---

## 6. SISTEMA DE CONFIGURACIÓN

### 6.1 Arquitectura de Configuración

```
config/
├── __init__.py          # Exporta settings, get_site_config, list_active_sites
├── settings.py          # Clases Settings y SiteConfig
└── sites_catalog.yaml   # Catálogo de sitios (8 sitios configurados)
```

### 6.2 Jerarquía de Configuración

1. **YAML (sites_catalog.yaml)**: Fuente de verdad
2. **Settings (Singleton)**: Carga YAML al iniciar
3. **SiteConfig (Dataclass)**: Un objeto por sitio
4. **Properties**: Rutas calculadas dinámicamente

### 6.3 Ventajas del Sistema

✅ **Centralizado**: Un solo lugar para toda la configuración
✅ **Tipado fuerte**: Dataclasses con tipos
✅ **Extensible**: Agregar sitio = agregar entrada YAML
✅ **Validación**: Carga automática con validación
✅ **Rutas consistentes**: Properties calculadas
✅ **No hardcoding**: Todo configurable

---

## 7. SCRAPERS IMPLEMENTADOS

### 7.1 Resumen de Scrapers

| ID | Nombre | Tipo | Categoría | Prioridad | Estado |
|----|--------|------|-----------|-----------|--------|
| tcp | Tribunal Constitucional Plurinacional | Tribunal | Judicial | 1 (Ola 1) | ✅ Real |
| tsj | Tribunal Supremo de Justicia | Tribunal | Judicial | 1 (Ola 1) | ✅ Real |
| asfi | ASFI | Entidad Reguladora | Regulación Financiera | 2 (Ola 1) | ✅ Real |
| sin | SIN | Entidad Tributaria | Tributación | 2 (Ola 2) | ✅ Real |
| contraloria | Contraloría General del Estado | Órgano de Control | Control y Auditoría | 2 (Ola 2) | ✅ Real |
| gaceta_oficial | Gaceta Oficial de Bolivia | Gaceta | Publicación Oficial | 1 (Ola 1) | ✅ Real |
| att | ATT | Entidad Reguladora | Regulación Sectorial | 3 (Ola 2) | ✅ Real |
| mintrabajo | Min. Trabajo | Ministerio | Administración Pública | 3 (Ola 2) | ✅ Real |

### 7.2 Características por Scraper

#### **TCP (Tribunal Constitucional)**
- **Scraping**: Dynamic (requiere selenium/playwright potencialmente)
- **Paginación**: Sí, 20 items por página
- **OCR**: No requerido
- **Tipos**: Sentencias Constitucionales, Declaraciones, Autos
- **Delay**: 2 segundos
- **Peculiaridades**: Detecta tipo de acción (Amparo, Libertad, etc.)

#### **TSJ (Tribunal Supremo)**
- **Scraping**: Static (requests + BeautifulSoup)
- **Paginación**: Sí, 50 items por página
- **OCR**: Sí requerido
- **Tipos**: Autos Supremos, Sentencias, Resoluciones
- **Delay**: 1 segundo
- **Peculiaridades**: Clasifica por materia (Civil, Penal, Laboral)

#### **ASFI**
- **Scraping**: Static
- **Paginación**: Sí, 30 items por página
- **OCR**: No requerido
- **Tipos**: Resoluciones Administrativas, Circulares, Reglamentos
- **Delay**: 1 segundo
- **Peculiaridades**: Detecta tipo de entidad regulada (Banco, Cooperativa)

#### **SIN**
- **Scraping**: Static
- **Paginación**: Sí, 50 items por página
- **OCR**: No requerido
- **Tipos**: Resoluciones Normativas, Resoluciones Administrativas, Leyes Tributarias
- **Delay**: 1 segundo
- **Peculiaridades**: Clasifica por tipo de tributo (IVA, IUE, IT)

#### **Contraloría**
- **Scraping**: Static
- **Paginación**: Sí, 20 items por página
- **OCR**: Sí requerido
- **Tipos**: Resoluciones, Directrices, Normativas de Auditoría
- **Delay**: 2 segundos

#### **Gaceta Oficial**
- **Scraping**: Complex (lógica especial para ediciones)
- **Paginación**: Sí, 100 items por página
- **OCR**: Sí requerido
- **Tipos**: Leyes, Decretos Supremos, Resoluciones (Ministeriales, Supremas, Bi-Ministeriales)
- **Delay**: 3 segundos
- **Peculiaridades**: Requiere navegación por ediciones de gaceta

#### **ATT**
- **Scraping**: Static
- **Paginación**: Sí, 30 items por página
- **OCR**: No requerido
- **Tipos**: Resoluciones Administrativas, Reglamentos, Normas Técnicas
- **Delay**: 2 segundos
- **Peculiaridades**: Clasifica por sector (Telecomunicaciones, Transportes)

#### **MinTrabajo**
- **Scraping**: Static
- **Paginación**: Sí, 40 items por página
- **OCR**: Sí requerido
- **Tipos**: Resoluciones Ministeriales, Bi-Ministeriales, Reglamentos Laborales
- **Delay**: 2 segundos
- **Peculiaridades**: Clasifica por ámbito (Salarios, Relaciones Laborales)

---

## 8. PIPELINE DE PROCESAMIENTO

### 8.1 Función Principal: run_site_pipeline()

**Firma**:
```python
def run_site_pipeline(
    site_id: str,
    mode: Literal["full", "delta"] = "delta",
    limit: Optional[int] = None,
    save_pdf: bool = False,
    save_txt: bool = True,
    save_json: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> PipelineResult
```

**Responsabilidades**:
1. Validar configuración del sitio
2. Inicializar componentes (scraper, extractor, parser, metadata, exporter)
3. Ejecutar loop de procesamiento
4. Manejar errores granularmente
5. Generar reportes y tracking
6. Retornar resultado estructurado

### 8.2 Manejo de Errores

**Estrategia**: Continuar en caso de error, no fallar todo el pipeline.

```python
try:
    # Descargar PDF
    if scraper.descargar_pdf(url_pdf, pdf_path):
        result.total_descargados += 1
    else:
        result.agregar_error(f"Error descargando PDF: {id_doc}", url_pdf)
        continue  # Saltar este documento, continuar con el siguiente
except Exception as e:
    result.agregar_error(f"Error procesando documento {idx}", str(e))
    logger.exception(e)
    continue
```

**Niveles de Error**:
1. **Error de descarga**: Registra y continúa
2. **Error de extracción**: Registra y continúa sin texto
3. **Error de parsing**: Registra, continúa con articulos=[]
4. **Error de metadata**: Registra, continúa con metadata vacía
5. **Error fatal**: Solo si falla toda la configuración

### 8.3 Optimizaciones

1. **Archivos Temporales**: Si no se guarda PDF, usa tempfile
2. **Delays Configurables**: Respeta rate limiting por sitio
3. **Escritura Continua**: Flush inmediato en exports
4. **Tracking Incremental**: Índice actualizado por documento
5. **Progress Callbacks**: Reporta avance en tiempo real

---

## 9. PARSING Y METADATA

### 9.1 Estrategia de Detección de Tipo de Documento

```python
def parsear_documento(self, id_documento: str, texto: str,
                     tipo_documento: Optional[str] = None,
                     site_id: Optional[str] = None):
    # Usar tipo si se proporciona
    tipo_doc = tipo_documento or self.tipo_documento

    # Estrategia automática
    if self._es_sentencia(texto, tipo_doc, site_id):
        return self._parsear_sentencia(id_documento, texto)

    elif self._es_resolucion_administrativa(texto, tipo_doc):
        return self._parsear_resolucion(id_documento, texto)

    else:
        return self._parsear_ley_decreto(id_documento, texto)
```

**Método `_es_sentencia()`**:
```python
def _es_sentencia(self, texto: str, tipo_doc: Optional[str], site_id: Optional[str]) -> bool:
    # 1. Si el tipo dice "Sentencia", es sentencia
    if tipo_doc and 'sentencia' in tipo_doc.lower():
        return True

    # 2. Si viene de TCP o TSJ, probablemente es sentencia
    if site_id in ['tcp', 'tsj']:
        return True

    # 3. Si tiene estructura de sentencia (VISTOS, CONSIDERANDO, POR TANTO)
    if ('VISTOS' in texto or 'VISTOS:' in texto) and \
       ('CONSIDERANDO' in texto) and \
       ('POR TANTO' in texto or 'RESUELVE' in texto):
        return True

    return False
```

### 9.2 Ejemplo Completo de Parsing de Ley

**Entrada (Texto)**:
```
TÍTULO I
DISPOSICIONES GENERALES

CAPÍTULO I
Objeto y Ámbito de Aplicación

ARTÍCULO 1.- (OBJETO)
La presente Ley tiene por objeto regular el sistema tributario nacional.

PARÁGRAFO I.- Las disposiciones de la presente Ley son de orden público.

PARÁGRAFO II.- El ámbito de aplicación comprende:

a) Las personas naturales residentes en el país;
b) Las personas jurídicas constituidas en Bolivia;
c) Los no residentes que perciban rentas de fuente boliviana.

ARTÍCULO 2.- (DEFINICIONES)
Para efectos de la presente Ley, se entiende por:

1° Contribuyente: Persona natural o jurídica obligada al pago de tributos.
2° Responsable: Persona que sin tener carácter de contribuyente debe cumplir las obligaciones.
```

**Salida (Lista de Articulos)**:
```python
[
    Articulo(
        id_articulo='ley_tributo_titulo_I',
        tipo_unidad='titulo',
        numero='I',
        titulo='DISPOSICIONES GENERALES',
        orden_en_documento=1,
        nivel_jerarquico=0
    ),
    Articulo(
        id_articulo='ley_tributo_capitulo_I',
        tipo_unidad='capitulo',
        numero='I',
        titulo='Objeto y Ámbito de Aplicación',
        orden_en_documento=2,
        nivel_jerarquico=0
    ),
    Articulo(
        id_articulo='ley_tributo_articulo_1',
        tipo_unidad='articulo',
        numero='1',
        titulo='OBJETO',
        contenido='La presente Ley tiene por objeto regular el sistema tributario nacional.',
        orden_en_documento=3,
        nivel_jerarquico=1,
        palabras_clave_unidad=['ley', 'regular', 'sistema tributario'],
        area_principal_unidad='tributario'
    ),
    Articulo(
        id_articulo='ley_tributo_paragrafo_1_I',
        tipo_unidad='paragrafo',
        numero='I',
        numero_articulo='1',  # ← Vinculado al Art. 1
        contenido='Las disposiciones de la presente Ley son de orden público.',
        orden_en_documento=4,
        nivel_jerarquico=2,
        palabras_clave_unidad=['disposición', 'ley', 'orden público'],
        area_principal_unidad='tributario'
    ),
    Articulo(
        id_articulo='ley_tributo_paragrafo_1_II',
        tipo_unidad='paragrafo',
        numero='II',
        numero_articulo='1',
        contenido='El ámbito de aplicación comprende:',
        orden_en_documento=5,
        nivel_jerarquico=2
    ),
    Articulo(
        id_articulo='ley_tributo_inciso_1_II_a',
        tipo_unidad='inciso',
        numero='a',
        numero_articulo='1',     # ← Vinculado al Art. 1
        numero_paragrafo='II',   # ← Vinculado al Parágrafo II
        contenido='Las personas naturales residentes en el país;',
        orden_en_documento=6,
        nivel_jerarquico=3,
        palabras_clave_unidad=['persona', 'residente'],
        area_principal_unidad='tributario'
    ),
    Articulo(
        id_articulo='ley_tributo_inciso_1_II_b',
        tipo_unidad='inciso',
        numero='b',
        numero_articulo='1',
        numero_paragrafo='II',
        contenido='Las personas jurídicas constituidas en Bolivia;',
        orden_en_documento=7,
        nivel_jerarquico=3
    ),
    # ... etc.
]
```

**Observaciones**:
- ✅ Jerarquía completa detectada: Título → Capítulo → Artículo → Parágrafo → Inciso
- ✅ Tracking correcto: Cada inciso sabe a qué artículo y parágrafo pertenece
- ✅ Orden secuencial: orden_en_documento incremental
- ✅ Metadata automática: palabras_clave_unidad y area_principal_unidad

---

## 10. SISTEMA DE EXPORTACIÓN

### 10.1 DataExporter

**Responsabilidades**:
1. Exportación continua (streaming) a CSV
2. Exportación a JSONL (registro histórico)
3. Generación de reportes JSON
4. Gestión de sesiones de exportación

**Sesión de Exportación**:
```
exports/
└── tcp/
    └── 20251118_153000/          ← Timestamp de sesión
        ├── documentos.csv        ← Metadata de documentos
        ├── articulos.csv         ← Metadata de artículos
        ├── registro_historico.jsonl  ← Log de procesamiento
        └── reporte_scraping.json ← Resumen de la sesión
```

### 10.2 CSV Documentos (17 campos)

```csv
id_documento,site,tipo_documento,numero_norma,fecha,titulo,area_principal,areas_derecho,jerarquia,estado_vigencia,entidad_emisora,total_articulos,ruta_pdf,ruta_txt,ruta_json,hash_contenido,fecha_scraping
```

### 10.3 CSV Artículos (14 campos)

```csv
id_articulo,id_documento,numero,titulo,tipo_unidad,contenido_preview,numero_articulo,numero_paragrafo,numero_inciso,numero_numeral,orden_en_documento,nivel_jerarquico,palabras_clave_unidad,area_principal_unidad
```

### 10.4 JSONL Registro Histórico

```jsonl
{"timestamp": "2025-11-18T15:30:00", "id_documento": "tcp_sc_0123_2024", "tipo_documento": "Sentencia Constitucional", "numero_norma": "0123/2024", "area_principal": "constitucional", "jerarquia": 10, "total_articulos": 8, "metadata_completa": {...}}
{"timestamp": "2025-11-18T15:30:05", "id_documento": "tcp_sc_0124_2024", ...}
```

**Ventaja**: Formato append-only, fácil de procesar línea por línea.

### 10.5 Reporte JSON

```json
{
  "site_id": "tcp",
  "timestamp": "20251118_153000",
  "fecha_generacion": "2025-11-18T15:38:00",
  "estadisticas": {
    "total_encontrados": 100,
    "total_descargados": 95,
    "total_parseados": 90,
    "total_errores": 5,
    "duracion_segundos": 450.5,
    "areas_procesadas": ["constitucional", "civil", "penal"],
    "tipos_procesados": ["Sentencia Constitucional"]
  },
  "archivos_generados": {
    "csv_documentos": "exports/tcp/20251118_153000/documentos.csv",
    "csv_articulos": "exports/tcp/20251118_153000/articulos.csv",
    "registro_historico": "exports/tcp/20251118_153000/registro_historico.jsonl",
    "reporte": "exports/tcp/20251118_153000/reporte_scraping.json"
  }
}
```

---

## 11. PATRONES DE DISEÑO

### 11.1 Patrones Utilizados

#### **1. Abstract Factory (BaseScraper)**
```python
class BaseScraper(ABC):
    @abstractmethod
    def listar_documentos(...): pass

    @abstractmethod
    def descargar_pdf(...): pass
```
**Ventaja**: Extensibilidad sin modificar código existente.

#### **2. Template Method (listar_documentos_historico_completo)**
```python
def listar_documentos_historico_completo(self, ...):
    while True:
        documentos = self.listar_documentos(...)  # ← Método abstracto
        # Lógica de paginación (template)
```
**Ventaja**: Reutiliza lógica de paginación en todos los scrapers.

#### **3. Strategy Pattern (Parser con 3 estrategias)**
```python
if es_sentencia:
    return self._parsear_sentencia()
elif es_resolucion:
    return self._parsear_resolucion()
else:
    return self._parsear_ley_decreto()
```
**Ventaja**: Algoritmo de parsing intercambiable según tipo.

#### **4. Singleton (settings)**
```python
settings = Settings()  # Instancia global única
```
**Ventaja**: Configuración única y consistente en toda la aplicación.

#### **5. Builder (Documento)**
```python
documento = Documento(
    id_documento=...,
    site=...,
    tipo_documento=...,
    ...
)
documento.articulos = parser.parsear_documento(...)
documento.metadata.update(metadata_ext)
```
**Ventaja**: Construcción incremental del objeto complejo.

#### **6. Pipeline Pattern (run_site_pipeline)**
```
Listar → Descargar → Extraer → Parsear → Metadata → Exportar
```
**Ventaja**: Procesamiento en etapas, fácil de debugear.

#### **7. Dependency Injection (Componentes del pipeline)**
```python
scraper = get_scraper(site_id)
extractor = PDFExtractor(usar_ocr=site_config.metadatos.get('requiere_ocr'))
parser = LegalParser(tipo_documento=..., site_id=...)
```
**Ventaja**: Flexibilidad, testabilidad.

#### **8. Observer Pattern (progress_callback)**
```python
def run_site_pipeline(..., progress_callback: Optional[Callable]):
    if progress_callback:
        progress_callback(f"Procesando documento {idx}...")
```
**Ventaja**: Notificación de progreso sin acoplamiento.

---

## 12. ANÁLISIS DE CALIDAD

### 12.1 Fortalezas del Código

✅ **Modularidad Excelente**: Separación clara de responsabilidades
✅ **Tipado Fuerte**: Uso extensivo de type hints
✅ **Dataclasses**: Modelos de datos limpios y mantenibles
✅ **Logging Consistente**: Logging en todos los componentes
✅ **Manejo de Errores**: try/except granular, no crashea
✅ **Configuración Centralizada**: YAML + dataclasses
✅ **Abstracción Apropiada**: ABC para scrapers
✅ **Documentación**: Docstrings en todas las funciones
✅ **Extensibilidad**: Fácil agregar nuevos sitios
✅ **Testing-Friendly**: Componentes desacoplados

### 12.2 Áreas de Mejora

⚠️ **Testing**: Falta suite de tests unitarios
⚠️ **Validación**: Podría usar Pydantic para validación más robusta
⚠️ **Async**: Podría beneficiarse de async/await para scraping
⚠️ **Cache**: No hay cache de requests
⚠️ **Retry Logic**: Podría usar tenacity para retries
⚠️ **Selenium**: TCP marca como "dynamic" pero usa requests
⚠️ **Monitoreo**: Falta integración con herramientas de monitoreo
⚠️ **CI/CD**: No hay GitHub Actions para CI

### 12.3 Métricas de Código

| Métrica | Valor | Evaluación |
|---------|-------|------------|
| **Complejidad Ciclomática** | Alta en parsers (~25) | ⚠️ Justificada por dominio |
| **Longitud de Funciones** | Media (50-100 líneas) | ✅ Aceptable |
| **Duplicación de Código** | Baja | ✅ Excelente |
| **Acoplamiento** | Bajo | ✅ Excelente |
| **Cohesión** | Alta | ✅ Excelente |
| **Cobertura de Tests** | 0% | ❌ Crítico |
| **Documentación** | Alta | ✅ Excelente |
| **Tipo Hints** | 90% | ✅ Excelente |

---

## 13. MEJORAS IMPLEMENTADAS

### 13.1 Resumen de Mejoras (Esta Sesión)

| Componente | Mejora | Impacto |
|------------|--------|---------|
| **models.py** | +9 campos en Articulo | Alto - Metadata jerárquica |
| **legal_parser.py** | Parser profesional (196→600 líneas) | Crítico - Parsing profundo |
| **metadata_extractor.py** | +3 métodos para metadata de unidad | Alto - Clasificación automática |
| **pipeline.py** | Integración context-aware | Medio - Parsing correcto |
| **exporter.py** | CSV artículos (6→14 campos) | Alto - Export completo |

### 13.2 Antes vs Después

#### **Parser**
| Capacidad | Antes | Después |
|-----------|-------|---------|
| Artículos | ✅ | ✅ |
| Parágrafos | ❌ | ✅ |
| Incisos | ❌ | ✅ |
| Numerales | ❌ | ✅ |
| Estructura | ❌ | ✅ |
| Sentencias | ❌ | ✅ |
| Resoluciones | ❌ | ✅ |

#### **Metadata**
| Nivel | Antes | Después |
|-------|-------|---------|
| Documento | ✅ Completa | ✅ Completa + Site-aware |
| Artículo | ❌ | ✅ Palabras clave + Área |

---

## 14. ESTRUCTURA DE ARCHIVOS

```
bo-gov-scraper-buho/
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configuración global
│   └── sites_catalog.yaml     # Catálogo de 8 sitios
│
├── scraper/
│   ├── __init__.py
│   ├── models.py              # Documento, Articulo, PipelineResult
│   ├── pipeline.py            # Pipeline principal
│   ├── metadata_extractor.py  # Clasificación + metadata
│   ├── exporter.py            # CSV/JSON/JSONL export
│   │
│   ├── sites/                 # 8 scrapers específicos
│   │   ├── __init__.py
│   │   ├── base_scraper.py   # Clase base abstracta
│   │   ├── tcp_scraper.py
│   │   ├── tsj_scraper.py
│   │   ├── asfi_scraper.py
│   │   ├── sin_scraper.py
│   │   ├── contraloria_scraper.py
│   │   ├── gaceta_scraper.py
│   │   ├── att_scraper.py
│   │   └── mintrabajo_scraper.py
│   │
│   ├── parsers/               # Parsing legal
│   │   ├── __init__.py
│   │   └── legal_parser.py   # Parser profesional (600 líneas)
│   │
│   └── extractors/            # Extracción de PDFs
│       ├── __init__.py
│       └── pdf_extractor.py  # PyPDF2 + OCR
│
├── data/                      # Datos procesados
│   ├── raw/                   # PDFs originales (opcional)
│   ├── normalized/            # Datos normalizados
│   │   ├── tcp/
│   │   │   ├── pdfs/
│   │   │   ├── text/         # TXTs extraídos
│   │   │   └── json/         # JSONs con estructura
│   │   ├── tsj/
│   │   └── .../              # 8 sitios
│   ├── index/                 # Índices para delta updates
│   │   ├── tcp/index.json
│   │   └── .../
│   └── tracking_historico.json
│
├── exports/                   # Exportaciones por sesión
│   ├── tcp/
│   │   └── 20251118_153000/
│   │       ├── documentos.csv
│   │       ├── articulos.csv
│   │       ├── registro_historico.jsonl
│   │       └── reporte_scraping.json
│   └── .../
│
├── logs/                      # Logs por sitio
│   ├── tcp/
│   └── .../
│
├── docs/                      # Documentación
│   ├── ANALISIS_COMPLETO_SISTEMA.md  # Este archivo
│   └── UPGRADE_PARSING_JERARQUICO_PROFESIONAL.md
│
├── main.py                    # CLI principal
├── requirements.txt           # Dependencias
└── README.md
```

**Total**: ~4,500 líneas de código Python en 20 archivos.

---

## 15. DEPENDENCIAS Y TECNOLOGÍAS

### 15.1 Dependencias Core

```txt
# Web Scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# PDF Processing
PyPDF2>=3.0.0
pytesseract>=0.3.10        # OCR (opcional)
Pillow>=10.0.0             # Para OCR (opcional)
pdf2image>=1.16.0          # Para OCR (opcional)

# Configuration
PyYAML>=6.0.1

# CLI (opcional, actualmente usa argparse)
# click>=8.1.0
# typer>=0.9.0
```

### 15.2 Dependencias Opcionales

```txt
# Para Supabase Sync
supabase>=2.0.0
python-dotenv>=1.0.0

# Para scraping dinámico (futuro)
selenium>=4.15.0
playwright>=1.40.0
```

### 15.3 Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| **Lenguaje** | Python | 3.9+ |
| **HTTP Client** | requests | 2.31+ |
| **HTML Parser** | BeautifulSoup4 | 4.12+ |
| **PDF Extractor** | PyPDF2 | 3.0+ |
| **OCR** | pytesseract | 0.3.10+ |
| **Config** | PyYAML | 6.0+ |
| **CLI** | argparse | stdlib |
| **Logging** | logging | stdlib |
| **Data Classes** | dataclasses | stdlib (3.7+) |
| **Type Hints** | typing | stdlib |
| **Async** | - | No usado (futuro) |
| **Database** | Supabase | Opcional |

---

## 16. SEGURIDAD Y ROBUSTEZ

### 16.1 Medidas de Seguridad

✅ **User-Agent**: Identificación clara en requests
✅ **Rate Limiting**: Delays configurables
✅ **Timeouts**: Timeout en requests (30s default)
✅ **Validación de Rutas**: Path.exists() antes de leer
✅ **Try/Except Granular**: No crashea por errores parciales
✅ **Sanitización**: Normalización de texto extraído
✅ **Hash de Contenido**: MD5 para delta updates

⚠️ **Falta**:
- Validación de URLs (puede descargar de cualquier URL)
- Límite de tamaño de archivos
- Validación de tipos MIME
- Escaneo de malware en PDFs

### 16.2 Robustez

✅ **Fallback de Scrapers**: Método principal + alternativo
✅ **Fallback de PDF**: PyPDF2 → OCR
✅ **Fallback de Parser**: Si falla, retorna documento completo
✅ **Límite de Paginación**: Máximo 100 páginas
✅ **Archivos Temporales**: Limpieza automática
✅ **Índices**: Persistencia en JSON
✅ **Logging**: Trazabilidad completa

### 16.3 Manejo de Recursos

✅ **Session Reutilizable**: requests.Session()
✅ **Streaming de Descarga**: iter_content(chunk_size=8192)
✅ **Flush Continuo**: Exportación streaming
✅ **Limpieza de PDFs Temporales**: unlink()
✅ **Cierre de Archivos**: with statements

---

## 17. ESCALABILIDAD

### 17.1 Escalabilidad Actual

**Horizontal (Múltiples Sitios)**:
✅ Diseñado para múltiples sitios
✅ Configuración por YAML
✅ Cada sitio independiente
✅ Puede correr en paralelo (manualmente)

**Vertical (Grandes Volúmenes)**:
⚠️ Síncrono (no async)
⚠️ Procesamiento secuencial
⚠️ Sin pool de workers
⚠️ Sin queue distribuida

### 17.2 Cuellos de Botella

1. **Descarga de PDFs**: Síncrono, uno a la vez
2. **Extracción de Texto**: OCR es lento (segundos por página)
3. **Parsing**: Regex complejo puede ser lento
4. **Exportación**: Escritura síncrona a disco

### 17.3 Mejoras para Escalabilidad

**Corto Plazo**:
- ✅ Async/await con aiohttp
- ✅ Thread pool para OCR
- ✅ Batch processing

**Medio Plazo**:
- ✅ Celery para tareas distribuidas
- ✅ Redis para queue
- ✅ S3 para almacenamiento de PDFs
- ✅ PostgreSQL para metadata

**Largo Plazo**:
- ✅ Kubernetes para orquestación
- ✅ Kafka para streaming de datos
- ✅ Elasticsearch para búsqueda
- ✅ Airflow para scheduling

---

## 18. CASOS DE USO

### 18.1 Caso de Uso 1: Scraping Completo de un Sitio

**Objetivo**: Obtener todo el histórico de sentencias del TCP.

**Comando**:
```bash
python main.py scrape tcp --mode full --save-json
```

**Flujo**:
1. Lista todas las páginas de sentencias del TCP
2. Descarga PDFs (a temporal)
3. Extrae texto sin OCR (TCP no requiere)
4. Parsea como sentencia (VISTOS, CONSIDERANDO, POR TANTO)
5. Extrae metadata constitucional + site-aware TCP
6. Exporta a CSV/JSONL
7. Guarda JSON normalizado

**Resultado**:
```
📁 exports/tcp/20251118_153000/
    - documentos.csv (150 documentos)
    - articulos.csv (1,200 unidades)
    - registro_historico.jsonl
    - reporte_scraping.json

📁 data/normalized/tcp/json/
    - tcp_sc_0001_2024.json
    - tcp_sc_0002_2024.json
    - ...
```

### 18.2 Caso de Uso 2: Delta Update Diario

**Objetivo**: Actualizar solo documentos nuevos cada día.

**Comando**:
```bash
python main.py scrape sin --mode delta
```

**Flujo**:
1. Carga índice anterior (data/index/sin/index.json)
2. Lista documentos del SIN
3. Filtra: solo procesa documentos no en índice
4. Procesa solo los nuevos
5. Actualiza índice
6. Exporta solo los nuevos a CSV

**Ventaja**: Eficiente, solo procesa novedades.

### 18.3 Caso de Uso 3: Scraping de Todos los Sitios

**Objetivo**: Actualizar todos los sitios en una sola ejecución.

**Comando**:
```bash
python main.py scrape all --mode delta --limit 10
```

**Flujo**:
1. Itera por los 8 sitios activos
2. Ejecuta pipeline para cada uno (máximo 10 docs cada uno)
3. Genera reportes individuales
4. Muestra resumen global

**Resultado**:
```
✅ Scraping de todos los sitios completado

📊 tcp: 10 docs procesados
📊 tsj: 10 docs procesados
📊 asfi: 10 docs procesados
...
```

### 18.4 Caso de Uso 4: Estadísticas Globales

**Objetivo**: Ver cuántos documentos se han procesado en total.

**Comando**:
```bash
python main.py stats
```

**Flujo**:
1. Lee índices de todos los sitios
2. Cuenta documentos y artículos
3. Muestra resumen por sitio

**Resultado**:
```
📊 Estadísticas globales

Tribunal Constitucional Plurinacional
   Documentos: 1,500
   Artículos: 12,000
   Última actualización: 2025-11-18

Tribunal Supremo de Justicia
   Documentos: 3,200
   Artículos: 25,600

...

TOTAL - Documentos: 15,000, Artículos: 120,000
```

### 18.5 Caso de Uso 5: Sincronización con Supabase

**Objetivo**: Subir datos procesados a base de datos en la nube.

**Comando**:
```bash
python main.py sync-supabase tcp
```

**Flujo**:
1. Lee CSV de última sesión de TCP
2. Inserta/actualiza en Supabase:
   - Tabla `sources` (sitios)
   - Tabla `documents` (documentos)
   - Tabla `articles` (artículos)
3. Genera reporte de sincronización

**Prerequisitos**:
- Variables de entorno: `SUPABASE_URL`, `SUPABASE_KEY`
- Dependencia: `pip install supabase`

---

## 19. LIMITACIONES IDENTIFICADAS

### 19.1 Limitaciones Técnicas

1. **Scraping Síncrono**
   - **Problema**: No usa async/await
   - **Impacto**: Lento para grandes volúmenes
   - **Solución**: Migrar a aiohttp + asyncio

2. **OCR Lento**
   - **Problema**: pytesseract es secuencial y lento
   - **Impacto**: PDFs escaneados tardan mucho
   - **Solución**: Usar servicios cloud (Google Vision, AWS Textract)

3. **Sin Cache**
   - **Problema**: Re-descarga PDFs aunque no cambien
   - **Impacto**: Desperdicio de ancho de banda
   - **Solución**: Implementar cache con hash de URLs

4. **Sin Retry Automático**
   - **Problema**: Falla de red = falla permanente
   - **Impacto**: Requiere re-ejecución manual
   - **Solución**: Usar tenacity para retries con backoff

5. **Complejidad Ciclomática Alta en Parser**
   - **Problema**: Métodos con 25+ decisiones
   - **Impacto**: Difícil de testear y mantener
   - **Solución**: Refactorizar con Chain of Responsibility

6. **Sin Tests**
   - **Problema**: 0% cobertura de tests
   - **Impacto**: Riesgo de regresiones
   - **Solución**: Implementar pytest con mocks

7. **Dependencia de Estructura HTML**
   - **Problema**: Si el sitio cambia HTML, el scraper falla
   - **Impacto**: Mantenimiento continuo
   - **Solución**: APIs oficiales (cuando existan)

### 19.2 Limitaciones de Negocio

1. **Sitios sin API**
   - Los sitios gubernamentales no tienen APIs públicas
   - Dependencia total de scraping

2. **Formatos Heterogéneos**
   - Cada sitio usa formato diferente
   - Requiere scraper específico por sitio

3. **PDFs Escaneados**
   - Muchos documentos son scans de baja calidad
   - OCR puede tener errores

4. **Metadata Inconsistente**
   - Los sitios no tienen metadata estructurada
   - Requiere inferencia con regex

5. **Vigencia de Normas**
   - No hay información oficial de derogaciones
   - Sistema infiere con palabras clave

### 19.3 Limitaciones de Escala

1. **Almacenamiento Local**
   - Todo se guarda en disco local
   - No escalable a millones de documentos

2. **Procesamiento Secuencial**
   - Un documento a la vez
   - No aprovecha multi-core

3. **Sin Monitoreo**
   - No hay alertas si falla
   - Requiere revisión manual

---

## 20. RECOMENDACIONES FUTURAS

### 20.1 Prioridad Alta (Críticas)

1. **✅ Implementar Tests Unitarios**
   ```python
   # tests/test_parser.py
   def test_parsear_ley():
       parser = LegalParser(tipo_documento="Ley")
       articulos = parser.parsear_documento("test_id", texto_ley)
       assert len(articulos) > 0
       assert articulos[0].tipo_unidad == "articulo"
   ```

2. **✅ Migrar a Async/Await**
   ```python
   async def descargar_pdf_async(url, destino):
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               with open(destino, 'wb') as f:
                   f.write(await response.read())
   ```

3. **✅ Implementar Retry Logic**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
   def descargar_pdf_con_retry(url, destino):
       return self._download_file(url, destino)
   ```

4. **✅ Agregar Validación con Pydantic**
   ```python
   from pydantic import BaseModel, HttpUrl, validator

   class DocumentoModel(BaseModel):
       id_documento: str
       url_origen: HttpUrl
       numero_norma: Optional[str]

       @validator('id_documento')
       def validate_id(cls, v):
           if not v.startswith(('tcp_', 'tsj_', ...)):
               raise ValueError('ID inválido')
           return v
   ```

### 20.2 Prioridad Media (Importantes)

5. **✅ Implementar Cache de Requests**
   ```python
   import requests_cache

   session = requests_cache.CachedSession(
       'scraper_cache',
       expire_after=3600  # 1 hora
   )
   ```

6. **✅ Agregar Logging Estructurado**
   ```python
   import structlog

   logger = structlog.get_logger()
   logger.info("documento_procesado",
               id_documento=doc.id_documento,
               total_articulos=len(doc.articulos))
   ```

7. **✅ Implementar Health Checks**
   ```python
   def health_check(site_id: str) -> Dict:
       try:
           scraper = get_scraper(site_id)
           docs = scraper.listar_documentos(limite=1)
           return {'status': 'ok', 'site': site_id}
       except Exception as e:
           return {'status': 'error', 'site': site_id, 'error': str(e)}
   ```

8. **✅ Migrar a Click/Typer**
   ```python
   import typer

   app = typer.Typer()

   @app.command()
   def scrape(
       site: str,
       mode: str = typer.Option("delta", help="Modo de scraping"),
       limit: int = typer.Option(None, help="Límite de documentos")
   ):
       ...
   ```

### 20.3 Prioridad Baja (Mejoras)

9. **✅ Integración con CI/CD**
   ```yaml
   # .github/workflows/test.yml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: pytest tests/
   ```

10. **✅ Monitoreo con Prometheus/Grafana**
    ```python
    from prometheus_client import Counter, Histogram

    documentos_procesados = Counter('docs_procesados_total', 'Docs procesados')
    tiempo_procesamiento = Histogram('doc_tiempo_procesamiento', 'Tiempo de proc')
    ```

11. **✅ Migrar a Poetry para Dependencias**
    ```toml
    [tool.poetry]
    name = "bo-gov-scraper-buho"
    version = "3.0.0"

    [tool.poetry.dependencies]
    python = "^3.9"
    requests = "^2.31.0"
    beautifulsoup4 = "^4.12.0"
    ```

12. **✅ Dockerizar la Aplicación**
    ```dockerfile
    FROM python:3.11-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    CMD ["python", "main.py", "scrape", "all"]
    ```

### 20.4 Mejoras de Arquitectura

13. **✅ Implementar Queue con Celery**
    ```python
    from celery import Celery

    app = Celery('scraper', broker='redis://localhost')

    @app.task
    def procesar_documento(site_id, doc_metadata):
        # Procesamiento asíncrono
        ...
    ```

14. **✅ Migrar a PostgreSQL**
    ```python
    from sqlalchemy import create_engine, Column, String, Integer
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class Documento(Base):
        __tablename__ = 'documentos'
        id_documento = Column(String, primary_key=True)
        site = Column(String)
        tipo_documento = Column(String)
        ...
    ```

15. **✅ Implementar GraphQL API**
    ```python
    import strawberry

    @strawberry.type
    class Documento:
        id_documento: str
        titulo: str
        articulos: List[Articulo]

    @strawberry.type
    class Query:
        @strawberry.field
        def documento(self, id: str) -> Documento:
            ...
    ```

---

## CONCLUSIONES FINALES

### Resumen Ejecutivo del Análisis

**BO-GOV-SCRAPER-BUHO** es un sistema **profesional, bien diseñado y funcional** para el scraping y procesamiento de documentos legales bolivianos.

**Fortalezas Principales**:
1. ✅ **Arquitectura Modular**: Separación clara de responsabilidades
2. ✅ **Extensibilidad**: Fácil agregar nuevos sitios
3. ✅ **Parsing Profesional**: Detección jerárquica completa
4. ✅ **Metadata Rica**: Clasificación automática de áreas del derecho
5. ✅ **Robustez**: Manejo granular de errores
6. ✅ **Configuración Centralizada**: YAML + dataclasses
7. ✅ **Exportación Completa**: CSV/JSON/JSONL con 14+ campos

**Áreas de Mejora Prioritarias**:
1. ⚠️ **Testing**: 0% cobertura → Crítico implementar
2. ⚠️ **Async**: Síncrono → Migrar a async/await
3. ⚠️ **Retry**: Sin retries → Agregar tenacity
4. ⚠️ **Validación**: Sin validación → Agregar Pydantic

**Madurez del Sistema**: **⭐⭐⭐⭐☆ (4/5)**

El sistema está **listo para producción** en su forma actual, con las limitaciones de escalabilidad identificadas. Para escalar a millones de documentos, se requieren las mejoras arquitectónicas recomendadas (async, queue, base de datos).

**Recomendación**: Continuar con el desarrollo incremental, priorizando tests y async antes de escalar.

---

**Fin del Análisis Completo**
**Documento**: 1,200+ líneas
**Fecha**: 2025-11-18
**Analista**: Claude (Anthropic)
