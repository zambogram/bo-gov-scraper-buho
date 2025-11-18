"""
Extractor de texto desde PDFs con soporte para OCR
"""
import re
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extractor de texto desde archivos PDF"""

    def __init__(self, usar_ocr: bool = False):
        """
        Inicializar extractor

        Args:
            usar_ocr: Si usar OCR para PDFs escaneados
        """
        self.usar_ocr = usar_ocr
        self._pypdf_disponible = False
        self._pytesseract_disponible = False

        # Intentar importar PyPDF2
        try:
            import PyPDF2
            self._pypdf_disponible = True
        except ImportError:
            logger.warning("PyPDF2 no disponible. Instalar con: pip install PyPDF2")

        # Intentar importar pytesseract si se solicita OCR
        if usar_ocr:
            try:
                import pytesseract
                from PIL import Image
                self._pytesseract_disponible = True
            except ImportError:
                logger.warning("pytesseract no disponible. Instalar con: pip install pytesseract pillow")

    def extraer_texto(self, ruta_pdf: Path) -> str:
        """
        Extraer texto de un PDF

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            Texto extraído y normalizado
        """
        if not ruta_pdf.exists():
            raise FileNotFoundError(f"PDF no encontrado: {ruta_pdf}")

        texto = ""

        # Intentar extracción con PyPDF2 primero
        if self._pypdf_disponible:
            try:
                texto = self._extraer_con_pypdf(ruta_pdf)
            except Exception as e:
                logger.error(f"Error extrayendo con PyPDF2: {e}")

        # Si el texto está vacío o muy corto y OCR está habilitado, intentar OCR
        if (not texto or len(texto) < 100) and self.usar_ocr and self._pytesseract_disponible:
            try:
                logger.info(f"Intentando OCR para {ruta_pdf.name}")
                texto_ocr = self._extraer_con_ocr(ruta_pdf)
                if len(texto_ocr) > len(texto):
                    texto = texto_ocr
            except Exception as e:
                logger.error(f"Error en OCR: {e}")

        # Normalizar texto
        texto = self._normalizar_texto(texto)

        return texto

    def _extraer_con_pypdf(self, ruta_pdf: Path) -> str:
        """Extraer texto usando PyPDF2"""
        import PyPDF2

        texto_completo = []

        with open(ruta_pdf, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_paginas = len(pdf_reader.pages)

            for num_pag in range(num_paginas):
                try:
                    pagina = pdf_reader.pages[num_pag]
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo.append(texto)
                except Exception as e:
                    logger.warning(f"Error en página {num_pag + 1}: {e}")
                    continue

        return "\n".join(texto_completo)

    def _extraer_con_ocr(self, ruta_pdf: Path) -> str:
        """Extraer texto usando OCR (Tesseract)"""
        import pytesseract
        from PIL import Image
        import pdf2image

        texto_completo = []

        try:
            # Convertir PDF a imágenes
            imagenes = pdf2image.convert_from_path(str(ruta_pdf))

            for i, imagen in enumerate(imagenes):
                try:
                    # Aplicar OCR
                    texto = pytesseract.image_to_string(imagen, lang='spa')
                    if texto:
                        texto_completo.append(texto)
                except Exception as e:
                    logger.warning(f"Error OCR en página {i + 1}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error convirtiendo PDF a imágenes: {e}")

        return "\n".join(texto_completo)

    def _normalizar_texto(self, texto: str) -> str:
        """
        Normalizar texto extraído

        Args:
            texto: Texto sin procesar

        Returns:
            Texto normalizado
        """
        if not texto:
            return ""

        # Eliminar caracteres de control excepto saltos de línea
        texto = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', texto)

        # Normalizar espacios en blanco
        texto = re.sub(r'[ \t]+', ' ', texto)

        # Normalizar saltos de línea (max 2 consecutivos)
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        # Eliminar espacios al inicio y final de cada línea
        lineas = [linea.strip() for linea in texto.split('\n')]
        texto = '\n'.join(lineas)

        # Eliminar líneas vacías al inicio y final
        texto = texto.strip()

        return texto

    def guardar_texto(self, texto: str, ruta_salida: Path) -> Path:
        """
        Guardar texto extraído

        Args:
            texto: Texto a guardar
            ruta_salida: Ruta del archivo de salida

        Returns:
            Path del archivo guardado
        """
        # Asegurar que el directorio existe
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        # Guardar
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write(texto)

        return ruta_salida

    def procesar_pdf(self, ruta_pdf: Path, ruta_txt: Path) -> str:
        """
        Procesar PDF completo: extraer y guardar texto

        Args:
            ruta_pdf: Ruta al PDF
            ruta_txt: Ruta donde guardar el texto

        Returns:
            Texto extraído
        """
        texto = self.extraer_texto(ruta_pdf)
        self.guardar_texto(texto, ruta_txt)
        logger.info(f"✓ Texto extraído: {ruta_txt}")
        return texto
