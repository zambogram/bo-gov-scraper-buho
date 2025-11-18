"""
Configuración y fixtures para pytest
"""
import pytest
from pathlib import Path
import json
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def sample_documento_data():
    """Datos de ejemplo para un documento"""
    return {
        'id_documento': 'test_ley_123_2024',
        'site': 'tcp',
        'tipo_documento': 'Ley',
        'numero_norma': '123',
        'fecha': '2024-05-15',
        'titulo': 'Ley de Ejemplo para Testing',
        'sumilla': 'Esta es una ley de ejemplo para testing',
        'url_origen': 'https://example.com/ley123',
        'texto_completo': 'Artículo 1. Este es el contenido del artículo 1.\nArtículo 2. Este es el contenido del artículo 2.',
        'metadata': {
            'tipo_norma': 'Ley',
            'jerarquia': 2,
            'area_principal': 'tributario',
            'areas_derecho': ['tributario', 'financiero'],
            'estado_vigencia': 'vigente',
            'entidad_emisora': 'Asamblea Legislativa Plurinacional',
            'palabras_clave': ['impuesto', 'tributario', 'fiscal'],
            'modifica_normas': [],
            'deroga_normas': [],
            'estadisticas': {
                'total_caracteres': 150,
                'total_palabras': 30,
                'estimado_paginas': 1
            }
        },
        'hash_contenido': 'abc123def456',
        'fecha_scraping': '2024-05-20T10:30:00'
    }


@pytest.fixture
def sample_articulo_data():
    """Datos de ejemplo para un artículo"""
    return {
        'id_articulo': 'test_ley_123_2024_art_1',
        'id_documento': 'test_ley_123_2024',
        'numero': '1',
        'titulo': 'Objeto de la Ley',
        'contenido': 'La presente ley tiene por objeto regular...',
        'tipo_unidad': 'articulo',
        'metadata': {}
    }


@pytest.fixture
def sample_texto_legal():
    """Texto legal de ejemplo para testing de extractores"""
    return """
    LEY N° 843
    DE REFORMA TRIBUTARIA

    La Asamblea Legislativa Plurinacional decreta:

    Artículo 1.- Esta ley tiene por objeto establecer un nuevo régimen tributario.

    Artículo 2.- Se crea el Impuesto al Valor Agregado (IVA).

    Artículo 3.- La presente ley modifica la Ley 123 y deroga la Ley 456.
    """


@pytest.fixture
def mock_site_config():
    """Configuración mock de un sitio"""
    from dataclasses import dataclass

    @dataclass
    class MockSiteConfig:
        id: str = "tcp"
        nombre: str = "Tribunal Constitucional Plurinacional"
        tipo: str = "Tribunal"
        categoria: str = "Judicial"
        url_base: str = "https://tcp.gob.bo"
        prioridad: int = 1
        ola: int = 1
        activo: bool = True

    return MockSiteConfig()
