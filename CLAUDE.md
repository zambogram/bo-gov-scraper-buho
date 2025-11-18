# 🦉 BÚHO - Scraper del Estado Boliviano

## 📖 ¿QUÉ ES ESTE PROYECTO?

Este proyecto es un **scraper** (programa que descarga y procesa información de sitios web) diseñado para extraer documentos y datos de páginas gubernamentales de Bolivia. El objetivo es recopilar, organizar y procesar información pública de forma automática.

---

## 📂 ESTRUCTURA DEL PROYECTO

```
bo-gov-scraper-buho/
│
├── venv/                    ← Entorno virtual de Python (NO se sube a GitHub)
│   └── (librerías instaladas aquí)
│
├── app/                     ← Interfaz visual del proyecto
│   └── streamlit_app.py     ← Aplicación web para visualizar datos
│
├── scraper/                 ← Código principal del scraper
│   ├── __init__.py          ← Archivo que marca esta carpeta como módulo Python
│   └── metadata.py          ← Funciones para extraer metadatos de documentos
│
├── data/                    ← Datos descargados
│   └── README.md            ← Aquí se guardarán PDFs, imágenes, etc.
│
├── exports/                 ← Archivos exportados procesados
│   └── README.md            ← Aquí se guardarán Excel, CSV, etc.
│
├── main.py                  ← Punto de entrada principal del programa
├── requirements.txt         ← Lista de librerías necesarias
├── .gitignore               ← Archivos que Git ignorará
├── LICENSE                  ← Licencia del proyecto
└── README.md                ← Descripción general del proyecto

```

---

## 🎯 ¿PARA QUÉ SIRVE CADA CARPETA?

### 📁 **venv/** - Entorno Virtual
**¿Qué es?** Una "burbuja" aislada donde viven todas las librerías de Python que necesita este proyecto.

**¿Por qué existe?** Para que las librerías de este proyecto no interfieran con otros proyectos de Python en tu computadora. Es como tener un set de herramientas específicas solo para este trabajo.

**Importante:** Esta carpeta NO se sube a GitHub (está en `.gitignore`).

---

### 📁 **app/** - Aplicación Visual
**¿Qué es?** Aquí va el código de la interfaz web hecha con Streamlit.

**¿Para qué sirve?** Streamlit permite crear una página web interactiva donde puedes:
- Ver los datos que se han descargado
- Iniciar el proceso de scraping con botones
- Visualizar estadísticas y gráficos
- Exportar datos a Excel

**Ejemplo:** Piensa en esto como el "tablero de control" del proyecto.

---

### 📁 **scraper/** - Motor del Scraper
**¿Qué es?** El "cerebro" del proyecto. Aquí va todo el código que hace el trabajo de:
- Navegar por las páginas web
- Descargar documentos (PDFs, imágenes)
- Extraer texto usando OCR (reconocimiento óptico de caracteres)
- Organizar la información

**Archivos importantes:**
- `__init__.py`: Archivo especial que convierte la carpeta en un "módulo" de Python (permite importar código desde aquí)
- `metadata.py`: Funciones para extraer información como fecha, autor, título, etc. de los documentos

---

### 📁 **data/** - Datos Sin Procesar
**¿Qué es?** Almacén de todo lo que se descarga directamente de internet.

**¿Qué contiene?**
- PDFs gubernamentales
- Imágenes de documentos
- HTML de páginas web
- Archivos temporales

**Importante:** Esta carpeta crece con el tiempo y puede ocupar mucho espacio.

---

### 📁 **exports/** - Datos Procesados
**¿Qué es?** Aquí se guardan los resultados finales, ya procesados y organizados.

**¿Qué contiene?**
- Archivos Excel (.xlsx) con datos tabulados
- CSV con información extraída
- Reportes en PDF
- Bases de datos SQLite

**Diferencia con `data/`:**
- `data/` = lo que descargas (crudo, sin procesar)
- `exports/` = lo que produces (limpio, organizado, listo para usar)

---

## 🛠️ HERRAMIENTAS INSTALADAS

### **Web Scraping** (Descarga y navegación)
- **requests** → Descarga páginas web (como un navegador simple)
- **beautifulsoup4** → Lee y analiza HTML (estructura de páginas web)
- **lxml** → Procesa XML y HTML rápidamente
- **selenium** → Automatiza un navegador real (para páginas complejas con JavaScript)

### **OCR y Procesamiento de Imágenes** (Lectura de texto en imágenes)
- **pytesseract** → Lee texto de imágenes (OCR = Optical Character Recognition)
- **Pillow** → Edita y procesa imágenes
- **pdf2image** → Convierte PDFs a imágenes (para luego aplicar OCR)

### **Análisis de Datos**
- **pandas** → Organiza datos en tablas (como Excel pero en Python)
- **openpyxl** → Lee y escribe archivos Excel

### **Interfaz de Usuario**
- **streamlit** → Crea aplicaciones web interactivas sin saber HTML/CSS/JavaScript

### **Utilidades**
- **python-dotenv** → Lee variables de entorno (configuraciones secretas)
- **tqdm** → Muestra barras de progreso bonitas en la terminal

---

## 🚀 DESARROLLO POR FASES

### **FASE 1: Configuración Inicial** ✅ COMPLETADA
**Objetivo:** Preparar el entorno de trabajo.

**Tareas realizadas:**
- ✅ Crear entorno virtual (`venv/`)
- ✅ Instalar todas las librerías necesarias
- ✅ Verificar que todo funciona correctamente
- ✅ Documentar el proyecto (este archivo)

---

