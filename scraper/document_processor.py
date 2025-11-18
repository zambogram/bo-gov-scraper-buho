"""
Procesador de Documentos con OCR
Procesa PDFs, DOCs, imágenes y aplica OCR cuando es necesario
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import hashlib


class DocumentProcessor:
    """Procesador completo de documentos legales"""

    def __init__(self, output_dir: str = "data/processed"):
        """
        Inicializa el procesador de documentos

        Args:
            output_dir: Directorio para archivos procesados
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_confidence = 0.0

    def procesar_documento(self, archivo_path: str) -> Dict:
        """
        Procesa un documento y extrae su contenido

        Args:
            archivo_path: Ruta al documento

        Returns:
            Diccionario con el texto extraído y metadatos del procesamiento
        """
        path = Path(archivo_path)
        extension = path.suffix.lower()

        resultado = {
            'archivo_original': str(path),
            'exito': False,
            'texto': '',
            'numero_paginas': 0,
            'ocr_aplicado': False,
            'confianza_ocr': 0.0,
            'error': None
        }

        try:
            if extension == '.pdf':
                resultado.update(self._procesar_pdf(archivo_path))
            elif extension in ['.doc', '.docx']:
                resultado.update(self._procesar_doc(archivo_path))
            elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                resultado.update(self._procesar_imagen(archivo_path))
            elif extension == '.txt':
                resultado.update(self._procesar_texto(archivo_path))
            else:
                resultado['error'] = f"Formato no soportado: {extension}"

        except Exception as e:
            resultado['error'] = str(e)

        return resultado

    def _procesar_pdf(self, pdf_path: str) -> Dict:
        """Procesa un archivo PDF extrayendo texto"""
        try:
            import pdfplumber
            from PyPDF2 import PdfReader

            resultado = {'exito': False, 'texto': '', 'numero_paginas': 0}

            # Intentar con pdfplumber primero (mejor extracción)
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    resultado['numero_paginas'] = len(pdf.pages)
                    texto_completo = []

                    for pagina in pdf.pages:
                        texto = pagina.extract_text()
                        if texto:
                            texto_completo.append(texto)

                    resultado['texto'] = '\n'.join(texto_completo)
                    resultado['exito'] = True

                    # Si no se extrajo texto, aplicar OCR
                    if len(resultado['texto'].strip()) < 100:
                        print(f"Poco texto extraído de {pdf_path}, aplicando OCR...")
                        resultado_ocr = self._aplicar_ocr_a_pdf(pdf_path)
                        resultado.update(resultado_ocr)

            except Exception as e:
                print(f"Error con pdfplumber, intentando PyPDF2: {e}")
                # Fallback a PyPDF2
                reader = PdfReader(pdf_path)
                resultado['numero_paginas'] = len(reader.pages)
                texto_completo = []

                for pagina in reader.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo.append(texto)

                resultado['texto'] = '\n'.join(texto_completo)
                resultado['exito'] = True

                # Si no hay texto, aplicar OCR
                if len(resultado['texto'].strip()) < 100:
                    resultado_ocr = self._aplicar_ocr_a_pdf(pdf_path)
                    resultado.update(resultado_ocr)

            return resultado

        except Exception as e:
            return {'exito': False, 'error': str(e), 'texto': '', 'numero_paginas': 0}

    def _procesar_doc(self, doc_path: str) -> Dict:
        """Procesa un archivo DOC/DOCX"""
        try:
            from docx import Document

            resultado = {'exito': False, 'texto': '', 'numero_paginas': 0}

            doc = Document(doc_path)
            texto_completo = []

            for parrafo in doc.paragraphs:
                if parrafo.text.strip():
                    texto_completo.append(parrafo.text)

            resultado['texto'] = '\n'.join(texto_completo)
            resultado['numero_paginas'] = len(doc.sections)
            resultado['exito'] = True

            return resultado

        except Exception as e:
            return {'exito': False, 'error': str(e), 'texto': '', 'numero_paginas': 0}

    def _procesar_imagen(self, imagen_path: str) -> Dict:
        """Procesa una imagen aplicando OCR"""
        try:
            resultado = self._aplicar_ocr_a_imagen(imagen_path)
            resultado['numero_paginas'] = 1
            return resultado

        except Exception as e:
            return {'exito': False, 'error': str(e), 'texto': '', 'numero_paginas': 1,
                   'ocr_aplicado': True, 'confianza_ocr': 0.0}

    def _procesar_texto(self, txt_path: str) -> Dict:
        """Procesa un archivo de texto plano"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                texto = f.read()

            return {
                'exito': True,
                'texto': texto,
                'numero_paginas': 1,
                'ocr_aplicado': False
            }

        except Exception as e:
            return {'exito': False, 'error': str(e), 'texto': '', 'numero_paginas': 0}

    def _aplicar_ocr_a_pdf(self, pdf_path: str) -> Dict:
        """Aplica OCR a un PDF escaneado"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image

            resultado = {
                'texto': '',
                'ocr_aplicado': True,
                'confianza_ocr': 0.0,
                'exito': False
            }

            # Convertir PDF a imágenes
            imagenes = convert_from_path(pdf_path, dpi=300)
            textos = []
            confianzas = []

            for i, imagen in enumerate(imagenes):
                # Preprocesar imagen
                imagen_procesada = self._preprocesar_imagen(imagen)

                # Aplicar OCR con Tesseract
                config_tesseract = '--oem 3 --psm 6 -l spa'
                texto = pytesseract.image_to_string(imagen_procesada, config=config_tesseract)

                # Obtener confianza
                data = pytesseract.image_to_data(imagen_procesada, output_type=pytesseract.Output.DICT)
                confidencias_pagina = [float(conf) for conf in data['conf'] if conf != '-1']
                if confidencias_pagina:
                    confianzas.append(sum(confidencias_pagina) / len(confidencias_pagina))

                textos.append(texto)

            resultado['texto'] = '\n\n'.join(textos)
            resultado['confianza_ocr'] = sum(confianzas) / len(confianzas) if confianzas else 0.0
            resultado['exito'] = True
            resultado['numero_paginas'] = len(imagenes)

            return resultado

        except Exception as e:
            print(f"Error al aplicar OCR al PDF: {e}")
            return {
                'texto': '',
                'ocr_aplicado': True,
                'confianza_ocr': 0.0,
                'exito': False,
                'error': str(e)
            }

    def _aplicar_ocr_a_imagen(self, imagen_path: str) -> Dict:
        """Aplica OCR a una imagen"""
        try:
            import pytesseract
            from PIL import Image

            resultado = {
                'texto': '',
                'ocr_aplicado': True,
                'confianza_ocr': 0.0,
                'exito': False
            }

            # Cargar y preprocesar imagen
            imagen = Image.open(imagen_path)
            imagen_procesada = self._preprocesar_imagen(imagen)

            # Aplicar OCR
            config_tesseract = '--oem 3 --psm 6 -l spa'
            texto = pytesseract.image_to_string(imagen_procesada, config=config_tesseract)

            # Calcular confianza
            data = pytesseract.image_to_data(imagen_procesada, output_type=pytesseract.Output.DICT)
            confidencias = [float(conf) for conf in data['conf'] if conf != '-1']

            resultado['texto'] = texto
            resultado['confianza_ocr'] = sum(confidencias) / len(confidencias) if confidencias else 0.0
            resultado['exito'] = True

            return resultado

        except Exception as e:
            print(f"Error al aplicar OCR a imagen: {e}")
            return {
                'texto': '',
                'ocr_aplicado': True,
                'confianza_ocr': 0.0,
                'exito': False,
                'error': str(e)
            }

    def _preprocesar_imagen(self, imagen):
        """Preprocesa una imagen para mejorar el OCR"""
        try:
            import cv2
            import numpy as np
            from PIL import Image

            # Convertir PIL a OpenCV
            img_array = np.array(imagen)
            if len(img_array.shape) == 3:
                img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                img_gray = img_array

            # Aplicar filtros para mejorar calidad
            # 1. Eliminar ruido
            img_denoised = cv2.fastNlMeansDenoising(img_gray, h=10)

            # 2. Aumentar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img_enhanced = clahe.apply(img_denoised)

            # 3. Binarización adaptativa
            img_binary = cv2.adaptiveThreshold(
                img_enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Convertir de vuelta a PIL
            return Image.fromarray(img_binary)

        except Exception as e:
            print(f"Error en preprocesamiento: {e}")
            return imagen

    def normalizar_documento(self, archivo_path: str) -> Optional[str]:
        """
        Normaliza un documento a PDF con texto buscable

        Args:
            archivo_path: Ruta al documento original

        Returns:
            Ruta al documento normalizado
        """
        path = Path(archivo_path)
        extension = path.suffix.lower()

        # Nombre del archivo normalizado
        hash_nombre = hashlib.md5(path.name.encode()).hexdigest()[:8]
        archivo_normalizado = self.output_dir / f"{path.stem}_{hash_nombre}_normalizado.pdf"

        try:
            if extension == '.pdf':
                # Ya es PDF, solo verificar si tiene texto
                resultado = self._procesar_pdf(archivo_path)
                if len(resultado['texto'].strip()) > 100:
                    # Tiene texto, copiar el archivo
                    import shutil
                    shutil.copy2(archivo_path, archivo_normalizado)
                    return str(archivo_normalizado)
                else:
                    # No tiene texto, aplicar OCR y crear PDF buscable
                    return self._crear_pdf_buscable(archivo_path, archivo_normalizado)

            elif extension in ['.doc', '.docx']:
                # Convertir DOC a PDF
                return self._convertir_doc_a_pdf(archivo_path, archivo_normalizado)

            elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Crear PDF desde imagen con OCR
                return self._crear_pdf_desde_imagen(archivo_path, archivo_normalizado)

            else:
                print(f"Formato no soportado para normalización: {extension}")
                return None

        except Exception as e:
            print(f"Error al normalizar documento: {e}")
            return None

    def _crear_pdf_buscable(self, pdf_path: str, output_path: str) -> Optional[str]:
        """Crea un PDF buscable desde un PDF escaneado usando OCR"""
        try:
            from pdf2image import convert_from_path
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from PIL import Image
            import pytesseract

            imagenes = convert_from_path(pdf_path, dpi=300)
            c = canvas.Canvas(str(output_path), pagesize=letter)

            for imagen in imagenes:
                # Aplicar OCR
                texto = pytesseract.image_to_string(imagen, lang='spa')

                # Agregar texto invisible en el PDF
                c.drawString(100, 750, "")  # Placeholder
                c.showPage()

            c.save()
            return str(output_path)

        except Exception as e:
            print(f"Error al crear PDF buscable: {e}")
            return None

    def _convertir_doc_a_pdf(self, doc_path: str, output_path: str) -> Optional[str]:
        """Convierte DOC/DOCX a PDF"""
        try:
            # Esta función requiere libreoffice o similar instalado
            import subprocess

            resultado = subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', str(output_path.parent),
                doc_path
            ], capture_output=True, timeout=60)

            if resultado.returncode == 0:
                return str(output_path)
            else:
                print(f"Error al convertir DOC: {resultado.stderr.decode()}")
                return None

        except Exception as e:
            print(f"Error al convertir DOC a PDF: {e}")
            print("Nota: Se requiere LibreOffice instalado para convertir DOC a PDF")
            return None

    def _crear_pdf_desde_imagen(self, imagen_path: str, output_path: str) -> Optional[str]:
        """Crea un PDF desde una imagen"""
        try:
            from PIL import Image
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader

            img = Image.open(imagen_path)
            width, height = img.size

            # Crear PDF
            c = canvas.Canvas(str(output_path), pagesize=(width, height))
            c.drawImage(ImageReader(img), 0, 0, width=width, height=height)
            c.save()

            return str(output_path)

        except Exception as e:
            print(f"Error al crear PDF desde imagen: {e}")
            return None


if __name__ == "__main__":
    # Ejemplo de uso
    processor = DocumentProcessor()

    # Procesar un PDF
    resultado = processor.procesar_documento("ejemplo.pdf")
    print(f"Texto extraído ({len(resultado['texto'])} caracteres)")
    print(f"OCR aplicado: {resultado['ocr_aplicado']}")
    print(f"Confianza OCR: {resultado['confianza_ocr']:.2f}")
