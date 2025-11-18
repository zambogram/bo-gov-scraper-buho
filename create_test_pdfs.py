#!/usr/bin/env python3
"""
Script para crear PDFs de prueba para el sistema de OCR.
Crea 3 PDFs de ejemplo:
1. PDF digital (con texto extraíble)
2. PDF escaneado simulado (imagen sin texto)
3. PDF híbrido (poco texto)
"""

import fitz  # PyMuPDF
import os
from pathlib import Path

def create_digital_pdf():
    """Crea un PDF digital con mucho texto"""
    doc = fitz.open()
    page = doc.new_page()

    text = """
    DECRETO SUPREMO N° 12345

    EVO MORALES AYMA
    PRESIDENTE CONSTITUCIONAL DEL ESTADO PLURINACIONAL DE BOLIVIA

    CONSIDERANDO:

    Que el artículo 172 de la Constitución Política del Estado, establece
    entre las atribuciones del Presidente del Estado, la de ejecutar y hacer
    cumplir las leyes, expidiendo los Decretos Supremos y resoluciones
    necesarias.

    Que mediante Ley N° 1234 de fecha 15 de enero de 2024, se establece
    el marco normativo para la implementación de políticas públicas en
    materia de desarrollo sostenible y conservación del medio ambiente.

    Que es necesario reglamentar los procedimientos y mecanismos de
    implementación de las disposiciones contenidas en la Ley N° 1234,
    a fin de garantizar su correcta aplicación en todo el territorio nacional.

    EN CONSEJO DE MINISTROS,

    DECRETA:

    Artículo 1.- (OBJETO) El presente Decreto Supremo tiene por objeto
    establecer los lineamientos, procedimientos y mecanismos para la
    implementación de la Ley N° 1234, de fecha 15 de enero de 2024.

    Artículo 2.- (ÁMBITO DE APLICACIÓN) Las disposiciones del presente
    Decreto Supremo son de aplicación obligatoria en todo el territorio
    nacional y para todas las instituciones públicas y privadas.

    Artículo 3.- (DEFINICIONES) Para efectos del presente Decreto Supremo,
    se establecen las siguientes definiciones:

    a) Desarrollo Sostenible: Desarrollo que satisface las necesidades
       del presente sin comprometer la capacidad de las futuras
       generaciones para satisfacer sus propias necesidades.

    b) Conservación Ambiental: Conjunto de medidas y acciones orientadas
       a la protección, preservación y restauración del medio ambiente.

    c) Política Pública: Conjunto de decisiones y acciones adoptadas por
       el Estado para atender determinadas problemáticas de interés público.

    Artículo 4.- (VIGENCIA) El presente Decreto Supremo entrará en vigencia
    a partir de su publicación en la Gaceta Oficial de Bolivia.

    Dado en el Palacio de Gobierno de la ciudad de La Paz, a los quince
    días del mes de noviembre del año dos mil veinticuatro.

    FDO. EVO MORALES AYMA
    PRESIDENTE CONSTITUCIONAL DEL ESTADO PLURINACIONAL DE BOLIVIA
    """

    # Insertar texto en múltiples posiciones para simular documento real
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv", align=0)

    output_path = "data/pdfs/decreto_digital.pdf"
    doc.save(output_path)
    doc.close()
    print(f"✅ Creado: {output_path} (PDF DIGITAL - mucho texto extraíble)")


def create_scanned_pdf():
    """Crea un PDF que simula estar escaneado (imagen)"""
    doc = fitz.open()
    page = doc.new_page()

    # Dibujar rectángulos y líneas para simular un documento escaneado
    # Esto crea una imagen visual pero sin texto extraíble

    # Título (dibujado, no texto)
    rect = fitz.Rect(100, 50, 500, 100)
    page.draw_rect(rect, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9))

    # Simular párrafos con líneas
    y = 120
    for i in range(20):
        # Líneas horizontales que simulan texto
        page.draw_line((80, y), (520, y), width=0.5)
        page.draw_line((80, y+5), (500, y+5), width=0.5)
        page.draw_line((80, y+10), (510, y+10), width=0.5)
        y += 30

    # Agregar MUY poco texto (para simular metadatos)
    small_rect = fitz.Rect(500, 780, 590, 800)
    page.insert_textbox(small_rect, "Pág. 1", fontsize=8, fontname="helv")

    output_path = "data/pdfs/documento_escaneado.pdf"
    doc.save(output_path)
    doc.close()
    print(f"✅ Creado: {output_path} (PDF ESCANEADO - casi sin texto extraíble)")