### **FASE 2: Primer Scraper Funcional** 🎯 SIGUIENTE PASO
**Objetivo:** Crear un scraper simple que funcione.

**Tareas pendientes:**
1. Identificar la primera página objetivo (ejemplo: gaceta oficial, ministerio específico)
2. Crear función básica de descarga con `requests`
3. Extraer enlaces a documentos con `beautifulsoup4`
4. Descargar PDFs encontrados
5. Guardar archivos en `data/` con nombres organizados
6. Crear log de actividad (registro de lo que se descargó)

**Entregable:** Un script que descargue 10 documentos de prueba.

---

### **FASE 3: OCR y Extracción de Texto**
**Objetivo:** Convertir PDFs e imágenes a texto legible.

**Tareas:**
1. Convertir PDFs a imágenes con `pdf2image`
2. Aplicar OCR con `pytesseract`
3. Limpiar texto extraído (quitar caracteres raros)
4. Guardar texto en archivos `.txt`
5. Crear función para detectar idioma (español)

**Entregable:** Textos extraídos de los 10 documentos de Fase 2.

---

### **FASE 4: Extracción de Metadatos**
**Objetivo:** Obtener información sobre cada documento.

**Tareas:**
1. Extraer fecha de publicación
2. Identificar entidad emisora (ministerio, secretaría, etc.)
3. Detectar tipo de documento (resolución, ley, decreto, etc.)
4. Extraer número de documento
5. Crear tabla con todos los metadatos

**Entregable:** Excel con columnas: Fecha | Entidad | Tipo | Número | Archivo

---

### **FASE 5: Interfaz Streamlit**
**Objetivo:** Crear una aplicación web para controlar el scraper.

**Tareas:**
1. Diseñar página principal con título y descripción
2. Botón "Iniciar Scraping"
3. Mostrar progreso en tiempo real
4. Tabla con documentos descargados
5. Botón para exportar a Excel
6. Gráficos de estadísticas (documentos por fecha, por entidad)

**Entregable:** Aplicación web funcional.

---

### **FASE 6: Automatización y Escalabilidad**
**Objetivo:** Hacer el scraper robusto y automático.

**Tareas:**
1. Manejo de errores (si una página no carga, continuar)
2. Sistema de reintentos automáticos
3. Guardar progreso (si se interrumpe, continuar donde quedó)
4. Scraping paralelo (varios documentos a la vez)
5. Programar ejecución automática diaria

**Entregable:** Scraper que corre solo, sin supervisión.

---

### **FASE 7: Búsqueda y Análisis**
**Objetivo:** Permitir buscar en todos los documentos.

**Tareas:**
1. Crear base de datos SQLite
2. Indexar todos los textos extraídos
3. Función de búsqueda por palabra clave
4. Búsqueda avanzada (por fecha, entidad, tipo)
5. Exportar resultados de búsqueda

**Entregable:** Buscador funcional en la app de Streamlit.

---

## ⚙️ CÓMO USAR ESTE PROYECTO

### **Activar el entorno virtual**
Cada vez que trabajes en el proyecto, primero debes "activar" el entorno virtual:

```bash
source venv/bin/activate
```

**¿Cómo sé que está activado?**
Verás `(venv)` al inicio de tu línea de comandos:
```
(venv) user@computer:~/bo-gov-scraper-buho$
```

### **Ejecutar el programa principal**
```bash
python main.py
```

### **Ejecutar la aplicación Streamlit**
```bash
streamlit run app/streamlit_app.py
```
Esto abrirá una página web en `http://localhost:8501`

### **Instalar nuevas librerías**
Si necesitas agregar una librería:
```bash
pip install nombre-libreria
pip freeze > requirements.txt  # Actualiza el archivo
```

### **Desactivar el entorno virtual**
Cuando termines de trabajar:
```bash
deactivate
```

---

## 📝 NOTAS IMPORTANTES

1. **NUNCA subas la carpeta `venv/` a GitHub** → Ya está en `.gitignore`
2. **NUNCA subas datos sensibles** → Contraseñas, tokens, claves van en `.env`
3. **Documentos descargados pueden ser grandes** → La carpeta `data/` puede crecer mucho
4. **Respeta los robots.txt** → No todos los sitios permiten scraping
5. **Añade delays entre requests** → No satures los servidores (usa `time.sleep(1)`)

---

## 🐛 SOLUCIÓN DE PROBLEMAS COMUNES

### **Error: "No module named X"**
**Solución:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### **Error: "pytesseract no funciona"**
**Solución:** Necesitas instalar Tesseract OCR en tu sistema:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang
```

### **Error: "pdf2image no funciona"**
**Solución:** Necesitas instalar Poppler:
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

---

## 📚 RECURSOS DE APRENDIZAJE

- **Python Básico:** https://docs.python.org/es/3/tutorial/
- **BeautifulSoup:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- **Pandas:** https://pandas.pydata.org/docs/user_guide/index.html
- **Streamlit:** https://docs.streamlit.io/
- **Web Scraping Ético:** https://www.scraperapi.com/blog/web-scraping-ethics/

---

## ✅ CHECKLIST PARA COMENZAR FASE 2

Antes de iniciar el desarrollo del primer scraper, verifica:

- [x] Entorno virtual creado y activado
- [x] Todas las librerías instaladas correctamente
- [x] Archivo `requirements.txt` actualizado
- [x] Estructura de carpetas lista
- [x] `.gitignore` configurado
- [ ] Página objetivo identificada
- [ ] Navegador web abierto para inspeccionar HTML
- [ ] Archivo `main.py` listo para escribir código

---

**¡Listo para comenzar! 🚀**

_Última actualización: 2025-11-18_
