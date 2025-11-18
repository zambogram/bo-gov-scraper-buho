#!/usr/bin/env python3
"""
Script de validación de cobertura para TCP Jurisprudencia

Este script te ayuda a:
1. Comparar el total de documentos obtenidos vs total esperado de la API
2. Verificar que no se cortó la paginación prematuramente
3. Detectar documentos duplicados
4. Generar reporte de validación

Uso:
    python scripts/validar_cobertura_tcp.py --json data/raw/tcp_jurisprudencia/documentos_TIMESTAMP.json
    python scripts/validar_cobertura_tcp.py --csv data/raw/tcp_jurisprudencia/documentos_TIMESTAMP.csv
"""

import argparse
import json
import pandas as pd
from pathlib import Path
from collections import Counter
from datetime import datetime


def validar_desde_json(archivo_json: Path):
    """
    Valida cobertura desde archivo JSON de metadatos

    Args:
        archivo_json: Path al archivo JSON generado por el scraper
    """
    print(f"📊 VALIDACIÓN DE COBERTURA - TCP JURISPRUDENCIA")
    print("=" * 70)
    print(f"Archivo: {archivo_json}")
    print()

    # Cargar datos
    with open(archivo_json, 'r', encoding='utf-8') as f:
        documentos = json.load(f)

    total_docs = len(documentos)
    print(f"✅ Total documentos en JSON: {total_docs}")

    # Validación 1: Documentos duplicados
    print(f"\n📋 VALIDACIÓN 1: Duplicados")
    print("-" * 70)

    ids = [doc.get('id_documento') for doc in documentos]
    duplicados = [id_doc for id_doc, count in Counter(ids).items() if count > 1]

    if duplicados:
        print(f"⚠️  {len(duplicados)} IDs duplicados encontrados:")
        for id_doc in duplicados[:10]:
            print(f"   - {id_doc}")
    else:
        print(f"✅ No hay documentos duplicados")

    # Validación 2: Campos faltantes
    print(f"\n📋 VALIDACIÓN 2: Campos faltantes")
    print("-" * 70)

    campos_importantes = [
        'id_documento',
        'numero_resolucion',
        'tipo_documento',
        'fecha_resolucion'
    ]

    docs_con_campos_faltantes = 0
    for doc in documentos:
        faltantes = [campo for campo in campos_importantes if not doc.get(campo)]
        if faltantes:
            docs_con_campos_faltantes += 1

    if docs_con_campos_faltantes > 0:
        porcentaje = (docs_con_campos_faltantes / total_docs) * 100
        print(f"⚠️  {docs_con_campos_faltantes} documentos ({porcentaje:.1f}%) con campos faltantes")
    else:
        print(f"✅ Todos los documentos tienen campos completos")

    # Validación 3: URLs de PDF
    print(f"\n📋 VALIDACIÓN 3: URLs de PDF")
    print("-" * 70)

    docs_con_pdf = sum(1 for doc in documentos if doc.get('url_pdf'))
    docs_con_pdf_descargado = sum(1 for doc in documentos if doc.get('ruta_pdf'))

    print(f"URLs de PDF disponibles: {docs_con_pdf}/{total_docs} ({docs_con_pdf/total_docs*100:.1f}%)")
    print(f"PDFs descargados: {docs_con_pdf_descargado}/{total_docs} ({docs_con_pdf_descargado/total_docs*100:.1f}%)")

    # Validación 4: Distribución por año
    print(f"\n📋 VALIDACIÓN 4: Distribución temporal")
    print("-" * 70)

    años = []
    for doc in documentos:
        fecha = doc.get('fecha_resolucion', '')
        if fecha:
            try:
                año = fecha[:4]  # Asumir formato YYYY-MM-DD
                if año.isdigit():
                    años.append(int(año))
            except:
                pass

    if años:
        año_min = min(años)
        año_max = max(años)
        print(f"Rango de años: {año_min} - {año_max}")

        # Mostrar distribución
        from collections import Counter
        distribucion = Counter(años)
        print(f"\nTop 10 años con más documentos:")
        for año, count in sorted(distribucion.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {año}: {count} documentos")

        # Detectar años sospechosos (muy pocos documentos)
        años_sospechosos = [año for año, count in distribucion.items() if count < 5]
        if años_sospechosos:
            print(f"\n⚠️  Años con < 5 documentos (posible paginación incompleta):")
            for año in sorted(años_sospechosos):
                print(f"   {año}: {distribucion[año]} documentos")
    else:
        print(f"⚠️  No se pudieron extraer fechas")

    # Validación 5: Tipos de documento
    print(f"\n📋 VALIDACIÓN 5: Tipos de documento")
    print("-" * 70)

    tipos = [doc.get('tipo_documento', 'Sin tipo') for doc in documentos]
    distribucion_tipos = Counter(tipos)

    for tipo, count in distribucion_tipos.most_common():
        porcentaje = (count / total_docs) * 100
        print(f"   {tipo}: {count} ({porcentaje:.1f}%)")

    # Resumen final
    print(f"\n" + "=" * 70)
    print(f"📊 RESUMEN FINAL")
    print("=" * 70)
    print(f"Total documentos: {total_docs}")
    print(f"IDs únicos: {len(set(ids))}")
    print(f"Documentos con PDF: {docs_con_pdf_descargado}")
    print(f"Rango temporal: {año_min}-{año_max}" if años else "N/A")
    print()

    # Recomendaciones
    print(f"💡 RECOMENDACIONES:")
    print("-" * 70)

    if duplicados:
        print(f"⚠️  Eliminar {len(duplicados)} documentos duplicados")

    if docs_con_campos_faltantes > 50:
        print(f"⚠️  Revisar extracción de metadatos (muchos campos faltantes)")

    if años_sospechosos and len(años_sospechosos) > 5:
        print(f"⚠️  Verificar paginación - varios años con pocos documentos")

    if docs_con_pdf_descargado < total_docs * 0.9:
        print(f"⚠️  Muchos PDFs no descargados - revisar URLs y descarga")

    if not (duplicados or docs_con_campos_faltantes > 50 or años_sospechosos):
        print(f"✅ Todo parece correcto - cobertura validada")


def validar_desde_csv(archivo_csv: Path):
    """Valida cobertura desde CSV"""
    print(f"📊 VALIDACIÓN DE COBERTURA - TCP JURISPRUDENCIA")
    print("=" * 70)
    print(f"Archivo: {archivo_csv}")
    print()

    # Cargar CSV
    df = pd.read_csv(archivo_csv)

    print(f"✅ Total documentos en CSV: {len(df)}")
    print(f"📊 Columnas: {len(df.columns)}")

    # Duplicados
    print(f"\n📋 VALIDACIÓN: Duplicados")
    duplicados = df[df.duplicated(subset=['id_documento'], keep=False)]
    if len(duplicados) > 0:
        print(f"⚠️  {len(duplicados)} documentos duplicados")
    else:
        print(f"✅ No hay duplicados")

    # Valores nulos
    print(f"\n📋 VALIDACIÓN: Valores nulos")
    print(df.isnull().sum().head(10))

    # Distribución por año (si existe columna fecha)
    if 'fecha_resolucion' in df.columns:
        df['año'] = pd.to_datetime(df['fecha_resolucion'], errors='coerce').dt.year
        print(f"\n📋 Distribución por año:")
        print(df['año'].value_counts().sort_index().head(10))

    # Tipos de documento
    if 'tipo_documento' in df.columns:
        print(f"\n📋 Tipos de documento:")
        print(df['tipo_documento'].value_counts())


def comparar_con_total_esperado(archivo_json: Path, total_esperado: int):
    """
    Compara el total de documentos obtenidos vs el total esperado de la API

    Args:
        archivo_json: Path al JSON
        total_esperado: Total indicado en el campo "total" del JSON de la API
    """
    with open(archivo_json, 'r', encoding='utf-8') as f:
        documentos = json.load(f)

    total_obtenido = len(documentos)
    diferencia = abs(total_obtenido - total_esperado)
    porcentaje_diferencia = (diferencia / total_esperado * 100) if total_esperado > 0 else 0

    print(f"\n📊 COMPARACIÓN CON TOTAL ESPERADO")
    print("=" * 70)
    print(f"Total esperado (API): {total_esperado}")
    print(f"Total obtenido: {total_obtenido}")
    print(f"Diferencia: {diferencia} ({porcentaje_diferencia:.1f}%)")

    if porcentaje_diferencia < 5:
        print(f"✅ Cobertura completa (< 5% diferencia)")
    else:
        print(f"⚠️  Cobertura incompleta - revisar paginación")
        print(f"\n💡 Posibles causas:")
        print(f"   - Paginación cortada prematuramente")
        print(f"   - Parámetros incorrectos en la API")
        print(f"   - Documentos agregados durante el scraping")


def main():
    parser = argparse.ArgumentParser(
        description='Validar cobertura de scraping TCP Jurisprudencia',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--json',
        type=Path,
        help='Archivo JSON de metadatos'
    )

    parser.add_argument(
        '--csv',
        type=Path,
        help='Archivo CSV de documentos'
    )

    parser.add_argument(
        '--total-esperado',
        type=int,
        help='Total esperado según la API (campo "total" del JSON)'
    )

    args = parser.parse_args()

    if args.json:
        validar_desde_json(args.json)

        if args.total_esperado:
            comparar_con_total_esperado(args.json, args.total_esperado)

    elif args.csv:
        validar_desde_csv(args.csv)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
