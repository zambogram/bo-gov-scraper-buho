"""
BÚHO - Bolivian Government Document Scraper
Streamlit Web Interface
"""
import sys
import os
import json
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import get_scraper, SCRAPERS
from scraper.parser import LegalParser

# Page configuration
st.set_page_config(
    page_title="BÚHO - Government Scraper",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🦉 BÚHO - Bolivian Government Document Scraper")
st.markdown("---")


# Sidebar
with st.sidebar:
    st.header("📋 Sites")

    # Get stats for all sites
    site_stats = {}
    for site_name in SCRAPERS.keys():
        scraper = get_scraper(site_name)
        stats = scraper.get_stats()
        site_stats[site_name] = stats

    # Site selector
    selected_site = st.selectbox(
        "Select Site",
        options=list(SCRAPERS.keys()),
        format_func=lambda x: x.upper()
    )

    # Display selected site info
    if selected_site:
        stats = site_stats[selected_site]
        st.markdown(f"### {selected_site.upper()}")
        st.metric("Total Documents", stats['total_documents'])
        st.metric("Total Articles", stats['total_articles'])
        st.caption(f"Last Update: {stats['last_update'] or 'Never'}")

    st.markdown("---")

    # Scraping controls
    st.header("🔧 Actions")

    # Scraping limit
    scrape_limit = st.number_input("Scrape Limit", min_value=1, max_value=100, value=10)
    only_new = st.checkbox("Only New Documents")

    # Single site scraping
    if st.button(f"🔍 Scrape {selected_site.upper()}", use_container_width=True):
        with st.spinner(f"Scraping {selected_site}..."):
            scraper = get_scraper(selected_site)
            result = scraper.scrape(limit=scrape_limit, only_new=only_new)

            # Parse articles
            documents = scraper.load_index()
            articles = LegalParser.parse_all_documents(documents)
            scraper.save_articles(articles)

            st.success(f"""
            ✅ Scraping Complete!
            - New: {result['new']}
            - Modified: {result['modified']}
            - Unchanged: {result['unchanged']}
            - Articles Parsed: {len(articles)}
            """)

    # All sites scraping
    if st.button("🔍 Scrape ALL Sites", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_sites = len(SCRAPERS)
        total_stats = {'new': 0, 'modified': 0, 'unchanged': 0, 'errors': 0}

        for i, site_name in enumerate(SCRAPERS.keys()):
            status_text.text(f"Scraping {site_name}...")
            scraper = get_scraper(site_name)
            result = scraper.scrape(limit=scrape_limit, only_new=only_new)

            # Parse articles
            documents = scraper.load_index()
            articles = LegalParser.parse_all_documents(documents)
            scraper.save_articles(articles)

            for key in total_stats:
                total_stats[key] += result.get(key, 0)

            progress_bar.progress((i + 1) / total_sites)

        status_text.empty()
        progress_bar.empty()

        st.success(f"""
        ✅ All Sites Scraped!
        - Total New: {total_stats['new']}
        - Total Modified: {total_stats['modified']}
        - Total Unchanged: {total_stats['unchanged']}
        """)

    st.markdown("---")

    # Export controls
    st.header("📤 Export")

    if st.button(f"💾 Export {selected_site.upper()} JSONL", use_container_width=True):
        scraper = get_scraper(selected_site)
        result = scraper.export_jsonl()
        st.success(f"""
        ✅ Exported!
        - Documents: {result['documents']}
        - Articles: {result['articles']}
        """)

    if st.button("💾 Export ALL JSONL", use_container_width=True):
        total_docs = 0
        total_arts = 0
        for site_name in SCRAPERS.keys():
            scraper = get_scraper(site_name)
            result = scraper.export_jsonl()
            total_docs += result['documents']
            total_arts += result['articles']

        st.success(f"""
        ✅ All Exports Complete!
        - Total Documents: {total_docs}
        - Total Articles: {total_arts}
        """)

    st.markdown("---")

    # Supabase sync controls
    st.header("☁️ Supabase Sync")

    try:
        from sync.supabase_sync import sync_documents_to_supabase, sync_articles_to_supabase, sync_all_sites

        if st.button(f"⬆️ Sync {selected_site.upper()} (New)", use_container_width=True):
            with st.spinner("Syncing..."):
                doc_stats = sync_documents_to_supabase(selected_site, only_new=True)
                art_stats = sync_articles_to_supabase(selected_site, only_new=True)
                st.success(f"""
                ✅ Synced!
                - Docs Inserted: {doc_stats['inserted']}
                - Articles Inserted: {art_stats['inserted']}
                """)

        if st.button(f"⬆️ Sync {selected_site.upper()} (All)", use_container_width=True):
            with st.spinner("Syncing..."):
                doc_stats = sync_documents_to_supabase(selected_site, only_new=False)
                art_stats = sync_articles_to_supabase(selected_site, only_new=False)
                st.success(f"""
                ✅ Synced!
                - Docs: {doc_stats['inserted']} inserted, {doc_stats['updated']} updated
                - Articles: {art_stats['inserted']} inserted, {art_stats['updated']} updated
                """)

        if st.button("⬆️ Sync ALL Sites (New)", use_container_width=True):
            with st.spinner("Syncing all sites..."):
                result = sync_all_sites(only_new=True)
                st.success(f"""
                ✅ All Sites Synced!
                - Docs Inserted: {result['documents']['inserted']}
                - Articles Inserted: {result['articles']['inserted']}
                """)

        if st.button("⬆️ Sync ALL Sites (All)", use_container_width=True):
            with st.spinner("Syncing all sites..."):
                result = sync_all_sites(only_new=False)
                st.success(f"""
                ✅ All Sites Synced!
                - Docs: {result['documents']['inserted']} inserted, {result['documents']['updated']} updated
                - Articles: {result['articles']['inserted']} inserted, {result['articles']['updated']} updated
                """)

    except Exception as e:
        st.warning(f"Supabase not configured: {str(e)}")
        st.caption("Set SUPABASE_URL and SUPABASE_KEY in .env file")


# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📄 Documents", "📑 Articles", "📊 Statistics", "📝 Logs"])

with tab1:
    st.header(f"Documents - {selected_site.upper()}")

    scraper = get_scraper(selected_site)
    documents = scraper.load_index()

    if documents:
        # Convert to DataFrame
        df_docs = pd.DataFrame(documents)

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", len(documents))
        with col2:
            new_count = len([d for d in documents if d.get('status') == 'new'])
            st.metric("New", new_count)
        with col3:
            modified_count = len([d for d in documents if d.get('status') == 'modified'])
            st.metric("Modified", modified_count)

        # Display table
        st.dataframe(
            df_docs[['id', 'title', 'url', 'status', 'scraped_at']],
            use_container_width=True,
            height=400
        )

        # Document viewer
        st.subheader("📖 Document Viewer")
        selected_doc = st.selectbox(
            "Select Document to View",
            options=range(len(documents)),
            format_func=lambda i: documents[i]['title']
        )

        if selected_doc is not None:
            doc = documents[selected_doc]
            st.json(doc)

    else:
        st.info(f"No documents found for {selected_site}. Run scraping first.")

with tab2:
    st.header(f"Articles - {selected_site.upper()}")

    articles = scraper.load_articles()

    if articles:
        # Convert to DataFrame
        df_articles = pd.DataFrame(articles)

        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Articles", len(articles))
        with col2:
            unique_docs = len(set(a['document_id'] for a in articles))
            st.metric("Source Documents", unique_docs)

        # Display table
        st.dataframe(
            df_articles[['id', 'document_id', 'article_number', 'content']].head(100),
            use_container_width=True,
            height=400
        )

        # Article viewer
        st.subheader("📖 Article Viewer")
        selected_article = st.selectbox(
            "Select Article to View",
            options=range(min(50, len(articles))),
            format_func=lambda i: f"Article {articles[i]['article_number']} - {articles[i]['id']}"
        )

        if selected_article is not None:
            article = articles[selected_article]
            st.markdown(f"**Article {article['article_number']}**")
            st.text_area("Content", article['content'], height=200)
            with st.expander("Metadata"):
                st.json(article.get('metadata', {}))

    else:
        st.info(f"No articles found for {selected_site}. Run scraping first.")

with tab3:
    st.header("📊 Statistics & Analytics")

    # Overall statistics
    st.subheader("Overall Statistics")

    total_docs = sum(s['total_documents'] for s in site_stats.values())
    total_articles = sum(s['total_articles'] for s in site_stats.values())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sites", len(SCRAPERS))
    with col2:
        st.metric("Total Documents", total_docs)
    with col3:
        st.metric("Total Articles", total_articles)

    # Volume by site chart
    st.subheader("📊 Volume by Site")

    site_names = list(site_stats.keys())
    doc_counts = [site_stats[s]['total_documents'] for s in site_names]
    article_counts = [site_stats[s]['total_articles'] for s in site_names]

    fig_volume = go.Figure(data=[
        go.Bar(name='Documents', x=site_names, y=doc_counts),
        go.Bar(name='Articles', x=site_names, y=article_counts)
    ])
    fig_volume.update_layout(
        title="Documents and Articles by Site",
        xaxis_title="Site",
        yaxis_title="Count",
        barmode='group'
    )
    st.plotly_chart(fig_volume, use_container_width=True)

    # Site comparison
    st.subheader("📊 Site Comparison")

    comparison_df = pd.DataFrame([
        {
            'Site': s,
            'Documents': site_stats[s]['total_documents'],
            'Articles': site_stats[s]['total_articles'],
            'Last Update': site_stats[s]['last_update'] or 'Never'
        }
        for s in site_names
    ])

    st.dataframe(comparison_df, use_container_width=True)

    # Pie chart
    fig_pie = px.pie(
        values=doc_counts,
        names=site_names,
        title="Document Distribution by Site"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with tab4:
    st.header("📝 Logs")

    # Display sync logs if available
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'sync')

    if os.path.exists(logs_dir):
        log_files = sorted([f for f in os.listdir(logs_dir) if f.endswith('.json')], reverse=True)

        if log_files:
            st.subheader("Recent Sync Logs")

            selected_log = st.selectbox("Select Log File", log_files)

            if selected_log:
                log_path = os.path.join(logs_dir, selected_log)
                with open(log_path, 'r') as f:
                    log_data = json.load(f)

                st.json(log_data)
        else:
            st.info("No sync logs found yet.")
    else:
        st.info("Logs directory not created yet.")

    # Live scraping logs
    st.subheader("🔴 Live Scraping Status")
    st.info("Live logging will appear here during scraping operations.")


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🦉 <strong>BÚHO</strong> - Bolivian Government Document Scraper | FASE 10</p>
    <p><small>Scraping: TCP, TSJ, ASFI, SIN, Contraloría</small></p>
</div>
""", unsafe_allow_html=True)
