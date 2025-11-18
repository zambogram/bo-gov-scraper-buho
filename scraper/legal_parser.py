"""
MÓDULO 4: LEGAL PARSER
======================
Este módulo se encarga de:
1. Segmentar el texto de documentos legales en artículos
2. Identificar la estructura jerárquica:
   - Artículos
   - Incisos (subdivisiones de artículos)
   - Parágrafos
3. Generar una estructura JSON con el documento completo
4. Extraer cada artículo con su contenido

Los documentos legales bolivianos tienen estructura como:
  ARTÍCULO 1.-
  ARTÍCULO 2.- (TÍTULO DEL ARTÍCULO)
  I. Primer inciso
  II. Segundo inciso
  PARÁGRAFO I.- Texto del parágrafo

Autor: Sistema BÚHO
"""

import re
import json
import os
from typing import List, Dict, Optional


class LegalParser:
    """
    Clase para parsear y segmentar documentos legales bolivianos.

    Identifica y extrae:
    - Artículos
    - Incisos (numeración romana)
    - Parágrafos
    - Títulos y capítulos
    """

    def __init__(self):
        """Inicializa el parser legal."""
        pass

    def segment_articles(self, text: str) -> List[Dict[str, any]]:
        """
        Segmenta el texto en artículos.

        Busca patrones como:
        - ARTÍCULO 1.-
        - ARTICULO 1°.-
        - Art. 1.-

        Args:
            text: Texto completo del documento

        Returns:
            Lista de diccionarios, cada uno representando un artículo:
            - numero: Número del artículo
            - titulo: Título del artículo (si existe)
            - contenido: Texto completo del artículo
            - incisos: Lista de incisos (si existen)
            - paragrafos: Lista de parágrafos (si existen)
        """
        # Patrón para detectar inicio de artículos
        # Captura: ARTÍCULO 1.- o ARTICULO 1°.- o Art. 1.-
        article_pattern = r'(?:ARTÍCULO|ARTICULO|ART\.?)\s+(\d+)[°º]?\.?[-\.]'

        # Dividir el texto en secciones por artículos
        article_matches = list(re.finditer(article_pattern, text, re.IGNORECASE))

        if not article_matches:
            print(f"    ⚠ No se encontraron artículos en el documento")
            return []

        articles = []

        for i, match in enumerate(article_matches):
            article_num = match.group(1)
            start_pos = match.start()

            # El contenido del artículo va desde este match hasta el siguiente
            # (o hasta el final del texto si es el último artículo)
            if i < len(article_matches) - 1:
                end_pos = article_matches[i + 1].start()
            else:
                end_pos = len(text)

            article_text = text[start_pos:end_pos].strip()

            # Extraer título del artículo (si existe)
            # Formato: ARTÍCULO 1.- (TÍTULO DEL ARTÍCULO)
            title_match = re.search(r'\(([^)]+)\)', article_text[:200])
            article_title = title_match.group(1).strip() if title_match else ''

            # Extraer contenido (después del número y título)
            content_start = match.end()
            if title_match:
                content_start = match.start() + title_match.end()

            article_content = article_text[content_start - start_pos:].strip()

            # Extraer incisos (I., II., III., etc.)
            incisos = self.extract_incisos(article_content)

            # Extraer parágrafos
            paragrafos = self.extract_paragrafos(article_content)

            articles.append({
                'numero': int(article_num),
                'titulo': article_title,
                'contenido': article_content,
                'texto_completo': article_text,
                'incisos': incisos,
                'paragrafos': paragrafos,
                'num_incisos': len(incisos),
                'num_paragrafos': len(paragrafos)
            })

        print(f"    ✓ Se encontraron {len(articles)} artículos")
        return articles

    def extract_incisos(self, text: str) -> List[Dict[str, str]]:
        """
        Extrae incisos de un artículo.

        Los incisos usan numeración romana: I., II., III., IV., etc.

        Args:
            text: Texto del artículo

        Returns:
            Lista de incisos con su número y contenido
        """
        # Patrón para incisos: I., II., III., IV., V., etc.
        inciso_pattern = r'^([IVXLCDM]+)\.\s+'

        incisos = []
        lines = text.split('\n')

        current_inciso_num = None
        current_inciso_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Verificar si la línea empieza con un inciso
            match = re.match(inciso_pattern, line)
            if match:
                # Guardar el inciso anterior si existe
                if current_inciso_num:
                    incisos.append({
                        'numero': current_inciso_num,
                        'contenido': ' '.join(current_inciso_text).strip()
                    })

                # Empezar nuevo inciso
                current_inciso_num = match.group(1)
                current_inciso_text = [line[match.end():]]
            elif current_inciso_num:
                # Continuar con el inciso actual
                current_inciso_text.append(line)

        # Guardar el último inciso
        if current_inciso_num:
            incisos.append({
                'numero': current_inciso_num,
                'contenido': ' '.join(current_inciso_text).strip()
            })

        return incisos

    def extract_paragrafos(self, text: str) -> List[Dict[str, str]]:
        """
        Extrae parágrafos de un artículo.

        Los parágrafos tienen formato: PARÁGRAFO I., PARÁGRAFO II., etc.

        Args:
            text: Texto del artículo

        Returns:
            Lista de parágrafos con su número y contenido
        """
        # Patrón para parágrafos
        paragrafo_pattern = r'PARÁGRAFO\s+([IVXLCDM]+)\.?[-\.]'

        paragrafo_matches = list(re.finditer(paragrafo_pattern, text, re.IGNORECASE))

        if not paragrafo_matches:
            return []

        paragrafos = []

        for i, match in enumerate(paragrafo_matches):
            paragrafo_num = match.group(1)
            start_pos = match.end()

            # El contenido va hasta el siguiente parágrafo o fin del texto
            if i < len(paragrafo_matches) - 1:
                end_pos = paragrafo_matches[i + 1].start()
            else:
                end_pos = len(text)

            paragrafo_content = text[start_pos:end_pos].strip()

            paragrafos.append({
                'numero': paragrafo_num,
                'contenido': paragrafo_content
            })

        return paragrafos

    def extract_metadata_from_text(self, text: str) -> Dict[str, str]:
        """
        Extrae metadatos adicionales del texto del documento.

        Busca:
        - Considerandos
        - Secciones de "Decreta", "Promulga", etc.
        - Firmas y cargos

        Args:
            text: Texto completo del documento

        Returns:
            Diccionario con metadatos encontrados
        """
        metadata = {}

        # Buscar considerandos
        considerandos_match = re.search(
            r'CONSIDERANDO:(.*?)(?:DECRETA|PROMULGA|RESUELVE)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if considerandos_match:
            metadata['considerandos'] = considerandos_match.group(1).strip()

        # Buscar tipo de acción (DECRETA, PROMULGA, RESUELVE)
        action_match = re.search(r'(DECRETA|PROMULGA|RESUELVE):', text, re.IGNORECASE)
        if action_match:
            metadata['tipo_accion'] = action_match.group(1).upper()

        return metadata

    def parse_document(self, text: str, document_id: str = '') -> Dict[str, any]:
        """
        FUNCIÓN PRINCIPAL: Parsea un documento legal completo.

        Esta es la función que debes llamar para parsear documentos.

        Args:
            text: Texto completo del documento
            document_id: ID del documento (opcional)

        Returns:
            Diccionario con la estructura completa del documento:
            - document_id: ID del documento
            - metadata: Metadatos del documento
            - articles: Lista de artículos con su contenido
            - total_articles: Número total de artículos
            - texto_completo_length: Longitud del texto original
        """
        print(f"\n  {'='*56}")
        print(f"  PARSEANDO DOCUMENTO: {document_id or 'SIN ID'}")
        print(f"  {'='*56}")

        # Extraer artículos
        print(f"  → Segmentando artículos...")
        articles = self.segment_articles(text)

        # Extraer metadatos adicionales
        print(f"  → Extrayendo metadatos del documento...")
        doc_metadata = self.extract_metadata_from_text(text)

        # Construir estructura del documento
        document_structure = {
            'document_id': document_id,
            'metadata': doc_metadata,
            'articles': articles,
            'total_articles': len(articles),
            'texto_completo_length': len(text)
        }

        print(f"\n  RESUMEN DE PARSEO:")
        print(f"  - Total de artículos: {len(articles)}")
        print(f"  - Total de incisos: {sum(a['num_incisos'] for a in articles)}")
        print(f"  - Total de parágrafos: {sum(a['num_paragrafos'] for a in articles)}")
        print(f"  {'='*56}\n")

        return document_structure

    def save_to_json(self, document_structure: Dict[str, any], output_dir: str = "data/parsed") -> Optional[str]:
        """
        Guarda la estructura del documento en un archivo JSON.

        Args:
            document_structure: Estructura del documento generada por parse_document()
            output_dir: Directorio donde guardar el JSON

        Returns:
            Ruta del archivo JSON guardado o None si falla
        """
        try:
            os.makedirs(output_dir, exist_ok=True)

            # Generar nombre de archivo
            doc_id = document_structure.get('document_id', 'documento')
            # Sanitizar nombre de archivo
            doc_id = re.sub(r'[<>:"/\\|?*]', '_', doc_id)
            json_filename = f"{doc_id}.json"
            json_path = os.path.join(output_dir, json_filename)

            # Guardar JSON con formato legible
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(document_structure, f, ensure_ascii=False, indent=2)

            print(f"    ✓ JSON guardado en: {json_filename}")
            return json_path

        except Exception as e:
            print(f"    ✗ Error al guardar JSON: {str(e)}")
            return None


def main():
    """
    Función de prueba del parser legal.

    NOTA PARA EL USUARIO:
    Esta es solo una función de prueba. Para usar el parser en el pipeline
    completo, debes llamarlo desde main.py usando run_full_pipeline().
    """
    # Texto de ejemplo de un documento legal
    sample_text = """
    LEY N° 1234 DE 15 DE JULIO DE 2023

    CONSIDERANDO:
    Que es necesario regular...

    DECRETA:

    ARTÍCULO 1.- (OBJETO)
    La presente Ley tiene por objeto establecer el marco legal para...

    ARTÍCULO 2.- (DEFINICIONES)
    Para efectos de la presente Ley, se establecen las siguientes definiciones:

    I. Término 1: Definición del término 1.
    II. Término 2: Definición del término 2.
    III. Término 3: Definición del término 3.

    PARÁGRAFO I.- Las definiciones son de aplicación obligatoria.

    ARTÍCULO 3.- (DISPOSICIONES FINALES)
    La presente Ley entrará en vigencia a partir de su publicación.
    """

    parser = LegalParser()
    document = parser.parse_document(sample_text, document_id='LEY-1234-2023')

    # Mostrar resultados
    print("\nEstructura del documento:")
    print(json.dumps(document, ensure_ascii=False, indent=2))

    # Guardar en JSON
    parser.save_to_json(document)


if __name__ == "__main__":
    main()
