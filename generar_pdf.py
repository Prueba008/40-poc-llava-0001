#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para generar un documento PDF con descripciones de procesos y diagramas.
"""

import os
import logging
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor

# ================= CONFIGURACIÓN =================
MARKDOWN_FILE = "./analisis/analisis_completo.md"
PNG_DIR = "./analisis/diagramas_png"
OUTPUT_PDF = "./documentacion/arquitectura_chatgpt_mastery.pdf"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# =================================================

# Crear directorio de salida si no existe
output_dir = os.path.dirname(OUTPUT_PDF)
if output_dir:
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Error al crear directorio {output_dir}: {e}")
        raise

def parse_markdown_to_text(md_content: str) -> list:
    """
    Convierte contenido Markdown a texto plano con estructura.
    """
    lines = md_content.split('\n')
    sections = []
    current_section = []
    current_code_block = False
    
    for line in lines:
        line = line.rstrip()
        
        # Detectar bloques de código PlantUML
        if line.strip().startswith('```plantuml'):
            current_code_block = True
            continue
        elif line.strip().startswith('```') and current_code_block:
            current_code_block = False
            continue
        elif current_code_block:
            continue
        
        # Detectar encabezados
        if line.startswith('#'):
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            sections.append(line)
        else:
            current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections

def get_image_for_section(section_text: str, png_dir: str) -> str:
    """
    Busca una imagen PNG correspondiente a la sección.
    """
    # Mapeo de secciones a diagramas
    section_mapping = {
        'A. API Gateway': 'ChatGPT  Mastery_diagrama_1.png',
        'B. Base de Datos Vectorial': 'ChatGPT  Mastery_diagrama_2.png',
        'C. Microservicios de búsqueda': 'ChatGPT  Mastery_diagrama_3.png',
        'D. CMS para videos': 'ChatGPT  Mastery_diagrama_4.png',
        'E. Motores de recomendación': 'ChatGPT  Mastery_diagrama_5.png',
        'F. NoSQL para el catálogo': 'ChatGPT  Mastery_diagrama_6.png',
        'G. CDNs para el contenido de video': 'ChatGPT  Mastery_diagrama_7.png',
        'H. Infraestructura en Kubernetes': 'ChatGPT  Mastery_diagrama_8.png',
    }
    
    for key, image_name in section_mapping.items():
        if key in section_text:
            image_path = os.path.join(png_dir, image_name)
            if os.path.exists(image_path):
                return image_path
    
    return None

def create_pdf():
    """Genera el documento PDF."""
    
    # Validar y leer archivo Markdown
    if not os.path.exists(MARKDOWN_FILE):
        logger.error(f"Archivo markdown no encontrado: {MARKDOWN_FILE}")
        return False
    
    try:
        with open(MARKDOWN_FILE, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except IOError as e:
        logger.error(f"Error al leer archivo {MARKDOWN_FILE}: {e}")
        return False
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2E4053'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#2C3E50'),
        spaceAfter=12,
        leading=16,
        fontName='Helvetica'
    )
    
    # Estilo para componentes (A, B, C, etc.)
    component_style = ParagraphStyle(
        'Component',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=HexColor('#1F618D'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Título principal
    story.append(Paragraph("Análisis de Arquitectura de Software", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Parsear secciones
    sections = parse_markdown_to_text(md_content)
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Detectar tipo de sección
        if section.startswith('# '):
            # Título principal
            text = section[2:].strip()
            story.append(Paragraph(text, subtitle_style))
            story.append(Spacer(1, 0.2*inch))
        elif section.startswith('## '):
            # Subtítulo
            text = section[3:].strip()
            story.append(Paragraph(text, subtitle_style))
            story.append(Spacer(1, 0.2*inch))
        elif section.startswith(('### ', '#### ')):
            # Sub-subtítulo o componente
            text = section.lstrip('#').strip()
            story.append(Paragraph(text, component_style))
            story.append(Spacer(1, 0.1*inch))
        elif section.startswith(('A. ', 'B. ', 'C. ', 'D. ', 'E. ', 'F. ', 'G. ', 'H. ')):
            # Componente de arquitectura
            story.append(Paragraph(section, component_style))
            story.append(Spacer(1, 0.1*inch))
        else:
            # Texto normal
            story.append(Paragraph(section, normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Buscar y agregar imagen correspondiente
        image_path = get_image_for_section(section, PNG_DIR)
        if image_path:
            try:
                img = Image(image_path, width=4*inch, height=2*inch)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                print(f"Error al cargar imagen {image_path}: {e}")
    
    # Construir PDF
    try:
        doc.build(story)
        print(f"✅ PDF generado exitosamente: {OUTPUT_PDF}")
        return True
    except Exception as e:
        print(f"❌ Error al generar PDF: {e}")
        return False

if __name__ == "__main__":
    create_pdf()
