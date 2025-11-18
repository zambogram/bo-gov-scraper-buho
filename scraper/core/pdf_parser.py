"""
Parser avanzado de PDFs con detección automática de OCR
Extrae texto y estructura de documentos legales
"""
import re
import os
from typing import Dict, List, Optional, Tuple
from io import BytesIO

try:
    import PyPDF2
    import pdfplumber
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
except ImportError:
    print("Advertencia: Algunas librerías de PDF no están instaladas")


class PDFParser:
    """
    Parser avanzado de PDFs con soporte para:
    - Detección automática de PDFs escaneados vs digitales
    - Extracción de texto con OCR si es necesario
    - Parsing de estructura jerárquica de documentos legales
    """

    def __init__(self, pdf_path: str):
        """
        Inicializa el parser

        Args:
            pdf_path: Ruta al archivo PDF
        """
        self.pdf_path = pdf_path
        self.is_scanned = None
        self.text = None
        self.metadata = {}

    def detect_scanned(self, threshold: float = 0.5) -> bool:
        """
        Detecta si el PDF es escaneado (requiere OCR)

        Args:
            threshold: Umbral de texto digital (0-1)

        Returns:
            True si es escaneado, False si es digital
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return True

                # Analizar primera página
                first_page = pdf.pages[0]
                text = first_page.extract_text() or ""

                # Si tiene poco o ningún texto, probablemente es escaneado
                if len(text.strip()) < 100:
                    return True

                # Verificar calidad del texto
                # PDFs digitales tienen más caracteres alfanuméricos
                alphanum = sum(c.isalnum() for c in text)
                ratio = alphanum / len(text) if len(text) > 0 else 0

                return ratio < threshold

        except Exception as e:
            print(f"Error detectando tipo de PDF: {e}")
            return True  # Asumir escaneado en caso de error

    def extract_text_digital(self) -> str:
        """
        Extrae texto de PDF digital

        Returns:
            Texto extraído
        """
        text_parts = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)

            return "\n".join(text_parts)

        except Exception as e:
            print(f"Error extrayendo texto digital: {e}")
            return ""

    def extract_text_ocr(self, lang: str = 'spa') -> str:
        """
        Extrae texto usando OCR

        Args:
            lang: Idioma para OCR (spa=español)

        Returns:
            Texto extraído
        """
        text_parts = []

        try:
            # Convertir PDF a imágenes
            images = convert_from_path(self.pdf_path, dpi=300)

            # Aplicar OCR a cada página
            for i, image in enumerate(images):
                try:
                    page_text = pytesseract.image_to_string(image, lang=lang)
                    text_parts.append(page_text)
                except Exception as e:
                    print(f"Error en OCR de página {i+1}: {e}")

            return "\n".join(text_parts)

        except Exception as e:
            print(f"Error en extracción OCR: {e}")
            return ""

    def extract_text(self, force_ocr: bool = False) -> str:
        """
        Extrae texto del PDF, usando OCR si es necesario

        Args:
            force_ocr: Forzar uso de OCR

        Returns:
            Texto extraído
        """
        if self.text is not None:
            return self.text

        # Detectar tipo de PDF
        self.is_scanned = self.detect_scanned() if not force_ocr else True

        # Extraer texto según tipo
        if force_ocr or self.is_scanned:
            print(f"  → PDF escaneado detectado, usando OCR...")
            self.text = self.extract_text_ocr()
        else:
            self.text = self.extract_text_digital()

        return self.text

    def extract_metadata(self) -> Dict:
        """
        Extrae metadatos del PDF

        Returns:
            Diccionario con metadatos
        """
        metadata = {
            "filename": os.path.basename(self.pdf_path),
            "file_size": os.path.getsize(self.pdf_path),
            "is_scanned": self.is_scanned,
            "pages": 0,
        }

        try:
            with open(self.pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata["pages"] = len(pdf_reader.pages)

                # Metadatos del PDF
                info = pdf_reader.metadata
                if info:
                    metadata.update({
                        "title": info.get("/Title", ""),
                        "author": info.get("/Author", ""),
                        "subject": info.get("/Subject", ""),
                        "creator": info.get("/Creator", ""),
                        "producer": info.get("/Producer", ""),
                        "creation_date": info.get("/CreationDate", ""),
                    })

        except Exception as e:
            print(f"Error extrayendo metadatos: {e}")

        return metadata

    def parse_sections(self, section_patterns: Dict[str, str]) -> Dict[str, str]:
        """
        Parsea secciones específicas del documento

        Args:
            section_patterns: Dict con nombre_sección: patrón_regex

        Returns:
            Dict con nombre_sección: contenido
        """
        if self.text is None:
            self.extract_text()

        sections = {}

        # Ordenar patrones por posición en el texto
        pattern_positions = []
        for name, pattern in section_patterns.items():
            match = re.search(pattern, self.text, re.IGNORECASE | re.MULTILINE)
            if match:
                pattern_positions.append((match.start(), name, pattern))

        pattern_positions.sort()

        # Extraer contenido de cada sección
        for i, (start_pos, name, pattern) in enumerate(pattern_positions):
            # Inicio de esta sección
            match = re.search(pattern, self.text, re.IGNORECASE | re.MULTILINE)
            section_start = match.end()

            # Fin de esta sección (inicio de la siguiente o final del texto)
            if i + 1 < len(pattern_positions):
                section_end = pattern_positions[i + 1][0]
            else:
                section_end = len(self.text)

            # Extraer contenido
            content = self.text[section_start:section_end].strip()
            sections[name] = content

        return sections

    def parse_tribunal_constitucional(self) -> Dict:
        """
        Parser específico para documentos del Tribunal Constitucional

        Returns:
            Estructura parseada
        """
        patterns = {
            "vistos": r"VISTOS?\s*[:.]?",
            "antecedentes": r"ANTECEDENTES?\s*[:.]?",
            "problematica": r"PROBLEM[ÁA]TICA\s*[:.]?",
            "considerando": r"CONSIDERANDO\s*[:.]?",
            "fundamentos": r"FUNDAMENTOS?\s+JUR[ÍI]DICOS?\s*[:.]?",
            "por_tanto": r"POR\s+TANTO\s*[:.]?",
        }

        sections = self.parse_sections(patterns)

        return {
            "tipo": "tribunal_constitucional",
            "metadata": self.extract_metadata(),
            "secciones": sections,
            "texto_completo": self.text
        }

    def parse_tribunal_supremo(self) -> Dict:
        """
        Parser específico para documentos del Tribunal Supremo

        Returns:
            Estructura parseada
        """
        patterns = {
            "resultandos": r"RESULTANDOS?\s*[:.]?",
            "considerandos": r"CONSIDERANDOS?\s*[:.]?",
            "parte_resolutiva": r"PARTE\s+RESOLUTIVA\s*[:.]?|RESUELVE\s*[:.]?",
        }

        sections = self.parse_sections(patterns)

        return {
            "tipo": "tribunal_supremo",
            "metadata": self.extract_metadata(),
            "secciones": sections,
            "texto_completo": self.text
        }

    def parse_contraloria(self) -> Dict:
        """
        Parser específico para documentos de Contraloría

        Returns:
            Estructura parseada
        """
        # Buscar numerales romanos
        numeral_pattern = r"^([IVX]+)\.\s*(.+?)(?=^[IVX]+\.|$)"

        numerales = {}
        matches = re.finditer(numeral_pattern, self.text or "", re.MULTILINE | re.DOTALL)

        for match in matches:
            numeral = match.group(1)
            contenido = match.group(2).strip()
            numerales[f"numeral_{numeral}"] = contenido

        return {
            "tipo": "contraloria",
            "metadata": self.extract_metadata(),
            "numerales": numerales,
            "texto_completo": self.text
        }

    def parse_generic(self) -> Dict:
        """
        Parser genérico para cualquier documento

        Returns:
            Estructura básica parseada
        """
        return {
            "tipo": "generico",
            "metadata": self.extract_metadata(),
            "texto_completo": self.text or self.extract_text()
        }
