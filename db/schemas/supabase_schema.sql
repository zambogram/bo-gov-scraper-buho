-- Schema de Supabase para BO-GOV-SCRAPER-BUHO
-- Incluye metadata extendida: área del derecho, jerarquía, estado de vigencia, etc.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- Tabla: sources (fuentes/sitios)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(50) UNIQUE NOT NULL,  -- tcp, tsj, asfi, etc.
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100),                      -- Tribunal, Ministerio, Entidad Reguladora
    categoria VARCHAR(100),                 -- Judicial, Tributario, etc.
    url_base TEXT,
    prioridad INTEGER DEFAULT 99,
    activo BOOLEAN DEFAULT true,
    metadata JSONB,                         -- Metadata adicional
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_source_id ON sources(source_id);
CREATE INDEX IF NOT EXISTS idx_sources_activo ON sources(activo);

-- ==============================================================================
-- Tabla: documents (documentos legales)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identificación
    id_documento VARCHAR(255) UNIQUE NOT NULL,
    source_id VARCHAR(50) REFERENCES sources(source_id),

    -- Clasificación básica
    tipo_documento VARCHAR(100),            -- Ley, Decreto Supremo, Sentencia, etc.
    numero_norma VARCHAR(100),
    fecha DATE,
    fecha_publicacion DATE,

    -- Contenido
    titulo TEXT,
    sumilla TEXT,
    url_origen TEXT,

    -- METADATA EXTENDIDA (NUEVA)
    tipo_norma VARCHAR(100),                -- Tipo normalizado
    jerarquia INTEGER,                      -- 1-99 (1=CPE, 2=Ley, etc.)
    area_principal VARCHAR(100),            -- constitucional, penal, tributario, etc.
    areas_derecho TEXT[],                   -- Array de áreas detectadas
    estado_vigencia VARCHAR(50),            -- vigente, modificada, derogada
    entidad_emisora VARCHAR(255),
    palabras_clave TEXT[],                  -- Array de palabras clave
    modifica_normas TEXT[],                 -- Array de normas que modifica
    deroga_normas TEXT[],                   -- Array de normas que deroga

    -- Archivos y rutas
    ruta_pdf TEXT,
    ruta_txt TEXT,
    ruta_json TEXT,

    -- Control de versiones
    hash_contenido VARCHAR(32),             -- MD5 hash
    fecha_scraping TIMESTAMP WITH TIME ZONE,
    fecha_ultima_actualizacion TIMESTAMP WITH TIME ZONE,

    -- Estadísticas
    total_articulos INTEGER DEFAULT 0,
    total_caracteres INTEGER DEFAULT 0,
    total_palabras INTEGER DEFAULT 0,
    paginas_estimadas INTEGER DEFAULT 0,

    -- Metadata adicional (flexible)
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para documents
CREATE INDEX IF NOT EXISTS idx_documents_id_documento ON documents(id_documento);
CREATE INDEX IF NOT EXISTS idx_documents_source_id ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_tipo_documento ON documents(tipo_documento);
CREATE INDEX IF NOT EXISTS idx_documents_numero_norma ON documents(numero_norma);
CREATE INDEX IF NOT EXISTS idx_documents_fecha ON documents(fecha);
CREATE INDEX IF NOT EXISTS idx_documents_area_principal ON documents(area_principal);
CREATE INDEX IF NOT EXISTS idx_documents_jerarquia ON documents(jerarquia);
CREATE INDEX IF NOT EXISTS idx_documents_estado_vigencia ON documents(estado_vigencia);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(hash_contenido);
CREATE INDEX IF NOT EXISTS idx_documents_areas ON documents USING GIN(areas_derecho);
CREATE INDEX IF NOT EXISTS idx_documents_palabras_clave ON documents USING GIN(palabras_clave);

-- Full text search
CREATE INDEX IF NOT EXISTS idx_documents_titulo_fts ON documents USING GIN(to_tsvector('spanish', titulo));
CREATE INDEX IF NOT EXISTS idx_documents_sumilla_fts ON documents USING GIN(to_tsvector('spanish', sumilla));

-- ==============================================================================
-- Tabla: articles (artículos/secciones de documentos)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identificación
    id_articulo VARCHAR(255) UNIQUE NOT NULL,
    id_documento VARCHAR(255) REFERENCES documents(id_documento) ON DELETE CASCADE,

    -- Estructura
    numero VARCHAR(50),                     -- "1", "5", "I", etc.
    titulo TEXT,
    contenido TEXT NOT NULL,
    tipo_unidad VARCHAR(50),                -- articulo, seccion, capitulo, titulo, disposicion

    -- Orden
    orden INTEGER,                          -- Orden dentro del documento

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para articles
CREATE INDEX IF NOT EXISTS idx_articles_id_articulo ON articles(id_articulo);
CREATE INDEX IF NOT EXISTS idx_articles_id_documento ON articles(id_documento);
CREATE INDEX IF NOT EXISTS idx_articles_tipo_unidad ON articles(tipo_unidad);
CREATE INDEX IF NOT EXISTS idx_articles_orden ON articles(orden);

