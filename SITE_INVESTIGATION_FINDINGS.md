# Investigación de Sitios Gubernamentales Bolivianos
## Hallazgos de Estructuras Web y Estrategias de Scraping

**Fecha:** 18 de Noviembre de 2025
**Contexto:** Fase 2 del proyecto - Actualización de scrapers con lógica real

---

## Resumen Ejecutivo

**Disponibilidad Actual:** 6 de 8 sitios operativos (75%)
**Tipos de Scraping Identificados:**
- ✅ **HTML Estático** (3 sitios): ASFI, Gaceta Oficial, probablemente Contraloría/ATT/MinTrabajo
- ⚠️ **JavaScript SPA - Requiere Selenium** (1 sitio): TSJ
- ❌ **No Disponible** (2 sitios): TCP, SIN

---

## Hallazgos Detallados por Sitio

### 1. Gaceta Oficial de Bolivia ✅ COMPLETADO

**Estado:** Operativo y scraper implementado
**URL Base:** http://www.gacetaoficialdebolivia.gob.bo
**Tipo de Scraping:** HTML Estático con paginación

**Estructura:**
- Múltiples fuentes de datos: `/normas/listadonor/{código}`
- Paginación: `/page:2`, `/page:3`, etc.
- Documentos en cards con class `card-body`

**Cobertura Actual:**
- 500 documentos únicos de prueba (143 Leyes, 236 Decretos Supremos)
- 4 fuentes activas: Leyes (10), Decretos (11), Otras Normas (16), Listado General (0)
- Deduplicación por PDF ID implementada

**Estado del Scraper:** ✅ Implementado y probado
**Archivo:** `scraper/sites/advanced/gaceta_oficial_scraper.py`

---

### 2. Tribunal Constitucional Plurinacional (TCP) ❌ NO DISPONIBLE

**Estado:** Sitio caído (503 Service Unavailable)
**URL Base:** https://www.tcpbolivia.bo
**Error:** HTTPSConnectionPool: Max retries exceeded (503 error responses)

**Análisis:**
- Servidor completamente inaccesible
- Todos los endpoints retornan 503
- No se puede investigar estructura

**Recomendación:**
- Implementar monitoreo para detectar cuando vuelva online
- Mantener scraper existente con mejor manejo de errores
- Registrar en cola de reintentos

**Estado del Scraper:** 🔄 Pendiente de disponibilidad del sitio
**Archivo:** `scraper/sites/tcp_scraper.py`

---

### 3. Tribunal Supremo de Justicia (TSJ) ⚠️ REQUIERE SELENIUM

**Estado:** Operativo pero con arquitectura compleja
**URL Base:** https://tsj.bo
**URL Jurisprudencia:** https://jurisprudencia.tsj.bo

**Estructura Identificada:**
- **Tipo:** JavaScript SPA (Single Page Application)
- **Framework:** CoreUI / "GENESIS_TSJ"
- **Contenido:** Carga dinámica vía AJAX
- **PDFs en página principal:** 0 (todo cargado por JS)

**Análisis Técnico:**
```html
<!-- Página base (7.6 KB) -->
<title>GENESIS_TSJ</title>
<meta name="description" content="Sistema de Búsqueda de Resoluciones...">
```

**Endpoints Investigados:**
- ❌ `/api/autos` - No encontrado
- ❌ `/api/sentencias` - No encontrado
- ❌ `/api/jurisprudencia` - No encontrado
- ✅ `/jurisprudencia` - Responde 200 pero sin PDFs en HTML

**Recomendación:**
- Requiere Selenium o Playwright para renderizar JavaScript
- Alternativamente: investigar red developer tools para encontrar endpoints API ocultos
- Recurso intensivo - considerar prioridad vs otros sitios

**Estado del Scraper:** 🔄 Requiere re-implementación con Selenium
**Archivo:** `scraper/sites/tsj_scraper.py` (actual), `scraper/sites/advanced/selenium_scraper.py` (base disponible)

---

### 4. Autoridad de Supervisión del Sistema Financiero (ASFI) ✅ LISTO PARA IMPLEMENTAR

**Estado:** Operativo con estructura simple
**URL Base:** https://www.asfi.gob.bo
**Tipo de Scraping:** HTML Estático con tablas

**Estructura Identificada:**

#### Fuentes de Datos Disponibles:

1. **Normativa Nacional (Leyes)**
   - URL: `/pb/normativa-nacional`
   - PDFs encontrados: 17
   - Estructura: Tabla con filas, cada fila tiene título y enlace PDF
   - Ejemplo: "Ley N° 1670 de 05 de noviembre de 2025"
   - Patrón URL: `https://www.asfi.gob.bo/sites/default/files/YYYY-MM/...pdf`

2. **Reglamentos Vigentes**
   - URL: `/pb/reglamentos-vigentes`
   - PDFs encontrados: 8
   - Estructura: Similar, tabla con enlaces
   - Ejemplos: "Reglamento Específico de Contrataciones", "Tesorería.pdf"

3. **Otras Secciones:**
   - `/la/normativa-internacional` - Normativa internacional
   - `/pb/normativa-referida-transparencia-y-lucha-contra-corrupcion-aplicable-asfi`
   - `/pb/reglamentos-internos-fondos-inversion`

