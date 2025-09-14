# =========================
# Diagrama MPGP – Exportador (PNG, PDF, PPTX)
# =========================
import io
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
import drawsvg as draw
from cairosvg import svg2png, svg2pdf
from pptx import Presentation
from pptx.util import Inches
from PIL import Image

st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")

# --------- Parámetros del diagrama (editable por el usuario) ----------
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial")
st.caption("Genera PNG, PDF y PPTX con un solo clic (sin dependencias del sistema).")

colA, colB = st.columns(2)
with colA:
    titulo_inicio = st.text_input("Título de INICIO", "Planificación preventiva anual")
    bloque_1 = st.text_area(
        "Bloque 1",
        "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)",
        height=70,
    )
    bloque_2 = st.text_area(
        "Bloque 2",
        "Apreciación situacional del territorio\n(Procedimiento 1.2)",
        height=70,
    )
    bloque_3 = st.text_area(
        "Bloque 3",
        "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",
        height=70,
    )
    decision_txt = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")

with colB:
    rama_si_1 = st.text_area(
        "Rama SÍ – 1",
        "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
        height=70,
    )
    rama_si_2 = st.text_area(
        "Rama SÍ – 2",
        "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)",
        height=70,
    )
    rama_si_3 = st.text_area(
        "Rama SÍ – 3",
        "Planificación de programas policiales preventivos\n(Procedimiento 2.4)",
        height=70,
    )
    rama_si_4 = st.text_area(
        "Rama SÍ – 4",
        "Elaboración de órdenes de servicio para operativos",
        height=70,
    )
    rama_si_5 = st.text_area(
        "Rama SÍ – 5",
        "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
        height=90,
    )
    rama_si_6 = st.text_area(
        "Rama SÍ – 6",
        "Reporte de operativos (RAP, DATAPOL, informes)",
        height=70,
    )
    rama_si_7 = st.text_area(
        "Rama SÍ – 7",
        "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
        height=70,
    )
    rama_si_8 = st.text_area(
        "Rama SÍ – 8",
        "Retroalimentación a la planificación preventiva",
        height=70,
    )

colC, colD = st.columns(2)
with colC:
    rama_no_1 = st.text_area(
        "Rama NO – 1",
        "Patrullaje rutinario y vigilancia continua",
        height=70,
    )
    rama_no_2 = st.text_area(
        "Rama NO – 2",
        "Registro de factores menores en RAP",
        height=70,
    )
    rama_no_3 = st.text_area(
        "Rama NO – 3",
        "Integración al análisis situacional",
        height=70,
    )
with colD:
    fin_txt = st.text_area(
        "FIN",
        "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)",
        height=70,
    )

# ---------- Helpers de dibujo ----------
@dataclass
class Node:
    x: float
    y: float
    w: float
    h: float
    text: str
    shape: str = "rect"  # rect | oval | diamond
    fill: str = "#FFFFFF"
    stroke: str = "#1F4E79"

def multiline_text(d: draw.Drawing, txt: str, x: float, y: float, max_w: float, line_h: float = 16, fs: int = 13):
    """Dibuja texto centrado por líneas (split en \n)."""
    lines = [t.strip() for t in txt.split("\n")]
    offset = -(len(lines)-1) * line_h / 2
    for i, ln in enumerate(lines):
        d.append(draw.Text(ln, fs, x, y + offset + i*line_h, center=True, fill="#000000", font_family="Arial"))

def draw_node(d: draw.Drawing, n: Node):
    if n.shape == "rect":
        d.append(draw.Rectangle(n.x - n.w/2, n.y - n.h/2, n.w, n.h, rx=10, ry=10, fill=n.fill, stroke=n.stroke, stroke_width=2))
    elif n.shape == "oval":
        d.append(draw.Ellipse(n.x, n.y, n.w/2, n.h/2, fill=n.fill, stroke=n.stroke, stroke_width=2))
    elif n.shape == "diamond":
        pts = [
            (n.x, n.y - n.h/2),
            (n.x + n.w/2, n.y),
            (n.x, n.y + n.h/2),
            (n.x - n.w/2, n.y),
        ]
        d.append(draw.Lines(*[c for p in pts for c in p], close=True, fill=n.fill, stroke=n.stroke, stroke_width=2))
    multiline_text(d, n.text, n.x, n.y, n.w-12)

