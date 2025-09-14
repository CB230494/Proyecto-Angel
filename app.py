# =========================
# Diagrama MPGP – Exportador (PNG, PDF, PPTX) sin Cairo/Graphviz
# =========================
import io
from dataclasses import dataclass
from typing import Tuple, List

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from pptx import Presentation
from pptx.util import Inches

st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial")
st.caption("Genera PNG, PDF y PPTX sin dependencias del sistema (no usa Cairo ni Graphviz).")

# ---------- Fuentes ----------
def load_font(size=20):
    # Usa una fuente común en la mayoría de entornos; si no está, usa la default de PIL
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

FONT = load_font(22)
FONT_SMALL = load_font(18)
FONT_TITLE = load_font(28)
BLACK = (0, 0, 0)
BLUE = (31, 78, 121)
BORDER = (155, 187, 217)
LIGHTBLUE = (220, 235, 247)
LIGHTYELLOW = (255, 248, 225)
WHITE = (255, 255, 255)

# ---------- Inputs ----------
colA, colB = st.columns(2)
with colA:
    titulo_inicio = st.text_input("INICIO", "Planificación preventiva anual")
    bloque_1 = st.text_area("Bloque 1", "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)", height=70)
    bloque_2 = st.text_area("Bloque 2", "Apreciación situacional del territorio\n(Procedimiento 1.2)", height=70)
    bloque_3 = st.text_area("Bloque 3", "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)", height=70)
    decision_txt = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")

with colB:
    rama_si_1 = st.text_area("SÍ 1", "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)", height=70)
    rama_si_2 = st.text_area("SÍ 2", "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)", height=70)
    rama_si_3 = st.text_area("SÍ 3", "Planificación de programas policiales preventivos\n(Procedimiento 2.4)", height=70)
    rama_si_4 = st.text_area("SÍ 4", "Elaboración de órdenes de servicio para operativos", height=70)
    rama_si_5 = st.text_area("SÍ 5", "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local", height=90)
    rama_si_6 = st.text_area("SÍ 6", "Reporte de operativos (RAP, DATAPOL, informes)", height=70)
    rama_si_7 = st.text_area("SÍ 7", "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)", height=70)
    rama_si_8 = st.text_area("SÍ 8", "Retroalimentación a la planificación preventiva", height=70)

colC, colD = st.columns(2)
with colC:
    rama_no_1 = st.text_area("NO 1", "Patrullaje rutinario y vigilancia continua", height=70)
    rama_no_2 = st.text_area("NO 2", "Registro de factores menores en RAP", height=70)
    rama_no_3 = st.text_area("NO 3", "Integración al análisis situacional", height=70)
with colD:
    fin_txt = st.text_area("FIN", "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)", height=70)

# ---------- Motor de dibujo (Pillow) ----------
W, H = 2000, 1400  # lienzo
IMG_BG = (247, 250, 255)

@dataclass
class Node:
    x: int
    y: int
    w: int
    h: int
    text: str
    shape: str = "rect"   # rect | oval | diamond
    fill: Tuple[int,int,int] = WHITE
    stroke: Tuple[int,int,int] = BLUE

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    lines = []
    for raw in text.split("\n"):
        words = raw.split(" ")
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if draw.textlength(test, font=font) <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
    return lines

def draw_centered_multiline(draw: ImageDraw.ImageDraw, text: str, box, font=FONT, fill=BLACK, leading=6):
    x0, y0, x1, y1 = box
    max_w = x1 - x0 - 20
    lines = wrap_text(draw, text, font, max_w)
    line_h = font.size + leading
    total_h = len(lines) * line_h
    y = y0 + (y1 - y0 - total_h) // 2
    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = x0 + (x1 - x0 - w) // 2
        draw.text((x, y), ln, font=font, fill=fill)
        y += line_h

