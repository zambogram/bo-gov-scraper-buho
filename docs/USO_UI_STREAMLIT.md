# Guía de Uso - Interfaz Streamlit

## Introducción

La interfaz Streamlit de BÚHO proporciona una manera visual e interactiva para ejecutar scraping histórico completo, revisar documentos procesados, y descargar archivos normalizados.

## Iniciar la Aplicación

### Instalación de Dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

### Lanzar Streamlit

```bash
# Desde el directorio raíz del proyecto
streamlit run app/streamlit_app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Interfaz Principal

### Estructura de la UI

La aplicación tiene dos áreas principales:

1. **Sidebar (Barra Lateral)**: Controles de configuración y acciones
2. **Área Central**: Pestañas con diferentes vistas de datos

## Barra Lateral (Sidebar)

### 📍 Bloque 1: Selección de Sitio

#### Selector de Sitio
- **Dropdown**: Selecciona el sitio gubernamental a scrapear
- Opciones disponibles:
  - Tribunal Constitucional Plurinacional (TCP)
  - Tribunal Supremo de Justicia (TSJ)
  - ASFI (Autoridad de Supervisión del Sistema Financiero)
  - SIN (Servicio de Impuestos Nacionales)
  - Contraloría General del Estado

#### Información del Sitio (expandible)
Al hacer clic en "ℹ️ Información del sitio" se muestra:
- **Tipo**: Tipo de institución (Judicial, Regulatorio, Fiscal, etc.)
- **Categoría**: Categoría temática
- **Prioridad**: Prioridad de scraping
- **Ola**: Grupo de implementación
- **Última actualización**: Fecha de último scraping exitoso

### ⚙️ Bloque 2: Modo de Scraping

#### Selector de Modo
- **Delta (Sólo nuevos)**:
  - Descarga solo documentos nuevos desde última ejecución
  - Usa índice para saltar documentos ya procesados
  - ⚡ Rápido para actualizaciones diarias

- **Histórico completo**:
  - Descarga TODOS los documentos disponibles
  - Recorre todas las páginas hasta agotar resultados
  - ⏱️ Más lento, útil para primera carga

**Ejemplo de uso**:
- **Primera vez usando el sistema**: Selecciona "Histórico completo"
- **Actualizaciones diarias**: Selecciona "Sólo nuevos (Delta)"

#### Límite por Corrida
- **Número**: Máximo de documentos a procesar en esta sesión
- **Rango**: 1 - 1000
- **Valor por defecto**: 50
- **Uso**:
  - Para testing: usa 10-20
  - Para producción full: usa 1000 o sin límite

**Nota**: En modo "Histórico completo", el límite se aplica al total de documentos. Si hay 500 documentos disponibles pero configuras límite=50, solo procesará 50.

### 💾 Bloque 3: Qué Guardar

Checkboxes para controlar qué archivos se guardan:

#### Guardar PDF original
- ✅ **Activado**: Guarda PDFs en `data/raw/{site_id}/`
- ⚠️ **Desactivado**: PDFs se descargan temporalmente y se borran después
- **Recomendación**: Desactivar (ahorra espacio, TXT y JSON contienen toda la info)

#### Guardar texto normalizado (.txt)
- ✅ **Activado**: Guarda texto limpio en `data/normalized/{site_id}/text/`
- **Formato**: UTF-8, limpio, sin metadatos
- **Recomendación**: Activar siempre (útil para búsquedas)

#### Guardar estructura JSON (.json)
- ✅ **Activado**: Guarda documento completo con metadata en `data/normalized/{site_id}/json/`
- **Contiene**: Texto, artículos, metadata extendida, hashes
- **Recomendación**: Activar siempre (fuente canónica)

### 🚀 Bloque 4: Acciones

#### ▶️ Raspar sitio seleccionado
- Ejecuta scraping para el sitio actualmente seleccionado
- Usa configuración de modo, límite y qué guardar
- Muestra progreso en tiempo real

#### ▶️ Raspar TODOS los sitios
- Ejecuta scraping secuencial para todos los sitios activos
- Usa misma configuración para todos
- ⏱️ Puede tomar mucho tiempo

## Área Central - Pestañas

### 📄 Pestaña: Documentos

Vista general de documentos procesados para el sitio seleccionado.

#### Tabla de Documentos

Columnas:
- **ID**: ID único del documento
- **PDF**: ✓/✗ si PDF está guardado
- **TXT**: ✓/✗ si TXT está guardado
- **JSON**: ✓/✗ si JSON está guardado
- **Hash**: Hash del contenido (primeros 8 caracteres)
- **Actualización**: Fecha de última actualización

**Funciones**:
- Ordenable por columna
- Búsqueda integrada

#### Vista Previa de Documento

**Selector**: Dropdown para elegir documento específico

**Muestra**:
- **Col 1**: Metadata básica (ID, Hash, Fecha)
- **Col 2**: Primeras 500 caracteres del texto

**Uso**: Vista rápida sin abrir el documento completo

### 📑 Pestaña: Artículos

Vista de todos los artículos/secciones parseados de todos los documentos del sitio.

#### Tabla de Artículos

Columnas:
- **ID Artículo**: ID único del artículo
- **ID Documento**: Documento padre
- **Número**: Número del artículo ("1", "Art. 5", "I")
- **Título**: Título del artículo/sección
- **Tipo**: Tipo de unidad (articulo, seccion, capitulo, etc.)
- **Contenido**: Primeros 100 caracteres

#### Filtros

- **Por tipo**: Filtrar por tipo_unidad (articulo, seccion, etc.)
- **Por documento**: Filtrar por ID de documento específico

**Uso**: Explorar estructura de documentos, encontrar artículos específicos

### 📊 Pestaña: Estadísticas

Estadísticas agregadas de todos los sitios.

#### Métricas Globales

- **Total Documentos**: Suma de documentos de todos los sitios
- **Total Artículos**: Suma de artículos parseados
- **Promedio Artículos/Doc**: Promedio de artículos por documento

#### Tabla por Sitio

- **Sitio**: Nombre del sitio
- **Documentos**: Cantidad de documentos del sitio
- **Artículos**: Cantidad de artículos del sitio

#### Gráfico de Barras

Visualización de documentos y artículos por sitio.

### 🔍 Pestaña: QA/Revisión

**Vista más importante para control de calidad y descarga de documentos.**

#### Selector de Documento
Dropdown para elegir documento por ID

#### Sección 1: Información Básica

**3 Columnas**:
1. **ID Documento** y **Tipo**
2. **Número de Norma** y **Fecha**
3. **Hash Contenido** y **Fecha Scraping**

#### Sección 2: Metadata Extendida

**Fila 1 - Métricas**:
- **Jerarquía Normativa**: 1-99 (1 = más alta)
  - ⚠️ Marca con "No clasificada" si jerarquía = 99
- **Área Principal**: Área del derecho principal
  - ⚠️ Marca con "Sin clasificar" si área = "otros"
- **Estado Vigencia**: vigente/modificada/derogada
  - ✅ Vigente, ⚠️ Modificada, ❌ Derogada
- **Total Artículos**: Cantidad de artículos parseados

**Fila 2 - Clasificación**:
- **Áreas del Derecho Detectadas**: Badges con todas las áreas
- **Palabras Clave**: Top 10 palabras clave extraídas

**Fila 3 - Relaciones**:
- **Entidad Emisora**: Entidad que emitió la norma
- **Modifica Normas**: Números de normas modificadas
- **Deroga Normas**: Números de normas derogadas

#### Sección 3: Título y Sumilla

- **Título**: Título completo del documento
- **Sumilla**: Resumen/sumilla del documento (auto-generada o original)

#### Sección 4: Texto Completo

**Métricas del Texto**:
- **Caracteres**: Total de caracteres
- **Palabras**: Total de palabras
- **Páginas Estimadas**: Estimación (1 página ≈ 3000 caracteres)

**Text Area**: Muestra texto completo con scroll

#### Sección 5: Artículos Parseados

- **Info**: "Total artículos parseados: N"
- **Selector**: Dropdown para elegir artículo específico
- **Vista del artículo**:
  - Número, Tipo, ID
  - Título (si tiene)
  - Contenido completo

#### Sección 6: Alertas de Calidad

Sistema automático de detección de problemas:

**Alertas de Error (❌)**:
- No se parsearon artículos del documento
- Falta archivo de texto normalizado

**Alertas de Warning (⚠️)**:
- Falta título del documento
- Falta fecha de promulgación
- No se detectó número de norma
- Solo X artículos parseados (puede ser incompleto)
- Falta hash de contenido

**Alertas de Info (ℹ️)**:
- Área del derecho no clasificada automáticamente
- Jerarquía normativa no determinada
- Entidad emisora no detectada

#### Sección 7: Archivos Disponibles y Descarga ⭐

**La funcionalidad más importante para descarga de documentos.**

**3 Columnas - Una por tipo de archivo**:

##### Columna 1: PDF
- **Estado**: ✅ PDF disponible / ℹ️ PDF no guardado
- **Ruta**: Muestra ruta completa del archivo
- **Botón**: `⬇️ Descargar PDF`
  - Descarga archivo PDF original
  - Nombre: `{id_documento}.pdf`

##### Columna 2: TXT
- **Estado**: ✅ TXT disponible / ❌ TXT no disponible
- **Ruta**: Muestra ruta completa del archivo
- **Botón**: `⬇️ Descargar TXT`
  - Descarga texto normalizado limpio
  - Encoding: UTF-8
  - Nombre: `{id_documento}.txt`

##### Columna 3: JSON
- **Estado**: ✅ JSON disponible / ❌ JSON no disponible
- **Ruta**: Muestra ruta completa del archivo
- **Botón**: `⬇️ Descargar JSON`
  - Descarga documento estructurado completo
  - Contiene: texto, artículos, metadata extendida
  - Nombre: `{id_documento}.json`

**Uso típico**:
1. Seleccionar documento de interés
2. Revisar metadata y contenido
3. Hacer clic en botón de descarga del formato deseado
4. Archivo se descarga a carpeta de Descargas del navegador

**Manejo de Errores**:
- Si archivo no existe: Muestra "⚠️ Archivo no encontrado en disco"
- Si hay error leyendo: Muestra "⚠️ Error: {detalle}"

### 📝 Pestaña: Logs

Visualización de logs de ejecución.

#### Logs de la Sesión Actual

- Text Area con logs en tiempo real
- Se actualiza durante ejecución de scraping
- Últimos 20 mensajes visibles

#### Logs Históricos

- **Selector**: Dropdown de archivos .log en `data/{site_id}/logs/`
- **Text Area**: Contenido del archivo de log seleccionado
- Útil para debugging de sesiones pasadas

## Flujo de Trabajo Típico

### Caso 1: Primera Carga Histórica Completa

**Objetivo**: Descargar todo el archivo histórico de TCP

1. **Sidebar**:
   - Seleccionar sitio: "Tribunal Constitucional Plurinacional"
   - Modo: "Histórico completo"
   - Límite: 1000 (o sin límite)
   - Guardar PDF: ✗ (desactivar)
   - Guardar TXT: ✓
   - Guardar JSON: ✓

2. **Acción**: Click en "▶️ Raspar sitio seleccionado"

3. **Observar**:
   - Barra de progreso
   - Logs en tiempo real
   - Métricas al finalizar

4. **Resultado**:
   - Documentos aparecen en pestaña "Documentos"
   - Archivos guardados en:
     - `data/normalized/tcp/text/*.txt`
     - `data/normalized/tcp/json/*.json`

### Caso 2: Revisión y Descarga de Documento

**Objetivo**: Revisar sentencia específica y descargar JSON

1. **Pestaña**: Click en "🔍 QA/Revisión"

2. **Selector**: Elegir documento por ID (ej. `tcp_sc_0042_2024`)

3. **Revisar**:
   - Metadata extendida (área del derecho, jerarquía, etc.)
   - Título y sumilla
   - Texto completo
   - Artículos parseados
   - Alertas de calidad

4. **Descargar**:
   - Scroll hasta "📁 Archivos Disponibles y Descarga"
   - Click en "⬇️ Descargar JSON"
   - Archivo se descarga a tu carpeta de Descargas

### Caso 3: Actualización Diaria (Delta)

**Objetivo**: Actualizar documentos nuevos de todos los sitios

1. **Sidebar**:
   - Modo: "Sólo nuevos (Delta)"
   - Límite: 100
   - Guardar TXT: ✓
   - Guardar JSON: ✓

2. **Acción**: Click en "▶️ Raspar TODOS los sitios"

3. **Resultado**:
   - Solo documentos nuevos se procesan
   - Rápido (minutos vs horas)

### Caso 4: Análisis de Artículos de un Tema

**Objetivo**: Encontrar todos los artículos sobre "tributario"

1. **Pestaña**: "📑 Artículos"

2. **Sitio**: Seleccionar "SIN" (Servicio de Impuestos Nacionales)

3. **Filtros**:
   - Por tipo: "Todos"
   - Por documento: "Todos"

4. **Buscar**: Usar búsqueda integrada de tabla (Ctrl+F en navegador)

5. **Resultado**: Lista de artículos relacionados a impuestos

### Caso 5: Verificación de Calidad

**Objetivo**: Verificar que documentos tengan metadata completa

1. **Pestaña**: "🔍 QA/Revisión"

2. **Iteración**: Ir documento por documento

3. **Revisar Sección 6**: "⚠️ Alertas de Calidad"
   - Si hay ❌: Documento tiene problemas serios
   - Si hay ⚠️: Documento tiene campos faltantes
   - Si hay ✅: Documento está completo

4. **Acción**: Tomar nota de documentos con problemas para revisión manual

## Solución de Problemas

### Problema: "No hay documentos procesados"

**Causa**: No se ha ejecutado scraping aún

**Solución**:
1. Ir a sidebar
2. Configurar modo y límite
3. Click en "▶️ Raspar sitio seleccionado"

### Problema: Botón de descarga no aparece

**Causa**: Archivo no fue guardado

**Solución**:
- Verificar checkboxes de "Qué guardar" en sidebar
- Reejecutar scraping con checkbox activado

### Problema: "Archivo no encontrado en disco"

**Causa**: Archivo fue movido o borrado

**Solución**:
- Reejecutar scraping para ese sitio
- Verificar permisos de disco

### Problema: Scraping muy lento

**Causas posibles**:
- Modo "Histórico completo" con miles de documentos
- PDFs grandes
- Procesamiento de OCR

**Soluciones**:
- Usar límite más bajo para testing
- Desactivar "Guardar PDF"
- Ejecutar en horarios de baja carga

### Problema: Errores de metadata

**Causa**: Extractor de metadata no detectó campos

**Solución**:
- Normal para algunos documentos
- Verificar en pestaña QA/Revisión
- Ver "Alertas de Calidad" para detalles

## Atajos de Teclado

**Navegador**:
- `Ctrl + R`: Recargar aplicación
- `Ctrl + F`: Buscar en tabla actual
- `Ctrl + Shift + R`: Recargar sin caché

**Streamlit**:
- `R`: Rerun de la aplicación
- `C`: Limpiar caché

## Mejores Prácticas

### Para Scraping Inicial

1. **Empezar pequeño**: Usa límite=10 primero para probar
2. **Incrementar gradualmente**: 10 → 50 → 100 → sin límite
3. **No guardar PDFs**: Ahorra espacio, usa solo JSON/TXT
4. **Modo full**: Primera vez siempre usar "Histórico completo"

### Para Actualizaciones

1. **Modo delta**: Siempre usar "Sólo nuevos (Delta)"
2. **Límite alto**: 500-1000 es seguro
3. **Periodicidad**: Ejecutar 1 vez al día

### Para Análisis

1. **Usar QA/Revisión**: Vista más completa
2. **Exportar datos**: Descargar JSONs para análisis externo
3. **Verificar alertas**: Revisar calidad de metadata

### Para Descargas Masivas

1. **Seleccionar documentos**: Usar pestaña "Documentos" para ver lista
2. **Ir a QA/Revisión**: Para cada documento de interés
3. **Descargar**: Usar botones de descarga
4. **Alternativa CLI**: Para descargas masivas, usar scripts externos

## Arquitectura de la UI

### Tecnologías

- **Streamlit**: Framework de UI
- **Pandas**: DataFrames para tablas
- **Python**: Backend
- **JSON**: Formato de datos

### Flujo de Datos

```
[Sidebar Config] → [run_site_pipeline] → [Procesamiento] → [data/*] → [UI Refresh]
```

### Persistencia

- **Session State**: Variables temporales de sesión
- **Archivos**: Datos persistentes en `data/`
- **Índices**: JSON en `data/{site_id}/index.json`

## Recursos Adicionales

- **Documentación de Pipeline**: `docs/FASE_HISTORICO.md`
- **Formato de Datos**: `docs/FORMATO_DOCUMENTO_NORMALIZADO.md`
- **Código fuente UI**: `app/streamlit_app.py`
- **Pipeline**: `scraper/pipeline.py`

## Actualizaciones Futuras

**Planeadas**:
- Filtros avanzados por metadata
- Gráficos de tendencias temporales
- Exportación masiva a CSV/Excel
- Búsqueda de texto completo integrada
- Comparación de documentos

**Feedback**: Reportar issues en GitHub del proyecto
