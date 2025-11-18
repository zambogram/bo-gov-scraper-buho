# 🎯 GUÍA COMPLETA: Scraping Masivo de 30+ Sitios con Metadata Extendida

**Sistema Completo de Scraping → Metadata → Exportación → Análisis Continuo**

---

## 📋 Tabla de Contenidos

1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Configuración de Sitios (30+)](#configuración-de-sitios-30)
4. [Scraping Histórico Completo](#scraping-histórico-completo)
5. [Sistema de Metadata Extendida](#sistema-de-metadata-extendida)
6. [Exportación y Registro](#exportación-y-registro)
7. [Análisis Continuo de Nuevos Documentos](#análisis-continuo-de-nuevos-documentos)
8. [Monitoreo y Métricas](#monitoreo-y-métricas)

---

## 🎯 Visión General del Sistema

### Capacidades Completas

El sistema BÚHO ahora incluye:

✅ **Pipeline Extendido**
```
Sitio Web → PDF → Texto → Artículos → Metadata Extendida → Exportación → Registro Histórico
```

✅ **Metadata Automática**
- Número de norma
- Tipo de norma (Ley, DS, Resolución, etc.)
- Área del derecho (constitucional, penal, tributario, etc.)
- Jerarquía normativa (1-99)
- Estado de vigencia
- Entidad emisora
- Normas modificadas/derogadas
- Palabras clave

✅ **Exportación Simultánea**
- CSV de documentos
- CSV de artículos
- Registro histórico (JSONL)
- Reportes por sesión

✅ **Tracking Histórico**
- Progreso por sitio
- Estadísticas globales
- Historial de sesiones

---

## 🚀 Preparación del Entorno

### Paso 1: Instalación Base

```bash
# 1. Clonar (si no está clonado)
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar dependencias adicionales para OCR (opcional pero recomendado)
# En Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-spa
pip install pytesseract pdf2image

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env según necesidades
```

### Paso 2: Verificar Instalación

```bash
# Verificar que el sistema está operativo
python main.py listar

# Debe mostrar los 5 sitios activos
```

---

## 📝 Configuración de Sitios (30+)

### Agregar Nuevos Sitios al Catálogo

Editar `config/sites_catalog.yaml` y agregar sitios adicionales:

```yaml
sites:
  # ... sitios existentes ...

  ministerio_trabajo:
    id: ministerio_trabajo
    nombre: "Ministerio de Trabajo, Empleo y Previsión Social"
    tipo: "Ministerio"
    categoria: "Laboral"
    url_base: "https://www.mintrabajo.gob.bo"
    url_search: "https://www.mintrabajo.gob.bo/normativa"
    prioridad: 2
    ola: 2
    activo: true
    metadatos:
      tipo_documentos:
        - "Resolución Ministerial"
        - "Decreto Ejecutivo"
      fecha_inicio: "2000-01-01"
      idiomas: ["es"]
      formato_principal: "PDF"
      requiere_ocr: false
    scraper:
      tipo: "static"
      paginacion: true
      items_por_pagina: 50
      delay_entre_requests: 2

  tribunal_agroambiental:
    id: tribunal_agroambiental
    nombre: "Tribunal Agroambiental"
    tipo: "Tribunal"
    categoria: "Ambiental"
    url_base: "https://www.agroambiental.gob.bo"
    url_search: "https://www.agroambiental.gob.bo/jurisprudencia"
    prioridad: 2
    ola: 3
    activo: true
    metadatos:
      tipo_documentos:
        - "Sentencia Agroambiental"
        - "Resolución"
      fecha_inicio: "2014-01-01"
      idiomas: ["es"]
      formato_principal: "PDF"
      requiere_ocr: true
    scraper:
      tipo: "dynamic"
      paginacion: true
      items_por_pagina: 20
      delay_entre_requests: 3

  # Agregar más sitios siguiendo el mismo patrón...
  # Total objetivo: 30+ sitios
```

### Crear Scrapers para Nuevos Sitios

Para cada nuevo sitio, crear un scraper en `scraper/sites/`:

**Ejemplo: `scraper/sites/ministerio_trabajo_scraper.py`**

```python
"""
Scraper para Ministerio de Trabajo
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MinisterioTrabajoScraper(BaseScraper):
    """Scraper para Ministerio de Trabajo"""

    def __init__(self):
        super().__init__('ministerio_trabajo')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(self, limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Listar documentos del Ministerio de Trabajo

        IMPLEMENTAR LÓGICA REAL DE SCRAPING AQUÍ
        Por ahora, datos de ejemplo
        """
        # TODO: Implementar scraping real del sitio
        documentos_ejemplo = [
            {
                'id_documento': 'mteps_rm_0001_2024',
                'tipo_documento': 'Resolución Ministerial',
                'numero_norma': '001/2024',
                'fecha': '2024-01-10',
                'titulo': 'RM 001/2024 - Salario Mínimo',
                'url': f'{self.config.url_base}/normativa/rm-001-2024.pdf',
                'sumilla': 'Incremento del salario mínimo nacional'
            }
        ]

        if limite:
            documentos_ejemplo = documentos_ejemplo[:limite]

        return documentos_ejemplo

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """Descargar PDF"""
        # TODO: Implementar descarga real
        # Por ahora, usar método base
        return self._download_file(url, ruta_destino)
```

**Registrar el nuevo scraper en `scraper/sites/__init__.py`:**

```python
from .ministerio_trabajo_scraper import MinisterioTrabajoScraper

SCRAPERS = {
    # ... scrapers existentes ...
    'ministerio_trabajo': MinisterioTrabajoScraper,
}
```

---

## 🎬 Scraping Histórico Completo

### Estrategia para 30+ Sitios

#### Opción 1: Scraping Secuencial (Recomendado para Primera Vez)

```bash
# Ejecutar sitios en orden de prioridad
# Prioridad 1 (más importantes)
python main.py scrape tcp --mode full --limit 100 --save-txt --save-json
python main.py scrape tsj --mode full --limit 100 --save-txt --save-json
python main.py scrape gaceta_oficial --mode full --limit 500 --save-txt --save-json

# Prioridad 2
python main.py scrape asfi --mode full --limit 200 --save-txt --save-json
python main.py scrape sin --mode full --limit 200 --save-txt --save-json
python main.py scrape contraloria --mode full --limit 100 --save-txt --save-json

# Prioridad 3 y más...
# Continuar con todos los sitios
```

#### Opción 2: Scraping Masivo (Todos los Sitios)

```bash
# Procesar todos los sitios activos de una vez
# Límite conservador para primera pasada
python main.py scrape all --mode full --limit 50 --save-txt --save-json

# Para scraping masivo sin límite (CUIDADO: puede tomar días)
python main.py scrape all --mode full --save-txt --save-json
```

#### Opción 3: Script Automatizado

Crear `scripts/scrape_historico_completo.sh`:

```bash
#!/bin/bash
#  Script para scraping histórico completo de todos los sitios

SITIOS=(
  "tcp"
  "tsj"
  "asfi"
  "sin"
  "contraloria"
  "gaceta_oficial"
  "ministerio_trabajo"
  "tribunal_agroambiental"
  # ... agregar los 30+ sitios
)

LIMITE=100  # Límite por sitio

for sitio in "${SITIOS[@]}"; do
  echo "======================================"
  echo "Procesando: $sitio"
  echo "======================================"

  python main.py scrape "$sitio" --mode full --limit $LIMITE --save-txt --save-json

  # Pausa entre sitios para no sobrecargar
  sleep 30
done

echo "======================================"
echo "Scraping histórico completado"
echo "======================================"

# Mostrar estadísticas
python main.py stats
```

Ejecutar:

```bash
chmod +x scripts/scrape_historico_completo.sh
./scripts/scrape_historico_completo.sh
```

---

## 🏷️ Sistema de Metadata Extendida

### Metadata Automática Extraída

Para cada documento, el sistema extrae automáticamente:

1. **Identificación**
   - `numero_norma`: "1234", "456/2024", etc.
   - `tipo_norma`: "Ley", "Decreto Supremo", "Resolución", etc.
   - `jerarquia`: 1-99 (1=CPE, 2=Ley, 3=DS, etc.)

2. **Clasificación**
   - `area_principal`: "constitucional", "penal", "tributario", etc.
   - `areas_derecho`: Lista de áreas detectadas (top 3)

3. **Estado**
   - `estado_vigencia`: "vigente", "modificada", "derogada"
   - `entidad_emisora`: "Asamblea Legislativa", "Presidencia", etc.

4. **Relaciones**
   - `modifica_normas`: Lista de normas que modifica
   - `deroga_normas`: Lista de normas que deroga

5. **Contenido**
   - `palabras_clave`: Lista de palabras clave del documento
   - `sumilla_generada`: Sumilla automática si no existe
   - `estadisticas`: Total caracteres, palabras, páginas estimadas

### Consultar Metadata

La metadata se guarda en:

1. **JSON del documento** (`data/normalized/{site}/json/{id}.json`)
2. **CSV de exportación** (`exports/{site}/{timestamp}/documentos.csv`)
3. **Registro histórico** (`exports/{site}/{timestamp}/registro_historico.jsonl`)

---

## 📤 Exportación y Registro

### Archivos Generados por Sesión

Cada sesión de scraping genera:

```
exports/
└── {site_id}/
    └── {timestamp}/
        ├── documentos.csv          # Tabla de documentos
        ├── articulos.csv           # Tabla de artículos
        ├── registro_historico.jsonl # Log detallado (JSONL)
        └── reporte_scraping.json   # Reporte de la sesión
```

### Formato de Exportaciones

**documentos.csv:**
```csv
id_documento,site,tipo_documento,numero_norma,fecha,titulo,area_principal,areas_derecho,jerarquia,estado_vigencia,total_articulos,...
tcp_sc_0001_2024,tcp,Sentencia Constitucional,0001/2024,2024-01-15,SC 0001/2024,constitucional,"constitucional,procesal",10,vigente,25,...
```

**articulos.csv:**
```csv
id_articulo,id_documento,numero,titulo,tipo_unidad,contenido_preview
tcp_sc_0001_2024_art_1,tcp_sc_0001_2024,1,DEL OBJETO,articulo,El presente decreto tiene por objeto...
```

**registro_historico.jsonl:** (una línea JSON por documento)
```json
{"timestamp":"2024-11-18T10:30:00","id_documento":"tcp_sc_0001_2024","area_principal":"constitucional","jerarquia":10,"total_articulos":25,"metadata_completa":{...}}
```

### Tracking Histórico Global

El archivo `data/tracking_historico.json` mantiene registro de:

```json
{
  "inicio_proyecto": "2024-11-18T09:00:00",
  "sitios": {
    "tcp": {
      "primera_sesion": "2024-11-18T09:05:00",
      "ultima_sesion": "2024-11-18T10:30:00",
      "total_sesiones": 5,
      "total_documentos": 150,
      "total_articulos": 3750,
      "sesiones": [...]
    }
  },
  "estadisticas_globales": {
    "total_documentos": 15000,
    "total_articulos": 375000,
    "total_sesiones": 50
  }
}
```

---

## 🔄 Análisis Continuo de Nuevos Documentos

### Configurar Scraping Periódico

Una vez completado el scraping histórico, configurar análisis continuo:

**1. Script de Delta Update (`scripts/scrape_delta_daily.sh`):**

```bash
#!/bin/bash
# Script para delta updates diarios

SITIOS=(
  "tcp" "tsj" "asfi" "sin" "contraloria" "gaceta_oficial"
  # ... todos los sitios
)

for sitio in "${SITIOS[@]}"; do
  echo "Actualizando: $sitio"
  python main.py scrape "$sitio" --mode delta --limit 50 --save-txt --save-json
done

echo "Delta update completado"
```

**2. Configurar Cron Job (Linux/Mac):**

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar diariamente a las 2 AM
0 2 * * * /ruta/a/bo-gov-scraper-buho/scripts/scrape_delta_daily.sh >> /var/log/buho_scraper.log 2>&1
```

**3. Configurar Tarea Programada (Windows):**

Usar Task Scheduler con:
- Trigger: Diario a las 2 AM
- Action: Ejecutar `python main.py scrape all --mode delta --limit 50`

### Ciclo Completo de Nuevos Documentos

Cada nuevo documento pasa por:

1. ✅ **Detección** (modo delta)
2. ✅ **Descarga PDF**
3. ✅ **Extracción de texto** (con OCR si necesario)
4. ✅ **Parsing en artículos**
5. ✅ **Metadata extendida** (área, tipo, jerarquía, etc.)
6. ✅ **Guardado** (TXT, JSON)
7. ✅ **Exportación** (CSV, JSONL)
8. ✅ **Registro histórico**
9. ✅ **Índice actualizado**

---

## 📊 Monitoreo y Métricas

### Ver Estadísticas Globales

```bash
# Estadísticas de todos los sitios
python main.py stats

# Ver tracking histórico
cat data/tracking_historico.json | jq '.'

# Ver progreso de un sitio específico
cat data/index/tcp/index.json | jq '.total_documentos'
```

### Análisis de Exportaciones

**Documentos por área del derecho:**

```bash
# Contar documentos por área
cat exports/tcp/*/documentos.csv | cut -d',' -f7 | sort | uniq -c | sort -rn

# Ejemplo de salida:
#  450 constitucional
#  320 civil
#  180 penal
#  ...
```

**Documentos por jerarquía:**

```bash
# Ver distribución de jerarquías
cat exports/tcp/*/documentos.csv | cut -d',' -f9 | sort | uniq -c

# 10 = Sentencias Constitucionales
# 2 = Leyes
# etc.
```

### Dashboards (Futuro)

El sistema está preparado para integrar dashboards usando:
- Streamlit (ya implementado básico)
- Grafana + InfluxDB
- PowerBI / Tableau (importar CSVs)

---

## ✅ Checklist de Implementación

### Fase 1: Configuración (Semana 1)

- [ ] Instalar dependencias completas
- [ ] Configurar 30+ sitios en `sites_catalog.yaml`
- [ ] Crear scrapers para cada sitio nuevo
- [ ] Probar scraping de 1-2 documentos por sitio

### Fase 2: Scraping Histórico (Semanas 2-4)

- [ ] Ejecutar scraping histórico sitio por sitio
- [ ] Verificar metadata extendida
- [ ] Revisar exportaciones CSV/JSONL
- [ ] Validar tracking histórico

### Fase 3: Análisis Continuo (Semana 5+)

- [ ] Configurar delta updates automáticos
- [ ] Implementar monitoreo de errores
- [ ] Crear reportes semanales
- [ ] Optimizar scrapers lentos

---

## 🚀 Comandos Rápidos de Referencia

```bash
# Listar sitios
python main.py listar

# Scraping histórico completo de un sitio
python main.py scrape tcp --mode full --limit 100 --save-txt --save-json

# Delta update de todos los sitios
python main.py scrape all --mode delta --limit 50

# Estadísticas
python main.py stats

# Ver tracking
cat data/tracking_historico.json | jq '.estadisticas_globales'

# Ver exportaciones de último scraping
ls -lh exports/tcp/

# Contar documentos procesados
find data/normalized/*/json -name "*.json" | wc -l
```

---

## 📞 Troubleshooting

**Problema: OCR muy lento**
```bash
# Solución: Desactivar OCR para sitios con PDFs digitales
# En sites_catalog.yaml, configurar:
metadatos:
  requiere_ocr: false
```

**Problema: Memoria insuficiente**
```bash
# Solución: Procesar por lotes pequeños
python main.py scrape tcp --mode full --limit 20
# Repetir hasta completar
```

**Problema: Sitio web bloquea scraping**
```bash
# Solución: Aumentar delay
# En sites_catalog.yaml:
scraper:
  delay_entre_requests: 5  # Aumentar a 5 segundos
```

---

**Última actualización:** 2025-11-18
**Versión del sistema:** 2.0 (Metadata Extendida + Exportación)
