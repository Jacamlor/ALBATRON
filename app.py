import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Generador de Informes PDF desde TXT", layout="wide")

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

    def chapter_body(self, data):
        self.set_font("Arial", "", 10)
        col_widths = [30, 20, 30, 30, 20]  # Añadimos columna vacía
        for _, row in data.iterrows():
            self.cell(col_widths[0], 8, str(row["Código"]), border=1)
            self.cell(col_widths[1], 8, str(row["Talla"]), border=1)
            self.cell(col_widths[2], 8, str(row["Entregadas"]), border=1)
            self.cell(col_widths[3], 8, str(row["ClaveCriterioX"]), border=1)
            self.cell(col_widths[4], 8, "", border=1)  # columna vacía
            self.ln()

    def color_summary(self, data):
        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "Resumen por Talla:", ln=True)
        self.set_font("Arial", "", 10)
        for talla, total in data.groupby("Talla")["Entregadas"].sum().items():
            self.cell(0, 8, f"{talla}: {total}", ln=True)

        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "Resumen por Transfer:", ln=True)
        self.set_font("Arial", "", 10)
        for transfer, total in data.groupby("ClaveCriterioX")["Entregadas"].sum().items():
            self.cell(0, 8, f"Transfer {transfer}: {total}", ln=True)
        self.ln(5)

st.title("📄 Generador de Informes PDF desde TXT")

uploaded_file = st.file_uploader("Sube tu archivo TXT (tabulado)", type=["txt"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep='\\t', dtype=str)
        df = df.iloc[:, :6]
        df.columns = ["Código", "NºAlbarán", "Talla", "Entregadas", "Color", "ClaveCriterioX"]
        df["Entregadas"] = pd.to_numeric(df["Entregadas"], errors='coerce').fillna(0).astype(int)

        df_sorted = df.sort_values(by=["Color", "ClaveCriterioX"])

        pdf = ReportPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for albaran, albaran_group in df_sorted.groupby("NºAlbarán"):
            pdf.albaran_number = albaran
            pdf.add_page()
            for color, color_group in albaran_group.groupby("Color"):
                pdf.chapter_subtitle(color)
                if color_group["ClaveCriterioX"].nunique() > 1:
                    for transfer, transfer_group in color_group.groupby("ClaveCriterioX"):
                        pdf.chapter_body(transfer_group)
                else:
                    pdf.chapter_body(color_group)
                pdf.color_summary(color_group)

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

