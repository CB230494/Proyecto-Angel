# =========================
# 📊 Diagrama MPGP – Exportador (Pillow, flechas ordenadas + rótulos fuera)
# =========================
import io, math, textwrap
from typing import List
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from pptx import Presentation
from pptx.util import Inches

# ---- Config y estilos ----
st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial")
st.caption("Más espacio entre cuadros y rótulos Sí/No fuera de las flechas.")

BLUE=(31,78,121); BORDER=(155,187,217); LIGHTBLUE=(220,235,247); LIGHTYELLOW=(255,248,225)
WHITE=(255,255,255); BLACK=(0,0,0); BG=(247,250,255)
W,H=2000,1400; SAFE=16; ARROW_HEAD=18

def font(size):
    try: return ImageFont.truetype("DejaVuSans.ttf", size)
    except: return ImageFont.load_default()
FONT=font(22); FONT_SMALL=font(18); FONT_TITLE=font(28)

# ---- Inputs ----
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

st.markdown("### ⚙️ Ajustes de layout")
g1,g2,g3=st.columns(3)
with g1:
    start_offset=st.slider("Inicio rama SÍ (relativo a la decisión)", -260, 120, -90, 5)
with g2:
    step_user=st.slider("Espaciado vertical (px)", 120, 200, 140, 5)
with g3:
    compacto=st.toggle("Modo compacto", True)

# ---- helpers de texto/dibujo ----
def wrap_text(d, text, font, max_w):
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

def draw_centered(d, text, box, font=FONT, fill=BLACK, leading=6):
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

def arrow(d, p1, p2, color=BLUE, width=4):
    d.line([p1,p2], fill=color, width=width)
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    a1=(p2[0]-ARROW_HEAD*math.cos(ang-0.4), p2[1]-ARROW_HEAD*math.sin(ang-0.4))
    a2=(p2[0]-ARROW_HEAD*math.cos(ang+0.4), p2[1]-ARROW_HEAD*math.sin(ang+0.4))
    d.polygon([p2,a1,a2], fill=color)

