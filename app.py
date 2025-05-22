import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Generador de Informes PDF", layout="wide")

class ReportPDF(FPDF):
    def header(self):
        if hasattr(self, 'albaran_number'):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, f"Nº Albarán: {self.albaran_number}", ln=True, align="C")
            self.ln(5)

    def chapter_subtitle(self, color):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, f"Color: {color}", ln=True, fill=True)
        self.ln(2)

    def chapter_body_with_right_summary(self, data):
        self.set_font("Arial", "", 10)
        col_widths = [30, 20, 30, 30]
        headers = ["Código", "Talla", "Producir", "Transfer"]

        resumen_talla = data.groupby("Talla")["Entregadas"].sum().reset_index()
        resumen_transfer = data.groupby("ClaveCriterioX")["Entregadas"].sum().reset_index()

        resumen_text = ["Resumen por Talla:"]
        for _, row in resumen_talla.iterrows():
            resumen_text.append(f"{row['Talla']}: {row['Entregadas']}")
        resumen_text.append("Resumen por Transfer:")
        for _, row in resumen_transfer.iterrows():
            resumen_text.append(f"Transfer {row['ClaveCriterioX']}: {row['Entregadas']}")

        max_lines = max(len(data), len(resumen_text))

        for i in range(max_lines):
            if i < len(data):
                row = data.iloc[i]
                self.cell(col_widths[0], 8, str(row["Código"]), border=1)
                self.cell(col_widths[1], 8, str(row["Talla"]), border=1)
                self.cell(col_widths[2], 8, str(row["Entregadas"]), border=1)
                self.cell(col_widths[3], 8, str(row["ClaveCriterioX"]), border=1)
            else:
                for w in col_widths:
                    self.cell(w, 8, "", border=0)

            self.cell(10, 8, "", border=0)
            if i < len(resumen_text):
                if "Resumen" in resumen_text[i]:
                    self.set_font("Arial", "B", 10)
                else:
                    self.set_font("Arial", "", 10)
                self.cell(0, 8, resumen_text[i], ln=True)
            else:
                self.ln()

st.title("📄 Generador de Informes PDF por Albarán y Color")

uploaded_file = st.file_uploader("Sube tu archivo TXT (separado por tabulaciones)", type=["txt"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep='\t', dtype=str)
        df = df.iloc[:, :6]  # Mantener solo las columnas necesarias
        df.columns = ["Código", "NºAlbarán", "Talla", "Entregadas", "Color", "ClaveCriterioX"]

        # Convertir numéricos
        df["Entregadas"] = pd.to_numeric(df["Entregadas"], errors='coerce').fillna(0).astype(int)

        df_sorted = df.sort_values(by=["Color", "ClaveCriterioX"])

        pdf = ReportPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for albaran, albaran_group in df_sorted.groupby("NºAlbarán"):
            pdf.albaran_number = albaran
            pdf.add_page()
            for color, color_group in albaran_group.groupby("Color"):
                pdf.chapter_subtitle(color)
                pdf.chapter_body_with_right_summary(color_group)

        pdf_data = pdf.output(dest='S').encode('latin1')
        pdf_buffer = BytesIO(pdf_data)

        st.success("✅ PDF generado correctamente")
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_buffer,
            file_name="informe_por_albaran.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