def arrow(d: draw.Drawing, x1: float, y1: float, x2: float, y2: float, label: str = "", color: str = "#1F4E79"):
    d.append(draw.Line(x1, y1, x2, y2, stroke=color, stroke_width=2, marker_end=draw.Marker(-1, -3, -1, 3, scale=2)))
    if label:
        d.append(draw.Text(label, 12, (x1+x2)/2, (y1+y2)/2 - 6, center=True, fill=color, font_family="Arial", font_weight="bold"))

def build_svg() -> bytes:
    W, H = 1400, 1050
    d = draw.Drawing(W, H, origin=(0, 0))

    # Fondo
    d.append(draw.Rectangle(0, 0, W, H, fill="#F7FAFF"))

    # Coordenadas guía
    cx = W/2
    top_y = 110
    v_gap = 90
    box_w, box_h = 360, 70

    # Nodos columna central
    n_inicio = Node(cx, top_y, 360, 70, f"INICIO\n{titulo_inicio}", "oval", "#DCEBF7")
    n1 = Node(cx, top_y+1*v_gap, box_w, box_h, bloque_1)
    n2 = Node(cx, top_y+2*v_gap, box_w, box_h, bloque_2)
    n3 = Node(cx, top_y+3*v_gap, box_w, box_h, bloque_3)
    n_dec = Node(cx, top_y+4*v_gap, 360, 80, decision_txt, "diamond", "#FFF8E1")
    n_fin = Node(cx, top_y+8.7*v_gap, 380, 80, f"FIN\n{fin_txt}", "oval", "#DCEBF7")

    # Rama SÍ (derecha)
    rx = cx + 400
    rs_gap = 80
    rs_w, rs_h = 380, 68
    rs1 = Node(rx, n_dec.y + 0.6*v_gap, rs_w, rs_h, rama_si_1)
    rs2 = Node(rx, rs1.y + rs_gap, rs_w, rs_h, rama_si_2)
    rs3 = Node(rx, rs2.y + rs_gap, rs_w, rs_h, rama_si_3)
    rs4 = Node(rx, rs3.y + rs_gap, rs_w, rs_h, rama_si_4)
    rs5 = Node(rx, rs4.y + rs_gap, rs_w, rs_h+20, rama_si_5)
    rs6 = Node(rx, rs5.y + rs_gap+10, rs_w, rs_h, rama_si_6)
    rs7 = Node(rx, rs6.y + rs_gap, rs_w, rs_h, rama_si_7)
    rs8 = Node(rx, rs7.y + rs_gap, rs_w, rs_h, rama_si_8)

    # Rama NO (izquierda)
    lx = cx - 400
    rn1 = Node(lx, rs1.y, rs_w, rs_h, rama_no_1)
    rn2 = Node(lx, rs2.y, rs_w, rs_h, rama_no_2)
    rn3 = Node(lx, rs3.y, rs_w, rs_h, rama_no_3)

    # Dibujo
    for n in [n_inicio, n1, n2, n3, n_dec, n_fin, rs1, rs2, rs3, rs4, rs5, rs6, rs7, rs8, rn1, rn2, rn3]:
        draw_node(d, n)

    # Flechas columna central
    arrow(d, n_inicio.x, n_inicio.y + n_inicio.h/2, n1.x, n1.y - n1.h/2)
    arrow(d, n1.x, n1.y + n1.h/2, n2.x, n2.y - n2.h/2)
    arrow(d, n2.x, n2.y + n2.h/2, n3.x, n3.y - n3.h/2)
    arrow(d, n3.x, n3.y + n3.h/2, n_dec.x, n_dec.y - n_dec.h/2)

    # Ramas desde la decisión
    arrow(d, n_dec.x + 180, n_dec.y, rs1.x - rs1.w/2, rs1.y, "Sí")
    arrow(d, n_dec.x - 180, n_dec.y, rn1.x + rn1.w/2, rn1.y, "No")

    # Cadena SÍ
    arrow(d, rs1.x, rs1.y + rs1.h/2, rs2.x, rs2.y - rs2.h/2)
    arrow(d, rs2.x, rs2.y + rs2.h/2, rs3.x, rs3.y - rs3.h/2)
    arrow(d, rs3.x, rs3.y + rs3.h/2, rs4.x, rs4.y - rs4.h/2)
    arrow(d, rs4.x, rs4.y + rs4.h/2, rs5.x, rs5.y - rs5.h/2)
    arrow(d, rs5.x, rs5.y + rs5.h/2, rs6.x, rs6.y - rs6.h/2)
    arrow(d, rs6.x, rs6.y + rs6.h/2, rs7.x, rs7.y - rs7.h/2)
    arrow(d, rs7.x, rs7.y + rs7.h/2, rs8.x, rs8.y - rs8.h/2)
    # Retroalimentación a análisis situacional
    arrow(d, rs8.x - rs8.w/2, rs8.y, n2.x + box_w/2, n2.y, "Retroalimentación")

    # Cadena NO
    arrow(d, rn1.x, rn1.y + rn1.h/2, rn2.x, rn2.y - rn2.h/2)
    arrow(d, rn2.x, rn2.y + rn2.h/2, rn3.x, rn3.y - rn3.h/2)
    # Vuelve al análisis
    arrow(d, rn3.x + rn3.w/2, rn3.y, n2.x - box_w/2, n2.y, "")

    # Cierre a FIN (desde análisis situacional global)
    arrow(d, n2.x, n2.y + n2.h/2, n_fin.x, n_fin.y - n_fin.h/2)

    # Marco/título
    d.append(draw.Text("Modelo Preventivo de Gestión Policial – Función de Operacionales",
                       18, W/2, 35, center=True, fill="#1F4E79", font_family="Arial", font_weight="bold"))
    d.append(draw.Rectangle(20, 20, W-40, H-40, fill="none", stroke="#9BBBD9", stroke_width=2))
    return d.as_svg().encode("utf-8")

