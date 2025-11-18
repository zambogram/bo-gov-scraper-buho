"""
Tests para modelos de datos
"""
import pytest
from scraper.models import Documento, Articulo


class TestArticulo:
    """Tests para modelo Articulo"""

    def test_crear_articulo(self, sample_articulo_data):
        """Test crear artículo"""
        art = Articulo(**sample_articulo_data)

        assert art.id_articulo == sample_articulo_data['id_articulo']
        assert art.id_documento == sample_articulo_data['id_documento']
        assert art.numero == sample_articulo_data['numero']
        assert art.contenido == sample_articulo_data['contenido']

    def test_articulo_to_dict(self, sample_articulo_data):
        """Test convertir artículo a dict"""
        art = Articulo(**sample_articulo_data)
        data = art.to_dict()

        assert isinstance(data, dict)
        assert data['id_articulo'] == art.id_articulo
        assert data['contenido'] == art.contenido

    def test_articulo_from_dict(self, sample_articulo_data):
        """Test crear artículo desde dict"""
        art = Articulo.from_dict(sample_articulo_data)

        assert art.id_articulo == sample_articulo_data['id_articulo']
        assert art.numero == sample_articulo_data['numero']


class TestDocumento:
    """Tests para modelo Documento"""

    def test_crear_documento(self, sample_documento_data):
        """Test crear documento"""
        doc = Documento(
            id_documento=sample_documento_data['id_documento'],
            site=sample_documento_data['site'],
            tipo_documento=sample_documento_data['tipo_documento']
        )

        assert doc.id_documento == sample_documento_data['id_documento']
        assert doc.site == sample_documento_data['site']

    def test_documento_calcular_hash(self, sample_documento_data):
        """Test calcular hash de documento"""
        doc = Documento(
            id_documento=sample_documento_data['id_documento'],
            site=sample_documento_data['site'],
            tipo_documento=sample_documento_data['tipo_documento'],
            texto_completo="Contenido de prueba"
        )

        hash1 = doc.calcular_hash()
        assert hash1 is not None
        assert len(hash1) == 32  # MD5 hash

        # Hash debe ser consistente
        hash2 = doc.calcular_hash()
        assert hash1 == hash2

    def test_documento_actualizar_hash(self, sample_documento_data):
        """Test actualizar hash de documento"""
        doc = Documento(
            id_documento=sample_documento_data['id_documento'],
            site=sample_documento_data['site'],
            tipo_documento=sample_documento_data['tipo_documento'],
            texto_completo="Contenido inicial"
        )

        doc.actualizar_hash()
        hash1 = doc.hash_contenido

        # Cambiar contenido
        doc.texto_completo = "Contenido modificado"
        doc.actualizar_hash()
        hash2 = doc.hash_contenido

        # Hash debe cambiar
        assert hash1 != hash2

    def test_documento_agregar_articulo(self, sample_documento_data, sample_articulo_data):
        """Test agregar artículo a documento"""
        doc = Documento(
            id_documento=sample_documento_data['id_documento'],
            site=sample_documento_data['site'],
            tipo_documento=sample_documento_data['tipo_documento']
        )

        art = Articulo(**sample_articulo_data)
        doc.agregar_articulo(art)

        assert len(doc.articulos) == 1
        assert doc.articulos[0].id_articulo == sample_articulo_data['id_articulo']

    def test_documento_to_dict(self, sample_documento_data):
        """Test convertir documento a dict"""
        doc = Documento(**{k: v for k, v in sample_documento_data.items() if k != 'metadata'})
        data = doc.to_dict(incluir_articulos=False)

        assert isinstance(data, dict)
        assert data['id_documento'] == doc.id_documento
        assert data['site'] == doc.site
        assert 'total_articulos' in data

    def test_documento_to_dict_con_articulos(self, sample_documento_data, sample_articulo_data):
        """Test convertir documento a dict con artículos"""
        doc = Documento(
            id_documento=sample_documento_data['id_documento'],
            site=sample_documento_data['site'],
            tipo_documento=sample_documento_data['tipo_documento']
        )

        art = Articulo(**sample_articulo_data)
        doc.agregar_articulo(art)

        data = doc.to_dict(incluir_articulos=True)

        assert 'articulos' in data
        assert len(data['articulos']) == 1
        assert data['articulos'][0]['id_articulo'] == sample_articulo_data['id_articulo']

    def test_documento_from_dict(self, sample_documento_data, sample_articulo_data):
        """Test crear documento desde dict"""
        data = {
            'id_documento': sample_documento_data['id_documento'],
            'site': sample_documento_data['site'],
            'tipo_documento': sample_documento_data['tipo_documento'],
            'articulos': [sample_articulo_data]
        }

        doc = Documento.from_dict(data)

        assert doc.id_documento == data['id_documento']
        assert len(doc.articulos) == 1
        assert doc.articulos[0].id_articulo == sample_articulo_data['id_articulo']

    def test_documento_hash_consistencia(self):
        """Test consistencia de hash entre documentos iguales"""
        doc1 = Documento(
            id_documento="test_1",
            site="tcp",
            tipo_documento="Ley",
            texto_completo="Mismo contenido"
        )

        doc2 = Documento(
            id_documento="test_2",
            site="tcp",
            tipo_documento="Ley",
            texto_completo="Mismo contenido"
        )

        # Hash debe ser igual para mismo contenido
        hash1 = doc1.calcular_hash()
        hash2 = doc2.calcular_hash()
        assert hash1 == hash2
