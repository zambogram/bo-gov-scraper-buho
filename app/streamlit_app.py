"""
Interfaz web con Streamlit para el scraper de sitios gubernamentales de Bolivia.
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.catalog import CatalogManager, OLA1_SITE_IDS
from scraper.sites import get_scraper_class
from scraper.base import DocumentIndex


# Configuración de la página
st.set_page_config(
    page_title="Scraper Gubernamental Bolivia",
    page_icon="🇧🇴",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Función principal de la aplicación."""

    # Título principal
    st.title("🇧🇴 Scraper de Sitios Gubernamentales de Bolivia")
    st.markdown("---")

    # Sidebar con navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.radio(
        "Selecciona una página:",
        ["Dashboard", "Catálogo de Sitios", "Ejecutar Scraping", "Estadísticas", "Ayuda"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Catálogo de Sitios":
        show_catalog()
    elif page == "Ejecutar Scraping":
        show_scraping()
    elif page == "Estadísticas":
        show_statistics()
    elif page == "Ayuda":
        show_help()


def show_dashboard():
    """Muestra el dashboard principal."""
    st.header("Dashboard - Resumen General")

    catalog = CatalogManager()

    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_sites = catalog.get_total_sites()
        st.metric("Total Sitios", total_sites)

    with col2:
        ola1_sites = len(catalog.get_ola1_site_ids())
        st.metric("Sitios Ola 1", ola1_sites)

    with col3:
        implementados = len(catalog.list_sites(estado_scraper="implementado"))
        st.metric("Scrapers Implementados", implementados)

    with col4:
        # Contar documentos totales
        total_docs = 0
        index_dir = Path("data/index")
        if index_dir.exists():
            for index_file in index_dir.glob("*.json"):
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    total_docs += len(data)
        st.metric("Documentos Totales", total_docs)

    st.markdown("---")

    # Estado de scrapers Ola 1
    st.subheader("Estado de Scrapers - Ola 1 (Prioridad Máxima)")

    ola1_ids = catalog.get_ola1_site_ids()

    for site_id in ola1_ids:
        site_config = catalog.get_site(site_id)

        with st.expander(f"📄 {site_config.nombre}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**ID:** `{site_id}`")
                st.write(f"**Categoría:** {site_config.categoria}")
                st.write(f"**URL:** {site_config.url_base}")
                st.write(f"**Estado Scraper:** `{site_config.estado_scraper}`")

                # Estadísticas si existen
                index = DocumentIndex(site_id)
                stats = index.get_stats()
                if stats['total_documentos'] > 0:
                    st.write(f"**Documentos:** {stats['total_documentos']}")
                    st.write(f"**Última actualización:** {stats['ultima_actualizacion'][:19]}")

            with col2:
                if site_config.estado_scraper == "implementado":
                    st.success("✅ Implementado")
                else:
                    st.warning("⚠️ Pendiente")


def show_catalog():
    """Muestra el catálogo completo de sitios."""
    st.header("Catálogo de Sitios")

    catalog = CatalogManager()

    # Filtros
    col1, col2, col3 = st.columns(3)

    with col1:
        prioridad_filter = st.selectbox(
            "Filtrar por Prioridad",
            ["Todas", "1", "2"],
            index=0
        )

    with col2:
        categoria_filter = st.selectbox(
            "Filtrar por Categoría",
            ["Todas", "legislativo", "judicial", "regulatorio"],
            index=0
        )

    with col3:
        estado_filter = st.selectbox(
            "Filtrar por Estado",
            ["Todos", "implementado", "pendiente"],
            index=0
        )

    # Aplicar filtros
    prioridad = int(prioridad_filter) if prioridad_filter != "Todas" else None
    categoria = categoria_filter if categoria_filter != "Todas" else None
    estado = estado_filter if estado_filter != "Todos" else None

    sites = catalog.list_sites(
        prioridad=prioridad,
        categoria=categoria,
        estado_scraper=estado
    )

    st.markdown(f"**Total de sitios:** {len(sites)}")
    st.markdown("---")

    # Mostrar sitios
    for site in sites:
        with st.expander(f"{site.nombre} ({site.site_id})", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Descripción:** {site.descripcion}")
                st.write(f"**URL Base:** {site.url_base}")
                st.write(f"**Tipos de documentos:** {', '.join(site.tipo_documentos)}")
                st.write(f"**Formato disponible:** {site.formato_disponible}")
                st.write(f"**Notas:** {site.notas}")

            with col2:
                st.write(f"**Prioridad:** {site.prioridad}")
                st.write(f"**Categoría:** {site.categoria}")
                st.write(f"**Estado Scraper:** {site.estado_scraper}")
                st.write(f"**Frecuencia:** {site.frecuencia_actualizacion}")


def show_scraping():
    """Página para ejecutar scraping."""
    st.header("Ejecutar Scraping")

    catalog = CatalogManager()

    # Selección de sitio
    sites = catalog.list_sites(estado_scraper="implementado")
    site_options = {f"{s.nombre} ({s.site_id})": s.site_id for s in sites}

    selected_site_display = st.selectbox(
        "Selecciona un sitio:",
        list(site_options.keys())
    )

    site_id = site_options[selected_site_display]
    site_config = catalog.get_site(site_id)

    # Opciones de scraping
    col1, col2 = st.columns(2)

    with col1:
        limit = st.number_input(
            "Límite de documentos (0 = sin límite)",
            min_value=0,
            max_value=1000,
            value=10,
            step=5
        )

    with col2:
        solo_nuevos = st.checkbox(
            "Solo documentos nuevos o modificados",
            value=True
        )

    modo_demo = st.checkbox(
        "Modo demo (genera datos de prueba)",
        value=True,
        help="Recomendado para pruebas sin conexión a sitios reales"
    )

    st.markdown("---")

    # Botón de scraping
    if st.button("🚀 Ejecutar Scraping", type="primary"):
        scraper_class = get_scraper_class(site_id)

        if not scraper_class:
            st.error(f"No hay scraper implementado para {site_id}")
            return

        with st.spinner(f"Ejecutando scraping de {site_config.nombre}..."):
            try:
                # Crear y ejecutar scraper
                scraper = scraper_class(site_config, modo_demo=modo_demo)
                limit_val = limit if limit > 0 else None
                documentos = scraper.scrape(limit=limit_val, solo_nuevos=solo_nuevos)

                # Generar resumen
                resumen = scraper.generar_resumen(documentos)

                # Mostrar resultados
                st.success("✅ Scraping completado exitosamente")

                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Encontrados", resumen['total_encontrados'])
                with col2:
                    st.metric("Nuevos", resumen['nuevos'])
                with col3:
                    st.metric("Modificados", resumen['modificados'])
                with col4:
                    st.metric("Con PDF", resumen['con_pdf'])

                st.markdown("---")

                # Mostrar documentos
                if documentos:
                    st.subheader("Documentos Scrapeados")

                    for i, doc in enumerate(documentos[:10]):  # Mostrar primeros 10
                        estado_emoji = {
                            "nuevo": "🆕",
                            "modificado": "🔄",
                            "sin_cambios": "✓"
                        }.get(doc.estado, "❓")

                        st.write(f"{estado_emoji} **{doc.titulo}**")
                        st.caption(
                            f"Tipo: {doc.tipo_norma} | "
                            f"Número: {doc.numero_norma} | "
                            f"Fecha: {doc.fecha_publicacion}"
                        )

                        if i < len(documentos) - 1:
                            st.divider()

                    if len(documentos) > 10:
                        st.info(f"... y {len(documentos) - 10} documentos más")

            except Exception as e:
                st.error(f"Error durante el scraping: {str(e)}")
                st.exception(e)


def show_statistics():
    """Muestra estadísticas de scraping."""
    st.header("Estadísticas de Scraping")

    catalog = CatalogManager()
    index_dir = Path("data/index")

    if not index_dir.exists() or not list(index_dir.glob("*.json")):
        st.info("No hay datos de scraping todavía. Ejecuta algún scraper primero.")
        return

    # Por cada sitio con datos
    for index_file in sorted(index_dir.glob("*.json")):
        site_id = index_file.stem
        site_config = catalog.get_site(site_id)

        if not site_config:
            continue

        with st.expander(f"📊 {site_config.nombre}", expanded=True):
            index = DocumentIndex(site_id)
            stats = index.get_stats()

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Documentos", stats['total_documentos'])

            with col2:
                if stats['ultima_actualizacion']:
                    fecha = stats['ultima_actualizacion'][:19]
                    st.metric("Última Actualización", fecha)

            # Leer archivo de documentos
            docs_file = Path(f"data/raw/{site_id}/documentos.json")
            if docs_file.exists():
                with open(docs_file, 'r') as f:
                    documentos = json.load(f)

                # Contar por estado
                estados = {}
                tipos = {}
                for doc in documentos:
                    estado = doc.get('estado', 'desconocido')
                    estados[estado] = estados.get(estado, 0) + 1

                    tipo = doc.get('tipo_norma', 'Desconocido')
                    tipos[tipo] = tipos.get(tipo, 0) + 1

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Por Estado:**")
                    for estado, count in estados.items():
                        st.write(f"- {estado}: {count}")

                with col2:
                    st.write("**Por Tipo:**")
                    for tipo, count in list(tipos.items())[:5]:
                        st.write(f"- {tipo}: {count}")


def show_help():
    """Muestra ayuda y documentación."""
    st.header("Ayuda y Documentación")

    st.markdown("""
    ## Bienvenido al Scraper de Sitios Gubernamentales de Bolivia

    Esta herramienta permite recolectar y gestionar documentos legales y normativos
    de diferentes sitios web gubernamentales de Bolivia.

    ### Páginas Disponibles

    1. **Dashboard**: Vista general del estado de todos los scrapers
    2. **Catálogo de Sitios**: Explora todos los sitios disponibles con filtros
    3. **Ejecutar Scraping**: Ejecuta scrapers para recolectar documentos
    4. **Estadísticas**: Ve estadísticas detalladas de los documentos recolectados

    ### Sitios de la Ola 1 (Prioridad Máxima)

    - **Gaceta Oficial**: Leyes, decretos y resoluciones nacionales
    - **TSJ GENESIS**: Jurisprudencia del Tribunal Supremo de Justicia
    - **TCP**: Sentencias del Tribunal Constitucional Plurinacional
    - **ASFI**: Normativa del sistema financiero
    - **SIN**: Normativa tributaria

    ### Uso del CLI

    También puedes usar la herramienta desde la línea de comandos:

    ```bash
    # Listar sitios
    python main.py list --prioridad 1

    # Ejecutar scraping
    python main.py scrape gaceta_oficial --limit 10

    # Demo de la Ola 1
    python main.py demo-ola1 --limit 5

    # Ver estadísticas
    python main.py stats
    ```

    ### Estructura de Datos

    Los documentos se guardan en:
    - `data/raw/<site_id>/documentos.json` - Documentos scrapeados
    - `data/raw/<site_id>/pdfs/` - PDFs descargados
    - `data/index/<site_id>.json` - Índice para evitar duplicados

    ### Soporte

    Para reportar problemas o sugerencias, contacta al administrador del sistema.
    """)


if __name__ == "__main__":
    main()