def make_png(svg_bytes: bytes) -> bytes:
    return svg2png(bytestring=svg_bytes, output_width=1400, output_height=1050)

def make_pdf(svg_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    svg2pdf(bytestring=svg_bytes, write_to=buf)
    return buf.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation()
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    # ancho/alto estándar 10" x 7.5"
    img = Image.open(io.BytesIO(png_bytes))
    tmp = io.BytesIO(png_bytes)
    pic = slide.shapes.add_picture(tmp, Inches(0.25), Inches(0.25),
                                   width=Inches(9.5))  # margen visual
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()

# --------- Generación ----------
svg_bytes = build_svg()
png_bytes = make_png(svg_bytes)
pdf_bytes = make_pdf(svg_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, caption="Diagrama (vista previa PNG)", use_column_width=True)

# --------- Descargas ----------
st.download_button("⬇️ Descargar PNG", data=png_bytes, file_name="diagrama_modelo_preventivo.png", mime="image/png")
st.download_button("⬇️ Descargar PDF", data=pdf_bytes, file_name="diagrama_modelo_preventivo.pdf", mime="application/pdf")
st.download_button("⬇️ Descargar PPTX", data=pptx_bytes, file_name="diagrama_modelo_preventivo.pptx",
                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Tip: podés editar los textos de cada bloque arriba y volver a descargar los 3 formatos.")

