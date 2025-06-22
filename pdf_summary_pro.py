import PyPDF2
import fitz 
from datetime import datetime
import re
import os
from typing import Dict, List
from collections import Counter

class PDFAnalyzer:
    def __init__(self):
        self.supported_formats = ['.pdf']
        
    def extract_metadata(self, pdf_path: str) -> Dict[str, str]:
        metadata = {
            'autor': 'No disponible',
            'fecha_creacion': 'No disponible',
            'subjects': 'No disponible',
            'titulo': 'No disponible'
        }
        try:
            doc = fitz.open(pdf_path)
            pdf_metadata = doc.metadata
            metadata['autor'] = pdf_metadata.get('author', metadata['autor'])
            metadata['fecha_creacion'] = self._format_date(pdf_metadata.get('creationDate', ''))
            metadata['subjects'] = pdf_metadata.get('subject', metadata['subjects'])
            metadata['titulo'] = pdf_metadata.get('title', metadata['titulo'])
            doc.close()
        except:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    meta = reader.metadata
                    metadata['autor'] = str(meta.get('/Author', metadata['autor']))
                    metadata['fecha_creacion'] = self._format_date(meta.get('/CreationDate', ''))
                    metadata['subjects'] = str(meta.get('/Subject', metadata['subjects']))
                    metadata['titulo'] = str(meta.get('/Title', metadata['titulo']))
            except:
                pass
        return metadata

    def extract_text(self, pdf_path: str) -> str:
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() or ""
            except:
                pass
        return text

    def extract_introduction_section(self, text: str) -> str:
        """Extrae la sección de introducción, abstract o resumen del documento"""
        if not text.strip():
            return "No se pudo extraer texto del documento"
        
        # Patrones para identificar secciones introductorias
        intro_patterns = [
            r'(?i)(?:^|\n)\s*(?:abstract|resumen|abstracto)\s*[\:\.\-]?\s*\n(.*?)(?=\n\s*(?:1\.|introducción|introduction|palabras clave|keywords|índice|contenido))',
            r'(?i)(?:^|\n)\s*(?:introducción|introduction)\s*[\:\.\-]?\s*\n(.*?)(?=\n\s*(?:2\.|metodología|methodology|desarrollo|objective|objetivos))',
            r'(?i)(?:^|\n)\s*(?:1\.\s*introducción|1\.\s*introduction)\s*[\:\.\-]?\s*(.*?)(?=\n\s*(?:2\.|metodología|methodology))',
            r'(?i)(?:^|\n)\s*(?:resumen ejecutivo|executive summary)\s*[\:\.\-]?\s*\n(.*?)(?=\n\s*(?:1\.|introducción|introduction))'
        ]
        
        for pattern in intro_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                intro_text = match.group(1).strip()
                if len(intro_text) > 100:  # Asegurar que sea una sección sustancial
                    # Limpiar y formatear el texto
                    intro_text = self._clean_text(intro_text)
                    # Limitar a 1000 caracteres
                    if len(intro_text) > 1000:
                        intro_text = intro_text[:1000] + "..."
                    return intro_text
        
        # Si no encuentra secciones específicas, toma los primeros párrafos
        clean_text = self._clean_text(text)
        paragraphs = [p.strip() for p in clean_text.split('\n') if len(p.strip()) > 50]
        
        if paragraphs:
            intro_text = ' '.join(paragraphs[:3])  # Primeros 3 párrafos
            if len(intro_text) > 1000:
                intro_text = intro_text[:1000] + "..."
            return intro_text
        
        return "No se pudo identificar una sección introductoria"

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrae las palabras clave más importantes del documento"""
        if not text.strip():
            return []
        
        # Palabras comunes en español e inglés que se deben filtrar
        stop_words = {
            'de', 'la', 'que', 'el', 'en', 'y', 'a', 'con', 'del', 'se', 'las', 'por', 'un', 'para', 
            'es', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque',
            'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'hay', 'donde',
            'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros',
            'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo',
            'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos',
            'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú',
            'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía',
            'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro',
            'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'esos', 'esas',
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on',
            'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we',
            'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
            'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into',
            'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
            'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two',
            'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any',
            'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'been', 'has', 'had', 'were'
        }
        
        # Limpiar texto y extraer palabras
        clean_text = self._clean_text(text.lower())
        words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', clean_text)
        
        # Filtrar palabras comunes y muy cortas
        filtered_words = [word for word in words if word not in stop_words and len(word) >= 3]
        
        # Contar frecuencias
        word_counts = Counter(filtered_words)
        
        # Obtener las palabras más frecuentes
        most_common = word_counts.most_common(max_keywords)
        
        return [word for word, count in most_common]

    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Genera un resumen básico del documento (mantiene funcionalidad original)"""
        if not text.strip():
            return "No se pudo extraer texto del documento"
        clean = self._clean_text(text)
        sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if len(s.strip()) > 20]
        if not sentences:
            return "Documento sin contenido textual significativo"
        summary = '. '.join(sentences[:max_sentences])
        return summary[:500] + "..." if len(summary) > 500 else summary

    def get_document_stats(self, pdf_path: str) -> Dict[str, any]:
        stats = {'num_paginas': 0, 'tamaño_archivo': 0, 'num_palabras': 0, 'num_caracteres': 0}
        try:
            stats['tamaño_archivo'] = os.path.getsize(pdf_path)
            doc = fitz.open(pdf_path)
            stats['num_paginas'] = len(doc)
            doc.close()
            text = self.extract_text(pdf_path)
            stats['num_caracteres'] = len(text)
            stats['num_palabras'] = len(text.split())
        except:
            pass
        return stats

    def analyze_pdf(self, pdf_path: str) -> Dict[str, any]:
        file_name = os.path.basename(pdf_path)
        metadata = self.extract_metadata(pdf_path)
        text = self.extract_text(pdf_path)
        
        # Nuevas funcionalidades
        introduction = self.extract_introduction_section(text)
        keywords = self.extract_keywords(text)
        
        # Funcionalidad original
        summary = self.generate_summary(text)
        stats = self.get_document_stats(pdf_path)
        
        return {
            'archivo': file_name,
            'resumen': summary,
            'introduccion': introduction,  # Nueva funcionalidad
            'palabras_clave': keywords,    # Nueva funcionalidad
            'autor': metadata['autor'],
            'fecha_creacion': metadata['fecha_creacion'],
            'subjects': metadata['subjects'],
            'titulo': metadata['titulo'],
            'num_paginas': stats['num_paginas'],
            'tamaño_mb': round(stats['tamaño_archivo'] / (1024 * 1024), 2),
            'num_palabras': stats['num_palabras']
        }

    def analyze_multiple_pdfs(self, pdf_paths: List[str]) -> List[Dict[str, any]]:
        results = []
        for path in pdf_paths:
            try:
                results.append(self.analyze_pdf(path))
            except Exception as e:
                results.append({
                    'archivo': os.path.basename(path),
                    'resumen': f"Error: {str(e)}",
                    'introduccion': f"Error: {str(e)}",
                    'palabras_clave': [],
                    'autor': 'Error',
                    'fecha_creacion': 'Error',
                    'subjects': 'Error',
                    'titulo': 'Error',
                    'num_paginas': 0,
                    'tamaño_mb': 0,
                    'num_palabras': 0
                })
        return results

    def validate_pdf(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages) > 0
        except:
            return False

    def _format_date(self, date_str: str) -> str:
        try:
            if date_str.startswith('D:'):
                date_part = date_str[2:10]
                if len(date_part) == 8:
                    return f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%d/%m/%Y')
            return date_str
        except:
            return date_str

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)áéíóúüñÁÉÍÓÚÜÑ]', '', text)
        return text.strip()