# 📚 Documentación del Catálogo de Sitios

## Introducción

El archivo `config/sites_catalog.yaml` es la **fuente de verdad** del sistema BÚHO. Contiene todos los sitios estatales bolivianos que el motor puede scrapear, con sus URLs, características técnicas y metadatos.

## Estructura del Catálogo

### Campos Principales

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `site_id` | string | Identificador único (snake_case, sin espacios) | `"gaceta_oficial"` |
| `nombre` | string | Nombre completo legible del sitio | `"Gaceta Oficial del Estado..."` |
| `nivel` | enum | Nivel gubernamental | `"nacional"`, `"departamental"`, `"municipal"` |
| `tipo_fuente` | enum | Tipo de contenido legal | `"normativa"`, `"jurisprudencia"`, `"regulador"` |
| `prioridad` | int | Prioridad de implementación | `1` (crítico), `2` (importante), `3` (complementario) |
| `estado_scraper` | enum | Estado de desarrollo | `"pendiente"`, `"en_progreso"`, `"implementado"`, `"deshabilitado"` |

### URLs

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `url_base` | URL principal del sitio | `"https://www.asfi.gob.bo"` |
| `url_busqueda` | URL del buscador (si existe) | `"https://www.asfi.gob.bo/normativa"` |
| `url_listado` | URL de listado de documentos | `"https://..."` |

### Características Técnicas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `formato_documento` | enum | Formato de los documentos | `"pdf"`, `"html"`, `"mixto"` |
| `requiere_selenium` | bool | Si necesita navegador automatizado | `true` / `false` |
| `requiere_login` | bool | Si requiere autenticación | `true` / `false` |
| `tiene_api` | bool | Si tiene API disponible | `true` / `false` |

### Estructura Legal

| Campo | Descripción | Valores posibles |
|-------|-------------|------------------|
| `estructura_texto` | Cómo se segmenta el documento legal | `"articulos"`, `"sentencia_vistos_fundamentos_por_tanto"`, `"sentencia_constitucional"`, `"resolucion_administrativa"` |
| `tipos_documentos` | Array de tipos de documentos que publica | `["ley", "decreto_supremo", "resolucion"]` |

### Metadatos Operacionales

| Campo | Tipo | Descripción | Actualización |
|-------|------|-------------|---------------|
| `frecuencia_actualizacion` | enum | Frecuencia recomendada de scraping | `"diaria"`, `"semanal"`, `"mensual"` |
| `ultima_actualizacion` | timestamp | Última vez que se scrapeó | Automática (null al inicio) |
| `documentos_totales` | int | Total de documentos procesados | Automática (0 al inicio) |
| `articulos_totales` | int | Total de artículos/secciones extraídos | Automática (0 al inicio) |
| `notas` | string | Observaciones técnicas | Manual |

---

## Prioridades y Olas de Implementación

### Ola 1 - MVP Crítico (Prioridad 1)

**6 sitios fundamentales** que deben funcionar primero:

1. **gaceta_oficial** - Fuente oficial primaria de normativa
2. **tsj_genesis** - Autos supremos y sentencias
3. **tcp** - Jurisprudencia constitucional
4. **asfi** - Regulación financiera
5. **sin** - Normativa tributaria
6. **contraloria** - Control fiscal (Prioridad 2, pero incluida en Ola 1)

### Ola 2 - Expansión Importante (Prioridad 2)

**5 sitios complementarios**:

- **silep** - Base de datos legislativa histórica
- **ait** - Impugnación tributaria
- **aps** - Pensiones y seguros
- **att** - Telecomunicaciones y transportes
- **contraloria** - Control fiscal

### Ola 3+ - Complementarios (Prioridad 3)

**4+ sitios** adicionales:

- **lexivox** - Compendio no oficial (validación cruzada)
- **anb** - Aduana Nacional
- **Gacetas departamentales** (9 departamentos)
- **Municipios principales** (La Paz, Santa Cruz, Cochabamba, etc.)

---

## Cómo Usar el Catálogo

### Listar todos los sitios

```bash
python main.py list
```

Muestra todos los sitios con su estado, prioridad y estadísticas.

### Ver información detallada de un sitio

```bash
python main.py info gaceta_oficial
```

Muestra todos los campos del sitio específico.

### Filtrar por prioridad

```bash
python main.py list --prioridad 1
```

Muestra solo sitios de Ola 1 (prioridad 1).

### Filtrar por estado

```bash
python main.py list --estado implementado
```

Muestra solo sitios que ya tienen scraper implementado.

---

## Cómo Agregar un Nuevo Sitio

### Paso 1: Investigar el sitio

1. Identificar la URL base y URLs de búsqueda/listado
2. Determinar el formato de documentos (PDF, HTML)
3. Verificar si requiere Selenium o login
4. Analizar la estructura legal de los documentos

