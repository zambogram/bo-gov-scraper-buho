# Interfaz QA/Revisión - Streamlit

## Descripción General

Nueva pestaña en la aplicación Streamlit para realizar **Quality Assurance (QA)** y revisión detallada de documentos legales procesados, con visualización completa de la metadata extendida.

## Ubicación

**Pestaña:** 🔍 QA/Revisión
**Archivo:** `app/streamlit_app.py`
**Función:** `render_tab_qa_revision()`

## Características Principales

### 1. Selector de Documento

Permite seleccionar cualquier documento procesado por su `id_documento`:

```python
selected_doc_id = st.selectbox(
    "Seleccionar documento por ID",
    options=doc_ids,
    key="qa_selected_doc"
)
```

**Funcionalidad:**
- Lista todos los documentos del sitio seleccionado
- Busca el documento en el índice local
- Carga el JSON completo con toda la metadata

### 2. Secciones de la Interfaz

#### SECCIÓN 1: Información Básica

**Campos Mostrados:**
- **ID Documento:** Identificador único generado
- **Tipo de Documento:** Ley, Decreto Supremo, Sentencia, etc.
- **Número de Norma:** Extraído automáticamente
- **Fecha:** Fecha de promulgación
- **Hash Contenido:** MD5 para detectar cambios
- **Fecha Scraping:** Timestamp de cuándo se procesó

**Layout:** 3 columnas con información compacta

#### SECCIÓN 2: Metadata Extendida

**Métricas Visuales (4 columnas):**

1. **Jerarquía Normativa**
   - Valor: 1-99 (1=CPE, 2=Ley, etc.)
   - Alerta: "⚠️ No clasificada" si jerarquia == 99

2. **Área Principal**
   - Categorías: constitucional, penal, tributario, civil, etc.
   - Alerta: "⚠️ Sin clasificar" si área == 'otros'

3. **Estado de Vigencia**
   - Estados: vigente ✅, modificada ⚠️, derogada ❌
   - Visualización con emoji

4. **Total Artículos**
   - Contador de artículos parseados
   - Ayuda a verificar completitud

**Áreas del Derecho (2 columnas):**

- **Áreas Detectadas:** Badges con todas las áreas identificadas
  - Ejemplo: 📖 tributario, 📖 financiero, 📖 administrativo

- **Palabras Clave:** Lista de términos extraídos
  - Muestra las primeras 10 palabras clave

**Relaciones Normativas (3 columnas):**

- **Entidad Emisora:** Órgano que emite la norma
  - Ejemplo: "Asamblea Legislativa Plurinacional"

- **Modifica Normas:** Lista de normas modificadas
  - Ejemplo: "Ley 843", "DS 24051"

- **Deroga Normas:** Lista de normas derogadas

#### SECCIÓN 3: Título y Sumilla

- **Título Completo:** Título oficial del documento
- **Sumilla:** Resumen ejecutivo
  - Muestra sumilla original o sumilla auto-generada
  - Área de texto de 100px de altura

**Alertas:**
- ⚠️ Si falta título
- ⚠️ Si falta sumilla

#### SECCIÓN 4: Texto Completo

**Estadísticas del Texto (3 métricas):**
- **Caracteres:** Total de caracteres
- **Palabras:** Total de palabras
- **Páginas Estimadas:** ~3000 caracteres por página

**Visualización:**
- Área de texto scrollable (400px altura)
- Muestra el texto completo normalizado
- Lee desde archivo `.txt`

**Alertas:**
- ⚠️ Si archivo de texto no disponible

#### SECCIÓN 5: Artículos Parseados

**Selector de Artículo:**
```python
selected_art_idx = st.selectbox(
    "Seleccionar artículo",
    options=range(len(articulos)),
    format_func=lambda i: f"{articulos[i].get('numero', f'#{i+1}')} - {articulos[i].get('titulo', 'Sin título')[:50]}"
)
```

**Información por Artículo (3 columnas):**
- **Número:** "Artículo 1", "Art. 5", etc.
- **Tipo:** articulo, seccion, capitulo, titulo, disposicion
- **ID:** Identificador único del artículo

**Contenido:**
- Área de texto con el contenido completo del artículo
- 200px de altura, scrollable

**Alertas:**
- ⚠️ Si no se encontraron artículos parseados

#### SECCIÓN 6: Alertas de Calidad

Sistema automático de detección de problemas:

**Alertas de Error (Críticas):**
- ❌ No se parsearon artículos del documento
- ❌ Falta archivo de texto normalizado

**Alertas de Warning (Importantes):**
- ⚠️ Falta título del documento
- ⚠️ Falta fecha de promulgación
- ⚠️ No se detectó número de norma
- ⚠️ Solo X artículos parseados (puede ser incompleto)
- ⚠️ Falta hash de contenido

**Alertas Informativas:**
- ℹ️ Área del derecho no clasificada automáticamente
- ℹ️ Jerarquía normativa no determinada
- ℹ️ Entidad emisora no detectada

**Estado Ideal:**
- ✅ No se detectaron problemas de calidad

#### SECCIÓN 7: Archivos Disponibles

Verifica la existencia de archivos (3 columnas):

1. **PDF:**
   - ✅ PDF disponible (si existe)
   - ℹ️ PDF no guardado (si no se solicitó guardar)

2. **TXT:**
   - ✅ TXT disponible
   - ❌ TXT no disponible (error crítico)

3. **JSON:**
   - ✅ JSON disponible
   - ❌ JSON no disponible (error crítico)

Muestra la ruta completa de cada archivo en caption.

## Flujo de Uso

### Caso 1: Revisión de Documento Individual

