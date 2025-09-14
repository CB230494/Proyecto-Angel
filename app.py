# =========================
# 📊 Diagrama MPGP – Exportador (Pillow, flechas ordenadas)
# =========================
# - Sin matplotlib / reportlab / cairo
# - PNG, PDF y PPTX
# - Flechas con margen de seguridad (no pisan textos)
# - Rama "Sí" con espaciado uniforme y control
# =========================

import io, math, textwrap
from typing import List, Tuple
from dataclasses import dataclass

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches

# ---------- Config ----------
st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial")
st.caption("Flechas separadas de los textos, rótulos Sí/No visibles y espaciado uniforme.")

# ---------- Paleta ----------
BLUE = (31, 78, 121)
BORDER = (155, 187, 217)
LIGHTBLUE = (220, 235, 247)
LIGHTYELLOW = (255, 248, 225)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG = (247, 250, 255)

# ---------- Fuente ----------
def load_font(size=20):
    try: return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception: return ImageFont.load_default()

FONT = load_font(22)
FONT_SMALL = load_font(18)
FONT_TITLE = load_font(28)

# Lienzo
W, H = 2000, 1400
SAFE = 10        # margen para que las flechas no toquen cajas
HEAD = 18        # tamaño cabeza de flecha

# ---------- Entradas ----------
colA, colB = st.columns(2)
with colA:
    t_inicio = st.text_input("INICIO", "Planificación preventiva anual")
    b1 = st.text_area("Bloque 1", "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)")
    b2 = st.text_area("Bloque 2", "Apreciación situacional del territorio\n(Procedimiento 1.2)")
    b3 = st.text_area("Bloque 3", "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)")
    q_dec = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")
with colB:
    s1 = st.text_area("SÍ 1", "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)")
    s2 = st.text_area("SÍ 2", "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)")
    s3 = st.text_area("SÍ 3", "Planificación de programas policiales preventivos\n(Procedimiento 2.4)")
    s4 = st.text_area("SÍ 4", "Elaboración de órdenes de servicio para operativos")
    s5 = st.text_area("SÍ 5", "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local")
    s6 = st.text_area("SÍ 6", "Reporte de operativos (RAP, DATAPOL, informes)")
    s7 = st.text_area("SÍ 7", "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)")
    s8 = st.text_area("SÍ 8", "Retroalimentación a la planificación preventiva")
colC, colD = st.columns(2)
with colC:
    n1 = st.text_area("NO 1", "Patrullaje rutinario y vigilancia continua")
    n2 = st.text_area("NO 2", "Registro de factores menores en RAP")
    n3 = st.text_area("NO 3", "Integración al análisis situacional")
with colD:
    t_fin = st.text_area("FIN", "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)")

st.markdown("### ⚙️ Ajustes de layout")
c1, c2, c3 = st.columns(3)
with c1:
    start_offset = st.slider("Inicio rama SÍ (relativo a la decisión)", -240, 120, -80, 5)
with c2:
    step_user = st.slider("Espaciado vertical entre cuadros (px)", 90, 170, 120, 5)
with c3:
    compacto = st.toggle("Modo compacto (cuadros más bajos)", True)

# ---------- Helpers de texto/dibujo ----------
def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    lines = []
    for raw in text.split("\n"):
        words, line = raw.split(" "), ""
        for w in words:
            t = (line + " " + w).strip()
            if draw.textlength(t, font=font) <= max_w:
                line = t
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
    return lines

def draw_centered_multiline(draw: ImageDraw.ImageDraw, text: str, box, font=FONT, fill=BLACK, leading=6):
    x0, y0, x1, y1 = box
    max_w = x1 - x0 - 28
    lines = wrap_text(draw, text, font, max_w)
    line_h = font.size + leading
    total_h = len(lines) * line_h
    y = y0 + (y1 - y0 - total_h) // 2
    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = x0 + (x1 - x0 - w) // 2
        draw.text((x, y), ln, font=font, fill=fill)
        y += line_h

