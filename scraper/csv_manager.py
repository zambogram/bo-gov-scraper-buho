"""
MÓDULO 5: CSV MANAGER
=====================
Este módulo se encarga de:
1. Gestionar el CSV de documentos (documentos.csv)
2. Gestionar el CSV de artículos (articulos.csv)
3. Actualizar ambos CSVs sin perder datos anteriores
4. Evitar duplicados basándose en IDs únicos

FUENTES DE VERDAD:
- data/csv/documentos.csv: Un registro por cada documento legal procesado
- data/csv/articulos.csv: Un registro por cada artículo de cada documento

Autor: Sistema BÚHO
"""

import pandas as pd
import os
from typing import Dict, List, Optional
from datetime import datetime


class CSVManager:
    """
    Clase para gestionar los archivos CSV del proyecto.

    Mantiene dos CSVs principales:
    1. documentos.csv: Información de cada documento legal
    2. articulos.csv: Información de cada artículo de cada documento
    """

    def __init__(self, csv_dir: str = "data/csv"):
        """
        Inicializa el gestor de CSVs.

        Args:
            csv_dir: Directorio donde se guardan los CSVs
        """
        self.csv_dir = csv_dir
        os.makedirs(csv_dir, exist_ok=True)

        self.documentos_csv_path = os.path.join(csv_dir, 'documentos.csv')
        self.articulos_csv_path = os.path.join(csv_dir, 'articulos.csv')

        # Columnas para el CSV de documentos
        self.DOCUMENTOS_COLUMNS = [
            'document_id',           # ID único del documento
            'tipo_norma',            # Ley, Decreto, etc.
            'numero_norma',          # Número de la norma
            'fecha_norma',           # Fecha de la norma
            'entidad_emisora',       # Entidad que emitió
            'titulo_original',       # Título original del documento
            'url_pdf',               # URL del PDF original
            'filename_pdf',          # Nombre del archivo PDF
            'filepath_pdf',          # Ruta del PDF en disco
            'size_bytes',            # Tamaño del PDF en bytes
            'download_date',         # Fecha de descarga
            'texto_extraido',        # Si se extrajo texto (True/False)
            'metodo_extraccion',     # 'digital' o 'ocr'
            'filepath_txt',          # Ruta del archivo .txt
            'paginas',               # Número de páginas
            'caracteres_extraidos',  # Número de caracteres extraídos
            'total_articulos',       # Número de artículos encontrados
            'filepath_json',         # Ruta del JSON parseado
            'procesamiento_completo',# Si el procesamiento fue exitoso
            'error_mensaje',         # Mensaje de error si lo hubo
            'fecha_procesamiento'    # Fecha de procesamiento
        ]

        # Columnas para el CSV de artículos
        self.ARTICULOS_COLUMNS = [
            'articulo_id',           # ID único del artículo
            'document_id',           # ID del documento padre
            'numero_articulo',       # Número del artículo
            'titulo_articulo',       # Título del artículo
            'contenido',             # Contenido completo del artículo
            'num_incisos',           # Número de incisos
            'num_paragrafos',        # Número de parágrafos
            'caracteres',            # Longitud del contenido
            'fecha_extraccion'       # Fecha de extracción
        ]

    def load_or_create_documentos_csv(self) -> pd.DataFrame:
        """
        Carga el CSV de documentos si existe, o crea uno nuevo.

        Returns:
            DataFrame con los documentos
        """
        if os.path.exists(self.documentos_csv_path):
            print(f"    → Cargando CSV existente: {self.documentos_csv_path}")
            df = pd.read_csv(self.documentos_csv_path)
            print(f"      Se encontraron {len(df)} documentos existentes")
            return df
        else:
            print(f"    → Creando nuevo CSV: {self.documentos_csv_path}")
            return pd.DataFrame(columns=self.DOCUMENTOS_COLUMNS)

    def load_or_create_articulos_csv(self) -> pd.DataFrame:
        """
        Carga el CSV de artículos si existe, o crea uno nuevo.

        Returns:
            DataFrame con los artículos
        """
        if os.path.exists(self.articulos_csv_path):
            print(f"    → Cargando CSV existente: {self.articulos_csv_path}")
            df = pd.read_csv(self.articulos_csv_path)
            print(f"      Se encontraron {len(df)} artículos existentes")
            return df
        else:
            print(f"    → Creando nuevo CSV: {self.articulos_csv_path}")
            return pd.DataFrame(columns=self.ARTICULOS_COLUMNS)

    def add_or_update_document(self, document_data: Dict[str, any]) -> bool:
        """
        Agrega o actualiza un documento en el CSV de documentos.

        Args:
            document_data: Diccionario con los datos del documento

        Returns:
            True si se agregó/actualizó exitosamente
        """
        try:
            # Cargar CSV existente
            df = self.load_or_create_documentos_csv()

            document_id = document_data.get('document_id')

            # Verificar si el documento ya existe
            if document_id and document_id in df['document_id'].values:
                print(f"    → Actualizando documento existente: {document_id}")
                # Actualizar el registro existente
                idx = df[df['document_id'] == document_id].index[0]
                for col, value in document_data.items():
                    if col in df.columns:
                        df.at[idx, col] = value
            else:
                print(f"    → Agregando nuevo documento: {document_id}")
                # Agregar nuevo registro
                # Asegurar que todas las columnas existan
                for col in self.DOCUMENTOS_COLUMNS:
                    if col not in document_data:
                        document_data[col] = None

                # Usar pd.concat en lugar de append
                new_row = pd.DataFrame([document_data])
                df = pd.concat([df, new_row], ignore_index=True)

            # Guardar CSV actualizado
            df.to_csv(self.documentos_csv_path, index=False)
            print(f"    ✓ CSV de documentos actualizado: {len(df)} documentos totales")

            return True

        except Exception as e:
            print(f"    ✗ Error al actualizar documento en CSV: {str(e)}")
            return False

    def add_articles_from_document(self, document_id: str, articles: List[Dict[str, any]]) -> bool:
        """
        Agrega artículos de un documento al CSV de artículos.

        Args:
            document_id: ID del documento padre
            articles: Lista de artículos del documento

        Returns:
            True si se agregaron exitosamente
        """
        try:
            # Cargar CSV existente
            df = self.load_or_create_articulos_csv()

            # Eliminar artículos anteriores de este documento (si existen)
            df = df[df['document_id'] != document_id]

            # Preparar nuevos artículos
            new_articles = []
            fecha_extraccion = datetime.now().isoformat()

            for article in articles:
                articulo_id = f"{document_id}-ART-{article['numero']}"

                article_data = {
                    'articulo_id': articulo_id,
                    'document_id': document_id,
                    'numero_articulo': article['numero'],
                    'titulo_articulo': article.get('titulo', ''),
                    'contenido': article['contenido'],
                    'num_incisos': article.get('num_incisos', 0),
                    'num_paragrafos': article.get('num_paragrafos', 0),
                    'caracteres': len(article['contenido']),
                    'fecha_extraccion': fecha_extraccion
                }

                new_articles.append(article_data)

            # Agregar nuevos artículos
            if new_articles:
                new_df = pd.DataFrame(new_articles)
                df = pd.concat([df, new_df], ignore_index=True)

            # Guardar CSV actualizado
            df.to_csv(self.articulos_csv_path, index=False)
            print(f"    ✓ CSV de artículos actualizado: {len(new_articles)} artículos agregados")
            print(f"      Total de artículos en CSV: {len(df)}")

            return True

        except Exception as e:
            print(f"    ✗ Error al actualizar artículos en CSV: {str(e)}")
            return False

    def get_existing_document_ids(self) -> List[str]:
        """
        Obtiene la lista de IDs de documentos ya procesados.

        Returns:
            Lista de document_ids existentes
        """
        if os.path.exists(self.documentos_csv_path):
            df = pd.read_csv(self.documentos_csv_path)
            return df['document_id'].dropna().tolist()
        return []

    def get_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas de los CSVs.

        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total_documentos': 0,
            'total_articulos': 0,
            'documentos_procesados_completo': 0,
            'documentos_con_errores': 0,
            'tipos_norma': {}
        }

        # Estadísticas de documentos
        if os.path.exists(self.documentos_csv_path):
            df_docs = pd.read_csv(self.documentos_csv_path)
            stats['total_documentos'] = len(df_docs)
            stats['documentos_procesados_completo'] = len(df_docs[df_docs['procesamiento_completo'] == True])
            stats['documentos_con_errores'] = len(df_docs[df_docs['error_mensaje'].notna()])

            # Contar tipos de norma
            if 'tipo_norma' in df_docs.columns:
                tipo_counts = df_docs['tipo_norma'].value_counts().to_dict()
                stats['tipos_norma'] = tipo_counts

        # Estadísticas de artículos
        if os.path.exists(self.articulos_csv_path):
            df_arts = pd.read_csv(self.articulos_csv_path)
            stats['total_articulos'] = len(df_arts)

        return stats

    def print_summary(self):
        """
        Imprime un resumen del estado de los CSVs.
        """
        stats = self.get_statistics()

        print(f"\n{'='*60}")
        print(f"RESUMEN DE CSVs")
        print(f"{'='*60}")
        print(f"Ubicación: {self.csv_dir}")
        print(f"\nDOCUMENTOS:")
        print(f"  - Total de documentos: {stats['total_documentos']}")
        print(f"  - Procesados completos: {stats['documentos_procesados_completo']}")
        print(f"  - Con errores: {stats['documentos_con_errores']}")

        if stats['tipos_norma']:
            print(f"\n  Tipos de norma:")
            for tipo, count in stats['tipos_norma'].items():
                print(f"    - {tipo}: {count}")

        print(f"\nARTÍCULOS:")
        print(f"  - Total de artículos: {stats['total_articulos']}")

        print(f"\nARCHIVOS:")
        print(f"  - Documentos CSV: {self.documentos_csv_path}")
        print(f"  - Artículos CSV: {self.articulos_csv_path}")
        print(f"{'='*60}\n")


