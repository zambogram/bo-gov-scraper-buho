"""Exportador a formato Excel"""

import pandas as pd
from pathlib import Path
from typing import List, Dict


class ExcelExporter:
    """Exporta datos de leyes a formato Excel"""

    @staticmethod
    def exportar(datos: List[Dict], archivo_salida: str) -> bool:
        """
        Exporta una lista de leyes a Excel

        Args:
            datos: Lista de diccionarios con datos de leyes
            archivo_salida: Ruta del archivo Excel de salida

        Returns:
            True si se exportó correctamente
        """
        if not datos:
            print("No hay datos para exportar")
            return False

        try:
            Path(archivo_salida).parent.mkdir(parents=True, exist_ok=True)

            # Convertir a DataFrame
            df = pd.DataFrame(datos)

            # Convertir listas y dicts a strings
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)

            # Exportar a Excel con formato
            with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Leyes', index=False)

                # Ajustar ancho de columnas
                worksheet = writer.sheets['Leyes']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            print(f"✅ Exportado a Excel: {archivo_salida} ({len(datos)} registros)")
            return True

        except Exception as e:
            print(f"❌ Error exportando Excel: {e}")
            return False
