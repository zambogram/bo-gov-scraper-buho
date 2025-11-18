-- ================================================================
-- SCHEMA SUPABASE PARA BÚHO - MEMORIA LEGAL DINÁMICA (MLD)
-- ================================================================
-- Sistema de scraping de normativa boliviana con soporte para pgvector
-- Versión: FASE 8 - Exportaciones Profesionales
-- ================================================================

-- Extensión para vectores (embeddings con pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- ================================================================
-- TABLA: sources
-- Descripción: Catálogo de sitios fuente de normativa
-- ================================================================
CREATE TABLE IF NOT EXISTS sources (
    sitio TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    url TEXT NOT NULL,
    descripcion TEXT,
    configuracion JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE sources IS 'Catálogo de fuentes de normativa boliviana';
COMMENT ON COLUMN sources.sitio IS 'Identificador único del sitio (ej: gaceta, abi, verbo_juridico)';
COMMENT ON COLUMN sources.configuracion IS 'Configuración JSON del scraper para este sitio';

-- ================================================================
-- TABLA: documents
-- Descripción: Documentos normativos completos extraídos
-- ================================================================
CREATE TABLE IF NOT EXISTS documents (
    id_documento TEXT PRIMARY KEY,
    sitio TEXT NOT NULL REFERENCES sources(sitio),
    tipo_norma TEXT,
    numero_norma TEXT,
    fecha_norma TEXT,
    titulo TEXT,
    url_fuente TEXT,
    url_pdf TEXT,
    filename_pdf TEXT,
    metodo_extraccion TEXT,
    paginas INTEGER,
    caracteres INTEGER,
    total_articulos INTEGER,
    fecha_extraccion TIMESTAMP DEFAULT NOW(),
    estado TEXT DEFAULT 'extraido',
    raw_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE documents IS 'Documentos normativos completos (leyes, decretos, resoluciones, etc.)';
COMMENT ON COLUMN documents.id_documento IS 'ID único del documento (formato: sitio_tipo_numero_fecha)';
COMMENT ON COLUMN documents.metodo_extraccion IS 'Método usado: pdf_text, ocr, html, api';
COMMENT ON COLUMN documents.estado IS 'Estado del documento: extraido, procesado, vectorizado, error';
COMMENT ON COLUMN documents.raw_metadata IS 'Metadatos originales en formato JSON';

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_documents_sitio ON documents(sitio);
CREATE INDEX IF NOT EXISTS idx_documents_tipo_norma ON documents(tipo_norma);
CREATE INDEX IF NOT EXISTS idx_documents_fecha_norma ON documents(fecha_norma);
CREATE INDEX IF NOT EXISTS idx_documents_estado ON documents(estado);
CREATE INDEX IF NOT EXISTS idx_documents_fecha_extraccion ON documents(fecha_extraccion);

-- ================================================================
-- TABLA: articles
-- Descripción: Artículos individuales extraídos de los documentos
-- ================================================================
CREATE TABLE IF NOT EXISTS articles (
    id_articulo TEXT PRIMARY KEY,
    id_documento TEXT NOT NULL REFERENCES documents(id_documento) ON DELETE CASCADE,
    numero_articulo TEXT,
    titulo_articulo TEXT,
    contenido TEXT NOT NULL,
    tipo_norma TEXT,
    fecha_norma TEXT,
    sitio TEXT NOT NULL,
    orden INTEGER,
    raw TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE articles IS 'Artículos individuales de documentos normativos';
COMMENT ON COLUMN articles.id_articulo IS 'ID único del artículo (formato: id_documento_artNNN)';
COMMENT ON COLUMN articles.numero_articulo IS 'Número del artículo dentro del documento';
COMMENT ON COLUMN articles.orden IS 'Orden del artículo dentro del documento';
COMMENT ON COLUMN articles.raw IS 'Texto sin procesar del artículo';

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_articles_id_documento ON articles(id_documento);
CREATE INDEX IF NOT EXISTS idx_articles_sitio ON articles(sitio);
CREATE INDEX IF NOT EXISTS idx_articles_tipo_norma ON articles(tipo_norma);
CREATE INDEX IF NOT EXISTS idx_articles_fecha_norma ON articles(fecha_norma);
CREATE INDEX IF NOT EXISTS idx_articles_orden ON articles(orden);

-- Índice para búsqueda de texto completo
CREATE INDEX IF NOT EXISTS idx_articles_contenido_fulltext ON articles USING GIN(to_tsvector('spanish', contenido));

-- ================================================================
-- TABLA: embeddings
-- Descripción: Vectores de embeddings para búsqueda semántica
-- ================================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    id_articulo TEXT NOT NULL REFERENCES articles(id_articulo) ON DELETE CASCADE,
    embedding VECTOR(1536),
    modelo TEXT DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(id_articulo, modelo)
);

COMMENT ON TABLE embeddings IS 'Embeddings vectoriales para búsqueda semántica con pgvector';
COMMENT ON COLUMN embeddings.embedding IS 'Vector de 1536 dimensiones (OpenAI ada-002)';
COMMENT ON COLUMN embeddings.modelo IS 'Modelo usado para generar el embedding';

-- Índice para búsqueda vectorial por similitud de coseno
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_embeddings_articulo ON embeddings(id_articulo);

-- ================================================================
-- TABLA: extraction_logs
-- Descripción: Logs de extracción para auditoría y debugging
-- ================================================================
CREATE TABLE IF NOT EXISTS extraction_logs (
    id SERIAL PRIMARY KEY,
    id_documento TEXT REFERENCES documents(id_documento),
    sitio TEXT,
    tipo_operacion TEXT,
    estado TEXT,
    mensaje TEXT,
    detalles JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE extraction_logs IS 'Registro de operaciones de extracción y procesamiento';
COMMENT ON COLUMN extraction_logs.tipo_operacion IS 'Tipo: scraping, extraction, vectorization, export';

CREATE INDEX IF NOT EXISTS idx_extraction_logs_documento ON extraction_logs(id_documento);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_sitio ON extraction_logs(sitio);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_created_at ON extraction_logs(created_at);

-- ================================================================
-- VISTAS ÚTILES
-- ================================================================

-- Vista: Documentos con conteo de artículos
CREATE OR REPLACE VIEW view_documents_stats AS
SELECT
    d.id_documento,
    d.sitio,
    d.tipo_norma,
    d.numero_norma,
    d.fecha_norma,
    d.titulo,
    d.total_articulos,
    COUNT(a.id_articulo) AS articulos_extraidos,
    COUNT(e.id) AS articulos_vectorizados,
    d.estado,
    d.fecha_extraccion
FROM documents d
LEFT JOIN articles a ON d.id_documento = a.id_documento
LEFT JOIN embeddings e ON a.id_articulo = e.id_articulo
GROUP BY d.id_documento;

-- Vista: Artículos enriquecidos con metadata del documento
CREATE OR REPLACE VIEW view_articles_enriched AS
SELECT
    a.id_articulo,
    a.numero_articulo,
    a.titulo_articulo,
    a.contenido,
    a.orden,
    d.id_documento,
    d.tipo_norma,
    d.numero_norma,
    d.fecha_norma,
    d.titulo AS titulo_documento,
    d.sitio,
    s.nombre AS nombre_sitio,
    d.url_fuente,
    EXISTS(SELECT 1 FROM embeddings e WHERE e.id_articulo = a.id_articulo) AS tiene_embedding
FROM articles a
JOIN documents d ON a.id_documento = d.id_documento
JOIN sources s ON d.sitio = s.sitio;

-- ================================================================
-- FUNCIONES ÚTILES
-- ================================================================

-- Función: Búsqueda semántica por similitud de embeddings
CREATE OR REPLACE FUNCTION buscar_articulos_similares(
    query_embedding VECTOR(1536),
    limit_results INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id_articulo TEXT,
    numero_articulo TEXT,
    contenido TEXT,
    tipo_norma TEXT,
    numero_norma TEXT,
    fecha_norma TEXT,
    sitio TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id_articulo,
        a.numero_articulo,
        a.contenido,
        a.tipo_norma,
        d.numero_norma,
        a.fecha_norma,
        a.sitio,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM embeddings e
    JOIN articles a ON e.id_articulo = a.id_articulo
    JOIN documents d ON a.id_documento = d.id_documento
    WHERE 1 - (e.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Función: Actualizar timestamp de updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar updated_at
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- DATOS INICIALES: Fuentes de normativa boliviana
-- ================================================================

INSERT INTO sources (sitio, nombre, url, descripcion, configuracion) VALUES
('gaceta', 'Gaceta Oficial de Bolivia', 'https://www.gacetaoficialdebolivia.gob.bo', 'Gaceta Oficial del Estado Plurinacional de Bolivia', '{"scraping_enabled": true, "pdf_support": true, "ocr_enabled": false}'),
('abi', 'Agencia Boliviana de Información', 'https://www.abi.bo', 'Agencia de noticias estatal - Normativa y comunicados oficiales', '{"scraping_enabled": true, "pdf_support": false, "ocr_enabled": false}'),
('verbo_juridico', 'Verbo Jurídico', 'https://www.verbojuridico.com', 'Portal de información jurídica boliviana', '{"scraping_enabled": true, "pdf_support": true, "ocr_enabled": false}'),
('lexivox', 'Lexivox', 'https://www.lexivox.org', 'Base de datos de normativa boliviana', '{"scraping_enabled": true, "pdf_support": true, "ocr_enabled": false}'),
('tribunal_constitucional', 'Tribunal Constitucional Plurinacional', 'https://buscador.tcpbolivia.bo', 'Sentencias constitucionales', '{"scraping_enabled": true, "pdf_support": true, "ocr_enabled": false}')
ON CONFLICT (sitio) DO NOTHING;

-- ================================================================
-- POLÍTICAS RLS (Row Level Security) - OPCIONAL
-- ================================================================
-- Descomentar si necesitas control de acceso por roles

-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Allow public read access to documents" ON documents FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access to articles" ON articles FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access to embeddings" ON embeddings FOR SELECT USING (true);

-- ================================================================
-- FIN DEL SCHEMA
-- ================================================================
