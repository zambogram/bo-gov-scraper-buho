"""
Interfaz Streamlit para BO-GOV-SCRAPER-BUHO
Fase: Pipeline de scraping local con control total desde la UI
"""
import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import logging

# Agregar path del proyecto al PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, get_site_config, list_active_sites, get_last_update_date
from scraper import run_site_pipeline, run_all_sites_pipeline

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuración de página
st.set_page_config(
    page_title="BÚHO - Scraper Legal Bolivia",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# UTILIDADES
# ==============================================================================

def cargar_documentos_sitio(site_id: str) -> list:
    """Cargar documentos de un sitio desde el índice"""
    site_config = get_site_config(site_id)
    if not site_config or not site_config.index_file.exists():
        return []

    try:
        with open(site_config.index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            return index_data.get('documentos', {})
    except:
        return []


def cargar_articulos_documento(ruta_json: str) -> list:
    """Cargar artículos de un documento desde su JSON"""
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            return doc_data.get('articulos', [])
    except:
        return []


def cargar_texto_documento(ruta_txt: str, max_chars: int = 1000) -> str:
    """Cargar primeros N caracteres de un documento de texto"""
    try:
        with open(ruta_txt, 'r', encoding='utf-8') as f:
            texto = f.read(max_chars)
            if len(texto) == max_chars:
                texto += "..."
            return texto
    except:
        return "No disponible"


def obtener_estadisticas_globales() -> dict:
    """Obtener estadísticas de todos los sitios"""
    stats = {
        'total_documentos': 0,
        'total_articulos': 0,
        'por_sitio': {}
    }

    for site in list_active_sites():
        docs = cargar_documentos_sitio(site.id)
        num_docs = len(docs)
        num_arts = 0

        # Contar artículos
        for doc_id, doc_data in docs.items():
            if doc_data.get('ruta_json'):
                articulos = cargar_articulos_documento(doc_data['ruta_json'])
                num_arts += len(articulos)

        stats['total_documentos'] += num_docs
        stats['total_articulos'] += num_arts
        stats['por_sitio'][site.id] = {
            'nombre': site.nombre,
            'documentos': num_docs,
            'articulos': num_arts
        }

    return stats


# ==============================================================================
# SIDEBAR
# ==============================================================================

def render_sidebar():
    """Renderizar barra lateral con controles"""

    st.sidebar.title("🦉 BÚHO Scraper")
    st.sidebar.markdown("---")

    # -------------------------------------------------------------------------
    # BLOQUE 1: Sitio
    # -------------------------------------------------------------------------
    st.sidebar.subheader("📍 Sitio")

    sites = list_active_sites()
    site_options = {site.nombre: site.id for site in sites}

    selected_name = st.sidebar.selectbox(
        "Seleccionar sitio",
        options=list(site_options.keys()),
        key="selected_site_name"
    )

    selected_site_id = site_options[selected_name]
    site_config = get_site_config(selected_site_id)

    # Información del sitio
    with st.sidebar.expander("ℹ️ Información del sitio", expanded=False):
        st.write(f"**Tipo:** {site_config.tipo}")
        st.write(f"**Categoría:** {site_config.categoria}")
        st.write(f"**Prioridad:** {site_config.prioridad}")
        st.write(f"**Ola:** {site_config.ola}")

        last_update = get_last_update_date(selected_site_id)
        if last_update:
            st.write(f"**Última actualización:**  \n{last_update.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.write("**Última actualización:** Nunca")

    st.sidebar.markdown("---")

    # -------------------------------------------------------------------------
    # BLOQUE 2: Modo de scraping
    # -------------------------------------------------------------------------
    st.sidebar.subheader("⚙️ Modo de scraping")

    modo = st.sidebar.radio(
        "Modo",
        options=["delta", "full"],
        format_func=lambda x: "Sólo nuevos (Delta)" if x == "delta" else "Histórico completo",
        key="scraping_mode"
    )

    limite = st.sidebar.number_input(
        "Límite por corrida",
        min_value=1,
        max_value=1000,
        value=50,
        step=10,
        key="scraping_limit"
    )

    st.sidebar.markdown("---")

    # -------------------------------------------------------------------------
    # BLOQUE 3: Qué guardar
    # -------------------------------------------------------------------------
    st.sidebar.subheader("💾 Qué guardar")

    save_pdf = st.sidebar.checkbox("Guardar PDF original", value=False, key="save_pdf")
    save_txt = st.sidebar.checkbox("Guardar texto normalizado (.txt)", value=True, key="save_txt")
    save_json = st.sidebar.checkbox("Guardar estructura JSON (.json)", value=True, key="save_json")

    st.sidebar.markdown("---")

    # -------------------------------------------------------------------------
    # BLOQUE 4: Acciones
    # -------------------------------------------------------------------------
    st.sidebar.subheader("🚀 Acciones")

    btn_scrape_site = st.sidebar.button(
        "▶️ Raspar sitio seleccionado",
        key="btn_scrape_site",
        use_container_width=True
    )

    btn_scrape_all = st.sidebar.button(
        "▶️ Raspar TODOS los sitios",
        key="btn_scrape_all",
        use_container_width=True
    )

    return {
        'site_id': selected_site_id,
        'site_config': site_config,
        'modo': modo,
        'limite': limite,
        'save_pdf': save_pdf,
        'save_txt': save_txt,
        'save_json': save_json,
        'btn_scrape_site': btn_scrape_site,
        'btn_scrape_all': btn_scrape_all,
    }


# ==============================================================================
# PESTAÑA: DOCUMENTOS
# ==============================================================================

def render_tab_documentos(site_id: str, site_config):
    """Renderizar pestaña de documentos"""

    st.subheader(f"📄 Documentos - {site_config.nombre}")

    # Cargar documentos
    docs_dict = cargar_documentos_sitio(site_id)

    if not docs_dict:
        st.info("No hay documentos procesados para este sitio aún. Ejecuta el scraper para obtener datos.")
        return

    # Convertir a DataFrame
    docs_list = []
    for doc_id, doc_data in docs_dict.items():
        docs_list.append({
            'ID': doc_id,
            'PDF': '✓' if doc_data.get('ruta_pdf') else '✗',
            'TXT': '✓' if doc_data.get('ruta_txt') else '✗',
            'JSON': '✓' if doc_data.get('ruta_json') else '✗',
            'Hash': doc_data.get('hash', '')[:8],
            'Actualización': doc_data.get('fecha_actualizacion', 'N/A'),
            '_ruta_txt': doc_data.get('ruta_txt'),
            '_ruta_json': doc_data.get('ruta_json'),
        })

    df = pd.DataFrame(docs_list)

    st.write(f"**Total documentos:** {len(docs_list)}")

    # Mostrar tabla
    st.dataframe(
        df[['ID', 'PDF', 'TXT', 'JSON', 'Hash', 'Actualización']],
        use_container_width=True,
        hide_index=True
    )

    # Selector de documento para vista previa
    st.markdown("---")
    st.subheader("👁️ Vista previa")

    selected_doc = st.selectbox(
        "Seleccionar documento",
        options=docs_list,
        format_func=lambda x: x['ID'],
        key="selected_doc"
    )

    if selected_doc:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Metadata**")
            st.json({
                'ID': selected_doc['ID'],
                'Hash': selected_doc['Hash'],
                'Última actualización': selected_doc['Actualización']
            })

        with col2:
            st.markdown("**Primeras líneas del texto**")
            if selected_doc['_ruta_txt']:
                texto = cargar_texto_documento(selected_doc['_ruta_txt'], max_chars=500)
                st.text_area("Texto", texto, height=200, key="preview_text")
            else:
                st.info("Texto no disponible")


# ==============================================================================
# PESTAÑA: ARTÍCULOS
# ==============================================================================

def render_tab_articulos(site_id: str, site_config):
    """Renderizar pestaña de artículos"""

    st.subheader(f"📑 Artículos - {site_config.nombre}")

    # Cargar todos los artículos de todos los documentos del sitio
    docs_dict = cargar_documentos_sitio(site_id)

    if not docs_dict:
        st.info("No hay artículos disponibles. Procesa documentos primero.")
        return

    # Recopilar artículos
    articulos_list = []
    for doc_id, doc_data in docs_dict.items():
        if doc_data.get('ruta_json'):
            articulos = cargar_articulos_documento(doc_data['ruta_json'])
            for art in articulos:
                articulos_list.append({
                    'ID Artículo': art.get('id_articulo', ''),
                    'ID Documento': art.get('id_documento', ''),
                    'Número': art.get('numero', ''),
                    'Título': art.get('titulo', '')[:50] if art.get('titulo') else '',
                    'Tipo': art.get('tipo_unidad', 'articulo'),
                    'Contenido': art.get('contenido', '')[:100] + '...',
                })

    if not articulos_list:
        st.info("No se encontraron artículos parseados.")
        return

    df_arts = pd.DataFrame(articulos_list)

    st.write(f"**Total artículos:** {len(articulos_list)}")

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filter_tipo = st.selectbox(
            "Filtrar por tipo",
            options=['Todos'] + list(df_arts['Tipo'].unique()),
            key="filter_tipo"
        )

    with col2:
        filter_doc = st.selectbox(
            "Filtrar por documento",
            options=['Todos'] + list(df_arts['ID Documento'].unique()),
            key="filter_doc"
        )

    # Aplicar filtros
    df_filtered = df_arts.copy()
    if filter_tipo != 'Todos':
        df_filtered = df_filtered[df_filtered['Tipo'] == filter_tipo]
    if filter_doc != 'Todos':
        df_filtered = df_filtered[df_filtered['ID Documento'] == filter_doc]

    # Mostrar tabla
    st.dataframe(
        df_filtered,
        use_container_width=True,
        hide_index=True
    )


# ==============================================================================
# PESTAÑA: ESTADÍSTICAS
# ==============================================================================

def render_tab_estadisticas():
    """Renderizar pestaña de estadísticas"""

    st.subheader("📊 Estadísticas Globales")

    stats = obtener_estadisticas_globales()

    # Métricas globales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documentos", stats['total_documentos'])
    with col2:
        st.metric("Total Artículos", stats['total_articulos'])
    with col3:
        prom = stats['total_articulos'] / stats['total_documentos'] if stats['total_documentos'] > 0 else 0
        st.metric("Promedio Artículos/Doc", f"{prom:.1f}")

    st.markdown("---")

    # Estadísticas por sitio
    st.subheader("Por sitio")

    if stats['por_sitio']:
        df_sitios = pd.DataFrame([
            {
                'Sitio': data['nombre'],
                'Documentos': data['documentos'],
                'Artículos': data['articulos']
            }
            for site_id, data in stats['por_sitio'].items()
        ])

        # Tabla
        st.dataframe(df_sitios, use_container_width=True, hide_index=True)

        # Gráfico de barras
        st.bar_chart(df_sitios.set_index('Sitio')[['Documentos', 'Artículos']])
    else:
        st.info("No hay datos disponibles aún.")


# ==============================================================================
# PESTAÑA: LOGS
# ==============================================================================

def render_tab_logs(site_id: str, site_config):
    """Renderizar pestaña de logs"""

    st.subheader(f"📝 Logs - {site_config.nombre}")

    # Mostrar logs de sesión si existen
    if 'pipeline_logs' in st.session_state:
        st.text_area(
            "Logs de la sesión actual",
            "\n".join(st.session_state['pipeline_logs']),
            height=400,
            key="logs_display"
        )
    else:
        st.info("No hay logs de la sesión actual. Ejecuta el scraper para ver logs en tiempo real.")

    # Buscar archivos de log en disco
    st.markdown("---")
    st.subheader("Logs históricos")

    logs_dir = site_config.logs_dir
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            selected_log = st.selectbox(
                "Seleccionar archivo de log",
                options=log_files,
                format_func=lambda x: x.name,
                key="selected_log_file"
            )

            if selected_log:
                try:
                    with open(selected_log, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    st.text_area("Contenido", log_content, height=300, key="log_file_content")
                except:
                    st.error("Error leyendo archivo de log")
        else:
            st.info("No hay archivos de log históricos.")
    else:
        st.info("Directorio de logs no existe aún.")


# ==============================================================================
# EJECUTAR SCRAPING
# ==============================================================================

def ejecutar_scraping_sitio(site_id: str, modo: str, limite: int, save_pdf: bool, save_txt: bool, save_json: bool):
    """Ejecutar scraping de un sitio con feedback visual"""

    st.info(f"🚀 Iniciando scraping de {site_id}...")

    # Inicializar logs de sesión
    if 'pipeline_logs' not in st.session_state:
        st.session_state['pipeline_logs'] = []

    # Contenedor para progreso
    progress_container = st.container()
    progress_bar = progress_container.progress(0)
    status_text = progress_container.empty()
    logs_container = progress_container.expander("📋 Ver logs en tiempo real", expanded=True)
    logs_area = logs_container.empty()

    # Callback para actualizar progreso
    def progress_callback(mensaje: str):
        st.session_state['pipeline_logs'].append(mensaje)
        logs_area.text("\n".join(st.session_state['pipeline_logs'][-20:]))

    # Ejecutar pipeline
    try:
        result = run_site_pipeline(
            site_id=site_id,
            mode=modo,
            limit=limite,
            save_pdf=save_pdf,
            save_txt=save_txt,
            save_json=save_json,
            progress_callback=progress_callback
        )

        progress_bar.progress(100)

        # Mostrar resultados
        st.success("✅ Scraping completado!")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Encontrados", result.total_encontrados)
        with col2:
            st.metric("Descargados", result.total_descargados)
        with col3:
            st.metric("Parseados", result.total_parseados)
        with col4:
            st.metric("Errores", result.total_errores)

        if result.total_errores > 0:
            with st.expander("❌ Ver errores"):
                for error in result.errores:
                    st.error(f"{error['descripcion']}: {error['detalle']}")

    except Exception as e:
        st.error(f"❌ Error ejecutando scraping: {e}")
        progress_bar.progress(0)


def ejecutar_scraping_todos(modo: str, limite: int, save_pdf: bool, save_txt: bool, save_json: bool):
    """Ejecutar scraping de todos los sitios"""

    st.info("🚀 Iniciando scraping de TODOS los sitios activos...")

    # Inicializar logs
    if 'pipeline_logs' not in st.session_state:
        st.session_state['pipeline_logs'] = []

    try:
        results = run_all_sites_pipeline(
            mode=modo,
            limit=limite,
            save_pdf=save_pdf,
            save_txt=save_txt,
            save_json=save_json,
            progress_callback=lambda msg: st.session_state['pipeline_logs'].append(msg)
        )

        st.success("✅ Scraping de todos los sitios completado!")

        # Mostrar resumen
        for site_id, result in results.items():
            with st.expander(f"📊 {site_id}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Descargados", result.total_descargados)
                with col2:
                    st.metric("Parseados", result.total_parseados)
                with col3:
                    st.metric("Errores", result.total_errores)

    except Exception as e:
        st.error(f"❌ Error: {e}")


# ==============================================================================
# MAIN APP
# ==============================================================================

def main():
    """Función principal de la aplicación"""

    st.title("🦉 BÚHO - Scraper Legal Bolivia")
    st.markdown("**Sistema de scraping, procesamiento y almacenamiento local de normativa boliviana**")
    st.markdown("---")

    # Renderizar sidebar y obtener configuración
    sidebar_state = render_sidebar()

    # Manejar botones de scraping
    if sidebar_state['btn_scrape_site']:
        ejecutar_scraping_sitio(
            site_id=sidebar_state['site_id'],
            modo=sidebar_state['modo'],
            limite=sidebar_state['limite'],
            save_pdf=sidebar_state['save_pdf'],
            save_txt=sidebar_state['save_txt'],
            save_json=sidebar_state['save_json']
        )

    if sidebar_state['btn_scrape_all']:
        ejecutar_scraping_todos(
            modo=sidebar_state['modo'],
            limite=sidebar_state['limite'],
            save_pdf=sidebar_state['save_pdf'],
            save_txt=sidebar_state['save_txt'],
            save_json=sidebar_state['save_json']
        )

    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Documentos",
        "📑 Artículos",
        "📊 Estadísticas",
        "📝 Logs"
    ])

    with tab1:
        render_tab_documentos(sidebar_state['site_id'], sidebar_state['site_config'])

    with tab2:
        render_tab_articulos(sidebar_state['site_id'], sidebar_state['site_config'])

    with tab3:
        render_tab_estadisticas()

    with tab4:
        render_tab_logs(sidebar_state['site_id'], sidebar_state['site_config'])


if __name__ == "__main__":
    main()
