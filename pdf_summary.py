import PyPDF2
import fitz 
from datetime import datetime
import re
import os
from typing import Dict, List

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

    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        if not text.strip():
            return "No se pudo extraer texto del documento"
        clean = self._clean_text(text)
        sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if len(s.strip()) > 20]
        if not sentences:
            return "Documento sin contenido textual significativo"
        summary = '. '.join(sentences[:max_sentences])
        return summary[:297] + "..." if len(summary) > 300 else summary

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
        summary = self.generate_summary(text)
        stats = self.get_document_stats(pdf_path)
        return {
            'archivo': file_name,
            'resumen': summary,
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
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        return text.strip()

