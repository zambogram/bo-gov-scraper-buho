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

from config import settings, get_site_config, list_active_sites
from scraper import run_site_pipeline, run_all_sites_pipeline
from scraper.models import Documento

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


def cargar_documento_completo(ruta_json: str) -> dict:
    """Cargar documento completo desde JSON con toda su metadata"""
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


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

        # Obtener última actualización desde el índice
        tracking_path = Path(f"data/index/{selected_site_id}/index.json")
        if tracking_path.exists():
            try:
                with open(tracking_path) as f:
                    data = json.load(f)
                    last_update = data.get('last_updated', 'Nunca')
                    if last_update != 'Nunca':
                        try:
                            dt = datetime.fromisoformat(last_update)
                            st.write(f"**Última actualización:**  \n{dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.write(f"**Última actualización:** {last_update}")
                    else:
                        st.write("**Última actualización:** Nunca")
            except:
                st.write("**Última actualización:** Nunca")
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
# PESTAÑA: QA/REVISIÓN
# ==============================================================================

def render_tab_qa_revision(site_id: str, site_config):
    """Renderizar pestaña de QA y revisión de documentos con metadata extendida"""

    st.subheader(f"🔍 QA/Revisión - {site_config.nombre}")
    st.markdown("Revisa documentos procesados con toda su metadata extendida")

    # Cargar documentos
    docs_dict = cargar_documentos_sitio(site_id)

    if not docs_dict:
        st.warning("⚠️ No hay documentos disponibles para revisión. Ejecuta el scraper primero.")
        return

    # Selector de documento
    doc_ids = list(docs_dict.keys())

    selected_doc_id = st.selectbox(
        "Seleccionar documento por ID",
        options=doc_ids,
        key="qa_selected_doc"
    )

    if not selected_doc_id:
        return

    doc_info = docs_dict[selected_doc_id]

    # Cargar documento completo desde JSON
    if not doc_info.get('ruta_json'):
        st.error("❌ Este documento no tiene archivo JSON asociado")
        return

    doc_completo = cargar_documento_completo(doc_info['ruta_json'])

    if not doc_completo:
        st.error("❌ Error cargando documento completo")
        return

    # =========================================================================
    # SECCIÓN 1: Información Básica
    # =========================================================================
    st.markdown("---")
    st.subheader("📋 Información Básica")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**ID Documento:**")
        st.code(doc_completo.get('id_documento', 'N/A'))

        st.markdown("**Tipo:**")
        st.info(doc_completo.get('tipo_documento', 'N/A'))

    with col2:
        st.markdown("**Número de Norma:**")
        numero = doc_completo.get('numero_norma') or doc_completo.get('metadata', {}).get('numero_norma')
        st.code(numero or 'N/A')

        st.markdown("**Fecha:**")
        fecha = doc_completo.get('fecha') or doc_completo.get('metadata', {}).get('fecha_promulgacion')
        st.info(fecha or 'N/A')

    with col3:
        st.markdown("**Hash Contenido:**")
        st.code(doc_completo.get('hash_contenido', 'N/A')[:16])

        st.markdown("**Fecha Scraping:**")
        fecha_scraping = doc_completo.get('fecha_scraping', 'N/A')
        if fecha_scraping != 'N/A':
            try:
                dt = datetime.fromisoformat(fecha_scraping)
                st.info(dt.strftime('%Y-%m-%d %H:%M'))
            except:
                st.info(fecha_scraping)
        else:
            st.info('N/A')

    # =========================================================================
    # SECCIÓN 2: Metadata Extendida
    # =========================================================================
    st.markdown("---")
    st.subheader("🏛️ Metadata Extendida")

    metadata = doc_completo.get('metadata', {})

    # Fila 1: Jerarquía y área
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        jerarquia = metadata.get('jerarquia', 99)
        st.metric("Jerarquía Normativa", jerarquia)
        if jerarquia == 99:
            st.caption("⚠️ No clasificada")

    with col2:
        area_principal = metadata.get('area_principal', 'otros')
        st.metric("Área Principal", area_principal)
        if area_principal == 'otros':
            st.caption("⚠️ Sin clasificar")

    with col3:
        estado = metadata.get('estado_vigencia', 'vigente')
        emoji = '✅' if estado == 'vigente' else '⚠️' if estado == 'modificada' else '❌'
        st.metric("Estado Vigencia", f"{emoji} {estado}")

    with col4:
        total_articulos = doc_completo.get('total_articulos') or len(doc_completo.get('articulos', []))
        st.metric("Total Artículos", total_articulos)

    # Fila 2: Áreas y palabras clave
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Áreas del Derecho Detectadas:**")
        areas = metadata.get('areas_derecho', [])
        if areas:
            badges_html = " ".join([f'<span style="background-color: #262730; padding: 4px 12px; border-radius: 12px; margin: 2px; display: inline-block;">📖 {area}</span>' for area in areas])
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.caption("⚠️ Sin áreas detectadas")

    with col2:
        st.markdown("**Palabras Clave:**")
        palabras_clave = metadata.get('palabras_clave', [])
        if palabras_clave:
            st.write(", ".join(palabras_clave[:10]))  # Primeras 10
        else:
            st.caption("⚠️ Sin palabras clave")

    # Fila 3: Relaciones normativas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Entidad Emisora:**")
        entidad = metadata.get('entidad_emisora', 'No detectada')
        if entidad == 'No detectada' or not entidad:
            st.caption("⚠️ No detectada")
        else:
            st.info(entidad)

    with col2:
        st.markdown("**Modifica Normas:**")
        modifica = metadata.get('modifica_normas', [])
        if modifica:
            st.write(", ".join(modifica))
        else:
            st.caption("Ninguna")

    with col3:
        st.markdown("**Deroga Normas:**")
        deroga = metadata.get('deroga_normas', [])
        if deroga:
            st.write(", ".join(deroga))
        else:
            st.caption("Ninguna")

    # =========================================================================
    # SECCIÓN 3: Título y Sumilla
    # =========================================================================
    st.markdown("---")
    st.subheader("📝 Título y Sumilla")

    titulo = doc_completo.get('titulo')
    if titulo:
        st.markdown(f"**Título:**")
        st.info(titulo)
    else:
        st.warning("⚠️ Sin título registrado")

    sumilla = doc_completo.get('sumilla') or metadata.get('sumilla_generada')
    if sumilla:
        st.markdown(f"**Sumilla:**")
        st.text_area("", sumilla, height=100, key="qa_sumilla", disabled=True)
    else:
        st.warning("⚠️ Sin sumilla disponible")

    # =========================================================================
    # SECCIÓN 4: Texto Completo
    # =========================================================================
    st.markdown("---")
    st.subheader("📄 Texto Completo")

    if doc_info.get('ruta_txt'):
        try:
            with open(doc_info['ruta_txt'], 'r', encoding='utf-8') as f:
                texto_completo = f.read()

            # Estadísticas del texto
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Caracteres", len(texto_completo))
            with col2:
                st.metric("Palabras", len(texto_completo.split()))
            with col3:
                estimado_paginas = max(1, len(texto_completo) // 3000)
                st.metric("Páginas Estimadas", estimado_paginas)

            # Mostrar texto
            st.text_area(
                "Contenido completo",
                texto_completo,
                height=400,
                key="qa_texto_completo"
            )
        except Exception as e:
            st.error(f"❌ Error cargando texto: {e}")
    else:
        st.warning("⚠️ Archivo de texto no disponible")

    # =========================================================================
    # SECCIÓN 5: Artículos Parseados
    # =========================================================================
    st.markdown("---")
    st.subheader("📑 Artículos Parseados")

    articulos = doc_completo.get('articulos', [])

    if articulos:
        st.info(f"Total artículos parseados: {len(articulos)}")

        # Selector de artículo
        selected_art_idx = st.selectbox(
            "Seleccionar artículo",
            options=range(len(articulos)),
            format_func=lambda i: f"{articulos[i].get('numero', f'#{i+1}')} - {articulos[i].get('titulo', 'Sin título')[:50]}",
            key="qa_selected_article"
        )

        if selected_art_idx is not None:
            articulo = articulos[selected_art_idx]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Número:**")
                st.code(articulo.get('numero', 'N/A'))
            with col2:
                st.markdown("**Tipo:**")
                st.info(articulo.get('tipo_unidad', 'articulo'))
            with col3:
                st.markdown("**ID:**")
                st.code(articulo.get('id_articulo', 'N/A')[:20])

            if articulo.get('titulo'):
                st.markdown("**Título del artículo:**")
                st.info(articulo['titulo'])

            st.markdown("**Contenido:**")
            st.text_area(
                "",
                articulo.get('contenido', 'Sin contenido'),
                height=200,
                key=f"qa_art_content_{selected_art_idx}"
            )
    else:
        st.warning("⚠️ No se encontraron artículos parseados")

    # =========================================================================
    # SECCIÓN 6: Alertas de Calidad
    # =========================================================================
    st.markdown("---")
    st.subheader("⚠️ Alertas de Calidad")

    alertas = []

    # Verificar campos críticos faltantes
    if not doc_completo.get('titulo'):
        alertas.append(("warning", "Falta título del documento"))

    if not doc_completo.get('fecha') and not metadata.get('fecha_promulgacion'):
        alertas.append(("warning", "Falta fecha de promulgación"))

    if not metadata.get('numero_norma'):
        alertas.append(("warning", "No se detectó número de norma"))

    if metadata.get('area_principal') == 'otros':
        alertas.append(("info", "Área del derecho no clasificada automáticamente"))

    if metadata.get('jerarquia', 99) == 99:
        alertas.append(("info", "Jerarquía normativa no determinada"))

    if not metadata.get('entidad_emisora'):
        alertas.append(("info", "Entidad emisora no detectada"))

    if not articulos:
        alertas.append(("error", "No se parsearon artículos del documento"))
    elif len(articulos) < 3:
        alertas.append(("warning", f"Solo {len(articulos)} artículos parseados (puede ser incompleto)"))

    if not doc_info.get('ruta_txt'):
        alertas.append(("error", "Falta archivo de texto normalizado"))

    if not doc_completo.get('hash_contenido'):
        alertas.append(("warning", "Falta hash de contenido (no se puede verificar cambios)"))

    # Mostrar alertas
    if alertas:
        for tipo, mensaje in alertas:
            if tipo == "error":
                st.error(f"❌ {mensaje}")
            elif tipo == "warning":
                st.warning(f"⚠️ {mensaje}")
            else:
                st.info(f"ℹ️ {mensaje}")
    else:
        st.success("✅ No se detectaron problemas de calidad")

    # =========================================================================
    # SECCIÓN 7: Archivos Disponibles y Descarga
    # =========================================================================
    st.markdown("---")
    st.subheader("📁 Archivos Disponibles y Descarga")

    col1, col2, col3 = st.columns(3)

    with col1:
        if doc_info.get('ruta_pdf'):
            st.success("✅ PDF disponible")
            st.caption(doc_info['ruta_pdf'])

            # Botón de descarga PDF
            try:
                pdf_path = Path(doc_info['ruta_pdf'])
                if pdf_path.exists():
                    with open(pdf_path, 'rb') as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"{selected_doc_id}.pdf",
                        mime="application/pdf",
                        key=f"download_pdf_{selected_doc_id}"
                    )
                else:
                    st.caption("⚠️ Archivo no encontrado en disco")
            except Exception as e:
                st.caption(f"⚠️ Error: {e}")
        else:
            st.info("ℹ️ PDF no guardado")

    with col2:
        if doc_info.get('ruta_txt'):
            st.success("✅ TXT disponible")
            st.caption(doc_info['ruta_txt'])

            # Botón de descarga TXT
            try:
                txt_path = Path(doc_info['ruta_txt'])
                if txt_path.exists():
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        txt_content = f.read()
                    st.download_button(
                        label="⬇️ Descargar TXT",
                        data=txt_content,
                        file_name=f"{selected_doc_id}.txt",
                        mime="text/plain",
                        key=f"download_txt_{selected_doc_id}"
                    )
                else:
                    st.caption("⚠️ Archivo no encontrado en disco")
            except Exception as e:
                st.caption(f"⚠️ Error: {e}")
        else:
            st.error("❌ TXT no disponible")

    with col3:
        if doc_info.get('ruta_json'):
            st.success("✅ JSON disponible")
            st.caption(doc_info['ruta_json'])

            # Botón de descarga JSON
            try:
                json_path = Path(doc_info['ruta_json'])
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_content = f.read()
                    st.download_button(
                        label="⬇️ Descargar JSON",
                        data=json_content,
                        file_name=f"{selected_doc_id}.json",
                        mime="application/json",
                        key=f"download_json_{selected_doc_id}"
                    )
                else:
                    st.caption("⚠️ Archivo no encontrado en disco")
            except Exception as e:
                st.caption(f"⚠️ Error: {e}")
        else:
            st.error("❌ JSON no disponible")


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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Documentos",
        "📑 Artículos",
        "📊 Estadísticas",
        "🔍 QA/Revisión",
        "📝 Logs"
    ])

    with tab1:
        render_tab_documentos(sidebar_state['site_id'], sidebar_state['site_config'])

    with tab2:
        render_tab_articulos(sidebar_state['site_id'], sidebar_state['site_config'])

    with tab3:
        render_tab_estadisticas()

    with tab4:
        render_tab_qa_revision(sidebar_state['site_id'], sidebar_state['site_config'])

    with tab5:
        render_tab_logs(sidebar_state['site_id'], sidebar_state['site_config'])


if __name__ == "__main__":
    main()
