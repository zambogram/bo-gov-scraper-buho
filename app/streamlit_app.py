"""
Interfaz Web Streamlit para BÚHO
Dashboard interactivo para el scraper de leyes bolivianas
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.database import LawDatabase
from scraper.multi_site_scraper import MultiSiteScraper
from scraper.document_processor import DocumentProcessor
from scraper.metadata import MetadataExtractor
from exporters import CSVExporter, JSONExporter, ExcelExporter


# Configuración de la página
st.set_page_config(
    page_title="BÚHO - Scraper de Leyes Bolivianas",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""

    # Header
    st.markdown('<h1 class="main-header">🦉 BÚHO</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Sistema de Scraping de Leyes Bolivianas</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Bandera_de_Bolivia_%28Estado%29.svg/320px-Bandera_de_Bolivia_%28Estado%29.svg.png", width=200)
        st.title("🦉 BÚHO")
        st.markdown("---")

        page = st.radio(
            "Navegación",
            ["📊 Dashboard", "🔍 Scraper", "📄 Procesamiento", "💾 Base de Datos", "📤 Exportar", "⚙️ Configuración"],
            key="navigation"
        )

        st.markdown("---")
        st.markdown("### Información del Sistema")
        st.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}\n\n⏰ Hora: {datetime.now().strftime('%H:%M:%S')}")

    # Renderizar página seleccionada
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "🔍 Scraper":
        render_scraper()
    elif page == "📄 Procesamiento":
        render_processing()
    elif page == "💾 Base de Datos":
        render_database()
    elif page == "📤 Exportar":
        render_export()
    elif page == "⚙️ Configuración":
        render_settings()


def render_dashboard():
    """Renderiza el dashboard principal con estadísticas"""
    st.header("📊 Dashboard de Estadísticas")

    try:
        with LawDatabase() as db:
            stats = db.obtener_estadisticas()

            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="📚 Total de Leyes",
                    value=stats['total_leyes'],
                    delta="Histórico completo"
                )

            with col2:
                vigentes = next((v['cantidad'] for v in stats['vigencia'] if v['vigente']), 0)
                st.metric(
                    label="✅ Leyes Vigentes",
                    value=vigentes,
                    delta=f"{vigentes/stats['total_leyes']*100:.1f}%" if stats['total_leyes'] > 0 else "0%"
                )

            with col3:
                st.metric(
                    label="🌐 Sitios Scrapeados",
                    value=len(stats['por_sitio']),
                    delta="Activos"
                )

            with col4:
                st.metric(
                    label="📂 Áreas del Derecho",
                    value=len(stats['por_area']),
                    delta="Clasificadas"
                )

            st.markdown("---")

            # Gráficos
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Leyes por Área del Derecho")
                if stats['por_area']:
                    df_area = pd.DataFrame(stats['por_area'][:10])
                    fig = px.bar(
                        df_area,
                        x='cantidad',
                        y='area_derecho',
                        orientation='h',
                        color='cantidad',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos disponibles")

            with col2:
                st.subheader("📋 Leyes por Tipo de Norma")
                if stats['por_tipo']:
                    df_tipo = pd.DataFrame(stats['por_tipo'])
                    fig = px.pie(
                        df_tipo,
                        values='cantidad',
                        names='tipo_norma',
                        hole=0.4
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos disponibles")

            # Timeline de leyes por año
            st.subheader("📅 Evolución Histórica de Leyes")
            if stats['por_anio']:
                df_anio = pd.DataFrame([a for a in stats['por_anio'] if a['anio']])
                fig = px.line(
                    df_anio,
                    x='anio',
                    y='cantidad',
                    markers=True,
                    title='Número de Leyes por Año'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos históricos disponibles")

            # Tabla de sitios web
            st.subheader("🌐 Leyes por Sitio Web")
            if stats['por_sitio']:
                df_sitios = pd.DataFrame(stats['por_sitio'])
                st.dataframe(df_sitios, use_container_width=True)
            else:
                st.info("No hay datos de sitios disponibles")

    except Exception as e:
        st.error(f"Error al cargar estadísticas: {e}")
        st.info("La base de datos aún no contiene información. Ejecuta el scraper primero.")


def render_scraper():
    """Renderiza la interfaz del scraper"""
    st.header("🔍 Scraper de Sitios Web")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Configuración del Scraping")

        workers = st.slider(
            "Número de hilos concurrentes",
            min_value=1,
            max_value=10,
            value=5,
            help="Más hilos = más rápido, pero más carga en los servidores"
        )

        st.info(f"⚡ Se utilizarán {workers} hilos para scrapear sitios simultáneamente")

    with col2:
        st.subheader("Estado")
        status_placeholder = st.empty()
        status_placeholder.info("⏸️ Esperando inicio")

    st.markdown("---")

    if st.button("🚀 Iniciar Scraping", type="primary"):
        with st.spinner("Scrapeando sitios web..."):
            try:
                scraper = MultiSiteScraper()

                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Iniciando scraper...")
                resultados = scraper.scrapear_todos_los_sitios(max_workers=workers)

                progress_bar.progress(100)

                st.success("✅ Scraping completado!")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sitios exitosos", len(resultados['exitosos']))
                with col2:
                    st.metric("Sitios fallidos", len(resultados['fallidos']))
                with col3:
                    st.metric("Documentos encontrados", resultados['total_documentos'])

                if resultados['exitosos']:
                    st.subheader("📊 Resultados por Sitio")
                    for resultado in resultados['exitosos']:
                        with st.expander(f"✅ {resultado['sitio']}"):
                            st.write(f"**Documentos encontrados:** {resultado['documentos_encontrados']}")
                            st.write(f"**Documentos descargados:** {resultado['documentos_descargados']}")
                            if resultado.get('errores'):
                                st.warning(f"**Errores:** {len(resultado['errores'])}")

            except Exception as e:
                st.error(f"❌ Error durante el scraping: {e}")


def render_processing():
    """Renderiza la interfaz de procesamiento"""
    st.header("📄 Procesamiento de Documentos")

    col1, col2 = st.columns(2)

    with col1:
        aplicar_ocr = st.checkbox(
            "Aplicar OCR a documentos escaneados",
            value=True,
            help="Reconocimiento óptico de caracteres para PDFs escaneados"
        )

    with col2:
        dividir_pdfs = st.checkbox(
            "Dividir PDFs grandes",
            value=True,
            help="Divide PDFs de más de 50 páginas en secciones manejables"
        )

    st.markdown("---")

    if st.button("⚙️ Procesar Documentos", type="primary"):
        with st.spinner("Procesando documentos..."):
            try:
                from main import BuhoScraper
                buho = BuhoScraper()

                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Procesando documentos...")
                buho.procesar_documentos(
                    aplicar_ocr=aplicar_ocr,
                    dividir_pdfs=dividir_pdfs
                )

                progress_bar.progress(100)
                st.success("✅ Procesamiento completado!")

            except Exception as e:
                st.error(f"❌ Error durante el procesamiento: {e}")


def render_database():
    """Renderiza la interfaz de la base de datos"""
    st.header("💾 Base de Datos de Leyes")

    try:
        with LawDatabase() as db:
            # Filtros
            st.subheader("🔍 Búsqueda y Filtros")

            col1, col2, col3 = st.columns(3)

            with col1:
                area_filter = st.selectbox(
                    "Área del Derecho",
                    ["Todas"] + ["Laboral", "Penal", "Civil", "Tributario", "Ambiental", "Constitucional"]
                )

            with col2:
                vigente_filter = st.selectbox(
                    "Vigencia",
                    ["Todas", "Vigente", "No vigente"]
                )

            with col3:
                tipo_filter = st.selectbox(
                    "Tipo de Norma",
                    ["Todos", "Ley", "Decreto Supremo", "Resolución"]
                )

            # Aplicar filtros
            filtros = {}
            if area_filter != "Todas":
                filtros['area_derecho'] = area_filter
            if vigente_filter != "Todas":
                filtros['vigente'] = vigente_filter == "Vigente"
            if tipo_filter != "Todos":
                filtros['tipo_norma'] = tipo_filter

            # Buscar leyes
            leyes = db.buscar_ley(**filtros) if filtros else []

            st.markdown(f"**Resultados encontrados:** {len(leyes)}")

            if leyes:
                # Convertir a DataFrame para mostrar
                df = pd.DataFrame(leyes)

                # Seleccionar columnas importantes
                columnas_mostrar = ['numero_ley', 'titulo', 'area_derecho', 'tipo_norma',
                                   'fecha_promulgacion', 'vigente']
                columnas_disponibles = [c for c in columnas_mostrar if c in df.columns]

                st.dataframe(
                    df[columnas_disponibles],
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No se encontraron leyes con los filtros seleccionados")

    except Exception as e:
        st.error(f"Error al acceder a la base de datos: {e}")


def render_export():
    """Renderiza la interfaz de exportación"""
    st.header("📤 Exportar Datos")

    st.subheader("Selecciona los formatos de exportación")

    col1, col2, col3 = st.columns(3)

    with col1:
        export_csv = st.checkbox("📄 CSV", value=True)
    with col2:
        export_json = st.checkbox("📋 JSON", value=True)
    with col3:
        export_excel = st.checkbox("📊 Excel", value=True)

    formatos = []
    if export_csv:
        formatos.append('csv')
    if export_json:
        formatos.append('json')
    if export_excel:
        formatos.append('excel')

    st.markdown("---")

    if st.button("💾 Exportar Datos", type="primary", disabled=len(formatos) == 0):
        if formatos:
            with st.spinner("Exportando datos..."):
                try:
                    from main import BuhoScraper
                    buho = BuhoScraper()
                    buho.exportar_datos(formatos=formatos)

                    st.success(f"✅ Datos exportados en formatos: {', '.join(formatos)}")
                    st.info(f"📁 Archivos guardados en: exports/{buho.timestamp}/")

                except Exception as e:
                    st.error(f"❌ Error durante la exportación: {e}")
        else:
            st.warning("⚠️ Selecciona al menos un formato de exportación")


def render_settings():
    """Renderiza la interfaz de configuración"""
    st.header("⚙️ Configuración del Sistema")

    st.subheader("📝 Archivos de Configuración")

    st.info("""
    **Configuración de Sitios Web**: `config/sites_config.yaml`

    - Habilitar/deshabilitar sitios
    - Ajustar prioridades
    - Configurar selectores CSS

    **Esquema de Metadatos**: `config/metadata_schema.yaml`

    - Definir campos de metadatos
    - Patrones de extracción regex
    - Áreas del derecho
    """)

    st.markdown("---")

    st.subheader("🔧 Herramientas del Sistema")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗄️ Crear Backup de BD"):
            try:
                from scraper.database import crear_backup_db
                backup_path = crear_backup_db()
                st.success(f"✅ Backup creado: {backup_path}")
            except Exception as e:
                st.error(f"❌ Error al crear backup: {e}")

    with col2:
        if st.button("📊 Ver Estadísticas Completas"):
            try:
                from main import BuhoScraper
                buho = BuhoScraper()
                buho.mostrar_estadisticas()
                st.success("✅ Ver la terminal para estadísticas completas")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.markdown("---")

    st.subheader("ℹ️ Información del Sistema")

    st.code("""
    🦉 BÚHO - Scraper de Leyes Bolivianas
    Versión: 1.0.0
    Desarrollado con: Python, Streamlit, SQLite
    Licencia: MIT
    """)


if __name__ == "__main__":
    main()