def quad_curve_points(p0,p1,p2,steps=70):
    pts=[]
    for i in range(steps+1):
        t=i/steps
        x=(1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t**2*p2[0]
        y=(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t**2*p2[1]
        pts.append((x,y))
    return pts

def curved_arrow(d, p1, p2, curve=0.48, color=BLUE, width=4):
    mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
    dx,dy=p2[0]-p1[0],p2[1]-p1[1]; L=max(1,math.hypot(dx,dy))
    nx,ny=-dy/L,dx/L
    ctrl=(mx+curve*L*0.6*nx, my+curve*L*0.6*ny)
    pts=quad_curve_points(p1,ctrl,p2)
    d.line(pts, fill=color, width=width)
    x1,y1=pts[-2]; x2,y2=pts[-1]; ang=math.atan2(y2-y1,x2-x1)
    a1=(x2-ARROW_HEAD*math.cos(ang-0.4), y2-ARROW_HEAD*math.sin(ang-0.4))
    a2=(x2-ARROW_HEAD*math.cos(ang+0.4), y2-ARROW_HEAD*math.sin(ang+0.4))
    d.polygon([(x2,y2),a1,a2], fill=color)

def draw_label(d, x, y, text): d.text((x,y), text, font=FONT_SMALL, fill=BLUE, anchor="mm")

# ---- render principal ----
def render_png():
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    d.rectangle([20,20,W-20,H-20],outline=BORDER,width=3)
    d.text((W//2,50),"Modelo Preventivo de Gestión Policial – Función de Operacionales",font=FONT_TITLE,fill=BLUE,anchor="mm")

    cx=W//2; vgap=130; bw,bh=480,104; y0=120
    def box(x,y,w=bw,h=bh): return [x-w//2, y-h//2, x+w//2, y+h//2]
    def big(x,y,w,h): return [x-w//2, y-h//2, x+w//2, y+h//2]

    r_inicio=box(cx,y0);        oval(d,r_inicio); draw_centered(d,f"INICIO\n{t_inicio}",r_inicio)
    r1=box(cx,y0+vgap);         rrect(d,r1); draw_centered(d,b1,r1)
    r2=box(cx,y0+vgap*2);       rrect(d,r2); draw_centered(d,b2,r2)
    r3=box(cx,y0+vgap*3);       rrect(d,r3); draw_centered(d,b3,r3)
    r_dec=big(cx,y0+vgap*4,520,124); diamond(d,r_dec); draw_centered(d,q_dec,r_dec)
    r_fin=big(cx,y0+vgap*8+60,540,124); oval(d,r_fin); draw_centered(d,f"FIN\n{t_fin}",r_fin)

    # Conectores con margen SAFE
    def top(r): return ((r[0]+r[2])//2, r[1]-SAFE)
    def bot(r): return ((r[0]+r[2])//2, r[3]+SAFE)
    def left(r): return (r[0]-SAFE, (r[1]+r[3])//2)
    def right(r): return (r[2]+SAFE, (r[1]+r[3])//2)

    # Columna central
    arrow(d, bot(r_inicio), top(r1))
    arrow(d, bot(r1), top(r2))
    arrow(d, bot(r2), top(r3))
    arrow(d, bot(r3), top(r_dec))
    arrow(d, bot(r2), top(r_fin))  # Fin directo desde bloque 2 (para despejar el centro)

    # ---- Rama SÍ (más espacio) ----
    rx=cx+600
    n_items=8
    start_y=(r_dec[1]+r_dec[3])//2 + start_offset
    safe_bottom=r_fin[1]-190
    step=min(step_user, max(120, (safe_bottom-start_y)/max(1,(n_items-1))))

    h_si=84 if compacto else 98
    h_si5=h_si+(0 if compacto else 10)

    Ys=[start_y + i*step for i in range(n_items)]
    textos_si=[s1,s2,s3,s4,s5,s6,s7,s8]
    rs=[]
    for i,(t,y) in enumerate(zip(textos_si,Ys)):
        h=h_si5 if i==4 else h_si
        r=big(rx,int(y),540,h); rrect(d,r); draw_centered(d,t,r); rs.append(r)

    # ---- Rama NO (alineada con los 3 primeros SÍ) ----
    lx=cx-600
    textos_no=[n1,n2,n3]; rn=[]
    for i,t in enumerate(textos_no):
        r=big(lx,int(Ys[i]),540,h_si); rrect(d,r); draw_centered(d,t,r); rn.append(r)

    # Decisión → ramas (rótulos fuera)
    arrow(d, right(r_dec), (rs[0][0]-SAFE, (rs[0][1]+rs[0][3])//2))
    arrow(d, left(r_dec),  (rn[0][2]+SAFE, (rn[0][1]+rn[0][3])//2))
    # Etiquetas colocadas arriba y hacia afuera
    draw_label(d, right(r_dec)[0]+60, right(r_dec)[1]-40, "Sí")
    draw_label(d, left(r_dec)[0]-60,  left(r_dec)[1]-40,  "No")

    # Cadena SÍ
    for i in range(len(rs)-1):
        p1=((rs[i][0]+rs[i][2])//2, rs[i][3]+SAFE)
        p2=((rs[i+1][0]+rs[i+1][2])//2, rs[i+1][1]-SAFE)
        arrow(d,p1,p2)

    # Cadena NO
    for i in range(len(rn)-1):
        p1=((rn[i][0]+rn[i][2])//2, rn[i][3]+SAFE)
        p2=((rn[i+1][0]+rn[i+1][2])//2, rn[i+1][1]-SAFE)
        arrow(d,p1,p2)

    # Retroalimentación (curva externa)
    curved_arrow(d, (rs[-1][0]-SAFE, (rs[-1][1]+rs[-1][3])//2),
                    (r2[2]+SAFE,     (r2[1]+r2[3])//2),
                    curve=0.55)

    out=io.BytesIO(); img.save(out,format="PNG"); return out.getvalue()

def make_pdf_from_png(png_bytes):
    from PIL import Image as PImage
    img=PImage.open(io.BytesIO(png_bytes)).convert("RGB")
    out=io.BytesIO(); img.save(out,format="PDF"); return out.getvalue()

def make_pptx(png_bytes):
    prs=Presentation(); slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.2), Inches(0.2), width=Inches(9.6))
    out=io.BytesIO(); prs.save(out); return out.getvalue()

# ---- Render & Descargas ----
png_bytes=render_png()
pdf_bytes=make_pdf_from_png(png_bytes)
pptx_bytes=make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, use_column_width=True)
c1,c2,c3=st.columns(3)
with c1: st.download_button("⬇️ PNG", png_bytes, "diagrama_modelo_preventivo.png", "image/png")
with c2: st.download_button("⬇️ PDF", pdf_bytes, "diagrama_modelo_preventivo.pdf", "application/pdf")
with c3: st.download_button("⬇️ PPTX", pptx_bytes, "diagrama_modelo_preventivo.pptx",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Si aún ves rótulos muy cerca, subí el espaciado o mueve el inicio de la rama SÍ más arriba.")


