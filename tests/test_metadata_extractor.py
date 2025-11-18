"""
Tests para LegalMetadataExtractor
"""
import pytest
from scraper.metadata_extractor import LegalMetadataExtractor


class TestLegalMetadataExtractor:
    """Tests para extractor de metadata legal"""

    @pytest.fixture
    def extractor(self):
        """Fixture para el extractor"""
        return LegalMetadataExtractor()

    def test_extraer_numero_norma(self, extractor):
        """Test extracción de número de norma"""
        texto = "LEY N° 843 DE REFORMA TRIBUTARIA"
        numero = extractor._extraer_numero_norma(texto)
        assert numero == "843"

    def test_extraer_numero_decreto(self, extractor):
        """Test extracción de número de decreto"""
        texto = "DECRETO SUPREMO N° 24051"
        numero = extractor._extraer_numero_norma(texto)
        assert numero == "24051"

    def test_extraer_tipo_norma(self, extractor):
        """Test extracción de tipo de norma"""
        texto = "LEY N° 843"
        tipo = extractor._extraer_tipo_norma(texto)
        assert tipo == "Ley"

        texto_ds = "DECRETO SUPREMO N° 123"
        tipo_ds = extractor._extraer_tipo_norma(texto_ds)
        assert tipo_ds == "Decreto Supremo"

    def test_determinar_jerarquia(self, extractor):
        """Test determinación de jerarquía normativa"""
        assert extractor._determinar_jerarquia("Ley") == 2
        assert extractor._determinar_jerarquia("Decreto Supremo") == 3
        assert extractor._determinar_jerarquia("Resolución Ministerial") == 5
        assert extractor._determinar_jerarquia("Documento Legal") == 99

    def test_clasificar_area_tributario(self, extractor, sample_texto_legal):
        """Test clasificación de área del derecho - tributario"""
        areas = extractor._clasificar_area_derecho(sample_texto_legal.lower())
        assert 'tributario' in areas or len(areas) > 0

    def test_clasificar_area_penal(self, extractor):
        """Test clasificación de área del derecho - penal"""
        texto_penal = "delito homicidio pena prisión código penal"
        areas = extractor._clasificar_area_derecho(texto_penal)
        assert 'penal' in areas

    def test_estado_vigencia_vigente(self, extractor):
        """Test estado de vigencia - vigente"""
        texto = "Esta ley está vigente"
        estado = extractor._determinar_estado_vigencia(texto)
        assert estado == "vigente"

    def test_estado_vigencia_derogada(self, extractor):
        """Test estado de vigencia - derogada"""
        texto = "Esta ley ha sido derogada"
        estado = extractor._determinar_estado_vigencia(texto)
        assert estado == "derogada"

    def test_estado_vigencia_modificada(self, extractor):
        """Test estado de vigencia - modificada"""
        texto = "Esta ley ha sido modificada"
        estado = extractor._determinar_estado_vigencia(texto)
        assert estado == "modificada"

    def test_extraer_normas_modificadas(self, extractor, sample_texto_legal):
        """Test extracción de normas modificadas"""
        normas = extractor._extraer_normas_modificadas(sample_texto_legal)
        assert '123' in normas

    def test_extraer_normas_derogadas(self, extractor, sample_texto_legal):
        """Test extracción de normas derogadas"""
        normas = extractor._extraer_normas_derogadas(sample_texto_legal)
        assert '456' in normas

    def test_extraer_metadata_completa(self, extractor, sample_texto_legal):
        """Test extracción completa de metadata"""
        metadata = extractor.extraer_metadata_completa(
            texto=sample_texto_legal,
            titulo="Ley N° 843 de Reforma Tributaria"
        )

        # Verificar campos básicos
        assert metadata['numero_norma'] is not None
        assert metadata['tipo_norma'] is not None
        assert metadata['jerarquia'] is not None

        # Verificar áreas
        assert 'areas_derecho' in metadata
        assert len(metadata['areas_derecho']) > 0

        # Verificar estado
        assert metadata['estado_vigencia'] in ['vigente', 'modificada', 'derogada']

        # Verificar relaciones
        assert 'modifica_normas' in metadata
        assert 'deroga_normas' in metadata

        # Verificar estadísticas
        assert 'estadisticas' in metadata
        assert metadata['estadisticas']['total_caracteres'] > 0

    def test_palabras_clave_tributario(self, extractor):
        """Test extracción de palabras clave - área tributaria"""
        areas = ['tributario']
        palabras = extractor._extraer_palabras_clave("", areas)
        assert len(palabras) > 0
        assert any('tributario' in p or 'impuesto' in p for p in palabras)

    def test_generar_sumilla(self, extractor):
        """Test generación automática de sumilla"""
        texto = """
        Primera línea significativa del documento.
        Segunda línea con más contenido importante.
        Tercera línea adicional.
        """
        sumilla = extractor._generar_sumilla(texto)
        assert len(sumilla) > 0
        assert len(sumilla) <= 303  # 300 + "..."