def rounded_rect(draw: ImageDraw.ImageDraw, box, radius=20, fill=WHITE, outline=BLUE, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def oval(draw: ImageDraw.ImageDraw, box, fill=LIGHTBLUE, outline=BLUE, width=3):
    draw.ellipse(box, fill=fill, outline=outline, width=width)

def diamond(draw: ImageDraw.ImageDraw, box, fill=LIGHTYELLOW, outline=BLUE, width=3):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    pts = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.line(pts + [pts[0]], fill=outline, width=width)

def arrow(draw: ImageDraw.ImageDraw, p1, p2, color=BLUE, width=4, label:str=""):
    # línea
    draw.line([p1, p2], fill=color, width=width)
    # cabeza triangular
    import math
    ang = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    L = 18
    a1 = (p2[0] - L*math.cos(ang - 0.4), p2[1] - L*math.sin(ang - 0.4))
    a2 = (p2[0] - L*math.cos(ang + 0.4), p2[1] - L*math.sin(ang + 0.4))
    draw.polygon([p2, a1, a2], fill=color)
    if label:
        mx = (p1[0]+p2[0])//2
        my = (p1[1]+p2[1])//2 - 14
        draw.text((mx, my), label, font=FONT_SMALL, fill=color, anchor="mm")

def render_png() -> bytes:
    img = Image.new("RGB", (W, H), IMG_BG)
    d = ImageDraw.Draw(img)

    # Marco y título
    d.rectangle([20, 20, W-20, H-20], outline=BORDER, width=3)
    title = "Modelo Preventivo de Gestión Policial – Función de Operacionales"
    d.text((W//2, 50), title, font=FONT_TITLE, fill=BLUE, anchor="mm")

    # Geometría
    cx = W//2
    vgap = 130
    box = (420, 90)  # w, h
    y0 = 120

    # Nodos columna central
    def box_rect(x,y): return [x-box[0]//2, y-box[1]//2, x+box[0]//2, y+box[1]//2]
    def box_big(x,y,w,h): return [x-w//2, y-h//2, x+w//2, y+h//2]

    # Inicio (óvalo)
    r_inicio = box_rect(cx, y0)
    oval(d, r_inicio, fill=LIGHTBLUE, outline=BLUE)
    draw_centered_multiline(d, f"INICIO\n{titulo_inicio}", r_inicio, font=FONT)

    r1 = box_rect(cx, y0+vgap)
    rounded_rect(d, r1)
    draw_centered_multiline(d, bloque_1, r1)

    r2 = box_rect(cx, y0+vgap*2)
    rounded_rect(d, r2)
    draw_centered_multiline(d, bloque_2, r2)

    r3 = box_rect(cx, y0+vgap*3)
    rounded_rect(d, r3)
    draw_centered_multiline(d, bloque_3, r3)

    r_dec = box_big(cx, y0+vgap*4, 440, 110)
    diamond(d, r_dec, fill=LIGHTYELLOW, outline=BLUE)
    draw_centered_multiline(d, decision_txt, r_dec)

    r_fin = box_big(cx, y0+vgap*8+60, 460, 110)
    oval(d, r_fin, fill=LIGHTBLUE, outline=BLUE)
    draw_centered_multiline(d, f"FIN\n{fin_txt}", r_fin)

    # Rama SÍ (derecha)
    rx = cx + 500
    rs = []
    texts_si = [rama_si_1, rama_si_2, rama_si_3, rama_si_4, rama_si_5, rama_si_6, rama_si_7, rama_si_8]
    y = r_dec[1] + 80
    for i, t in enumerate(texts_si):
        h = 90 if i == 4 else 80
        rect = box_big(rx, y + i*105, 480, h)
        rounded_rect(d, rect)
        draw_centered_multiline(d, t, rect)
        rs.append(rect)

    # Rama NO (izquierda)
    lx = cx - 500
    rn = []
    texts_no = [rama_no_1, rama_no_2, rama_no_3]
    for i, t in enumerate(texts_no):
        rect = box_big(lx, rs[0][1] + i*105, 480, 80)
        rounded_rect(d, rect)
        draw_centered_multiline(d, t, rect)
        rn.append(rect)

    # Flechas columna central
    def center_bottom(r): return ((r[0]+r[2])//2, r[3])
    def center_top(r): return ((r[0]+r[2])//2, r[1])
    def mid_left(r): return (r[0], (r[1]+r[3])//2)
    def mid_right(r): return (r[2], (r[1]+r[3])//2)

    arrow(d, center_bottom(r_inicio), center_top(r1))
    arrow(d, center_bottom(r1), center_top(r2))
    arrow(d, center_bottom(r2), center_top(r3))
    arrow(d, center_bottom(r3), center_top(r_dec))

    # Decisión
    arrow(d, (mid_right(r_dec)[0]+10, mid_right(r_dec)[1]), (mid_left(rs[0])[0]-10, mid_left(rs[0])[1]), label="Sí")
    arrow(d, (mid_left(r_dec)[0]-10, mid_left(r_dec)[1]), (mid_right(rn[0])[0]+10, mid_right(rn[0])[1]), label="No")

    # Cadena SÍ
    for i in range(len(rs)-1):
        arrow(d, center_bottom(rs[i]), center_top(rs[i+1]))
    # Retroalimentación a análisis (rs[-1] → r2)
    arrow(d, (mid_left(rs[-1])[0]-2, mid_left(rs[-1])[1]), (mid_right(r2)[0]+2, mid_right(r2)[1]), label="Retroalimentación")

    # Cadena NO
    for i in range(len(rn)-1):
        arrow(d, center_bottom(rn[i]), center_top(rn[i+1]))
    # Vuelta al análisis
    arrow(d, (mid_right(rn[-1])[0]+2, mid_right(rn[-1])[1]), (mid_left(r2)[0]-2, mid_left(r2)[1]))

    # Hacia FIN (simplificado desde r2)
    arrow(d, center_bottom(r2), center_top(r_fin))

    # Bytes PNG
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

def build_pdf(png_bytes: bytes) -> bytes:
    # Coloca el PNG en un A4 apaisado manteniendo márgenes
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    page_w, page_h = landscape(A4)
    margin = 24
    img_buf = io.BytesIO(png_bytes)
    # dimensionado
    from PIL import Image as PILImage
    im = PILImage.open(img_buf)
    iw, ih = im.size
    scale = min((page_w-2*margin)/iw, (page_h-2*margin)/ih)
    w, h = iw*scale, ih*scale
    x = (page_w - w)/2
    y = (page_h - h)/2
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), x, y, width=w, height=h)
    c.showPage()
    c.save()
    return buf.getvalue()

def build_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation()
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    pic = slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.25), Inches(0.25), width=Inches(9.5))
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()

# ---------- Generar y mostrar ----------
from reportlab.lib.utils import ImageReader  # (después de las funciones)

png_bytes = render_png()
pdf_bytes = build_pdf(png_bytes)
pptx_bytes = build_pptx(png_bytes)

st.subheader("Vista previa (PNG)")
st.image(png_bytes, use_column_width=True)

st.download_button("⬇️ Descargar PNG", data=png_bytes, file_name="diagrama_modelo_preventivo.png", mime="image/png")
st.download_button("⬇️ Descargar PDF", data=pdf_bytes, file_name="diagrama_modelo_preventivo.pdf", mime="application/pdf")
st.download_button("⬇️ Descargar PPTX", data=pptx_bytes, file_name="diagrama_modelo_preventivo.pptx",
                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Podés editar los textos de cada bloque arriba y volver a descargar los 3 formatos.")


