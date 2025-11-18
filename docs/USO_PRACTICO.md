# 📘 Guía de Uso Práctico - BÚHO

Esta guía te muestra cómo usar el sistema BÚHO paso a paso, con ejemplos reales y casos de uso prácticos.

---

## 📋 Tabla de Contenidos

1. [Instalación Completa](#1-instalación-completa)
2. [Primer Uso](#2-primer-uso)
3. [Explorando el Catálogo](#3-explorando-el-catálogo)
4. [Usando la UI Web](#4-usando-la-ui-web)
5. [Flujos de Trabajo Recomendados](#5-flujos-de-trabajo-recomendados)
6. [Casos de Uso Reales](#6-casos-de-uso-reales)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Instalación Completa

### Paso 1: Requisitos previos

Asegúrate de tener instalado:

```bash
python --version  # Debe ser 3.9 o superior
pip --version
```

### Paso 2: Clonar y configurar

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd bo-gov-scraper-buho

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python main.py --version
```

### Paso 3: Primer test

```bash
# Validar que el catálogo funciona
python main.py validate

# Deberías ver:
# ✓ Catálogo válido - sin errores
```

---

## 2. Primer Uso

### Ver todos los sitios disponibles

```bash
python main.py list
```

**Salida esperada:**
```
Total de sitios: 15

╭───────────────┬──────────────────────────────────┬───────┬────┬─────┬────────┬──────╮
│ ID            │ Nombre                           │ Tipo  │ Ni │ Pri │ Estado │ Docs │
├───────────────┼──────────────────────────────────┼───────┼────┼─────┼────────┼──────┤
│ gaceta_ofic...│ Gaceta Oficial del Estado...     │ norm  │ na │  1  │ ⏳ pen │    0 │
│ tsj_genesis   │ Tribunal Supremo...              │ juri  │ na │  1  │ ⏳ pen │    0 │
...
╰───────────────┴──────────────────────────────────┴───────┴────┴─────┴────────┴──────╯
```

### Ver solo sitios prioritarios (Ola 1)

```bash
python main.py list --prioridad 1
```

**Resultado:** Solo verás los 5 sitios de prioridad máxima (MVP).

### Información detallada de un sitio

```bash
python main.py info gaceta_oficial
```

**Salida esperada:**
```
Gaceta Oficial del Estado Plurinacional de Bolivia

╭─────────────────────────── 📋 Información Básica ────────────────────────────╮
│    ID:            gaceta_oficial                                             │
│    Nivel:         nacional                                                   │
│    Tipo:          normativa                                                  │
│    Prioridad:     1 (MVP)                                                    │
│    Estado:        ⏳ pendiente                                               │
╰──────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────── 🔗 URLs ───────────────────────────────────╮
│    URL Base:         http://www.gacetaoficialdebolivia.gob.bo                │
│    URL Búsqueda:     ...                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
...
```

### Ver estadísticas generales

```bash
python main.py stats
```

**Muestra:**
- Total de sitios catalogados
- Cuántos están implementados vs pendientes
- Distribución por prioridad, nivel y tipo
- Total de documentos y artículos procesados

---

## 3. Explorando el Catálogo

### Filtros avanzados

#### Por tipo de fuente

```bash
# Solo normativa
python main.py list --tipo normativa

# Solo jurisprudencia
python main.py list --tipo jurisprudencia

# Solo reguladores
python main.py list --tipo regulador
```

#### Por nivel gubernamental

```bash
# Solo sitios nacionales
python main.py list --nivel nacional

# Solo departamentales
python main.py list --nivel departamental

# Solo municipales
python main.py list --nivel municipal
```

#### Por estado de implementación

```bash
# Sitios ya implementados
python main.py list --estado implementado

# Sitios pendientes
python main.py list --estado pendiente

# Sitios en desarrollo
python main.py list --estado en_progreso
```

#### Combinando filtros

```bash
# Normativa nacional prioritaria pendiente
python main.py list --tipo normativa --nivel nacional --prioridad 1 --estado pendiente
```

### Salida en JSON

```bash
# Para procesamiento programático
python main.py list --prioridad 1 --json > ola1_sites.json
python main.py info tcp --json > tcp_info.json
python main.py stats --json > catalog_stats.json
```

---

## 4. Usando la UI Web

### Iniciar Streamlit

```bash
streamlit run app/streamlit_app.py
```

Se abrirá automáticamente en tu navegador: `http://localhost:8501`

### Navegación

#### Página Dashboard (🏠)

- **Métricas clave:** Total de sitios, implementados, documentos, artículos
- **Gráficos:** Distribución por prioridad, nivel y tipo
- **Sitios Ola 1:** Vista rápida de los sitios prioritarios

#### Página Sitios (📋)

1. **Sidebar:** Usa los filtros para refinar la búsqueda
   - Prioridad: Todas, 1, 2, 3
   - Estado: Todos, Implementado, Pendiente, etc.
   - Nivel: Todos, Nacional, Departamental, Municipal
   - Tipo: Todos, Normativa, Jurisprudencia, Regulador

2. **Tarjetas de sitios:** Cada sitio muestra:
   - Nombre y estado
   - Documentos y artículos procesados
   - Botón "Ver detalles" (expandible)
   - Botones de acción (Scrape, Info)

3. **Detalles expandibles:** Click en "Ver detalles" para ver:
   - URLs completas
   - Características técnicas
   - Tipos de documentos
   - Notas específicas

#### Página Estadísticas (📊)

- **Resumen general:** Métricas agregadas
- **Tabla completa:** Todos los sitios con sus datos
- **Exportar CSV:** Botón para descargar la tabla

#### Página Configuración (⚙️)

- **Validar catálogo:** Verifica la integridad
- **Rutas del proyecto:** Información de directorios

---

## 5. Flujos de Trabajo Recomendados

### Flujo 1: Exploración Inicial

**Objetivo:** Familiarizarte con el sistema.

```bash
# 1. Ver todos los sitios
python main.py list

# 2. Ver solo prioridad 1
python main.py list --prioridad 1

# 3. Ver detalles de un sitio interesante
python main.py info gaceta_oficial
python main.py info tcp
python main.py info asfi

# 4. Ver estadísticas generales
python main.py stats

# 5. Validar que todo esté bien
python main.py validate
```

### Flujo 2: Análisis de un Tipo Específico

**Objetivo:** Explorar solo sitios de jurisprudencia.

```bash
# 1. Listar sitios de jurisprudencia
python main.py list --tipo jurisprudencia

# 2. Ver detalles de cada uno
python main.py info tsj_genesis
python main.py info tcp
python main.py info ait

# 3. Exportar a JSON para análisis
python main.py list --tipo jurisprudencia --json > jurisprudencia_sites.json
```

### Flujo 3: Planificación de Scraping

**Objetivo:** Preparar el scraping de sitios de Ola 1.

```bash
# 1. Ver sitios Ola 1
python main.py list --prioridad 1

# 2. Revisar características técnicas
python main.py info gaceta_oficial  # requiere_selenium: true
python main.py info tcp              # requiere_selenium: true
python main.py info asfi             # requiere_selenium: false

# 3. Probar comando demo (cuando esté implementado)
python main.py demo-ola1 --limit 3
```

### Flujo 4: Monitoreo Continuo

**Objetivo:** Revisar el estado del sistema.

```bash
# 1. Validar integridad
python main.py validate

# 2. Ver estadísticas
python main.py stats

# 3. Ver sitios implementados
python main.py list --estado implementado

# 4. Verificar última actualización de cada sitio
python main.py stats --json | jq '.total_documentos'
```

---

## 6. Casos de Uso Reales

### Caso 1: "Necesito scrapear toda la normativa nacional"

**Pasos:**

```bash
# 1. Identificar sitios de normativa nacional
python main.py list --tipo normativa --nivel nacional

# Resultado:
# - gaceta_oficial (Prioridad 1)
# - silep (Prioridad 2)
# - lexivox (Prioridad 3)

# 2. Ver detalles de cada uno
python main.py info gaceta_oficial
python main.py info silep

# 3. Cuando estén implementados, ejecutar:
python main.py scrape gaceta_oficial --limit 100
python main.py scrape silep --limit 100

# 4. Exportar datos
# (Comando de exportación - próximamente)
```

### Caso 2: "Solo me interesa jurisprudencia del TCP"

**Pasos:**

```bash
# 1. Ver info del TCP
python main.py info tcp

# 2. Verificar estado
# Estado: pendiente → Esperar implementación

# 3. Cuando esté implementado:
python main.py scrape tcp --limit 50

# 4. Exportar solo TCP
# (Comando de exportación específica - próximamente)
```

### Caso 3: "Necesito datos de reguladores financieros"

**Pasos:**

```bash
# 1. Listar reguladores
python main.py list --tipo regulador

# 2. Identificar financieros: ASFI, APS
python main.py info asfi
python main.py info aps

# 3. Scrapear ambos
python main.py scrape asfi --limit 100
python main.py scrape aps --limit 100

# 4. Consolidar exportación
# (Comando de exportación consolidada - próximamente)
```

### Caso 4: "Quiero un dashboard visual para mi equipo"

**Pasos:**

```bash
# 1. Iniciar UI Streamlit
streamlit run app/streamlit_app.py

# 2. Compartir URL con tu equipo
# http://localhost:8501 (o tu IP si expones el puerto)

# 3. Usar filtros en el sidebar para explorar

# 4. Exportar estadísticas como CSV desde la UI
```

---

## 7. Troubleshooting

### Problema: "Catálogo no encontrado"

**Error:**
```
FileNotFoundError: Catálogo no encontrado en: config/sites_catalog.yaml
```

**Solución:**
```bash
# Verificar que estás en el directorio del proyecto
pwd

# Debe mostrar: .../bo-gov-scraper-buho

# Si no, navega al directorio correcto
cd /ruta/al/bo-gov-scraper-buho
```

### Problema: "Module 'scraper.catalog' not found"

**Solución:**
```bash
# Verifica que __init__.py existe
ls scraper/__init__.py

# Si no existe, créalo:
touch scraper/__init__.py
```

### Problema: "Site ID not found"

**Error:**
```
Sitio no encontrado: gacet_oficial
```

**Solución:**
```bash
# Verifica el spelling correcto
python main.py list | grep gaceta

# Debe ser: gaceta_oficial (con 'a' al final)
python main.py info gaceta_oficial
```

### Problema: "Scraper not implemented"

**Mensaje:**
```
⚠ Scraper no implementado aún
Estado actual: pendiente
```

**Explicación:**
- El sitio está catalogado pero el scraper aún no se ha desarrollado
- Verifica la prioridad y el roadmap en README.md
- Los scrapers se implementan por olas (Ola 1 primero)

### Problema: "Streamlit no inicia"

**Error:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solución:**
```bash
# Instalar Streamlit
pip install streamlit

# O reinstalar todas las dependencias
pip install -r requirements.txt
```

### Problema: "YAML parse error"

**Error:**
```
yaml.scanner.ScannerError: ...
```

**Solución:**
```bash
# El catálogo YAML tiene un error de sintaxis
# Valida el YAML en: https://www.yamllint.com/

# O revierte cambios recientes
git diff config/sites_catalog.yaml
git checkout config/sites_catalog.yaml
```

---

## 8. Consejos y Buenas Prácticas

### Consejo 1: Usa filtros combinados

En lugar de revisar todos los sitios, combina filtros:

```bash
python main.py list --prioridad 1 --tipo normativa
```

### Consejo 2: Exporta a JSON para análisis

```bash
python main.py list --json | jq '.[] | {id: .site_id, nombre: .nombre, estado: .estado_scraper}'
```

### Consejo 3: Valida antes de cambios importantes

```bash
# Antes de modificar el catálogo
python main.py validate

# Después de modificar
python main.py validate
```

### Consejo 4: Usa la UI para exploración, CLI para automatización

- **UI (Streamlit):** Exploración visual, presentaciones, demos
- **CLI:** Scripts, automatización, cron jobs, pipelines

### Consejo 5: Mantén el catálogo actualizado

Cuando descubras nuevos sitios:

1. Agrégalos al catálogo YAML
2. Valida: `python main.py validate`
3. Verifica que aparecen: `python main.py list`

---

## 9. Próximos Pasos

Una vez te familiarices con el sistema:

1. **Implementar scrapers** (si eres developer)
   - Ver `docs/SCRAPERS.md` (próximamente)

2. **Configurar Supabase**
   - Ver `docs/SUPABASE_SETUP.md` (próximamente)

3. **Automatizar scraping**
   - Configurar cron jobs
   - Ver `docs/AUTOMATION.md` (próximamente)

4. **Integrar con tu aplicación**
   - Usar datos exportados
   - Conectar con API de Supabase

---

## 10. Recursos Adicionales

- **README.md** - Guía general del proyecto
- **docs/SITES_CATALOG.md** - Documentación del catálogo
- **config/sites_catalog.yaml** - Archivo del catálogo

---

**¿Preguntas o problemas?**
Consulta el README.md o revisa los issues del proyecto.

---

**Última actualización:** 2025-01-18
**Versión:** 1.0.0
