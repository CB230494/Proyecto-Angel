# ===========================================
# MPGP – Generador de diagrama (ordenado/resumido)
# Flechas ortogonales + etiquetas "Sí/No" sin solapar
# Exporta: PNG / PDF  (+ PPTX si está disponible)
# ===========================================
import io, math
from typing import List, Tuple
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# PPTX opcional (no instalamos en runtime)
try:
    from pptx import Presentation
    from pptx.util import Inches
    HAS_PPTX = True
except Exception:
    HAS_PPTX = False

# ---------- Estilos ----------
W, H = 2200, 3000
BG = (247,250,255)
BLUE=(31,78,121); BORDER=(155,187,217)
LIGHTBLUE=(220,235,247); LIGHTY=(255,248,225)
WHITE=(255,255,255); BLACK=(20,20,20)

SAFE=18          # margen
ARW=18           # tamaño cabeza de flecha
GAP_Y=42         # separación vertical mínima entre cajas
GAP_X=60         # separación horizontal mínima para corredores

def _font(sz:int):
    try: return ImageFont.truetype("DejaVuSans.ttf", sz)
    except:  return ImageFont.load_default()

F_TITLE=_font(40); F=_font(26); FS=_font(22); FSEC=_font(32)

# ---------- Utilidades de texto/figuras ----------
def wrap(d:ImageDraw.ImageDraw, text:str, font, max_w:int)->List[str]:
    out=[]; text=str(text or "")
    for raw in text.split("\n"):
        words=raw.split(" "); cur=""
        for w in words:
            t=(cur+" "+w).strip()
            if d.textlength(t,font=font)<=max_w: cur=t
            else:
                if cur: out.append(cur)
                cur=w
        out.append(cur)
    return out

