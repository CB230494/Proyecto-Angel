# =========================
# 📊 Diagrama MPGP – Exportador
# =========================
import io
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches

# ⚙️ Config
st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial")
st.caption("Genera PNG, PDF y PPTX sin dependencias externas (solo Pillow + python-pptx).")

# 🎨 Paleta / fuentes
BLUE = (31, 78, 121)
BORDER = (155, 187, 217)
LIGHTBLUE = (220, 235, 247)
LIGHTYELLOW = (255, 248, 225)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def load_font(size=20):
    try: return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception: return ImageFont.load_default()

FONT = load_font(22)
FONT_SMALL = load_font(18)
FONT_TITLE = load_font(28)

W, H = 2000, 1400
IMG_BG = (247, 250, 255)

# 🎛 Inputs
colA, colB = st.columns(2)
with colA:
    titulo_inicio = st.text_input("INICIO", "Planificación preventiva anual")
    bloque_1 = st.text_area("Bloque 1", "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)")
    bloque_2 = st.text_area("Bloque 2", "Apreciación situacional del territorio\n(Procedimiento 1.2)")
    bloque_3 = st.text_area("Bloque 3", "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)")
    decision_txt = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")

with colB:
    rama_si_1 = st.text_area("SÍ 1", "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)")
    rama_si_2 = st.text_area("SÍ 2", "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)")
    rama_si_3 = st.text_area("SÍ 3", "Planificación de programas policiales preventivos\n(Procedimiento 2.4)")
    rama_si_4 = st.text_area("SÍ 4", "Elaboración de órdenes de servicio para operativos")
    rama_si_5 = st.text_area("SÍ 5", "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local")
    rama_si_6 = st.text_area("SÍ 6", "Reporte de operativos (RAP, DATAPOL, informes)")
    rama_si_7 = st.text_area("SÍ 7", "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)")
    rama_si_8 = st.text_area("SÍ 8", "Retroalimentación a la planificación preventiva")

colC, colD = st.columns(2)
with colC:
    rama_no_1 = st.text_area("NO 1", "Patrullaje rutinario y vigilancia continua")
    rama_no_2 = st.text_area("NO 2", "Registro de factores menores en RAP")
    rama_no_3 = st.text_area("NO 3", "Integración al análisis situacional")
with colD:
    fin_txt = st.text_area("FIN", "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)")

