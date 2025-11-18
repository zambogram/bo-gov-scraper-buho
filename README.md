# 🦉 BÚHO - Bolivian Government Document Scraper

Scraper completo de páginas del Estado boliviano con OCR, metadatos, parsing legal y sincronización con Supabase.

## 🌟 Características

### FASE 10 - Implementación Completa

- ✅ **Scrapers Múltiples**: TCP, TSJ, ASFI, SIN, Contraloría
- ✅ **Parsing Legal Automático**: Extracción de artículos y estructura legal
- ✅ **Delta Update**: Detección de documentos nuevos y modificados por MD5
- ✅ **Interfaz Web Streamlit**: UI completa para gestión y visualización
- ✅ **Exportación JSONL**: Exportación automática de documentos y artículos
- ✅ **Sincronización Supabase**: Sync bidireccional con base de datos
- ✅ **Scheduler Automático**: Scraping diario automatizado
- ✅ **Logs Detallados**: Sistema completo de logging

## 🏗️ Arquitectura del Proyecto

```
bo-gov-scraper-buho/
├── app/
│   └── streamlit_app.py          # Interfaz web Streamlit
├── scraper/
│   ├── base_scraper.py           # Clase base para scrapers
│   ├── tcp_scraper.py            # Scraper TCP
│   ├── tsj_scraper.py            # Scraper TSJ
│   ├── asfi_scraper.py           # Scraper ASFI
│   ├── sin_scraper.py            # Scraper SIN
│   ├── contraloria_scraper.py    # Scraper Contraloría
│   ├── parser.py                 # Parser legal
│   └── metadata.py               # Extractor de metadatos
├── sync/
│   └── supabase_sync.py          # Sincronización Supabase
├── scheduler/
│   └── run_daily.py              # Scheduler automático
├── data/
│   ├── index/                    # Índices JSON
│   └── articles/                 # Artículos parseados
├── exports/                      # Exportaciones JSONL
├── logs/                         # Logs de operaciones
├── docs/                         # Documentación
├── main.py                       # CLI principal
└── requirements.txt              # Dependencias
```

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Supabase (Opcional)

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de Supabase:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## 📖 Uso

### CLI - Interfaz de Línea de Comandos

#### Listar todos los sitios disponibles

```bash
python main.py listar
```

#### Scrapear un sitio específico

```bash
# Scrapear TCP (límite de 10 documentos)
python main.py scrape tcp --limit 10

# Scrapear solo documentos nuevos
python main.py scrape tcp --limit 20 --solo-nuevos
```

#### Actualizar todos los sitios

```bash
# Actualizar todos (límite de 10 por sitio)
python main.py actualizar-todos --limit 10

# Solo nuevos documentos
python main.py actualizar-todos --limit 10 --solo-nuevos
```

#### Exportar a JSONL

```bash
# Exportar un sitio
python main.py export-jsonl tcp

# Exportar todos
python main.py export-jsonl all
```

#### Ver estadísticas

```bash
python main.py stats tcp
```

### 🖥️ Interfaz Web Streamlit

#### Lanzar la UI

```bash
# Opción 1: Desde el CLI
python main.py ui

# Opción 2: Directamente con Streamlit
streamlit run app/streamlit_app.py
```

La interfaz estará disponible en `http://localhost:8501`

#### Funcionalidades de la UI

**Sidebar:**
- Lista de sitios con estadísticas en tiempo real
- Selector de sitio
- Control de límite de scraping
- Botones de acción:
  - Scrapear sitio individual
  - Scrapear todos los sitios
  - Exportar JSONL (individual/todos)
  - Sincronizar con Supabase (nuevos/todos)

**Panel Central:**
- **Pestaña Documentos**: Tabla con todos los documentos del índice
- **Pestaña Artículos**: Tabla con artículos parseados
- **Pestaña Estadísticas**: Gráficas y análisis
  - Volumen por sitio (barras)
  - Distribución de documentos (pie)
  - Comparación entre sitios
- **Pestaña Logs**: Visualización de logs de sync

### ☁️ Sincronización con Supabase

#### Crear las tablas en Supabase

Ejecuta este SQL en tu proyecto Supabase:

```sql
-- Tabla de documentos
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  site TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  content TEXT,
  md5 TEXT UNIQUE,
  metadata JSONB,
  scraped_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

-- Tabla de artículos
CREATE TABLE articles (
  id TEXT PRIMARY KEY,
  document_id TEXT REFERENCES documents(id),
  site TEXT NOT NULL,
  article_number INTEGER,
  content TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

-- Índices
CREATE INDEX idx_documents_site ON documents(site);
CREATE INDEX idx_documents_md5 ON documents(md5);
CREATE INDEX idx_articles_document ON articles(document_id);
CREATE INDEX idx_articles_site ON articles(site);
```

#### Sincronizar desde Python

```python
from sync.supabase_sync import (
    sync_documents_to_supabase,
    sync_articles_to_supabase,
    sync_all_sites
)

# Sincronizar un sitio (solo nuevos)
sync_documents_to_supabase('tcp', only_new=True)
sync_articles_to_supabase('tcp', only_new=True)

# Sincronizar todos los sitios
sync_all_sites(only_new=True)

# Sincronizar todo (incluyendo modificados)
sync_all_sites(only_new=False)
```

### ⏰ Scheduler Automático

#### Ejecutar scraping inmediato

```bash
python scheduler/run_daily.py --now
```

#### Ejecutar como daemon (scraping diario a las 2 AM)

```bash
python scheduler/run_daily.py --daemon
```

#### Configurar como servicio systemd (Linux)

Crea `/etc/systemd/system/buho-scraper.service`:

```ini
[Unit]
Description=BÚHO Daily Scraper
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bo-gov-scraper-buho
ExecStart=/path/to/venv/bin/python scheduler/run_daily.py --daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl enable buho-scraper
sudo systemctl start buho-scraper
sudo systemctl status buho-scraper
```

## 📊 Flujo de Datos

```
┌─────────────────┐
│   Web Scraping  │  ← TCP, TSJ, ASFI, SIN, Contraloría
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Delta Update   │  ← Detección MD5 (nuevo/modificado/sin cambios)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Index     │  ← data/index/{site}_index.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Legal Parser   │  ← Extracción de artículos
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JSON Articles   │  ← data/articles/{site}_articles.json
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│  JSONL Export   │   │ Supabase Sync    │
└─────────────────┘   └──────────────────┘
```

## 🎯 Sitios Soportados

| Sitio | Código | URL Base | Tipo de Documento |
|-------|--------|----------|-------------------|
| Tribunal Constitucional Plurinacional | `tcp` | tcpbolivia.bo | Sentencias Constitucionales |
| Tribunal Supremo de Justicia | `tsj` | tsj.bo | Autos Supremos |
| ASFI | `asfi` | asfi.gob.bo | Resoluciones Financieras |
| SIN | `sin` | impuestos.gob.bo | Resoluciones Normativas |
| Contraloría | `contraloria` | contraloria.gob.bo | Informes de Auditoría |

## 📝 Formato JSONL

### Documentos

```jsonl
{"id": "tcp-000001", "site": "tcp", "url": "...", "title": "...", "content": "...", "md5": "...", "metadata": {...}}
{"id": "tcp-000002", "site": "tcp", "url": "...", "title": "...", "content": "...", "md5": "...", "metadata": {...}}
```

### Artículos

```jsonl
{"id": "tcp-000001-art-001", "document_id": "tcp-000001", "site": "tcp", "article_number": 1, "content": "...", "metadata": {...}}
{"id": "tcp-000001-art-002", "document_id": "tcp-000001", "site": "tcp", "article_number": 2, "content": "...", "metadata": {...}}
```

## 🧪 Pruebas

```bash
# Test scraping
python main.py listar
python main.py scrape tcp --limit 2
python main.py scrape tsj --limit 2

# Test export
python main.py export-jsonl tcp

# Test UI
streamlit run app/streamlit_app.py

# Test scheduler
python scheduler/run_daily.py --now
```

## 📚 Documentación

- [FASE10_COMPLETO.md](docs/FASE10_COMPLETO.md) - Documentación técnica completa

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Ver archivo [LICENSE](LICENSE)

## 👤 Autor

Zambogram - bo-gov-scraper-buho

## 🙏 Agradecimientos

- Comunidad boliviana de datos abiertos
- Instituciones del Estado Plurinacional de Bolivia
- Contribuidores del proyecto

---

**🦉 BÚHO - Haciendo accesible la información pública boliviana**