def box_auto(d, x:int, y:int, w:int, text:str, min_h:int=84, pad:int=18, leading:int=6):
    max_w=w-2*pad
    lines=wrap(d, text, F, max_w)
    lh=F.size+leading
    h=max(min_h, pad*2 + lh*max(1,len(lines)))
    r=[x-w//2, y-h//2, x+w//2, y+h//2]
    return r, lines, h

def draw_center(d, r, lines:List[str], font=F, fill=BLACK, leading=6, pad=18):
    x0,y0,x1,y1=r; lh=font.size+leading
    total=lh*max(1,len(lines))
    y=y0+(y1-y0-total)//2
    for ln in lines:
        w=d.textlength(ln,font=font)
        d.text((x0+(x1-x0-w)//2, y), ln, font=font, fill=fill)
        y+=lh

def rrect(d, r, radius=24, fill=WHITE, outline=BLUE, w=3):
    d.rounded_rectangle(r, radius=radius, fill=fill, outline=outline, width=w)

def oval(d, r, fill=LIGHTBLUE, outline=BLUE, w=3):
    d.ellipse(r, fill=fill, outline=outline, width=w)

def diamond(d, r, fill=LIGHTY, outline=BLUE, w=3):
    x0,y0,x1,y1=r; cx=(x0+x1)//2; cy=(y0+y1)//2
    d.polygon([(cx,y0),(x1,cy),(cx,y1),(x0,cy)], fill=fill, outline=outline)

def arrow(d, p1:Tuple[int,int], p2:Tuple[int,int], color=BLUE, w=4):
    d.line([p1,p2], fill=color, width=w)
    ang=math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    a1=(p2[0]-ARW*math.cos(ang-0.4), p2[1]-ARW*math.sin(ang-0.4))
    a2=(p2[0]-ARW*math.cos(ang+0.4), p2[1]-ARW*math.sin(ang+0.4))
    d.polygon([p2,a1,a2], fill=color)

def label(d, x, y, text, pad=6):
    w=d.textlength(text, font=FS); h=FS.size
    box=[x-w/2-pad, y-h/2-pad, x+w/2+pad, y+h/2+pad]
    d.rounded_rectangle(box, radius=8, fill=WHITE, outline=BLUE, width=2)
    d.text((x,y), text, font=FS, fill=BLUE, anchor="mm")

def orth(d, p1, p2, via_x=None, via_y=None, color=BLUE, w=4):
    """Flecha ortogonal H–V–H/V–H–V; última pata con cabeza."""
    x1,y1=p1; x2,y2=p2
    pts=[(x1,y1)]
    if (via_x is not None) and (via_y is None):
        pts += [(via_x,y1),(via_x,y2),(x2,y2)]
    elif (via_y is not None) and (via_x is None):
        pts += [(x1,via_y),(x2,via_y),(x2,y2)]
    elif (via_x is not None) and (via_y is not None):
        pts += [(via_x,y1),(via_x,via_y),(x2,via_y),(x2,y2)]
    else:
        pts += [(x1,y2),(x2,y2)]
    for i in range(len(pts)-2):
        d.line([pts[i],pts[i+1]], fill=color, width=w)
    arrow(d, pts[-2], pts[-1], color=color, w=w)

def mid(p1, p2): return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)

# ---------- Render ----------
def render_png()->bytes:
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    # marco y título
    d.rectangle([40,40,W-40,H-40], outline=BORDER, width=3)
    d.text((W//2, 90), "Modelo Preventivo de Gestión Policial – Proyecto Integrado (RESUMEN)", font=F_TITLE, fill=BLUE, anchor="mm")

    cx=W//2; x_no=430; x_si=W-430

    # Centro
    y=180
    r,lines,_=box_auto(d,cx,y,540,"INICIO\nPlanificación preventiva anual",min_h=96)
    oval(d,r); draw_center(d,r,lines)
    y += (r[3]-r[1])//2 + GAP_Y + 60

    boxes_c=[]
    for txt in [
        "Definición y calendarización de Delegaciones\n(Proc. 1.1)",
        "Apreciación situacional del territorio\n(Proc. 1.2)",
        "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",
    ]:
        rc,lc,hc = box_auto(d,cx,y,600,txt,min_h=110)
        rrect(d,rc); draw_center(d,rc,lc); boxes_c.append(rc)
        if len(boxes_c)>1:
            prev=boxes_c[-2]
            arrow(d, ((prev[0]+prev[2])//2, prev[3]+SAFE), ((rc[0]+rc[2])//2, rc[1]-SAFE))
        y += hc//2 + GAP_Y + 60

    # Decisión
    r_dec=[cx-320, y-90, cx+320, y+90]
    diamond(d,r_dec); draw_center(d,r_dec, wrap(d,"¿Se identifican riesgos prioritarios?",F, 560))

    # FIN (más abajo, columna central)
    r_fin,lf, _ = box_auto(d,cx, r_dec[3]+420, 620, "FIN\nEvaluación global de resultados\n(Indicadores, metas, impacto – 3.3)", min_h=104)
    oval(d,r_fin); draw_center(d,r_fin,lf)
    arrow(d, ((r_dec[0]+r_dec[2])//2, r_dec[3]+SAFE), ((r_fin[0]+r_fin[2])//2, r_fin[1]-SAFE))

    # -------- Rama NO (izquierda) --------
    y_no_top = min(260, r_dec[1]-220)   # arranca más arriba para evitar choque
    chain_no = [
        "Patrullaje rutinario y vigilancia continua",
        "Registro de factores menores en RAP",
        "Integración al análisis situacional",
    ]
    rn=[]
    ycur=y_no_top
    for i,txt in enumerate(chain_no):
        rno,ln,h = box_auto(d, x_no, ycur, 600, txt, min_h=100)
        rrect(d,rno); draw_center(d,rno,ln); rn.append(rno)
        if i>0:
            arrow(d, ((rn[i-1][0]+rn[i-1][2])//2, rn[i-1][3]+SAFE),
                     ((rno[0]+rno[2])//2, rno[1]-SAFE))
        ycur += h//2 + GAP_Y + 60
    # Decisión -> NO1 (flecha ortogonal + etiqueta "No" arriba del tramo)
    p_from = (r_dec[0]-SAFE, (r_dec[1]+r_dec[3])//2)
    p_to   = (rn[0][2]+SAFE, (rn[0][1]+rn[0][3])//2)
    via_y  = p_to[1]  # línea horizontal a la altura del NO1
    orth(d, p_from, p_to, via_y=via_y)
    mx,my = mid(p_from,(p_to[0],via_y))
    label(d, mx, my-26, "No")  # offset hacia arriba para no tapar la línea

    # -------- Rama SÍ (derecha) --------
    # Colocamos el primer "Sí" claramente por ENCIMA de la decisión (evita choque)
    y_si_top = (r_dec[1]+r_dec[3])//2 - 260
    chain_si = [
        "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
        "Construcción de líneas de acción preventivas\n(Proc. 2.3)",
        "Planificación de programas policiales preventivos\n(Proc. 2.4)",
        "Elaboración de órdenes de servicio para operativos",
        "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
        "Reporte de operativos (RAP, DATAPOL, informes)",
        "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
        "Retroalimentación a la planificación preventiva",
    ]
    rs=[]; ycur=y_si_top
    for i,txt in enumerate(chain_si):
        min_h = 150 if i==4 else 100
        rsi,lsi,h = box_auto(d, x_si, ycur, 600, txt, min_h=min_h)
        rrect(d,rsi); draw_center(d,rsi,lsi); rs.append(rsi)
        if i>0:
            arrow(d, ((rs[i-1][0]+rs[i-1][2])//2, rs[i-1][3]+SAFE),
                     ((rsi[0]+rsi[2])//2, rsi[1]-SAFE))
        ycur += h//2 + GAP_Y + (40 if i<4 else 30)
    # Decisión -> SI1 (ortogonal + etiqueta "Sí" por encima)
    p_from = (r_dec[2]+SAFE, (r_dec[1]+r_dec[3])//2)
    p_to   = (rs[0][0]-SAFE, (rs[0][1]+rs[0][3])//2)
    via_y  = p_to[1]
    orth(d, p_from, p_to, via_y=via_y)
    mx,my = mid(p_from,(p_to[0],via_y))
    label(d, mx, my-26, "Sí")

    # Retroalimentación (SI8 → B2) en “riel” externo
    rail_x = rs[-1][2] + 180
    # tramo horizontal desde SI8 hasta riel
    arrow(d, (rs[-1][2]+SAFE, (rs[-1][1]+rs[-1][3])//2), (rail_x, (rs[-1][1]+rs[-1][3])//2))
    # riel vertical
    d.line([(rail_x, (rs[-1][1]+rs[-1][3])//2), (rail_x, (boxes_c[1][1]+boxes_c[1][3])//2)], fill=BLUE, width=4)
    # riel → B2
    arrow(d, (rail_x, (boxes_c[1][1]+boxes_c[1][3])//2), (boxes_c[1][2]+SAFE, (boxes_c[1][1]+boxes_c[1][3])//2))
    d.text((rail_x-10, ((rs[-1][1]+rs[-1][3])//2 + (boxes_c[1][1]+boxes_c[1][3])//2)//2),
           "Retroalimentación", font=FS, fill=BLUE, anchor="rm")

    # -------- NODOS Demandantes (2x3, compacto) --------
    sec_y = r_fin[3] + 40
    d.text((W//2, sec_y), "Focalización por Nodos Demandantes – Resumen (Proc. 1.4)", font=FSEC, fill=BLUE, anchor="mm")
    y_sup = sec_y+70; x0=220; bw=420; gap=70; bh=100
    nodos_txt = [
        "Convoca reunión EDO (2º nivel)",
        "Verifica insumos mínimos (capas, encuestas, informes)",
        "Completa Matriz de Nodos priorizados",
        "Elabora órdenes de servicio (evidencia/monitoreo)",
        "Presenta factores críticos y variaciones del mes anterior",
        "Analiza puntos críticos y oportunidades (cualitativo)",
    ]
    n=[]
    for i,txt in enumerate(nodos_txt):
        row=0 if i<3 else 1; col=i if i<3 else i-3
        xc = x0 + col*(bw+gap)
        yc = y_sup + row*170
        rn,ln,_ = box_auto(d, xc+bw//2, yc+bh//2, bw, txt, min_h=bh)
        rrect(d,rn); draw_center(d,rn,ln); n.append(rn)
    # flechas horizontales claras
    arrow(d, (n[0][2]+SAFE, (n[0][1]+n[0][3])//2), (n[1][0]-SAFE, (n[1][1]+n[1][3])//2))
    arrow(d, (n[1][2]+SAFE, (n[1][1]+n[1][3])//2), (n[2][0]-SAFE, (n[2][1]+n[2][3])//2))
    arrow(d, ((n[1][0]+n[1][2])//2, n[1][3]+SAFE), ((n[4][0]+n[4][2])//2, n[4][1]-SAFE))
    arrow(d, (n[3][2]+SAFE, (n[3][1]+n[3][3])//2), (n[4][0]-SAFE, (n[4][1]+n[4][3])//2))
    arrow(d, (n[4][2]+SAFE, (n[4][1]+n[4][3])//2), (n[5][0]-SAFE, (n[5][1]+n[5][3])//2))
    # Integración SÍ-1 → Nodos → SÍ-3 (corredores externos)
    orth(d, (rs[0][2]+SAFE, (rs[0][1]+rs[0][3])//2),
            (n[0][0]-SAFE, (n[0][1]+n[0][3])//2),
            via_x=rs[0][2]+GAP_X)
    orth(d, (n[5][2]+SAFE, (n[5][1]+n[5][3])//2),
            (rs[2][0]-SAFE, (rs[2][1]+rs[2][3])//2),
            via_x=rs[2][0]-GAP_X)

    # -------- Conducta delictiva reiterada (fila de 5) --------
    sec2_y = y_sup+170*2+100
    d.text((W//2, sec2_y), "Conducta delictiva reiterada – Resumen", font=FSEC, fill=BLUE, anchor="mm")
    y_r = sec2_y+60; rbw=420; rgap=90; rbh=100; rx0=160
    reiter_txt = [
        "Estudia antecedentes judiciales del objetivo",
        "Elabora ficha de conducta delictiva reiterada",
        "Remite fichas a operaciones regionales",
        "Presenta fichas en reunión EDO (primer nivel)",
        "Documenta para EDO (primer y segundo nivel)",
    ]
    rboxes=[]
    for i,txt in enumerate(reiter_txt):
        rc,lc,_ = box_auto(d, rx0+i*(rbw+rgap)+rbw//2, y_r+rbh//2, rbw, txt, min_h=rbh)
        rrect(d,rc); draw_center(d,rc,lc); rboxes.append(rc)
        if i>0:
            arrow(d, (rboxes[i-1][2]+SAFE,(rboxes[i-1][1]+rboxes[i-1][3])//2),
                     (rc[0]-SAFE,(rc[1]+rc[3])//2))

    # Integración SÍ-6 → Reiterada → SÍ-7 con ruteo ortogonal limpio
    orth(d, (rs[5][2]+SAFE, (rs[5][1]+rs[5][3])//2),
            (rboxes[0][0]-SAFE, (rboxes[0][1]+rboxes[0][3])//2),
            via_x=rs[5][2]+GAP_X)
    orth(d, (rboxes[-1][2]+SAFE, (rboxes[-1][1]+rboxes[-1][3])//2),
            (rs[6][0]-SAFE, (rs[6][1]+rs[6][3])//2),
            via_x=rs[6][0]-GAP_X)

    # Export PNG en bytes
    out=io.BytesIO(); img.save(out, format="PNG")
    return out.getvalue()

def make_pdf(png:bytes)->bytes:
    img=Image.open(io.BytesIO(png)).convert("RGB")
    out=io.BytesIO(); img.save(out, "PDF"); return out.getvalue()

def make_pptx(png:bytes)->bytes:
    prs=Presentation(); slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png), Inches(0.3), Inches(0.3), width=Inches(10.0))
    out=io.BytesIO(); prs.save(out); return out.getvalue()

# ---------- UI ----------
st.set_page_config(page_title="MPGP – Generador ordenado", layout="wide")
st.title("MPGP – Diagrama integrado (ordenado y con flechas limpias)")

if st.button("🛠️ Generar/Actualizar diagrama", use_container_width=True) or "png" not in st.session_state:
    st.session_state.png = render_png()

st.image(st.session_state.png, use_column_width=True)
c1,c2,c3 = st.columns(3)
with c1:
    st.download_button("⬇️ PNG", st.session_state.png, "MPGP_integrado.png", "image/png", use_container_width=True)
with c2:
    st.download_button("⬇️ PDF", make_pdf(st.session_state.png), "MPGP_integrado.pdf", "application/pdf", use_container_width=True)
with c3:
    if HAS_PPTX:
        st.download_button("⬇️ PPTX", make_pptx(st.session_state.png),
                           "MPGP_integrado.pptx",
                           "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           use_container_width=True)
    else:
        st.info("Para habilitar PPTX agrega 'python-pptx==0.6.23' a requirements.txt y vuelve a desplegar.")

