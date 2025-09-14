# =========================
# 📊 Diagrama MPGP – Exportador (Pillow, layout estable y claro)
# =========================
# - PNG, PDF y PPTX
# - Conectores limpios (sin cruces)
# - Rótulos "Sí/No" pegados a su flecha y hacia afuera
# - Rama SÍ autoajustada para que SIEMPRE quepa
# - SÍ 5 redimensionable (alto) + ancho de toda la rama SÍ configurable
# =========================

import io, math
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from pptx import Presentation
from pptx.util import Inches

# ---------- Config / Estilos ----------
st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Modelo Preventivo de Gestión Policial – Función de Operacionales")
st.caption("Flechas ordenadas, rótulos bien posicionados, retroalimentación externa y SÍ 5 ajustable. Exporta PNG / PDF / PPTX.")

BLUE=(31,78,121); BORDER=(155,187,217); LIGHTBLUE=(220,235,247); LIGHTYELLOW=(255,248,225)
WHITE=(255,255,255); BLACK=(0,0,0); BG=(247,250,255)
W,H=2000,1400                 # Lienzo
SAFE=16                       # Separación mínima flecha-borde
ARROW_HEAD=18                 # Tamaño de la cabeza de flecha
HEAD_CLEAR=SAFE+ARROW_HEAD+6  # Punto de entrada/salida alejado del texto

def font(size:int):
    try: return ImageFont.truetype("DejaVuSans.ttf", size)
    except: return ImageFont.load_default()
FONT=font(22); FONT_SMALL=font(18); FONT_TITLE=font(28)

# ---------- Entradas de contenido ----------
cA,cB = st.columns(2)
with cA:
    t_inicio=st.text_input("INICIO","Planificación preventiva anual")
    b1=st.text_area("Bloque 1","Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)")
    b2=st.text_area("Bloque 2","Apreciación situacional del territorio\n(Procedimiento 1.2)")
    b3=st.text_area("Bloque 3","Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)")
    q_dec=st.text_input("Decisión","¿Se identifican riesgos prioritarios?")
with cB:
    s1=st.text_area("SÍ 1","Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)")
    s2=st.text_area("SÍ 2","Construcción de líneas de acción preventivas\n(Procedimiento 2.3)")
    s3=st.text_area("SÍ 3","Planificación de programas policiales preventivos\n(Procedimiento 2.4)")
    s4=st.text_area("SÍ 4","Elaboración de órdenes de servicio para operativos")
    s5=st.text_area("SÍ 5","Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local")
    s6=st.text_area("SÍ 6","Reporte de operativos (RAP, DATAPOL, informes)")
    s7=st.text_area("SÍ 7","Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)")
    s8=st.text_area("SÍ 8","Retroalimentación a la planificación preventiva")
cC,cD = st.columns(2)
with cC:
    n1=st.text_area("NO 1","Patrullaje rutinario y vigilancia continua")
    n2=st.text_area("NO 2","Registro de factores menores en RAP")
    n3=st.text_area("NO 3","Integración al análisis situacional")
with cD:
    t_fin=st.text_area("FIN","Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)")

# ---------- Ajustes de layout ----------
st.markdown("### ⚙️ Ajustes de layout")
g1,g2,g3 = st.columns(3)
with g1:
    start_offset=st.slider("Inicio rama SÍ (relativo al rombo)", -260, 120, -90, 5)
with g2:
    step_user=st.slider("Espaciado vertical deseado (px)", 120, 220, 150, 5)
with g3:
    compacto=st.toggle("Modo compacto", True)
g4,g5,g6 = st.columns(3)
with g4:
    altura_si5 = st.slider("Altura cuadro SÍ 5 (px)", 110, 260, 170, 5)
with g5:
    ancho_si   = st.slider("Ancho cuadros rama SÍ (px)", 520, 680, 580, 10)
with g6:
    retro_rail = st.slider("Separación lateral retroalimentación (px)", 120, 260, 180, 10)

# ---------- Utilidades de dibujo ----------
def wrap_text(d: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    out=[]
    for raw in text.split("\n"):
        words=raw.split(" "); line=""
        for w in words:
            t=(line+" "+w).strip()
            if d.textlength(t,font=font)<=max_w: line=t
            else:
                if line: out.append(line)
                line=w
        if line: out.append(line)
    return out

def draw_centered(d: ImageDraw.ImageDraw, text: str, box, font=FONT, fill=BLACK, leading=6):
    x0,y0,x1,y1=box; max_w=x1-x0-30
    lines=wrap_text(d,text,font,max_w); lh=font.size+leading; total=len(lines)*lh
    y=y0+(y1-y0-total)//2
    for ln in lines:
        w=d.textlength(ln,font=font); x=x0+(x1-x0-w)//2
        d.text((x,y),ln,font=font,fill=fill); y+=lh

def rrect(d, box, radius=22, fill=WHITE, outline=BLUE, width=3): d.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)
def oval(d, box, fill=LIGHTBLUE, outline=BLUE, width=3): d.ellipse(box,fill=fill,outline=outline,width=width)
def diamond(d, box, fill=LIGHTYELLOW, outline=BLUE, width=3):
    x0,y0,x1,y1=box; cx=(x0+x1)//2; cy=(y0+y1)//2
    pts=[(cx,y0),(x1,cy),(cx,y1),(x0,cy)]; d.polygon(pts,fill=fill,outline=outline)