# 🎨 Dibujo
def wrap_text(draw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    lines=[]
    for raw in text.split("\n"):
        words, line = raw.split(" "), ""
        for w in words:
            test=(line+" "+w).strip()
            if draw.textlength(test, font=font)<=max_w: line=test
            else:
                if line: lines.append(line)
                line=w
        if line: lines.append(line)
    return lines

def draw_centered_text(draw, text: str, box, font=FONT, fill=BLACK, leading=6):
    x0,y0,x1,y1=box
    lines=wrap_text(draw,text,font,x1-x0-20)
    line_h=font.size+leading
    total_h=len(lines)*line_h
    y=y0+(y1-y0-total_h)//2
    for ln in lines:
        w=draw.textlength(ln,font=font)
        x=x0+(x1-x0-w)//2
        draw.text((x,y),ln,font=font,fill=fill)
        y+=line_h

def rect_box(x,y,w=420,h=90): return [x-w//2,y-h//2,x+w//2,y+h//2]
def big_box(x,y,w,h): return [x-w//2,y-h//2,x+w//2,y+h//2]

def rounded_rect(d, box, fill=WHITE, outline=BLUE): d.rounded_rectangle(box, radius=20, fill=fill, outline=outline, width=3)
def oval(d, box, fill=LIGHTBLUE, outline=BLUE): d.ellipse(box, fill=fill, outline=outline, width=3)
def diamond(d, box, fill=LIGHTYELLOW, outline=BLUE):
    x0,y0,x1,y1=box; cx,cy=(x0+x1)//2,(y0+y1)//2
    pts=[(cx,y0),(x1,cy),(cx,y1),(x0,cy)]
    d.polygon(pts, fill=fill, outline=outline)

def arrow(d, p1, p2, color=BLUE, label=""):
    d.line([p1,p2], fill=color, width=4)
    import math
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0]); L=18
    a1=(p2[0]-L*math.cos(ang-0.4), p2[1]-L*math.sin(ang-0.4))
    a2=(p2[0]-L*math.cos(ang+0.4), p2[1]-L*math.sin(ang+0.4))
    d.polygon([p2,a1,a2], fill=color)
    if label:
        mx,my=(p1[0]+p2[0])//2,(p1[1]+p2[1])//2-14
        d.text((mx,my), label, font=FONT_SMALL, fill=color, anchor="mm")

def render_png() -> bytes:
    img=Image.new("RGB",(W,H),IMG_BG)
    d=ImageDraw.Draw(img)

    # Marco y título
    d.rectangle([20,20,W-20,H-20], outline=BORDER, width=3)
    d.text((W//2,50),"Modelo Preventivo de Gestión Policial – Función de Operacionales",
           font=FONT_TITLE, fill=BLUE, anchor="mm")

    # Columna central
    cx, vgap, y0 = W//2, 130, 120
    r_inicio=rect_box(cx,y0); oval(d,r_inicio); draw_centered_text(d,f"INICIO\n{titulo_inicio}",r_inicio)
    r1=rect_box(cx,y0+vgap); rounded_rect(d,r1); draw_centered_text(d,bloque_1,r1)
    r2=rect_box(cx,y0+vgap*2); rounded_rect(d,r2); draw_centered_text(d,bloque_2,r2)
    r3=rect_box(cx,y0+vgap*3); rounded_rect(d,r3); draw_centered_text(d,bloque_3,r3)
    r_dec=big_box(cx,y0+vgap*4,460,120); diamond(d,r_dec); draw_centered_text(d,decision_txt,r_dec)
    r_fin=big_box(cx,y0+vgap*8+60,480,120); oval(d,r_fin); draw_centered_text(d,f"FIN\n{fin_txt}",r_fin)

    # Rama SÍ (derecha)
    rx, rs = cx+520, []
    textos_si=[rama_si_1,rama_si_2,rama_si_3,rama_si_4,rama_si_5,rama_si_6,rama_si_7,rama_si_8]
    y=(r_dec[1]+r_dec[3])//2+80
    for i,t in enumerate(textos_si):
        rect_i=big_box(rx,y+i*110,500,110 if i==4 else 100)
        rounded_rect(d,rect_i); draw_centered_text(d,t,rect_i); rs.append(rect_i)

    # Rama NO (izquierda)
    lx, rn = cx-520, []
    textos_no=[rama_no_1,rama_no_2,rama_no_3]
    for i,t in enumerate(textos_no):
        rect_i=big_box(lx,(rs[0][1]+rs[0][3])//2+i*110,500,100)
        rounded_rect(d,rect_i); draw_centered_text(d,t,rect_i); rn.append(rect_i)

    # Helpers de puntos
    def c_bottom(r): return ((r[0]+r[2])//2, r[3])
    def c_top(r):    return ((r[0]+r[2])//2, r[1])
    def m_left(r):   return (r[0], (r[1]+r[3])//2)
    def m_right(r):  return (r[2], (r[1]+r[3])//2)

    # Flechas columna central
    arrow(d, c_bottom(r_inicio), c_top(r1))
    arrow(d, c_bottom(r1), c_top(r2))
    arrow(d, c_bottom(r2), c_top(r3))
    arrow(d, c_bottom(r3), c_top(r_dec))

    # 🚑 FIX: etiqueta como argumento nombrado (label=...) para no romper el color
    arrow(d, (m_right(r_dec)[0]+10, m_right(r_dec)[1]),
             (m_left(rs[0])[0]-10,  m_left(rs[0])[1]), label="Sí")
    arrow(d, (m_left(r_dec)[0]-10,  m_left(r_dec)[1]),
             (m_right(rn[0])[0]+10, m_right(rn[0])[1]), label="No")

    # Cadena SÍ
    for i in range(len(rs)-1): arrow(d, c_bottom(rs[i]), c_top(rs[i+1]))
    arrow(d, (m_left(rs[-1])[0]-2, m_left(rs[-1])[1]),
             (m_right(r2)[0]+2,    m_right(r2)[1]), label="Retroalimentación")

    # Cadena NO
    for i in range(len(rn)-1): arrow(d, c_bottom(rn[i]), c_top(rn[i+1]))
    arrow(d, (m_right(rn[-1])[0]+2, m_right(rn[-1])[1]),
             (m_left(r2)[0]-2,      m_left(r2)[1]))

    # Hacia FIN
    arrow(d, c_bottom(r2), c_top(r_fin))

    out=io.BytesIO(); img.save(out, format="PNG"); return out.getvalue()

# 📂 Exportadores
def make_pdf_from_png(png_bytes: bytes) -> bytes:
    A4W,A4H=3508,2480  # A4 landscape @300dpi
    page=Image.new("RGB",(A4W,A4H),(255,255,255))
    img=Image.open(io.BytesIO(png_bytes)).convert("RGB")
    scale=min((A4W-200)/img.width,(A4H-200)/img.height)
    img=img.resize((int(img.width*scale),int(img.height*scale)), Image.LANCZOS)
    x,y=(A4W-img.width)//2,(A4H-img.height)//2
    page.paste(img,(x,y))
    out=io.BytesIO(); page.save(out, format="PDF"); return out.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs=Presentation(); slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.25), Inches(0.25), width=Inches(9.5))
    out=io.BytesIO(); prs.save(out); return out.getvalue()

# 🚀 App
png_bytes = render_png()
pdf_bytes = make_pdf_from_png(png_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa (PNG)")
st.image(png_bytes, use_column_width=True)

st.download_button("⬇️ PNG", data=png_bytes, file_name="diagrama_modelo_preventivo.png", mime="image/png")
st.download_button("⬇️ PDF", data=pdf_bytes, file_name="diagrama_modelo_preventivo.pdf", mime="application/pdf")
st.download_button("⬇️ PPTX", data=pptx_bytes, file_name="diagrama_modelo_preventivo.pptx",
                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Editá los textos arriba y volvés a descargar los 3 formatos.")