def main():
    """
    Función de prueba del gestor de CSVs.

    NOTA PARA EL USUARIO:
    Esta es solo una función de prueba. Para usar el gestor en el pipeline
    completo, debes llamarlo desde main.py usando run_full_pipeline().
    """
    manager = CSVManager()

    # Ejemplo de agregar un documento
    doc_data = {
        'document_id': 'LEY-1234-2023-07-15',
        'tipo_norma': 'LEY',
        'numero_norma': '1234',
        'fecha_norma': '2023-07-15',
        'entidad_emisora': 'ASAMBLEA LEGISLATIVA',
        'titulo_original': 'LEY N° 1234 DE 15 DE JULIO DE 2023',
        'procesamiento_completo': True,
        'fecha_procesamiento': datetime.now().isoformat()
    }

    manager.add_or_update_document(doc_data)

    # Ejemplo de agregar artículos
    articles = [
        {'numero': 1, 'titulo': 'OBJETO', 'contenido': 'La presente Ley...', 'num_incisos': 0, 'num_paragrafos': 0},
        {'numero': 2, 'titulo': 'DEFINICIONES', 'contenido': 'Para efectos...', 'num_incisos': 3, 'num_paragrafos': 1},
    ]

    manager.add_articles_from_document('LEY-1234-2023-07-15', articles)

    # Mostrar resumen
    manager.print_summary()


if __name__ == "__main__":
    main()