def arrow(d: ImageDraw.ImageDraw, p1: Tuple[int,int], p2: Tuple[int,int], color=BLUE, width=4):
    d.line([p1,p2], fill=color, width=width)
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    a1=(p2[0]-ARROW_HEAD*math.cos(ang-0.4), p2[1]-ARROW_HEAD*math.sin(ang-0.4))
    a2=(p2[0]-ARROW_HEAD*math.cos(ang+0.4), p2[1]-ARROW_HEAD*math.sin(ang+0.4))
    d.polygon([p2,a1,a2], fill=color)

def arrow_down(d: ImageDraw.ImageDraw, p1: Tuple[int,int], p2: Tuple[int,int], **kw):
    """Flecha vertical; si p2 está arriba de p1, invierte para que apunte hacia abajo."""
    if p2[1] < p1[1]:
        p1, p2 = p2, p1
    arrow(d, p1, p2, **kw)

def label_near_segment_outward(
    d: ImageDraw.ImageDraw, p1, p2, text: str, page_center_x: int, offset: int = 36
):
    """Rótulo al lado del segmento (normal), siempre hacia afuera del centro horizontal."""
    mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    L = max(1.0, math.hypot(dx, dy))
    nx, ny = -dy/L, dx/L  # normal
    cand1 = (mx + nx*offset, my + ny*offset)
    cand2 = (mx - nx*offset, my - ny*offset)
    chosen = cand1 if abs(cand1[0]-page_center_x) > abs(cand2[0]-page_center_x) else cand2
    tx, ty = chosen
    w = d.textlength(text, font=FONT_SMALL); h = FONT_SMALL.size; pad=6
    d.rounded_rectangle([tx-w/2-pad, ty-h/2-pad, tx+w/2+pad, ty+h/2+pad],
                        radius=8, fill=WHITE, outline=None)
    d.text((tx, ty), text, font=FONT_SMALL, fill=BLUE, anchor="mm")

def poly_arrow(d: ImageDraw.ImageDraw, pts, color=BLUE, width=4):
    for i in range(len(pts)-2):
        d.line([pts[i], pts[i+1]], fill=color, width=width)
    arrow(d, pts[-2], pts[-1], color=color, width=width)