```
1. Usuario selecciona sitio en sidebar (ej: tcp)
2. Usuario va a pestaña "🔍 QA/Revisión"
3. Usuario selecciona documento por ID del dropdown
4. Sistema carga y muestra:
   ✅ Información básica
   ✅ Metadata extendida completa
   ✅ Texto completo
   ✅ Artículos parseados
   ⚠️ Alertas de calidad si hay problemas
5. Usuario puede navegar entre artículos
6. Usuario identifica problemas para corrección manual
```

### Caso 2: Validación de Metadata Extendida

```
1. Usuario ejecuta scraping de documentos nuevos
2. Usuario va a QA/Revisión
3. Usuario verifica:
   - ¿Se extrajo el número de norma correctamente?
   - ¿La clasificación de área es correcta?
   - ¿La jerarquía está bien determinada?
   - ¿Los artículos se parsearon completos?
4. Si encuentra errores:
   - Ajusta reglas en metadata_extractor.py
   - Re-procesa documentos
```

### Caso 3: Verificación Pre-Sync a Supabase

```
1. Usuario completa scraping masivo
2. Usuario revisa varios documentos en QA
3. Usuario verifica alertas de calidad
4. Si hay errores críticos:
   - Corrige problemas antes de sincronizar
5. Usuario ejecuta sync-supabase solo cuando QA es verde
```

## Código de Ejemplo

### Cargar Documento Completo

```python
def cargar_documento_completo(ruta_json: str) -> dict:
    """Cargar documento completo desde JSON con toda su metadata"""
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None
```

### Mostrar Metadata Extendida

```python
metadata = doc_completo.get('metadata', {})

# Jerarquía
jerarquia = metadata.get('jerarquia', 99)
st.metric("Jerarquía Normativa", jerarquia)
if jerarquia == 99:
    st.caption("⚠️ No clasificada")

# Área
area_principal = metadata.get('area_principal', 'otros')
st.metric("Área Principal", area_principal)
if area_principal == 'otros':
    st.caption("⚠️ Sin clasificar")

# Estado
estado = metadata.get('estado_vigencia', 'vigente')
emoji = '✅' if estado == 'vigente' else '⚠️' if estado == 'modificada' else '❌'
st.metric("Estado Vigencia", f"{emoji} {estado}")
```

### Sistema de Alertas

```python
alertas = []

# Verificar campos críticos
if not doc_completo.get('titulo'):
    alertas.append(("warning", "Falta título del documento"))

if metadata.get('area_principal') == 'otros':
    alertas.append(("info", "Área del derecho no clasificada automáticamente"))

if not articulos:
    alertas.append(("error", "No se parsearon artículos del documento"))

# Mostrar alertas
for tipo, mensaje in alertas:
    if tipo == "error":
        st.error(f"❌ {mensaje}")
    elif tipo == "warning":
        st.warning(f"⚠️ {mensaje}")
    else:
        st.info(f"ℹ️ {mensaje}")
```

## Estilos y Diseño

### Tema Oscuro (Dark Mode)

La interfaz mantiene el tema oscuro consistente:
- Fondos oscuros (`#262730`)
- Texto claro
- Badges con fondo oscuro y bordes redondeados

### Badges de Áreas del Derecho

```python
badges_html = " ".join([
    f'<span style="background-color: #262730; padding: 4px 12px; border-radius: 12px; margin: 2px; display: inline-block;">📖 {area}</span>'
    for area in areas
])
st.markdown(badges_html, unsafe_allow_html=True)
```

### Layout Responsivo

- **Columnas:** 2, 3 o 4 columnas según sección
- **Altura fija:** Text areas con altura definida para evitar scroll infinito
- **Separadores:** `st.markdown("---")` entre secciones

## Beneficios

### Para QA Manual
- ✅ Vista completa de un documento en una sola pantalla
- ✅ Fácil navegación entre documentos
- ✅ Identificación rápida de problemas
- ✅ Verificación de metadata extendida

### Para Desarrollo
- ✅ Debug rápido de extractors
- ✅ Validación de parsers
- ✅ Pruebas de clasificación automática
- ✅ Verificación de completitud

### Para Producción
- ✅ Revisión pre-sync a Supabase
- ✅ Auditoría de calidad de datos
- ✅ Detección temprana de errores
- ✅ Documentación de problemas

## Mejoras Futuras

### Filtros y Búsqueda
- Filtrar documentos por área
- Filtrar por estado de vigencia
- Filtrar por alertas de calidad
- Búsqueda por palabras clave

### Edición Manual
- Permitir corrección de metadata manualmente
- Guardar cambios en el JSON
- Historial de correcciones

### Comparación
- Comparar versiones de un documento
- Ver diferencias en texto y metadata
- Detectar cambios entre scrapings

### Exportación
- Exportar reporte de QA en PDF
- Exportar lista de alertas en CSV
- Generar informe de calidad por sitio

### Integración
- Marcar documentos como "revisados"
- Workflow de aprobación
- Comentarios y anotaciones

## Archivos Relacionados

- **UI:** `app/streamlit_app.py` (función `render_tab_qa_revision()`)
- **Modelos:** `scraper/models.py` (clase `Documento`)
- **Metadata:** `scraper/metadata_extractor.py` (clase `LegalMetadataExtractor`)
- **Exports:** `scraper/exporter.py` (clase `DataExporter`)

## Resumen

La pestaña QA/Revisión es una herramienta completa para:
- 📋 Revisar documentos procesados
- 🏛️ Verificar metadata extendida
- 📄 Validar texto y artículos
- ⚠️ Detectar problemas de calidad
- ✅ Garantizar datos correctos antes de sync

**Resultado:** Datos de alta calidad en Supabase y sistemas downstream.
