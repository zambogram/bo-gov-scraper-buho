# Directorio de Datos

Este directorio contiene los archivos JSON extraídos por los scrapers de BÚHO.

## Estructura de Datos

Los archivos JSON deben seguir el siguiente formato:

```json
{
  "sitio": "gaceta",
  "tipo_norma": "ley",
  "numero_norma": "1234",
  "fecha_norma": "2023-11-15",
  "titulo": "Título del documento",
  "url_fuente": "https://...",
  "url_pdf": "https://...pdf",
  "filename_pdf": "ley_1234.pdf",
  "metodo_extraccion": "pdf_text",
  "paginas": 15,
  "caracteres": 45000,
  "articulos": [
    {
      "numero": "1",
      "titulo": "Título del artículo",
      "contenido": "Texto completo del artículo..."
    }
  ]
}
```

## Campos Requeridos

### Documento
- `sitio`: Identificador del sitio fuente (gaceta, abi, verbo_juridico, etc.)
- `tipo_norma`: Tipo de norma (ley, decreto, resolución, etc.)
- `numero_norma`: Número de la norma
- `fecha_norma`: Fecha en formato YYYY-MM-DD
- `titulo`: Título del documento

### Artículos
- `numero`: Número del artículo
- `contenido`: Texto completo del artículo

## Archivo de Ejemplo

Ver `ejemplo_documento.json` para un ejemplo completo.

## Procesamiento

Para exportar estos datos a Supabase:

```bash
python main.py --export-supabase
```

Para exportar solo un archivo:

```bash
python main.py --export-documento data/mi_documento.json
```

## Sitios Soportados

- `gaceta` - Gaceta Oficial de Bolivia
- `abi` - Agencia Boliviana de Información
- `verbo_juridico` - Verbo Jurídico
- `lexivox` - Lexivox
- `tribunal_constitucional` - Tribunal Constitucional Plurinacional
