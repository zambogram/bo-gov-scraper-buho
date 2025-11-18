"""
Sistema de Base de Datos SQLite para Registro Histórico de Leyes Bolivianas
Mantiene un registro completo de todas las leyes scrapeadas con metadatos detallados
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


class LawDatabase:
    """Gestor de base de datos SQLite para leyes bolivianas"""

    def __init__(self, db_path: str = "data/laws.db"):
        """
        Inicializa la conexión a la base de datos

        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establece conexión con la base de datos"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Crea las tablas necesarias en la base de datos"""

        # Tabla principal de leyes
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS leyes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_unico TEXT UNIQUE NOT NULL,
            numero_ley TEXT NOT NULL,
            tipo_norma TEXT NOT NULL,
            titulo TEXT NOT NULL,

            -- Clasificación jurídica
            area_derecho TEXT NOT NULL,
            jerarquia_normativa TEXT NOT NULL,
            materia TEXT,  -- JSON array
            palabras_clave TEXT,  -- JSON array

            -- Información temporal
            fecha_promulgacion DATE NOT NULL,
            fecha_publicacion DATE,
            fecha_vigencia DATE,
            fecha_abrogacion DATE,
            vigente BOOLEAN DEFAULT 1,

            -- Origen y fuente
            organo_emisor TEXT NOT NULL,
            firmante TEXT,
            url_origen TEXT NOT NULL,
            sitio_web TEXT NOT NULL,
            fecha_scraping DATETIME NOT NULL,

            -- Documento
            formato_original TEXT NOT NULL,
            tamanio_bytes INTEGER NOT NULL,
            numero_paginas INTEGER,
            hash_md5 TEXT NOT NULL,
            hash_sha256 TEXT NOT NULL,
            ruta_archivo_original TEXT NOT NULL,
            ruta_archivo_procesado TEXT,
            archivos_divididos TEXT,  -- JSON array

            -- Procesamiento
            ocr_aplicado BOOLEAN DEFAULT 0,
            confianza_ocr REAL,
            idioma_detectado TEXT,
            texto_extraido TEXT,
            estado_procesamiento TEXT DEFAULT 'pendiente',
            errores_procesamiento TEXT,  -- JSON array

            -- Relaciones
            modifica_a TEXT,  -- JSON array
            modificada_por TEXT,  -- JSON array
            deroga_a TEXT,  -- JSON array
            derogada_por TEXT,
            reglamenta_a TEXT,
            reglamentada_por TEXT,  -- JSON array

            -- Contenido adicional
            resumen TEXT,
            articulos_principales TEXT,  -- JSON array
            disposiciones_transitorias TEXT,
            disposiciones_finales TEXT,
            anexos TEXT,  -- JSON array

            -- Estadísticas
            total_articulos INTEGER,
            total_palabras INTEGER,
            total_caracteres INTEGER,

            -- Metadatos del sistema
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
            actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabla de historial de scraping
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_scraping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sitio_web TEXT NOT NULL,
            fecha_inicio DATETIME NOT NULL,
            fecha_fin DATETIME,
            leyes_encontradas INTEGER DEFAULT 0,
            leyes_procesadas INTEGER DEFAULT 0,
            leyes_con_errores INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'iniciado',
            errores TEXT,  -- JSON array
            duracion_segundos REAL,
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabla de estadísticas globales
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS estadisticas_globales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_leyes INTEGER DEFAULT 0,
            total_sitios_scrapeados INTEGER DEFAULT 0,
            ultima_actualizacion DATETIME,
            estadisticas_por_area TEXT,  -- JSON object
            estadisticas_por_tipo TEXT,  -- JSON object
            estadisticas_por_anio TEXT,  -- JSON object
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
            actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabla de áreas del derecho
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas_derecho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT,
            total_leyes INTEGER DEFAULT 0,
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Índices para búsqueda rápida
        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_numero_ley ON leyes(numero_ley)
        """)

        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_area_derecho ON leyes(area_derecho)
        """)

        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fecha_promulgacion ON leyes(fecha_promulgacion)
        """)

        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vigente ON leyes(vigente)
        """)

        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sitio_web ON leyes(sitio_web)
        """)

        self.conn.commit()

    def insertar_ley(self, metadata: Dict[str, Any]) -> Optional[int]:
        """
        Inserta una nueva ley en la base de datos

        Args:
            metadata: Diccionario con todos los metadatos de la ley

        Returns:
            ID de la ley insertada o None si falló
        """
        try:
            # Generar código único si no existe
            if 'codigo_unico' not in metadata:
                metadata['codigo_unico'] = self._generar_codigo_unico(metadata)

            # Convertir arrays y objetos a JSON
            for campo in ['materia', 'palabras_clave', 'archivos_divididos',
                         'errores_procesamiento', 'modifica_a', 'modificada_por',
                         'deroga_a', 'reglamentada_por', 'articulos_principales', 'anexos']:
                if campo in metadata and isinstance(metadata[campo], (list, dict)):
                    metadata[campo] = json.dumps(metadata[campo], ensure_ascii=False)

            # Preparar la consulta
            columnas = ', '.join(metadata.keys())
            placeholders = ', '.join(['?' for _ in metadata])
            valores = list(metadata.values())

            query = f"INSERT OR REPLACE INTO leyes ({columnas}) VALUES ({placeholders})"
            self.cursor.execute(query, valores)
            self.conn.commit()

            return self.cursor.lastrowid

        except Exception as e:
            print(f"Error al insertar ley: {e}")
            self.conn.rollback()
            return None

    def actualizar_ley(self, codigo_unico: str, metadata: Dict[str, Any]) -> bool:
        """
        Actualiza una ley existente

        Args:
            codigo_unico: Código único de la ley
            metadata: Diccionario con metadatos a actualizar

        Returns:
            True si se actualizó correctamente
        """
        try:
            # Agregar timestamp de actualización
            metadata['actualizado_en'] = datetime.now().isoformat()

            # Convertir arrays y objetos a JSON
            for campo in ['materia', 'palabras_clave', 'archivos_divididos',
                         'errores_procesamiento', 'modifica_a', 'modificada_por',
                         'deroga_a', 'reglamentada_por', 'articulos_principales', 'anexos']:
                if campo in metadata and isinstance(metadata[campo], (list, dict)):
                    metadata[campo] = json.dumps(metadata[campo], ensure_ascii=False)

            # Preparar la consulta
            set_clause = ', '.join([f"{k} = ?" for k in metadata.keys()])
            valores = list(metadata.values()) + [codigo_unico]

            query = f"UPDATE leyes SET {set_clause} WHERE codigo_unico = ?"
            self.cursor.execute(query, valores)
            self.conn.commit()

            return self.cursor.rowcount > 0

        except Exception as e:
            print(f"Error al actualizar ley: {e}")
            self.conn.rollback()
            return False

    def buscar_ley(self, **criterios) -> List[Dict]:
        """
        Busca leyes según criterios específicos

        Args:
            **criterios: Pares clave-valor para buscar

        Returns:
            Lista de leyes que coinciden con los criterios
        """
        try:
            where_clauses = []
            valores = []

            for columna, valor in criterios.items():
                where_clauses.append(f"{columna} = ?")
                valores.append(valor)

            where_str = ' AND '.join(where_clauses)
            query = f"SELECT * FROM leyes WHERE {where_str}"

            self.cursor.execute(query, valores)
            resultados = self.cursor.fetchall()

            return [dict(row) for row in resultados]

        except Exception as e:
            print(f"Error al buscar ley: {e}")
            return []

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del scraping

        Returns:
            Diccionario con estadísticas detalladas
        """
        stats = {}

        # Total de leyes
        self.cursor.execute("SELECT COUNT(*) as total FROM leyes")
        stats['total_leyes'] = self.cursor.fetchone()['total']

        # Leyes por área del derecho
        self.cursor.execute("""
            SELECT area_derecho, COUNT(*) as cantidad
            FROM leyes
            GROUP BY area_derecho
            ORDER BY cantidad DESC
        """)
        stats['por_area'] = [dict(row) for row in self.cursor.fetchall()]

        # Leyes por tipo
        self.cursor.execute("""
            SELECT tipo_norma, COUNT(*) as cantidad
            FROM leyes
            GROUP BY tipo_norma
            ORDER BY cantidad DESC
        """)
        stats['por_tipo'] = [dict(row) for row in self.cursor.fetchall()]

        # Leyes por año
        self.cursor.execute("""
            SELECT strftime('%Y', fecha_promulgacion) as anio, COUNT(*) as cantidad
            FROM leyes
            WHERE fecha_promulgacion IS NOT NULL
            GROUP BY anio
            ORDER BY anio DESC
        """)
        stats['por_anio'] = [dict(row) for row in self.cursor.fetchall()]

        # Leyes vigentes vs abrogadas
        self.cursor.execute("""
            SELECT vigente, COUNT(*) as cantidad
            FROM leyes
            GROUP BY vigente
        """)
        stats['vigencia'] = [dict(row) for row in self.cursor.fetchall()]

        # Leyes por sitio web
        self.cursor.execute("""
            SELECT sitio_web, COUNT(*) as cantidad
            FROM leyes
            GROUP BY sitio_web
            ORDER BY cantidad DESC
        """)
        stats['por_sitio'] = [dict(row) for row in self.cursor.fetchall()]

        # Estado de procesamiento
        self.cursor.execute("""
            SELECT estado_procesamiento, COUNT(*) as cantidad
            FROM leyes
            GROUP BY estado_procesamiento
        """)
        stats['por_estado'] = [dict(row) for row in self.cursor.fetchall()]

        return stats

    def registrar_scraping(self, sitio_web: str, inicio: datetime) -> int:
        """
        Registra el inicio de un scraping

        Args:
            sitio_web: Nombre del sitio web
            inicio: Datetime de inicio

        Returns:
            ID del registro de scraping
        """
        self.cursor.execute("""
            INSERT INTO historial_scraping (sitio_web, fecha_inicio, estado)
            VALUES (?, ?, 'iniciado')
        """, (sitio_web, inicio.isoformat()))
        self.conn.commit()
        return self.cursor.lastrowid

    def actualizar_scraping(self, scraping_id: int, **datos):
        """
        Actualiza el registro de un scraping

        Args:
            scraping_id: ID del registro de scraping
            **datos: Datos a actualizar
        """
        set_clause = ', '.join([f"{k} = ?" for k in datos.keys()])
        valores = list(datos.values()) + [scraping_id]

        query = f"UPDATE historial_scraping SET {set_clause} WHERE id = ?"
        self.cursor.execute(query, valores)
        self.conn.commit()

    def obtener_historial_scraping(self, limite: int = 50) -> List[Dict]:
        """
        Obtiene el historial de scraping

        Args:
            limite: Número máximo de registros a devolver

        Returns:
            Lista de registros de scraping
        """
        self.cursor.execute("""
            SELECT * FROM historial_scraping
            ORDER BY fecha_inicio DESC
            LIMIT ?
        """, (limite,))

        return [dict(row) for row in self.cursor.fetchall()]

    def _generar_codigo_unico(self, metadata: Dict[str, Any]) -> str:
        """
        Genera un código único para una ley basado en sus metadatos

        Args:
            metadata: Metadatos de la ley

        Returns:
            Código único (hash SHA256)
        """
        # Combinar campos clave para generar el hash
        datos = f"{metadata.get('numero_ley', '')}" \
                f"{metadata.get('titulo', '')}" \
                f"{metadata.get('fecha_promulgacion', '')}" \
                f"{metadata.get('organo_emisor', '')}"

        return hashlib.sha256(datos.encode()).hexdigest()[:32]

    def exportar_a_csv(self, ruta_salida: str, filtros: Optional[Dict] = None):
        """
        Exporta las leyes a un archivo CSV

        Args:
            ruta_salida: Ruta del archivo CSV de salida
            filtros: Diccionario opcional con filtros
        """
        import csv

        # Construir query
        query = "SELECT * FROM leyes"
        valores = []

        if filtros:
            where_clauses = [f"{k} = ?" for k in filtros.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            valores = list(filtros.values())

        self.cursor.execute(query, valores)
        resultados = self.cursor.fetchall()

        if not resultados:
            print("No hay datos para exportar")
            return

        # Escribir CSV
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
            writer.writeheader()
            for row in resultados:
                writer.writerow(dict(row))

        print(f"Exportado {len(resultados)} registros a {ruta_salida}")

    def exportar_a_json(self, ruta_salida: str, filtros: Optional[Dict] = None):
        """
        Exporta las leyes a un archivo JSON

        Args:
            ruta_salida: Ruta del archivo JSON de salida
            filtros: Diccionario opcional con filtros
        """
        # Construir query
        query = "SELECT * FROM leyes"
        valores = []

        if filtros:
            where_clauses = [f"{k} = ?" for k in filtros.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            valores = list(filtros.values())

        self.cursor.execute(query, valores)
        resultados = [dict(row) for row in self.cursor.fetchall()]

        # Escribir JSON
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"Exportado {len(resultados)} registros a {ruta_salida}")

    def cerrar(self):
        """Cierra la conexión con la base de datos"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cerrar()


# Funciones auxiliares

def crear_backup_db(db_path: str = "data/laws.db"):
    """
    Crea un backup de la base de datos

    Args:
        db_path: Ruta a la base de datos
    """
    from shutil import copy2
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    try:
        copy2(db_path, backup_path)
        print(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error al crear backup: {e}")
        return None


if __name__ == "__main__":
    # Ejemplo de uso
    with LawDatabase() as db:
        # Ejemplo de metadatos
        ejemplo_metadata = {
            'numero_ley': 'Ley 1178',
            'tipo_norma': 'Ley',
            'titulo': 'Ley de Administración y Control Gubernamentales',
            'area_derecho': 'Administrativo',
            'jerarquia_normativa': 'Legal',
            'fecha_promulgacion': '1990-07-20',
            'vigente': True,
            'organo_emisor': 'Congreso Nacional',
            'url_origen': 'https://ejemplo.com/ley1178.pdf',
            'sitio_web': 'Gaceta Oficial',
            'fecha_scraping': datetime.now().isoformat(),
            'formato_original': 'PDF',
            'tamanio_bytes': 524288,
            'hash_md5': 'abc123',
            'hash_sha256': 'def456',
            'ruta_archivo_original': 'data/raw/ley1178.pdf',
            'estado_procesamiento': 'completado'
        }

        # Insertar ley de ejemplo
        ley_id = db.insertar_ley(ejemplo_metadata)
        print(f"Ley insertada con ID: {ley_id}")

        # Obtener estadísticas
        stats = db.obtener_estadisticas()
        print(f"\nEstadísticas:")
        print(f"Total de leyes: {stats['total_leyes']}")
