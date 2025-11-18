# 🦉 BO Gov Scraper Buho

Motor multi-sitio para scraping de sitios gubernamentales de Bolivia.

## 🚀 Características

- **Arquitectura modular**: Agrega nuevos sitios sin modificar el core
- **Configuración centralizada**: Todos los sitios en `config/sites.json`
- **Múltiples estrategias de paginación**: Scroll infinito, paginación numérica, botones
- **Soporte Selenium**: Para sitios con JavaScript dinámico
- **Sistema de logs completo**: Seguimiento detallado de cada ejecución
- **Extracción inteligente**: PDFs, texto, artículos con regex
- **Rate limiting**: Respeto automático de límites de velocidad
- **Salidas múltiples**: CSV, JSON y archivos descargados

## 🏛️ Sitios Soportados

- ✅ **Gaceta Oficial de Bolivia** - Implementado
- 🔜 **Hermes** (Contratos Públicos) - Configurado
- 🔜 **ICOES** (Comercio Exterior) - Configurado
- 🔜 **Derechos Reales** - Configurado
- 🔜 **SIN** (Impuestos Nacionales) - Configurado

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/zambogram/bo-gov-scraper-buho.git
cd bo-gov-scraper-buho

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso Rápido

### Listar sitios disponibles

```bash
python main.py --listar-sitios
```

### Scraping básico

```bash
# Obtener 10 documentos de la Gaceta
python main.py --sitio gaceta --limite 10

# Obtener todos los documentos disponibles
python main.py --sitio gaceta

# Reprocesar documentos existentes
python main.py --sitio gaceta --limite 50 --reprocesar
```

## 📁 Estructura del Proyecto

```
bo-gov-scraper-buho/
├── config/
│   └── sites.json              # Configuración de todos los sitios
├── scraper/
│   ├── base_site.py            # Clase base abstracta
│   └── sites/
│       └── gaceta.py           # Implementación Gaceta
├── logs/                       # Logs de ejecución
├── outputs/                    # Archivos descargados y datos
│   └── gaceta/
│       ├── pdfs/
│       ├── csv/
│       └── json/
├── main.py                     # CLI principal
├── requirements.txt
└── FASE7_MULTISITIO.md        # Documentación completa
```

## 📖 Documentación

Para documentación completa sobre cómo agregar nuevos sitios, extender el sistema y mejores prácticas, consulta:

**[FASE7_MULTISITIO.md](FASE7_MULTISITIO.md)**

Incluye:
- Arquitectura del sistema
- Guía paso a paso para agregar sitios
- Ejemplos completos de código
- Manejo de errores
- Mejores prácticas

## 🔧 Agregar un Nuevo Sitio (Resumen)

1. **Configurar** en `config/sites.json`:
```json
{
  "mi_sitio": {
    "id_sitio": "mi_sitio",
    "nombre": "Mi Sitio",
    "url_listado": "https://...",
    "selectores_css": { ... },
    ...
  }
}
```

2. **Crear scraper** en `scraper/sites/mi_sitio.py`:
```python
from ..base_site import BaseSiteScraper

class MiSitioScraper(BaseSiteScraper):
    def __init__(self):
        super().__init__(site_id='mi_sitio')

    def fetch_listing(self, limite=None):
        # Implementar...

    # ... otros métodos
```

3. **Registrar** en `main.py`:
```python
scrapers_map = {
    'gaceta': GacetaScraper,
    'mi_sitio': MiSitioScraper,  # ← Agregar aquí
}
```

4. **Probar**:
```bash
python main.py --sitio mi_sitio --limite 5
```

## 📊 Salidas

El sistema genera:

- **PDFs descargados**: `outputs/{sitio}/pdfs/`
- **Datos CSV**: `outputs/{sitio}/csv/`
- **Datos JSON**: `outputs/{sitio}/json/`
- **Logs detallados**: `logs/{sitio}_{fecha}.log`

## 🛠️ Requisitos

- Python 3.8+
- Google Chrome (para Selenium)
- Dependencias en `requirements.txt`

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/nuevo-sitio`)
3. Commit tus cambios (`git commit -m 'Agregar nuevo sitio X'`)
4. Push a la branch (`git push origin feature/nuevo-sitio`)
5. Abre un Pull Request

## 📧 Contacto

Para preguntas, sugerencias o reportar problemas, abre un issue en GitHub.

---

**Hecho con ❤️ en Bolivia 🇧🇴**