def rounded_rect(draw, box, radius=22, fill=WHITE, outline=BLUE, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def oval(draw, box, fill=LIGHTBLUE, outline=BLUE, width=3):
    draw.ellipse(box, fill=fill, outline=outline, width=width)

def diamond(draw, box, fill=LIGHTYELLOW, outline=BLUE, width=3):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    pts = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
    draw.polygon(pts, fill=fill, outline=outline)

def arrow(draw, p1, p2, color=BLUE, width=4, label:str="", label_dy:int=-18):
    # Línea con margen: p1->p2 ya vienen con SAFE aplicado
    draw.line([p1, p2], fill=color, width=width)
    ang = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    a1 = (p2[0] - HEAD*math.cos(ang - 0.4), p2[1] - HEAD*math.sin(ang - 0.4))
    a2 = (p2[0] - HEAD*math.cos(ang + 0.4), p2[1] - HEAD*math.sin(ang + 0.4))
    draw.polygon([p2, a1, a2], fill=color)
    if label:
        mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2 + label_dy
        draw.text((mx, my), label, font=FONT_SMALL, fill=color, anchor="mm")

def quad_curve_points(p0, p1, p2, steps=60):
    pts=[]
    for i in range(steps+1):
        t=i/steps
        x=(1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t**2*p2[0]
        y=(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t**2*p2[1]
        pts.append((x,y))
    return pts

def curved_arrow(draw, p1, p2, curve=0.35, color=BLUE, width=4, label:str=""):
    mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    L = max(1.0, math.hypot(dx, dy))
    nx, ny = -dy/L, dx/L
    ctrl = (mx + curve*L*0.6*nx, my + curve*L*0.6*ny)
    pts = quad_curve_points(p1, ctrl, p2, steps=70)
    draw.line(pts, fill=color, width=width)
    x1,y1=pts[-2]; x2,y2=pts[-1]
    ang=math.atan2(y2-y1, x2-x1)
    a1=(x2-HEAD*math.cos(ang-0.4), y2-HEAD*math.sin(ang-0.4))
    a2=(x2-HEAD*math.cos(ang+0.4), y2-HEAD*math.sin(ang+0.4))
    draw.polygon([(x2,y2),a1,a2], fill=color)
    if label:
        draw.text((mx, my-18), label, font=FONT_SMALL, fill=color, anchor="mm")

# ---------- Render ----------
def render_png() -> bytes:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, W-20, H-20], outline=BORDER, width=3)
    d.text((W//2, 50), "Modelo Preventivo de Gestión Policial – Función de Operacionales",
           font=FONT_TITLE, fill=BLUE, anchor="mm")

    # Columna central
    cx = W//2; vgap = 130; bw, bh = 460, 102; y0 = 120
    def rect_box(x,y,w=bw,h=bh): return [x-w//2, y-h//2, x+w//2, y+h//2]
    def big_box(x,y,w,h): return [x-w//2, y-h//2, x+w//2, y+h//2]

    r_inicio = rect_box(cx, y0);    oval(d, r_inicio); draw_centered_multiline(d, f"INICIO\n{t_inicio}", r_inicio)
    r1 = rect_box(cx, y0+vgap);     rounded_rect(d, r1); draw_centered_multiline(d, b1, r1)
    r2 = rect_box(cx, y0+vgap*2);   rounded_rect(d, r2); draw_centered_multiline(d, b2, r2)
    r3 = rect_box(cx, y0+vgap*3);   rounded_rect(d, r3); draw_centered_multiline(d, b3, r3)
    r_dec = big_box(cx, y0+vgap*4, 500, 122); diamond(d, r_dec); draw_centered_multiline(d, q_dec, r_dec)
    r_fin = big_box(cx, y0+vgap*8+60, 520, 122); oval(d, r_fin); draw_centered_multiline(d, f"FIN\n{t_fin}", r_fin)

    # Puntos de conexión con margen SAFE
    def c_bottom(r): return ((r[0]+r[2])//2, r[3]+SAFE)
    def c_top(r):    return ((r[0]+r[2])//2, r[1]-SAFE)
    def m_left(r):   return (r[0]-SAFE, (r[1]+r[3])//2)
    def m_right(r):  return (r[2]+SAFE, (r[1]+r[3])//2)

    # Flechas columna central (con margen)
    arrow(d, c_bottom(r_inicio), c_top(r1))
    arrow(d, c_bottom(r1), c_top(r2))
    arrow(d, c_bottom(r2), c_top(r3))
    arrow(d, c_bottom(r3), c_top(r_dec))
    arrow(d, c_bottom(r2), c_top(r_fin))  # cierre a FIN (sin pasar por el centro del rombo)

    # Rama SÍ
    rx = cx + 560
    n_items = 8
    start_y = (r_dec[1]+r_dec[3])//2 + start_offset
    safe_bottom = r_fin[1] - 160
    max_step = max(90, (safe_bottom - start_y) / max(1, (n_items-1)))
    step = min(step_user, max_step)

    h_si = 86 if compacto else 100
    h_si5 = h_si + (0 if compacto else 10)

    Ys = [start_y + i*step for i in range(n_items)]
    texts_si = [s1, s2, s3, s4, s5, s6, s7, s8]
    rs = []
    for i, (txt, y) in enumerate(zip(texts_si, Ys)):
        h = h_si5 if i == 4 else h_si
        rect_i = big_box(rx, int(y), 520, h)
        rounded_rect(d, rect_i); draw_centered_multiline(d, txt, rect_i); rs.append(rect_i)

    # Rama NO (alineada con los 3 primeros SÍ)
    lx = cx - 560
    texts_no = [n1, n2, n3]
    rn = []
    for i, txt in enumerate(texts_no):
        rect_i = big_box(lx, int(Ys[i]), 520, h_si)
        rounded_rect(d, rect_i); draw_centered_multiline(d, txt, rect_i); rn.append(rect_i)

    # Decisión → ramas (líneas más cortas y rótulos fuera)
    arrow(d, m_right(r_dec), (rs[0][0]-SAFE, (rs[0][1]+rs[0][3])//2), label="Sí", label_dy=-24)
    arrow(d, m_left(r_dec),  (rn[0][2]+SAFE, (rn[0][1]+rn[0][3])//2), label="No", label_dy=-24)

    # Cadena SÍ (de borde inferior a borde superior con SAFE)
    for i in range(len(rs)-1):
        p1 = ((rs[i][0]+rs[i][2])//2, rs[i][3]+SAFE)
        p2 = ((rs[i+1][0]+rs[i+1][2])//2, rs[i+1][1]-SAFE)
        arrow(d, p1, p2)

    # Cadena NO
    for i in range(len(rn)-1):
        p1 = ((rn[i][0]+rn[i][2])//2, rn[i][3]+SAFE)
        p2 = ((rn[i+1][0]+rn[i+1][2])//2, rn[i+1][1]-SAFE)
        arrow(d, p1, p2)

    # Retroalimentación (curva externa y alta para no tocar textos)
    curved_arrow(
        d,
        (rs[-1][0]-SAFE, (rs[-1][1]+rs[-1][3])//2),
        (r2[2]+SAFE,     (r2[1]+r2[3])//2),
        curve=-0.45, color=BLUE, label="Retroalimentación"
    )

    out = io.BytesIO(); img.save(out, format="PNG"); return out.getvalue()

# ---------- Exportadores ----------
def make_pdf_from_png(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO(); img.save(out, format="PDF"); return out.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation(); slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.25), Inches(0.25), width=Inches(9.6))
    out = io.BytesIO(); prs.save(out); return out.getvalue()

# ---------- Render & Descargas ----------
png_bytes = render_png()
pdf_bytes = make_pdf_from_png(png_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, use_column_width=True)
c1, c2, c3 = st.columns(3)
with c1: st.download_button("⬇️ PNG", png_bytes, "diagrama_modelo_preventivo.png", "image/png")
with c2: st.download_button("⬇️ PDF", pdf_bytes, "diagrama_modelo_preventivo.pdf", "application/pdf")
with c3: st.download_button("⬇️ PPTX", pptx_bytes, "diagrama_modelo_preventivo.pptx",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Si necesitás aún más aire, subí el **espaciado** o hacé más negativo el **inicio de la rama SÍ**.")