# ---------- Render principal ----------
def render_png() -> bytes:
    img=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(img)

    # Marco y título
    d.rectangle([20,20,W-20,H-20],outline=BORDER,width=3)
    d.text((W//2,50),"Modelo Preventivo de Gestión Policial – Función de Operacionales",
           font=FONT_TITLE,fill=BLUE,anchor="mm")

    # Columna central
    cx=W//2; vgap=130; bw,bh=480,104; y0=120
    def box(x,y,w=bw,h=bh): return [x-w//2, y-h//2, x+w//2, y+h//2]
    def big(x,y,w,h):       return [x-w//2, y-h//2, x+w//2, y+h//2]

    r_inicio=box(cx,y0);        oval(d,r_inicio); draw_centered(d,f"INICIO\n{t_inicio}",r_inicio)
    r1=box(cx,y0+vgap);         rrect(d,r1); draw_centered(d,b1,r1)
    r2=box(cx,y0+vgap*2);       rrect(d,r2); draw_centered(d,b2,r2)
    r3=box(cx,y0+vgap*3);       rrect(d,r3); draw_centered(d,b3,r3)
    r_dec=big(cx,y0+vgap*4,520,124); diamond(d,r_dec); draw_centered(d,q_dec,r_dec)
    r_fin=big(cx,y0+vgap*8+60,560,124); oval(d,r_fin); draw_centered(d,f"FIN\n{t_fin}",r_fin)

    # Conectores (sin pisar texto)
    def top_pt(r):   return ((r[0]+r[2])//2, r[1]-HEAD_CLEAR)
    def bot_pt(r):   return ((r[0]+r[2])//2, r[3]+SAFE)
    def left_pt(r):  return (r[0]-HEAD_CLEAR, (r[1]+r[3])//2)
    def right_pt(r): return (r[2]+HEAD_CLEAR, (r[1]+r[3])//2)

    # Flechas columna central: SIEMPRE hacia abajo
    arrow_down(d, bot_pt(r_inicio), top_pt(r1))
    arrow_down(d, bot_pt(r1),      top_pt(r2))
    arrow_down(d, bot_pt(r2),      top_pt(r3))
    arrow_down(d, bot_pt(r3),      top_pt(r_dec))
    # ❌ antes: r2 -> FIN (cruzaba el rombo)
    # ✅ ahora: del rombo al FIN
    arrow_down(d, ( (r_dec[0]+r_dec[2])//2, r_dec[3]+SAFE ), top_pt(r_fin))

    # ---------- Rama SÍ (autoajustada para que quepa) ----------
    rx=cx+620
    n_items=8
    start_y=(r_dec[1]+r_dec[3])//2 + start_offset
    h_si  = 86 if compacto else 100
    h_si5 = int(altura_si5)
    widths = int(ancho_si)
    heights=[h_si,h_si,h_si,h_si,h_si5,h_si,h_si,h_si]

    # límites verticales disponibles
    max_center_y = r_fin[1] - 40  # margen inferior
    min_center_y = (r_dec[1]+r_dec[3])//2 + 10  # justo bajo el rombo

    # Paso mínimo para no solapar
    min_step_required = max((heights[i]/2 + heights[i+1]/2 + 2*HEAD_CLEAR) for i in range(n_items-1))
    # Paso máximo que todavía cabe con el start_y pedido
    fit_step = (max_center_y - heights[-1]/2 - start_y) / max(1,(n_items-1))
    # Si con el start_y elegido no cabe, subimos el arranque al mínimo necesario
    if fit_step < min_step_required:
        needed_top = max_center_y - heights[-1]/2 - min_step_required*(n_items-1)
        start_y = max(min_center_y, needed_top)
        fit_step = (max_center_y - heights[-1]/2 - start_y) / max(1,(n_items-1))
    # Paso final: respeta tu slider pero no excede ni cae por debajo del mínimo
    step = min(step_user, fit_step)
    step = max(step, min_step_required)

    Ys=[start_y + i*step for i in range(n_items)]
    textos_si=[s1,s2,s3,s4,s5,s6,s7,s8]
    rs=[]
    for i,(t,y) in enumerate(zip(textos_si,Ys)):
        h = heights[i]
        r=big(rx,int(y),widths,h)
        rrect(d,r); draw_centered(d,t,r); rs.append(r)

    # ---------- Rama NO ----------
    lx=cx-620
    rn=[]
    for i,t in enumerate([n1,n2,n3]):
        r=big(lx,int(Ys[i]),widths,h_si)
        rrect(d,r); draw_centered(d,t,r); rn.append(r)

    # Decisión → ramas (rótulos pegados y hacia afuera)
    seg_si = (right_pt(r_dec), (rs[0][0]-HEAD_CLEAR, (rs[0][1]+rs[0][3])//2))
    seg_no = (left_pt(r_dec),  (rn[0][2]+HEAD_CLEAR, (rn[0][1]+rn[0][3])//2))
    arrow(d, *seg_si); label_near_segment_outward(d, *seg_si, "Sí", page_center_x=cx, offset=40)
    arrow(d, *seg_no); label_near_segment_outward(d, *seg_no, "No", page_center_x=cx, offset=40)

    # Cadenas verticales (punta fuera, siempre hacia abajo)
    for i in range(len(rs)-1):
        p1=((rs[i][0]+rs[i][2])//2, rs[i][3]+SAFE)
        p2=((rs[i+1][0]+rs[i+1][2])//2, rs[i+1][1]-HEAD_CLEAR)
        arrow_down(d,p1,p2)
    for i in range(len(rn)-1):
        p1=((rn[i][0]+rn[i][2])//2, rn[i][3]+SAFE)
        p2=((rn[i+1][0]+rn[i+1][2])//2, rn[i+1][1]-HEAD_CLEAR)
        arrow_down(d,p1,p2)

    # Retroalimentación: riel externo (sin cruces) y limitado al borde
    rail_x = min(W-40, rs[-1][2] + retro_rail)
    start = (rs[-1][2]+SAFE, (rs[-1][1]+rs[-1][3])//2)
    mid1  = (rail_x, start[1])
    mid2  = (rail_x, (r2[1]+r2[3])//2)
    end   = (r2[2]+HEAD_CLEAR, (r2[1]+r2[3])//2)
    poly_arrow(d, [start, mid1, mid2, end], color=BLUE, width=4)
    d.text((min(W-50, rail_x-10), (start[1]+mid2[1])//2),
           "Retroalimentación", font=FONT_SMALL, fill=BLUE, anchor="rm")

    out=io.BytesIO(); img.save(out, format="PNG"); return out.getvalue()

# ---------- Exportadores ----------
def make_pdf_from_png(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO(); img.save(out, format="PDF"); return out.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.2), Inches(0.2), width=Inches(9.6))
    out = io.BytesIO(); prs.save(out); return out.getvalue()

# ---------- Render & Descargas ----------
png_bytes = render_png()
pdf_bytes = make_pdf_from_png(png_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, use_column_width=True)

c1,c2,c3 = st.columns(3)
with c1: st.download_button("⬇️ PNG", png_bytes, "diagrama_modelo_preventivo.png", "image/png")
with c2: st.download_button("⬇️ PDF", pdf_bytes, "diagrama_modelo_preventivo.pdf", "application/pdf")
with c3: st.download_button("⬇️ PPTX", pptx_bytes, "diagrama_modelo_preventivo.pptx",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation")
