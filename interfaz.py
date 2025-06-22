import streamlit as st
from pdf_summary import PDFAnalyzer
import tempfile
import os

st.title("PDF")

analyzer = PDFAnalyzer()

uploaded_files = st.file_uploader("Carga uno o más archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    temp_paths = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            temp_paths.append(tmp.name)

    results = analyzer.analyze_multiple_pdfs(temp_paths)

    for res in results:
        st.subheader(res['archivo'])
        st.markdown(f"**Autor:** {res['autor']}")
        st.markdown(f"**Fecha de creación:** {res['fecha_creacion']}")
        st.markdown(f"**Título:** {res['titulo']}")
        st.markdown(f"**Temas:** {res['subjects']}")
        st.markdown(f"**Resumen:** {res['resumen']}")
        st.markdown(f"**Número de páginas:** {res['num_paginas']}")
        st.markdown(f"**Tamaño del archivo (MB):** {res['tamaño_mb']}")
        st.markdown(f"**Cantidad de palabras:** {res['num_palabras']}")
        st.markdown("---")

    # Limpieza de archivos temporales
    for path in temp_paths:
        os.remove(path)