### Paso 2: Agregar entrada al catálogo

Edita `config/sites_catalog.yaml` y agrega una nueva entrada siguiendo este template:

```yaml
- site_id: "nuevo_sitio"
  nombre: "Nombre Completo del Sitio"
  nivel: "nacional"  # o departamental, municipal
  tipo_fuente: "normativa"  # o jurisprudencia, regulador
  prioridad: 2
  estado_scraper: "pendiente"

  # URLs
  url_base: "https://ejemplo.gob.bo"
  url_busqueda: "https://ejemplo.gob.bo/buscar"
  url_listado: null

  # Características técnicas
  formato_documento: "pdf"
  requiere_selenium: false
  requiere_login: false
  tiene_api: false

  # Estructura legal
  estructura_texto: "articulos"
  tipos_documentos:
    - "resolucion"
    - "circular"

  # Metadatos
  frecuencia_actualizacion: "semanal"
  ultima_actualizacion: null
  documentos_totales: 0
  articulos_totales: 0

  notas: "Descripción y observaciones técnicas"
```

### Paso 3: Implementar el scraper

1. Crear archivo `scraper/sites/nuevo_sitio.py`
2. Implementar función `scrape_nuevo_sitio()`
3. Agregar al registry de scrapers en `scraper/__init__.py`
4. Actualizar `estado_scraper` a `"implementado"`

### Paso 4: Probar

```bash
python main.py scrape nuevo_sitio --limit 5
```

---

## Mantenimiento del Catálogo

### Actualización de URLs

Si una URL cambia:

1. Actualizar el campo correspondiente en el YAML
2. Probar el scraper: `python main.py scrape <site_id> --limit 1`
3. Verificar que funcione correctamente

### Actualización de metadatos

Los campos `ultima_actualizacion`, `documentos_totales` y `articulos_totales` se actualizan **automáticamente** por el sistema durante el scraping.

### Deshabilitar un sitio temporalmente

Cambiar `estado_scraper` a `"deshabilitado"`:

```yaml
estado_scraper: "deshabilitado"
notas: "Sitio temporalmente inaccesible - mantenimiento gubernamental"
```

---

## Buenas Prácticas

### Naming Convention

- `site_id`: siempre en **snake_case**, sin espacios
- Ejemplos buenos: `gaceta_oficial`, `tsj_genesis`, `ait`
- Ejemplos malos: `Gaceta-Oficial`, `TSJ Genesis`, `a.i.t`

### Prioridades

- **Prioridad 1**: Solo sitios absolutamente críticos para el MVP
- **Prioridad 2**: Sitios importantes pero no bloqueantes
- **Prioridad 3**: Complementarios, nice-to-have

### Estados

- **pendiente**: Sitio catalogado pero sin implementación
- **en_progreso**: Scraper en desarrollo activo
- **implementado**: Scraper funcional y probado
- **deshabilitado**: Temporalmente desactivado (mantenimiento, errores, etc.)

### Notas

Siempre incluir en `notas`:
- Particularidades técnicas del sitio
- Cambios históricos de URL
- Limitaciones conocidas
- Recomendaciones de scraping

---

## Estructura de Texto Legal

### Valores comunes:

| Valor | Descripción | Usado en |
|-------|-------------|----------|
| `articulos` | Documentos divididos en artículos numerados | Leyes, decretos, resoluciones |
| `sentencia_vistos_fundamentos_por_tanto` | Sentencias judiciales clásicas | TSJ, tribunales ordinarios |
| `sentencia_constitucional` | Sentencias con estructura TCP | TCP |
| `resolucion_administrativa` | Resoluciones administrativas | AIT, reguladores |

### Agregar nuevas estructuras

Si encuentras una estructura nueva:

1. Documentarla aquí
2. Implementar parser en `scraper/parsers/<estructura>.py`
3. Agregar tests en `tests/test_parsers.py`

---

## Troubleshooting

### Error: "Site ID not found"

El `site_id` no existe en el catálogo. Verifica el spelling o agrégalo al YAML.

### Error: "Scraper not implemented"

El sitio está en el catálogo pero no tiene scraper. Verifica `estado_scraper`.

### URLs no funcionan

1. Verificar que la URL sigue activa (puede haber cambiado)
2. Verificar si ahora requiere Selenium o login
3. Actualizar el catálogo con la información correcta

---

## Contacto y Contribuciones

Para agregar nuevos sitios o reportar problemas:

1. Verificar que el sitio sea **oficial** (.gob.bo)
2. Investigar completamente antes de agregar
3. Seguir el template de entrada del catálogo
4. Documentar particularidades en `notas`

---

**Última actualización**: 2025-01-18
**Versión del catálogo**: 1.0.0
**Sitios catalogados**: 16
**Sitios implementados**: 0 (en desarrollo)
