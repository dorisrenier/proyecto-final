import streamlit as st
from pdf_summary_pro import PDFAnalyzer
import tempfile
import os

st.title("Analizador de PDFs Avanzado")
st.markdown("Carga uno o más archivos PDF para obtener un análisis completo incluyendo metadatos, introducción y palabras clave.")

analyzer = PDFAnalyzer()

uploaded_files = st.file_uploader(
    "Carga uno o más archivos PDF", 
    type="pdf", 
    accept_multiple_files=True,
    help="Selecciona archivos PDF para analizar su contenido, metadatos y extraer palabras clave"
)

if uploaded_files:
    with st.spinner('Analizando archivos PDF...'):
        temp_paths = []

        # Guardar archivos temporalmente
        for file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.read())
                temp_paths.append(tmp.name)

        # Analizar archivos
        results = analyzer.analyze_multiple_pdfs(temp_paths)

        st.success(f"Se analizaron {len(results)} archivo(s) exitosamente")

        # Mostrar resultados
        for i, res in enumerate(results):
            with st.expander(f"📑 {res['archivo']}", expanded=True):
                
                # Información básica en columnas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Páginas", res['num_paginas'])
                    st.metric("Tamaño (MB)", res['tamaño_mb'])
                
                with col2:
                    st.metric("Palabras", f"{res['num_palabras']:,}")
                    st.write(f"**Fecha:** {res['fecha_creacion']}")
                
                with col3:
                    st.write(f"**Autor:** {res['autor']}")
                    st.write(f"**Título:** {res['titulo']}")
                
                # Temas/Subjects
                if res['subjects'] and res['subjects'] != 'No disponible':
                    st.markdown(f"**Temas:** {res['subjects']}")
                
                st.markdown("---")
                
                # Sección de Introducción/Abstract (NUEVA FUNCIONALIDAD)
                st.subheader("Introducción/Abstract")
                if res['introduccion'] and res['introduccion'] != "No se pudo identificar una sección introductoria":
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50;'>{res['introduccion']}</div>", unsafe_allow_html=True)
                else:
                    st.info("No se pudo identificar una sección introductoria específica en el documento.")
                
                st.markdown("---")
                
                # Palabras Clave (NUEVA FUNCIONALIDAD)
                st.subheader("Palabras Clave")
                if res['palabras_clave']:
                    # Mostrar palabras clave como badges
                    keywords_html = ""
                    for keyword in res['palabras_clave']:
                        keywords_html += f"<span style='background-color: #e1f5fe; color: #01579b; padding: 4px 8px; margin: 2px; border-radius: 12px; display: inline-block; font-size: 0.9em;'>{keyword}</span> "
                    st.markdown(keywords_html, unsafe_allow_html=True)
                else:
                    st.info("No se pudieron extraer palabras clave del documento.")
                
                st.markdown("---")
                
                # Resumen tradicional
                st.subheader("Resumen Automático")
                st.markdown(f"<div style='background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800;'>{res['resumen']}</div>", unsafe_allow_html=True)
                
                # Separador entre documentos
                if i < len(results) - 1:
                    st.markdown("<hr style='margin: 2rem 0; border: 2px solid #e0e0e0;'>", unsafe_allow_html=True)

        # Limpieza de archivos temporales
        for path in temp_paths:
            try:
                os.remove(path)
            except:
                pass

else:
    # Instrucciones cuando no hay archivos cargados
    st.info("Selecciona uno o más archivos PDF para comenzar el análisis.")
    