def create_minimal_text_pdf():
    """Crea un PDF con poco texto (caso límite)"""
    doc = fitz.open()
    page = doc.new_page()

    # Solo un título corto
    rect = fitz.Rect(200, 300, 400, 350)
    page.insert_textbox(rect, "LEY N° 789", fontsize=16, fontname="helv")

    # Algunas líneas decorativas
    page.draw_line((100, 400), (500, 400), width=2)

    output_path = "data/pdfs/ley_minimo_texto.pdf"
    doc.save(output_path)
    doc.close()
    print(f"✅ Creado: {output_path} (PDF HÍBRIDO - texto mínimo, cercano al umbral)")


def create_multi_page_digital():
    """Crea un PDF digital con varias páginas"""
    doc = fitz.open()

    for page_num in range(1, 4):
        page = doc.new_page()

        text = f"""
        GACETA OFICIAL DE BOLIVIA
        Página {page_num} de 3

        SECCIÓN TERCERA: DECRETOS SUPREMOS

        {'='*50}

        MINISTERIO DE ECONOMÍA Y FINANZAS PÚBLICAS

        Decreto Supremo N° 456{page_num}
        Fecha: {15+page_num} de Noviembre de 2024

        CONSIDERANDO:

        Que la Constitución Política del Estado en su artículo {150 + page_num}
        establece las competencias privativas del nivel central del Estado
        en materia de política económica y fiscal.

        Que es necesario implementar medidas económicas para fortalecer
        el desarrollo productivo del país y garantizar la estabilidad
        macroeconómica nacional.

        Que el Plan de Desarrollo Económico y Social {2024 + page_num}-{2029 + page_num}
        establece como prioridad el crecimiento económico con inclusión
        social y redistribución equitativa de la riqueza.

        EN CONSEJO DE MINISTROS,

        DECRETA:

        Artículo 1.- Se aprueba el programa de incentivos fiscales
        para el sector productivo nacional, conforme a los lineamientos
        establecidos en el anexo del presente Decreto Supremo.

        Artículo 2.- El Ministerio de Economía y Finanzas Públicas
        queda encargado de la implementación y seguimiento de las
        medidas establecidas en el artículo precedente.

        Artículo 3.- El presente Decreto Supremo entrará en vigencia
        a partir de la fecha de su publicación.

        {'='*50}

        Dado en el Palacio de Gobierno, ciudad de La Paz.

        FDO. Presidente del Estado Plurinacional de Bolivia
        FDO. Ministro de Economía y Finanzas Públicas
        """

        rect = fitz.Rect(50, 50, 550, 780)
        page.insert_textbox(rect, text, fontsize=10, fontname="helv", align=0)

    output_path = "data/pdfs/gaceta_multipagina.pdf"
    doc.save(output_path)
    doc.close()
    print(f"✅ Creado: {output_path} (PDF DIGITAL - 3 páginas)")


def main():
    """Crea todos los PDFs de prueba"""
    print("\n" + "="*70)
    print("CREANDO PDFs DE PRUEBA PARA SISTEMA DE OCR")
    print("="*70 + "\n")

    # Crear directorio si no existe
    Path("data/pdfs").mkdir(parents=True, exist_ok=True)

    try:
        create_digital_pdf()
        create_scanned_pdf()
        create_minimal_text_pdf()
        create_multi_page_digital()

        print("\n" + "="*70)
        print("✅ TODOS LOS PDFs DE PRUEBA CREADOS EXITOSAMENTE")
        print("="*70)

        print("\nArchivos creados en data/pdfs/:")
        import glob
        for pdf in sorted(glob.glob("data/pdfs/*.pdf")):
            size = os.path.getsize(pdf)
            print(f"  - {os.path.basename(pdf)} ({size:,} bytes)")

        print("\n" + "="*70)
        print("CARACTERÍSTICAS DE LOS PDFs:")
        print("="*70)
        print("1. decreto_digital.pdf")
        print("   - Tipo: DIGITAL")
        print("   - Texto: >2000 caracteres extraíbles")
        print("   - Detección esperada: DIGITAL (no OCR)")
        print()
        print("2. documento_escaneado.pdf")
        print("   - Tipo: ESCANEADO (simulado)")
        print("   - Texto: ~6 caracteres ('Pág. 1')")
        print("   - Detección esperada: ESCANEADO (aplicará OCR)")
        print()
        print("3. ley_minimo_texto.pdf")
        print("   - Tipo: HÍBRIDO")
        print("   - Texto: ~10 caracteres ('LEY N° 789')")
        print("   - Detección esperada: ESCANEADO (< 100 caracteres)")
        print()
        print("4. gaceta_multipagina.pdf")
        print("   - Tipo: DIGITAL")
        print("   - Páginas: 3")
        print("   - Texto: >6000 caracteres totales")
        print("   - Detección esperada: DIGITAL (no OCR)")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error al crear PDFs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
