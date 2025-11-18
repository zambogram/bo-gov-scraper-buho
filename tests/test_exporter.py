"""
Tests para DataExporter
"""
import pytest
import csv
import json
from pathlib import Path
from scraper.exporter import DataExporter
from scraper.models import Documento, Articulo


class TestDataExporter:
    """Tests para exportador de datos"""

    @pytest.fixture
    def exporter(self, temp_dir):
        """Fixture para el exportador"""
        return DataExporter(export_dir=temp_dir)

    @pytest.fixture
    def documento_completo(self, sample_documento_data, sample_articulo_data):
        """Fixture de documento completo con artículos"""
        doc = Documento(**{k: v for k, v in sample_documento_data.items() if k != 'metadata'})
        doc.metadata = sample_documento_data['metadata']

        # Agregar artículo
        art = Articulo(**sample_articulo_data)
        doc.agregar_articulo(art)

        # Calcular hash
        doc.actualizar_hash()

        return doc

    def test_iniciar_sesion_exportacion(self, exporter, temp_dir):
        """Test iniciar sesión de exportación"""
        exporter.iniciar_sesion_exportacion("tcp", "20250118_143025")

        # Verificar que se crearon los archivos
        session_dir = temp_dir / "tcp" / "20250118_143025"
        assert session_dir.exists()
        assert (session_dir / "documentos.csv").exists()
        assert (session_dir / "articulos.csv").exists()
        assert (session_dir / "registro_historico.jsonl").exists()

    def test_exportar_documento(self, exporter, documento_completo, temp_dir):
        """Test exportar documento"""
        exporter.iniciar_sesion_exportacion("tcp", "20250118_143025")

        metadata_extendida = documento_completo.metadata

        # Exportar documento
        exporter.exportar_documento(documento_completo, metadata_extendida)

        # Cerrar sesión
        rutas = exporter.finalizar_sesion_exportacion()

        # Verificar CSV de documentos
        with open(rutas['csv_documentos'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['id_documento'] == documento_completo.id_documento
            assert rows[0]['tipo_documento'] == documento_completo.tipo_documento

    def test_exportar_articulos(self, exporter, documento_completo, temp_dir):
        """Test exportar artículos"""
        exporter.iniciar_sesion_exportacion("tcp", "20250118_143025")

        metadata_extendida = documento_completo.metadata
        exporter.exportar_documento(documento_completo, metadata_extendida)

        rutas = exporter.finalizar_sesion_exportacion()

        # Verificar CSV de artículos
        with open(rutas['csv_articulos'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(documento_completo.articulos)

    def test_registro_historico_jsonl(self, exporter, documento_completo, temp_dir):
        """Test registro histórico en JSONL"""
        exporter.iniciar_sesion_exportacion("tcp", "20250118_143025")

        metadata_extendida = documento_completo.metadata
        exporter.exportar_documento(documento_completo, metadata_extendida)

        rutas = exporter.finalizar_sesion_exportacion()

        # Verificar JSONL
        with open(rutas['registro_historico'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1

            data = json.loads(lines[0])
            assert data['id_documento'] == documento_completo.id_documento
            assert 'metadata_completa' in data

    def test_generar_reporte_completo(self, exporter, temp_dir):
        """Test generar reporte completo"""
        stats = {
            'total_encontrados': 10,
            'total_descargados': 10,
            'total_parseados': 10,
            'total_errores': 0
        }

        reporte_path = exporter.generar_reporte_completo(
            "tcp",
            "20250118_143025",
            stats
        )

        assert reporte_path.exists()

        # Verificar contenido del reporte
        with open(reporte_path, 'r', encoding='utf-8') as f:
            reporte = json.load(f)

        assert reporte['site_id'] == "tcp"
        assert reporte['timestamp'] == "20250118_143025"
        assert 'estadisticas' in reporte
        assert reporte['estadisticas']['total_parseados'] == 10

    def test_metadata_extendida_en_csv(self, exporter, documento_completo, temp_dir):
        """Test que metadata extendida se exporta correctamente"""
        exporter.iniciar_sesion_exportacion("tcp", "20250118_143025")

        metadata_extendida = {
            'area_principal': 'tributario',
            'areas_derecho': ['tributario', 'financiero'],
            'jerarquia': 2,
            'estado_vigencia': 'vigente',
            'entidad_emisora': 'Asamblea Legislativa',
            'numero_norma': '843'
        }

        exporter.exportar_documento(documento_completo, metadata_extendida)
        rutas = exporter.finalizar_sesion_exportacion()

        # Verificar campos de metadata en CSV
        with open(rutas['csv_documentos'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)

            assert row['area_principal'] == 'tributario'
            assert 'tributario' in row['areas_derecho']
            assert row['jerarquia'] == '2'
            assert row['estado_vigencia'] == 'vigente'
