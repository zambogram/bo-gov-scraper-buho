"""
Metadata extraction and enrichment for legal documents
"""
import re
from datetime import datetime
from typing import Dict, Optional


class MetadataExtractor:
    """Extract and enrich metadata from legal documents"""

    @staticmethod
    def extract_date(text: str) -> Optional[str]:
        """Extract date from text"""
        date_patterns = [
            r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]

        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if groups[1] in months:
                            day, month_name, year = groups
                            month = months[month_name]
                            return f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
                        else:
                            # Numeric date
                            return f'{groups[2]}-{groups[1].zfill(2)}-{groups[0].zfill(2)}'
                except:
                    continue

        return None

    @staticmethod
    def extract_numero(text: str, doc_type: str = None) -> Optional[str]:
        """Extract document number from text"""
        patterns = [
            r'N[°º]\s*(\d+(?:/\d+)?)',
            r'Nro\.\s*(\d+(?:/\d+)?)',
            r'(\d+/\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def enrich_metadata(document: Dict) -> Dict:
        """Enrich document metadata with extracted information"""
        content = document.get('content', '')
        title = document.get('title', '')

        metadata = document.get('metadata', {})

        # Extract additional metadata
        if not metadata.get('fecha'):
            fecha = MetadataExtractor.extract_date(content) or MetadataExtractor.extract_date(title)
            if fecha:
                metadata['fecha'] = fecha

        if not metadata.get('numero'):
            numero = MetadataExtractor.extract_numero(content) or MetadataExtractor.extract_numero(title)
            if numero:
                metadata['numero'] = numero

        document['metadata'] = metadata
        return document
