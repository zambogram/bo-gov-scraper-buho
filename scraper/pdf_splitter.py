"""
Sistema de División y Estructuración de PDFs
Divide PDFs grandes en secciones manejables y añade metadatos a cada parte
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional
import re


class PDFSplitter:
    """Divisor inteligente de PDFs con detección de estructura"""

    def __init__(self, output_dir: str = "data/processed/split"):
        """
        Inicializa el divisor de PDFs

        Args:
            output_dir: Directorio para PDFs divididos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def dividir_pdf(self, pdf_path: str, max_paginas_por_seccion: int = 50,
                    dividir_por_estructura: bool = True) -> List[str]:
        """
        Divide un PDF en secciones más pequeñas

        Args:
            pdf_path: Ruta al PDF original
            max_paginas_por_seccion: Máximo de páginas por sección
            dividir_por_estructura: Si True, divide por capítulos/secciones

        Returns:
            Lista de rutas a los PDFs divididos
        """
        path = Path(pdf_path)
        archivos_generados = []

        try:
            doc = fitz.open(pdf_path)
            total_paginas = len(doc)

            print(f"Procesando PDF: {path.name} ({total_paginas} páginas)")

            if dividir_por_estructura:
                # Intentar detectar estructura del documento
                estructura = self._detectar_estructura(doc)

                if estructura:
                    print(f"Estructura detectada: {len(estructura)} secciones")
                    archivos_generados = self._dividir_por_estructura(
                        doc, estructura, path.stem
                    )
                else:
                    # No se detectó estructura, dividir por tamaño
                    archivos_generados = self._dividir_por_paginas(
                        doc, max_paginas_por_seccion, path.stem
                    )
            else:
                # Dividir solo por número de páginas
                archivos_generados = self._dividir_por_paginas(
                    doc, max_paginas_por_seccion, path.stem
                )

            doc.close()
            print(f"PDF dividido en {len(archivos_generados)} partes")

            return archivos_generados

        except Exception as e:
            print(f"Error al dividir PDF: {e}")
            return []

    def _detectar_estructura(self, doc: fitz.Document) -> List[Dict]:
        """
        Detecta la estructura del documento (capítulos, títulos, artículos)

        Args:
            doc: Documento PDF abierto

        Returns:
            Lista de secciones detectadas
        """
        estructura = []

        try:
            # Obtener tabla de contenidos si existe
            toc = doc.get_toc()

            if toc:
                for nivel, titulo, pagina in toc:
                    estructura.append({
                        'nivel': nivel,
                        'titulo': titulo,
                        'pagina_inicio': pagina - 1  # PyMuPDF usa 0-index
                    })
                return estructura

            # Si no hay TOC, buscar patrones de títulos en el texto
            estructura = self._detectar_titulos_por_texto(doc)

            return estructura

        except Exception as e:
            print(f"Error al detectar estructura: {e}")
            return []

    def _detectar_titulos_por_texto(self, doc: fitz.Document) -> List[Dict]:
        """Detecta títulos analizando el texto y formato"""
        estructura = []

        patrones_titulos = [
            r'^CAPÍTULO\s+[IVXLCDM]+',
            r'^TÍTULO\s+[IVXLCDM]+',
            r'^SECCIÓN\s+[IVXLCDM]+',
            r'^LIBRO\s+[IVXLCDM]+',
            r'^Capítulo\s+\d+',
            r'^Título\s+\d+',
        ]

        for pagina_num in range(min(len(doc), 100)):  # Analizar primeras 100 páginas
            pagina = doc[pagina_num]
            texto = pagina.get_text()

            for linea in texto.split('\n')[:20]:  # Primeras 20 líneas de cada página
                linea = linea.strip()

                for patron in patrones_titulos:
                    if re.match(patron, linea, re.IGNORECASE):
                        estructura.append({
                            'nivel': 1,
                            'titulo': linea[:100],
                            'pagina_inicio': pagina_num
                        })
                        break

        return estructura

    def _dividir_por_estructura(self, doc: fitz.Document, estructura: List[Dict],
                               nombre_base: str) -> List[str]:
        """Divide el PDF según la estructura detectada"""
        archivos_generados = []

        for i, seccion in enumerate(estructura):
            # Determinar rango de páginas
            pagina_inicio = seccion['pagina_inicio']
            pagina_fin = (estructura[i + 1]['pagina_inicio'] - 1
                         if i + 1 < len(estructura)
                         else len(doc) - 1)

            # Crear nuevo PDF con esta sección
            titulo_limpio = self._limpiar_nombre_archivo(seccion['titulo'])
            nombre_archivo = f"{nombre_base}_seccion_{i + 1:03d}_{titulo_limpio}.pdf"
            ruta_salida = self.output_dir / nombre_archivo

            # Extraer páginas
            nuevo_doc = fitz.open()
            nuevo_doc.insert_pdf(doc, from_page=pagina_inicio, to_page=pagina_fin)

            # Guardar
            nuevo_doc.save(str(ruta_salida))
            nuevo_doc.close()

            archivos_generados.append(str(ruta_salida))

        return archivos_generados

    def _dividir_por_paginas(self, doc: fitz.Document, max_paginas: int,
                            nombre_base: str) -> List[str]:
        """Divide el PDF en secciones de tamaño fijo"""
        archivos_generados = []
        total_paginas = len(doc)
        num_secciones = (total_paginas + max_paginas - 1) // max_paginas

        for i in range(num_secciones):
            pagina_inicio = i * max_paginas
            pagina_fin = min((i + 1) * max_paginas - 1, total_paginas - 1)

            nombre_archivo = f"{nombre_base}_parte_{i + 1:03d}_pag_{pagina_inicio + 1}-{pagina_fin + 1}.pdf"
            ruta_salida = self.output_dir / nombre_archivo

            # Crear nuevo PDF
            nuevo_doc = fitz.open()
            nuevo_doc.insert_pdf(doc, from_page=pagina_inicio, to_page=pagina_fin)

            # Guardar
            nuevo_doc.save(str(ruta_salida))
            nuevo_doc.close()

            archivos_generados.append(str(ruta_salida))

        return archivos_generados

    def agregar_metadatos_a_seccion(self, pdf_path: str, metadata: Dict) -> bool:
        """
        Agrega metadatos a un PDF dividido

        Args:
            pdf_path: Ruta al PDF
            metadata: Diccionario con metadatos

        Returns:
            True si se agregaron correctamente
        """
        try:
            doc = fitz.open(pdf_path)

            # Agregar metadatos
            doc.set_metadata({
                'title': metadata.get('titulo', ''),
                'author': metadata.get('firmante', metadata.get('organo_emisor', '')),
                'subject': f"{metadata.get('tipo_norma', '')} - {metadata.get('area_derecho', '')}",
                'keywords': ', '.join(metadata.get('palabras_clave', [])[:10]),
                'producer': 'BÚHO Scraper - Bolivia',
                'creator': 'bo-gov-scraper-buho'
            })

            # Guardar cambios
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()

            return True

        except Exception as e:
            print(f"Error al agregar metadatos: {e}")
            return False

    def dividir_por_articulos(self, pdf_path: str, texto_completo: str) -> List[str]:
        """
        Divide un PDF por artículos individuales

        Args:
            pdf_path: Ruta al PDF
            texto_completo: Texto extraído del PDF

        Returns:
            Lista de archivos generados
        """
        try:
            doc = fitz.open(pdf_path)
            path = Path(pdf_path)
            archivos_generados = []

            # Detectar artículos en el texto
            patron_articulo = r'Art[íi]culo\s+(\d+)[°º]?'
            matches = list(re.finditer(patron_articulo, texto_completo, re.IGNORECASE))

            if len(matches) < 2:
                print("No se detectaron suficientes artículos para dividir")
                doc.close()
                return []

            # Estimar páginas por artículo
            caracteres_por_pagina = len(texto_completo) / len(doc)

            articulos_info = []
            for i, match in enumerate(matches):
                num_articulo = match.group(1)
                posicion_inicio = match.start()
                posicion_fin = matches[i + 1].start() if i + 1 < len(matches) else len(texto_completo)

                pagina_estimada = int(posicion_inicio / caracteres_por_pagina)

                articulos_info.append({
                    'numero': num_articulo,
                    'pagina': pagina_estimada,
                    'texto_inicio': posicion_inicio,
                    'texto_fin': posicion_fin
                })

            # Agrupar artículos cercanos (para evitar PDFs de 1 página)
            grupos = self._agrupar_articulos(articulos_info, max_por_grupo=10)

            # Crear PDFs para cada grupo
            for i, grupo in enumerate(grupos):
                pagina_inicio = grupo[0]['pagina']
                pagina_fin = min(grupo[-1]['pagina'] + 2, len(doc) - 1)

                numeros_articulos = [a['numero'] for a in grupo]
                nombre_archivo = f"{path.stem}_articulos_{numeros_articulos[0]}-{numeros_articulos[-1]}.pdf"
                ruta_salida = self.output_dir / nombre_archivo

                nuevo_doc = fitz.open()
                nuevo_doc.insert_pdf(doc, from_page=pagina_inicio, to_page=pagina_fin)
                nuevo_doc.save(str(ruta_salida))
                nuevo_doc.close()

                archivos_generados.append(str(ruta_salida))

            doc.close()
            return archivos_generados

        except Exception as e:
            print(f"Error al dividir por artículos: {e}")
            return []

    def _agrupar_articulos(self, articulos: List[Dict], max_por_grupo: int = 10) -> List[List[Dict]]:
        """Agrupa artículos cercanos"""
        if not articulos:
            return []

        grupos = []
        grupo_actual = [articulos[0]]

        for articulo in articulos[1:]:
            if len(grupo_actual) < max_por_grupo:
                grupo_actual.append(articulo)
            else:
                grupos.append(grupo_actual)
                grupo_actual = [articulo]

        if grupo_actual:
            grupos.append(grupo_actual)

        return grupos

    def _limpiar_nombre_archivo(self, texto: str, max_length: int = 50) -> str:
        """Limpia un texto para usarlo como nombre de archivo"""
        # Eliminar caracteres no válidos
        texto = re.sub(r'[^\w\s-]', '', texto)
        # Reemplazar espacios por guiones bajos
        texto = re.sub(r'\s+', '_', texto)
        # Limitar longitud
        texto = texto[:max_length]
        return texto.lower()

    def obtener_info_secciones(self, archivos_divididos: List[str]) -> List[Dict]:
        """
        Obtiene información sobre las secciones divididas

        Args:
            archivos_divididos: Lista de rutas a PDFs divididos

        Returns:
            Lista con información de cada sección
        """
        info_secciones = []

        for archivo in archivos_divididos:
            try:
                doc = fitz.open(archivo)
                metadata = doc.metadata

                info = {
                    'archivo': archivo,
                    'nombre': Path(archivo).name,
                    'numero_paginas': len(doc),
                    'tamanio_bytes': Path(archivo).stat().st_size,
                    'metadata': metadata
                }

                doc.close()
                info_secciones.append(info)

            except Exception as e:
                print(f"Error al obtener info de {archivo}: {e}")

        return info_secciones


if __name__ == "__main__":
    # Ejemplo de uso
    splitter = PDFSplitter()

    # Dividir un PDF grande
    archivos = splitter.dividir_pdf("ley_grande.pdf", max_paginas_por_seccion=30)

    print(f"PDF dividido en {len(archivos)} partes:")
    for archivo in archivos:
        print(f"  - {archivo}")

    # Obtener información
    info = splitter.obtener_info_secciones(archivos)
    for seccion in info:
        print(f"{seccion['nombre']}: {seccion['numero_paginas']} páginas")