-- Full text search en artículos
CREATE INDEX IF NOT EXISTS idx_articles_contenido_fts ON articles USING GIN(to_tsvector('spanish', contenido));

-- ==============================================================================
-- Tabla: extraction_logs (logs de extracción)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS extraction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Referencia
    id_documento VARCHAR(255) REFERENCES documents(id_documento) ON DELETE CASCADE,
    source_id VARCHAR(50) REFERENCES sources(source_id),

    -- Sesión
    session_id VARCHAR(100),                -- Timestamp de sesión
    modo VARCHAR(20),                       -- full, delta

    -- Resultados
    exito BOOLEAN DEFAULT true,
    total_encontrados INTEGER DEFAULT 0,
    total_descargados INTEGER DEFAULT 0,
    total_parseados INTEGER DEFAULT 0,
    total_errores INTEGER DEFAULT 0,
    duracion_segundos NUMERIC(10, 2),

    -- Errores
    errores JSONB,                          -- Array de errores si los hay

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_logs_id_documento ON extraction_logs(id_documento);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_source_id ON extraction_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_session_id ON extraction_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_extraction_logs_created_at ON extraction_logs(created_at DESC);

-- ==============================================================================
-- Tabla: embeddings (vectores para búsqueda semántica - opcional)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Referencia
    id_documento VARCHAR(255) REFERENCES documents(id_documento) ON DELETE CASCADE,
    id_articulo VARCHAR(255) REFERENCES articles(id_articulo) ON DELETE CASCADE,

    -- Vector
    embedding vector(1536),                 -- OpenAI ada-002 o similar

    -- Metadata
    tipo VARCHAR(50),                       -- documento_completo, articulo, sumilla
    texto_source TEXT,                      -- Texto usado para generar embedding

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_id_documento ON embeddings(id_documento);
CREATE INDEX IF NOT EXISTS idx_embeddings_id_articulo ON embeddings(id_articulo);

-- ==============================================================================
-- Funciones y triggers
-- ==============================================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_sources_updated_at ON sources;
CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
CREATE TRIGGER update_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- Vistas útiles
-- ==============================================================================

-- Vista: documentos con información de fuente
CREATE OR REPLACE VIEW vw_documents_full AS
SELECT
    d.*,
    s.nombre as source_nombre,
    s.tipo as source_tipo,
    s.categoria as source_categoria
FROM documents d
LEFT JOIN sources s ON d.source_id = s.source_id;

-- Vista: estadísticas por área del derecho
CREATE OR REPLACE VIEW vw_stats_por_area AS
SELECT
    area_principal,
    COUNT(*) as total_documentos,
    COUNT(DISTINCT source_id) as total_fuentes,
    SUM(total_articulos) as total_articulos,
    AVG(jerarquia) as jerarquia_promedio
FROM documents
WHERE area_principal IS NOT NULL
GROUP BY area_principal
ORDER BY total_documentos DESC;

-- Vista: estadísticas por jerarquía
CREATE OR REPLACE VIEW vw_stats_por_jerarquia AS
SELECT
    jerarquia,
    tipo_norma,
    COUNT(*) as total_documentos,
    COUNT(DISTINCT source_id) as total_fuentes
FROM documents
WHERE jerarquia IS NOT NULL
GROUP BY jerarquia, tipo_norma
ORDER BY jerarquia;

-- Vista: documentos vigentes por área
CREATE OR REPLACE VIEW vw_vigentes_por_area AS
SELECT
    area_principal,
    estado_vigencia,
    COUNT(*) as total
FROM documents
WHERE area_principal IS NOT NULL
GROUP BY area_principal, estado_vigencia
ORDER BY area_principal, estado_vigencia;

-- ==============================================================================
-- Comentarios
-- ==============================================================================

COMMENT ON TABLE sources IS 'Fuentes de datos (sitios web gubernamentales)';
COMMENT ON TABLE documents IS 'Documentos legales con metadata extendida';
COMMENT ON TABLE articles IS 'Artículos y secciones de documentos legales';
COMMENT ON TABLE extraction_logs IS 'Logs de sesiones de scraping y extracción';
COMMENT ON TABLE embeddings IS 'Vectores para búsqueda semántica (opcional)';

COMMENT ON COLUMN documents.jerarquia IS 'Jerarquía normativa: 1=CPE, 2=Ley, 3=DS, etc.';
COMMENT ON COLUMN documents.area_principal IS 'Área principal del derecho detectada automáticamente';
COMMENT ON COLUMN documents.estado_vigencia IS 'Estado: vigente, modificada, derogada';
