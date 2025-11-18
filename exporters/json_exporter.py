"""Exportador a formato JSON"""

import json
from pathlib import Path
from typing import List, Dict


class JSONExporter:
    """Exporta datos de leyes a formato JSON"""

    @staticmethod
    def exportar(datos: List[Dict], archivo_salida: str, indent: int = 2) -> bool:
        """
        Exporta una lista de leyes a JSON

        Args:
            datos: Lista de diccionarios con datos de leyes
            archivo_salida: Ruta del archivo JSON de salida
            indent: Nivel de indentación

        Returns:
            True si se exportó correctamente
        """
        if not datos:
            print("No hay datos para exportar")
            return False

        try:
            Path(archivo_salida).parent.mkdir(parents=True, exist_ok=True)

            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=indent)

            print(f"✅ Exportado a JSON: {archivo_salida} ({len(datos)} registros)")
            return True

        except Exception as e:
            print(f"❌ Error exportando JSON: {e}")
            return False