**Ejemplo de Extracción:**
```html
<table>
  <tr>
    <td>Ley N° 1670 de 05 de noviembre de 2025</td>
    <td><a href="/sites/default/files/2025-11/LEY 1670.pdf">Descargar</a></td>
  </tr>
</table>
```

**Metadata Extraíble:**
- Tipo de documento: Ley, Reglamento
- Número de norma: Extraíble del título (ej: "1670")
- Fecha: Extraíble del título (ej: "05 de noviembre de 2025")
- URL del PDF: Directa desde tabla

**Recomendación:**
- Implementar scraper multi-fuente similar a Gaceta Oficial
- Parsear tablas HTML para extraer metadata
- No requiere paginación (documentos limitados por sección)

**Estado del Scraper:** 🔄 Pendiente de actualización
**Archivo:** `scraper/sites/asfi_scraper.py`

---

### 5. Servicio de Impuestos Nacionales (SIN) ❌ NO DISPONIBLE

**Estado:** Sitio caído (503 Service Unavailable)
**URL Base:** https://www.impuestos.gob.bo
**Error:** Similar a TCP - servidor no responde

**Análisis:**
- Todos los endpoints retornan 503
- Probablemente sobrecarga o mantenimiento

**Recomendación:**
- Monitoreo automático
- Cola de reintentos cuando vuelva

**Estado del Scraper:** 🔄 Pendiente de disponibilidad
**Archivo:** `scraper/sites/sin_scraper.py`

---

### 6. Contraloría General del Estado ✅ DISPONIBLE

**Estado:** Operativo (200 OK en health check)
**URL Base:** https://www.contraloria.gob.bo
**Tipo de Scraping:** Por investigar

**Estado del Scraper:** 🔄 Pendiente de investigación
**Archivo:** `scraper/sites/contraloria_scraper.py`

---

### 7. ATT - Autoridad de Telecomunicaciones y Transportes ✅ DISPONIBLE

**Estado:** Operativo (200 OK en health check)
**URL Base:** https://www.att.gob.bo
**Tipo de Scraping:** Por investigar

**Estado del Scraper:** 🔄 Pendiente de investigación
**Archivo:** `scraper/sites/att_scraper.py`

---

### 8. Ministerio de Trabajo ✅ DISPONIBLE

**Estado:** Operativo (200 OK en health check)
**URL Base:** https://www.mintrabajo.gob.bo
**Tipo de Scraping:** Por investigar

**Estado del Scraper:** 🔄 Pendiente de investigación
**Archivo:** `scraper/sites/mintrabajo_scraper.py`

---

## Mejoras de Infraestructura Implementadas

### Sistema de Resiliencia (base_scraper.py)

**Características:**
1. **Retry Automático**
   - 3 intentos con backoff exponencial (2s, 4s, 8s)
   - Reintentos para códigos: 429, 500, 502, 503, 504

2. **Health Checks**
   - Método `check_availability()` con cache de 5 minutos
   - Manejo específico de errores SSL, timeout, conexión
   - Estados descriptivos para debugging

3. **Manejo SSL Robusto**
   - Ignorar certificados mal configurados (`verify=False`)
   - Desactivar warnings de urllib3
   - Continuar scraping a pesar de errores SSL

**Utilidad Creada:** `check_sites_health.py`
- Verifica disponibilidad de todos los sitios activos
- Genera reporte con estadísticas
- Identifica sitios problemáticos por fase (Ola)

---

## Estrategia de Implementación Recomendada

### Prioridad 1 (Inmediato):
1. ✅ **Gaceta Oficial** - COMPLETADO
2. 🔄 **ASFI** - Estructura simple, listo para implementar
3. 🔄 **Contraloría, ATT, MinTrabajo** - Investigar estructuras

### Prioridad 2 (Requiere más recursos):
4. 🔄 **TSJ** - Requiere Selenium, mayor complejidad

### Prioridad 3 (Bloqueado):
5. ⏸️ **TCP** - Esperar disponibilidad del sitio
6. ⏸️ **SIN** - Esperar disponibilidad del sitio

---

## Próximos Pasos

### Corto Plazo (Hoy/Mañana):
1. Actualizar scraper de ASFI con fuentes múltiples
2. Investigar estructura de Contraloría, ATT, MinTrabajo
3. Implementar scrapers para sitios HTML simples

### Mediano Plazo (Esta Semana):
1. Implementar TSJ con Selenium (si es prioridad)
2. Configurar monitoreo automático de TCP y SIN
3. Crear cola de reintentos para sitios caídos

### Largo Plazo:
1. Sistema de alertas cuando sitios vuelvan online
2. Dashboard de disponibilidad histórica
3. Optimización de Selenium para TSJ

---

## Lecciones Aprendidas

1. **Infraestructura Inestable**: 25% de sitios gubernamentales caídos es normal
2. **Diversidad Tecnológica**: Mix de HTML estático y JavaScript SPAs
3. **Resiliencia es Crítica**: Retry logic y health checks son esenciales
4. **Priorizar Simplicidad**: Sitios HTML estáticos primero, SPAs después
5. **Gaceta Oficial es Clave**: Fuente oficial más importante y confiable

---

## Contacto y Mantenimiento

**Documento Actualizado:** 18 Nov 2025
**Próxima Revisión:** Al completar investigación de sitios restantes
**Health Check Command:** `python check_sites_health.py`
