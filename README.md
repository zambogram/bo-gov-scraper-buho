# 🦉 BÚHO - Sistema de Scraping Gubernamental de Bolivia

**FASE 9: Sites Reales + Parsers Avanzados + Delta-Update**

Sistema completo de scraping, parsing avanzado y actualización incremental de documentos legales de instituciones gubernamentales bolivianas.

## 🌟 Características

- ✅ **5 Scrapers de sitios reales** del Estado Boliviano
- ✅ **Parsing avanzado de PDFs** con detección automática de OCR
- ✅ **Sistema de actualización incremental** (Delta-Update)
- ✅ **CLI completo** con múltiples comandos
- ✅ **Arquitectura multisite** extensible
- ✅ **Gestión de índices** con hash MD5
- ✅ **Estadísticas detalladas** por sitio

## 🏛️ Sitios Soportados

| Código | Institución | Documentos |
|--------|-------------|------------|
| `tcp` | Tribunal Constitucional Plurinacional | SC, SCP, SCA |
| `tsj` | Tribunal Supremo de Justicia | Autos Supremos |
| `contraloria` | Contraloría General del Estado | Resoluciones |
| `asfi` | ASFI | Resoluciones, Circulares, Comunicados |
| `sin` | Servicio de Impuestos Nacionales | RND, RA, RM |

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho

# Instalar dependencias
pip install -r requirements.txt

# Opcional: Instalar Tesseract para OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Verificar instalación
python main.py --version
```

## 📖 Uso

### Comandos Básicos

```bash
# Listar sitios disponibles
python main.py listar

# Scraping de un sitio específico
python main.py scrape tcp

# Actualizar todos los sitios
python main.py actualizar-todos

# Ver estadísticas
python main.py estadisticas tcp

# Resumen general
python main.py resumen
```

### Opciones Avanzadas

```bash
# Solo documentos nuevos
python main.py scrape tcp --solo-nuevos

# Solo documentos modificados
python main.py scrape tsj --solo-modificados

# Limitar cantidad
python main.py scrape asfi --limit 10

# Actualizar sitios específicos
python main.py actualizar-todos --sitios tcp,tsj,asfi

# Limpiar índice
python main.py limpiar-index tcp
```

## 📊 Sistema Delta-Update

El sistema mantiene un índice incremental que:

- ✅ Evita descargas duplicadas
- ✅ Detecta documentos nuevos automáticamente
- ✅ Identifica modificaciones por hash MD5
- ✅ Mantiene estadísticas históricas
- ✅ Optimiza uso de recursos

### Estructura de Salidas

```
outputs/
├── tcp/
│   ├── index.json          # Índice incremental
│   ├── pdfs/               # PDFs descargados
│   │   ├── SCP_0001_2024.pdf
│   │   └── ...
│   └── json/               # Documentos parseados
│       ├── SCP_0001_2024.json
│       └── ...
├── tsj/
├── contraloria/
├── asfi/
└── sin/
```

## 🔧 Arquitectura

```
scraper/
├── core/                   # Módulos base
│   ├── base_scraper.py    # Clase abstracta
│   ├── pdf_parser.py      # Parser con OCR
│   ├── delta_manager.py   # Delta-Update
│   └── utils.py           # Utilidades
│
└── sites/                  # Scrapers específicos
    ├── tcp_scraper.py
    ├── tsj_scraper.py
    ├── contraloria_scraper.py
    ├── asfi_scraper.py
    └── sin_scraper.py
```

## 📄 Parsing de PDFs

El sistema parsea automáticamente las secciones específicas de cada tipo de documento:

### Tribunal Constitucional (TCP)
- VISTOS
- ANTECEDENTES
- PROBLEMÁTICA
- CONSIDERANDO
- FUNDAMENTOS JURÍDICOS
- POR TANTO

### Tribunal Supremo (TSJ)
- RESULTANDOS
- CONSIDERANDOS
- PARTE RESOLUTIVA

### Otros Sitios
- Estructura por artículos
- Numerales romanos
- Metadata específica

## 🔌 API Programática

```python
from scraper import get_scraper

# Obtener scraper
scraper = get_scraper('tcp')

# Ejecutar scraping
stats = scraper.run(only_new=True, limit=10)

# Resultados
print(f"Nuevos: {stats['total_new']}")
print(f"Modificados: {stats['total_modified']}")
```

## 📚 Documentación

Ver documentación completa en:
- [FASE9_SITES_REALES.md](docs/FASE9_SITES_REALES.md)

## 🧪 Ejemplos

### Scraping Completo

```bash
# Primera vez: scraping completo
python main.py actualizar-todos --limit 50

# Actualizaciones diarias: solo nuevos
python main.py actualizar-todos --solo-nuevos

# Verificar cambios: solo modificados
python main.py actualizar-todos --solo-modificados
```

### Uso Programático

```python
from scraper import TCPScraper

# Crear scraper
tcp = TCPScraper()

# Ejecutar
stats = tcp.run(only_new=True)

# Acceder al índice
docs = tcp.delta_manager.get_all_document_ids()
print(f"Total documentos: {len(docs)}")
```

## 🐛 Troubleshooting

### Error de OCR
```bash
# Verificar Tesseract
tesseract --version
tesseract --list-langs | grep spa
```

### Documentos duplicados
```bash
# Limpiar índice
python main.py limpiar-index tcp

# Usar flags apropiados
python main.py scrape tcp --solo-nuevos
```

## 🎯 Roadmap

- [ ] Soporte para más sitios gubernamentales
- [ ] API REST
- [ ] Dashboard web
- [ ] Búsqueda full-text
- [ ] Análisis con NLP
- [ ] Notificaciones automáticas
- [ ] Exportación a múltiples formatos

## 📊 Estadísticas del Proyecto

- **5 Sitios** gubernamentales
- **3 Tipos** de parsers especializados
- **7+ Formatos** de documentos soportados
- **100% Python** con arquitectura modular

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nuevo-sitio`)
3. Commit cambios (`git commit -am 'Agregar nuevo sitio'`)
4. Push a la rama (`git push origin feature/nuevo-sitio`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto es parte del sistema BÚHO de scraping gubernamental.

## 👥 Autor

Proyecto BÚHO - Sistema de Scraping Gubernamental de Bolivia

---

**Versión 9.0.0** - FASE 9 Completa
Enero 2025
