"""
BÚHO - Motor Multi-sitio de Scraping Jurídico Boliviano
========================================================

Interfaz web con Streamlit para gestionar el scraping de sitios estatales.

Características:
- Dashboard con estadísticas del catálogo
- Navegación por sitios (filtros por prioridad, estado, nivel, tipo)
- Vista detallada de cada sitio
- Scraping individual o por lotes
- Monitoreo de progreso y logs

Autor: BÚHO LegalTech
Fecha: 2025-01-18
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper.catalog import CatalogManager, SiteInfo


# ========================================
# CONFIGURACIÓN DE LA PÁGINA
# ========================================

st.set_page_config(
    page_title="BÚHO - Scraper Jurídico Boliviano",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========================================
# CSS PERSONALIZADO
# ========================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .site-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .status-implementado {
        background-color: #4CAF50;
        color: white;
    }
    .status-en_progreso {
        background-color: #FF9800;
        color: white;
    }
    .status-pendiente {
        background-color: #9E9E9E;
        color: white;
    }
    .status-deshabilitado {
        background-color: #F44336;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ========================================
# FUNCIONES AUXILIARES
# ========================================

def get_status_emoji(estado: str) -> str:
    """Obtener emoji según estado."""
    emojis = {
        "implementado": "✅",
        "en_progreso": "🔄",
        "pendiente": "⏳",
        "deshabilitado": "❌"
    }
    return emojis.get(estado, "❓")


def get_prioridad_color(prioridad: int) -> str:
    """Obtener color según prioridad."""
    colors = {
        1: "#F44336",  # Rojo
        2: "#FF9800",  # Naranja
        3: "#4CAF50"   # Verde
    }
    return colors.get(prioridad, "#9E9E9E")


def render_site_card(site: SiteInfo):
    """Renderizar tarjeta de sitio."""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"### {get_status_emoji(site.estado_scraper)} {site.nombre}")
            st.caption(f"`{site.site_id}` • {site.tipo_fuente.upper()} • {site.nivel.capitalize()}")

        with col2:
            st.metric("Documentos", f"{site.documentos_totales:,}")

        with col3:
            st.metric("Artículos", f"{site.articulos_totales:,}")

        # Detalles expandibles
        with st.expander("Ver detalles"):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**URLs:**")
                st.write(f"🔗 [Base]({site.url_base})")
                if site.url_busqueda:
                    st.write(f"🔍 [Búsqueda]({site.url_busqueda})")
                if site.url_listado:
                    st.write(f"📋 [Listado]({site.url_listado})")

            with col_b:
                st.markdown("**Características:**")
                st.write(f"📄 Formato: {site.formato_documento}")
                st.write(f"🌐 Selenium: {'✓' if site.requiere_selenium else '✗'}")
                st.write(f"🔐 Login: {'✓' if site.requiere_login else '✗'}")
                st.write(f"🔌 API: {'✓' if site.tiene_api else '✗'}")

            st.markdown("**Información adicional:**")
            st.write(f"📊 Frecuencia: {site.frecuencia_actualizacion}")
            st.write(f"📝 Estructura: {site.estructura_texto}")
            st.write(f"🗂️ Tipos: {', '.join(site.tipos_documentos[:3])}...")

            if site.notas:
                st.info(site.notas)

        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])

        with col_btn1:
            if site.estado_scraper == "implementado":
                if st.button(f"🚀 Scrape", key=f"scrape_{site.site_id}"):
                    st.warning("Función de scraping en desarrollo")
            else:
                st.button(f"⏳ No disponible", key=f"scrape_{site.site_id}", disabled=True)

        with col_btn2:
            if st.button(f"ℹ️ Info", key=f"info_{site.site_id}"):
                st.session_state.selected_site = site.site_id

        st.divider()


# ========================================
# INICIALIZAR ESTADO
# ========================================

if 'catalog' not in st.session_state:
    st.session_state.catalog = CatalogManager()

if 'selected_site' not in st.session_state:
    st.session_state.selected_site = None


# ========================================
# SIDEBAR: NAVEGACIÓN Y FILTROS
# ========================================

with st.sidebar:
    st.markdown("## 🦉 BÚHO")
    st.markdown("*Motor Multi-sitio de Scraping Jurídico*")

    st.divider()

    # Menú de navegación
    st.markdown("### 📍 Navegación")
    page = st.radio(
        "Ir a:",
        ["🏠 Dashboard", "📋 Sitios", "📊 Estadísticas", "⚙️ Configuración"],
        label_visibility="collapsed"
    )

    st.divider()

    # Filtros
    if page == "📋 Sitios":
        st.markdown("### 🔍 Filtros")

        filter_prioridad = st.selectbox(
            "Prioridad",
            ["Todas", "1 - MVP", "2 - Importante", "3 - Complementario"]
        )

        filter_estado = st.selectbox(
            "Estado",
            ["Todos", "Implementado", "En progreso", "Pendiente", "Deshabilitado"]
        )

        filter_nivel = st.selectbox(
            "Nivel",
            ["Todos", "Nacional", "Departamental", "Municipal"]
        )

        filter_tipo = st.selectbox(
            "Tipo",
            ["Todos", "Normativa", "Jurisprudencia", "Regulador"]
        )

    st.divider()

    # Info del catálogo
    stats = st.session_state.catalog.get_stats()
    st.markdown("### 📈 Resumen")
    st.metric("Total sitios", stats['total_sitios'])
    st.metric("Implementados", stats['implementados'])
    st.progress(stats['porcentaje_completado'] / 100)


# ========================================
# PÁGINA: DASHBOARD
# ========================================

if page == "🏠 Dashboard":
    st.markdown('<div class="main-header">🦉 BÚHO - Scraper Jurídico Boliviano</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Motor multi-sitio de captura, procesamiento y exportación de normativa y jurisprudencia boliviana</div>', unsafe_allow_html=True)

    # Métricas generales
    stats = st.session_state.catalog.get_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📚 Total Sitios",
            value=stats['total_sitios'],
            delta=None
        )

    with col2:
        st.metric(
            label="✅ Implementados",
            value=stats['implementados'],
            delta=f"{stats['porcentaje_completado']}%"
        )

    with col3:
        st.metric(
            label="📄 Documentos",
            value=f"{stats['total_documentos']:,}",
            delta=None
        )

    with col4:
        st.metric(
            label="📝 Artículos",
            value=f"{stats['total_articulos']:,}",
            delta=None
        )

    st.divider()

    # Distribuciones
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### 🎯 Por Prioridad")
        prio_data = stats['por_prioridad']
        st.bar_chart({
            "Prioridad 1": prio_data[1],
            "Prioridad 2": prio_data[2],
            "Prioridad 3": prio_data[3]
        })

    with col_b:
        st.markdown("### 🌎 Por Nivel")
        nivel_data = stats['por_nivel']
        st.bar_chart(nivel_data)

    with col_c:
        st.markdown("### 📚 Por Tipo")
        tipo_data = stats['por_tipo']
        st.bar_chart(tipo_data)

    st.divider()

    # Sitios Ola 1 (MVP)
    st.markdown("### 🚀 Sitios Ola 1 (MVP Crítico)")
    ola1_sites = st.session_state.catalog.get_ola1_sites()

    for site in ola1_sites:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.markdown(f"**{get_status_emoji(site.estado_scraper)} {site.nombre}**")
            st.caption(site.site_id)

        with col2:
            st.markdown(f"<span class='status-badge status-{site.estado_scraper}'>{site.estado_scraper}</span>", unsafe_allow_html=True)

        with col3:
            st.write(f"📄 {site.documentos_totales}")

        with col4:
            if site.estado_scraper == "implementado":
                st.button("Scrape", key=f"dash_scrape_{site.site_id}")
            else:
                st.button("Pendiente", key=f"dash_scrape_{site.site_id}", disabled=True)


# ========================================
# PÁGINA: SITIOS
# ========================================

elif page == "📋 Sitios":
    st.markdown("## 📋 Catálogo de Sitios")

    # Aplicar filtros
    prioridad = None if filter_prioridad == "Todas" else int(filter_prioridad[0])
    estado = None if filter_estado == "Todos" else filter_estado.lower().replace(" ", "_")
    nivel = None if filter_nivel == "Todos" else filter_nivel.lower()
    tipo_fuente = None if filter_tipo == "Todos" else filter_tipo.lower()

    sites = st.session_state.catalog.search_sites(
        prioridad=prioridad,
        estado=estado,
        nivel=nivel,
        tipo_fuente=tipo_fuente
    )

    st.info(f"📊 Mostrando **{len(sites)}** sitios")

    # Renderizar sitios
    for site in sorted(sites, key=lambda s: (s.prioridad, s.site_id)):
        render_site_card(site)


# ========================================
# PÁGINA: ESTADÍSTICAS
# ========================================

elif page == "📊 Estadísticas":
    st.markdown("## 📊 Estadísticas del Catálogo")

    stats = st.session_state.catalog.get_stats()

    # Tabla de resumen
    st.markdown("### 📈 Resumen General")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total de sitios", stats['total_sitios'])
        st.metric("Sitios implementados", stats['implementados'])
        st.metric("Sitios en progreso", stats['en_progreso'])
        st.metric("Sitios pendientes", stats['pendientes'])

    with col2:
        st.metric("Porcentaje completado", f"{stats['porcentaje_completado']}%")
        st.metric("Total documentos", f"{stats['total_documentos']:,}")
        st.metric("Total artículos", f"{stats['total_articulos']:,}")

    st.divider()

    # Tabla detallada
    st.markdown("### 📋 Listado Completo")

    all_sites = st.session_state.catalog.get_all_sites()

    df = pd.DataFrame([
        {
            "ID": site.site_id,
            "Nombre": site.nombre[:40] + "..." if len(site.nombre) > 40 else site.nombre,
            "Tipo": site.tipo_fuente,
            "Nivel": site.nivel,
            "Prioridad": site.prioridad,
            "Estado": site.estado_scraper,
            "Docs": site.documentos_totales,
            "Arts": site.articulos_totales,
            "Última actualización": site.ultima_actualizacion or "Nunca"
        }
        for site in all_sites
    ])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Botón de exportación
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"buho_sitios_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


# ========================================
# PÁGINA: CONFIGURACIÓN
# ========================================

elif page == "⚙️ Configuración":
    st.markdown("## ⚙️ Configuración")

    st.info("Página de configuración en desarrollo")

    st.markdown("### 🔧 Opciones disponibles (próximamente):")
    st.markdown("""
    - ⚡ Configurar frecuencia de scraping
    - 🔐 Gestionar credenciales de sitios
    - 🗄️ Configurar conexión a Supabase
    - 📧 Notificaciones por email
    - 🔄 Programar tareas automáticas
    - 📊 Configurar exportación de datos
    """)

    st.divider()

    st.markdown("### 🔍 Validar Catálogo")
    if st.button("Validar integridad del catálogo"):
        with st.spinner("Validando..."):
            errores = st.session_state.catalog.validate_catalog()

            if not errores:
                st.success("✅ Catálogo válido - sin errores")
            else:
                st.error(f"❌ Se encontraron {len(errores)} errores:")
                for error in errores:
                    st.write(f"- {error}")

    st.divider()

    st.markdown("### 📁 Rutas del Proyecto")
    st.code(f"""
Catálogo: config/sites_catalog.yaml
Datos:    data/
Exports:  exports/
Logs:     logs/
    """)


# ========================================
# FOOTER
# ========================================

st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.caption("💡 **BÚHO LegalTech** v1.0.0")
st.sidebar.caption("Bolivia 2025")
