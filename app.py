import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="ALBATRON", layout="wide")

class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"Nº Albarán: {self.albaran_number}", ln=True, align="L")
        self.ln(10)

    def chapter_subtitle(self, color, total_unidades):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(230, 230, 230)
        texto = f"Color: {color} - Total unidades: {total_unidades}"
        self.cell(0, 10, texto, ln=True, fill=True)
        self.ln(2)

    def chapter_body_with_right_summary(self, data):
        self.set_font("Arial", "", 10)
        col_widths = [25, 50, 15, 20, 25, 15]  # Código, Desc, Talla, Entregadas, Transfer, Vacía

        resumen_talla = data.groupby("Talla")["Entregadas"].sum().reset_index()
        resumen_transfer = data.groupby("Transfer")["Entregadas"].sum().reset_index()

        resumen_text = ["Resumen por Talla:"]
        for _, row in resumen_talla.iterrows():
            resumen_text.append(f"{row['Talla']}: {row['Entregadas']}")
        resumen_text.append("Resumen por Transfer:")
        for _, row in resumen_transfer.iterrows():
            resumen_text.append(f"Transfer {row['Transfer']}: {row['Entregadas']}")

        resumen_idx = 0

        transfer_groups = list(data.groupby("Transfer"))
        for i, (transfer, group) in enumerate(transfer_groups):
            if i > 0:
                self.ln(16)  # espacio equivalente a dos filas

            for _, row in group.iterrows():
                self.cell(col_widths[0], 8, str(row["Código"]), border=1)
                self.cell(col_widths[1], 8, str(row["Descripcion"]), border=1)
                self.cell(col_widths[2], 8, str(row["Talla"]), border=1)
                self.cell(col_widths[3], 8, str(row["Entregadas"]), border=1)
                self.cell(col_widths[4], 8, str(row["Transfer"]), border=1)
                self.cell(col_widths[5], 8, "", border=1)

                self.cell(10, 8, "", border=0)
                if resumen_idx < len(resumen_text):
                    if "Resumen" in resumen_text[resumen_idx]:
                        self.set_font("Arial", "B", 10)
                    else:
                        self.set_font("Arial", "", 10)
                    self.cell(0, 8, resumen_text[resumen_idx], ln=True)
                    resumen_idx += 1
                else:
                    self.ln()

st.title("📄 ALBATRON")

uploaded_file = st.file_uploader("Sube tu archivo TXT (tabulado)", type=["txt"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep="\t")

        # Renombrar columna si es necesario
        df = df.rename(columns={"ClaveCriterioX": "Transfer"})

        df["Entregadas"] = pd.to_numeric(df["Entregadas"], errors="coerce").fillna(0).astype(int)
        df_sorted = df.sort_values(by=["NºAlbarán", "Color", "Código", "Talla"])

        pdf = ReportPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for albaran, albaran_group in df_sorted.groupby("NºAlbarán"):
            pdf.albaran_number = albaran
            pdf.add_page()
            for color, color_group in albaran_group.groupby("Color"):
                total_unidades_color = color_group["Entregadas"].sum()
                pdf.chapter_subtitle(color, total_unidades_color)
                pdf.chapter_body_with_right_summary(color_group)

        pdf_output = pdf.output(dest="S").encode("latin1")
        pdf_buffer = BytesIO()
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)

        st.success("✅ PDF generado correctamente")
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_buffer.getvalue(),
            file_name="informe_por_albaran.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
