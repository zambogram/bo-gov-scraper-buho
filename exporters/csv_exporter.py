"""Exportador a formato CSV"""

import csv
from pathlib import Path
from typing import List, Dict


class CSVExporter:
    """Exporta datos de leyes a formato CSV"""

    @staticmethod
    def exportar(datos: List[Dict], archivo_salida: str) -> bool:
        """
        Exporta una lista de leyes a CSV

        Args:
            datos: Lista de diccionarios con datos de leyes
            archivo_salida: Ruta del archivo CSV de salida

        Returns:
            True si se exportó correctamente
        """
        if not datos:
            print("No hay datos para exportar")
            return False

        try:
            Path(archivo_salida).parent.mkdir(parents=True, exist_ok=True)

            with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
                # Obtener todos los campos únicos
                campos = set()
                for item in datos:
                    campos.update(item.keys())

                campos = sorted(campos)

                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()

                for item in datos:
                    # Convertir listas y dicts a strings
                    item_limpio = {}
                    for k, v in item.items():
                        if isinstance(v, (list, dict)):
                            item_limpio[k] = str(v)
                        else:
                            item_limpio[k] = v

                    writer.writerow(item_limpio)

            print(f"✅ Exportado a CSV: {archivo_salida} ({len(datos)} registros)")
            return True

        except Exception as e:
            print(f"❌ Error exportando CSV: {e}")
            return False
