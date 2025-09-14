# ===========================================
# MPGP – Generador de diagrama (ordenado/resumido)
# Exporta: PNG / PDF  (+ PPTX si está disponible)
# ===========================================
import io, math
from typing import List, Tuple
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# PPTX opcional (no instalar en runtime)
try:
    from pptx import Presentation
    from pptx.util import Inches
    HAS_PPTX = True
except Exception:
    HAS_PPTX = False

# ---------------- Estilos / colores ----------------
W, H = 2200, 3000            # lienzo grande (imprimible)
BG = (247, 250, 255)
BLUE=(31,78,121); BORDER=(155,187,217)
LIGHTBLUE=(220,235,247); LIGHTY=(255,248,225)
WHITE=(255,255,255); BLACK=(20,20,20)
SAFE=16; ARH=18; HEAD=SAFE+ARH+6

def font(sz:int):
    try: return ImageFont.truetype("DejaVuSans.ttf", sz)
    except: return ImageFont.load_default()
F_TITLE=font(40); F=font(26); FS=font(22)

# ---------------- Utilidades de dibujo ----------------
def sx(x)->str: return "" if x is None else str(x)

def wrap(d:ImageDraw.ImageDraw, text:str, font, max_w:int)->List[str]:
    text=sx(text); out=[]
    for raw in text.split("\n"):
        words=raw.split(" "); cur=""
        for w in words:
            t=(cur+" "+w).strip()
            if d.textlength(t, font=font) <= max_w: cur=t
            else:
                if cur: out.append(cur)
                cur=w
        out.append(cur)
    return out

def h_for_text(d, text, font, max_w, pad_v=18, leading=6, min_h=78):
    lines=wrap(d, text, font, max_w); lh=font.size+leading
    return max(min_h, pad_v*2 + lh*max(1,len(lines)))

def draw_center(d, text, box, font=F, fill=BLACK, leading=6, pad=18):
    x0,y0,x1,y1=box; max_w=x1-x0-2*pad
    lines=wrap(d, text, font, max_w); lh=font.size+leading
    total=lh*max(1,len(lines)); y=y0+(y1-y0-total)//2
    for ln in lines:
        w=d.textlength(ln, font=font)
        d.text((x0+(x1-x0-w)//2, y), ln, font=font, fill=fill); y+=lh

def rrect(d, box, r=24, fill=WHITE, outline=BLUE, w=3): d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)
def oval(d, box, fill=LIGHTBLUE, outline=BLUE, w=3): d.ellipse(box, fill=fill, outline=outline, width=w)
def diamond(d, box, fill=LIGHTY, outline=BLUE, w=3):
    x0,y0,x1,y1=box; cx=(x0+x1)//2; cy=(y0+y1)//2
    d.polygon([(cx,y0),(x1,cy),(cx,y1),(x0,cy)], fill=fill, outline=outline)

import math as _m
def arrow(d, p1:Tuple[int,int], p2:Tuple[int,int], color=BLUE, w=4):
    d.line([p1,p2], fill=color, width=w)
    ang=_m.atan2(p2[1]-p1[1], p2[0]-p1[0])
    a1=(p2[0]-ARH*_m.cos(ang-0.4), p2[1]-ARH*_m.sin(ang-0.4))
    a2=(p2[0]-ARH*_m.cos(ang+0.4), p2[1]-ARH*_m.sin(ang+0.4))
    d.polygon([p2,a1,a2], fill=color)

def label(d, mx,my,text):
    w=d.textlength(text,font=FS); h=FS.size; pad=6
    r=[mx-w/2-pad, my-h/2-pad, mx+w/2+pad, my+h/2+pad]
    d.rounded_rectangle(r, radius=8, fill=WHITE, outline=BLUE, width=2)
    d.text((mx,my), text, font=FS, fill=BLUE, anchor="mm")

# ---------------- Textos por defecto (resumidos) ----------------
TXT = {
"INICIO":"INICIO\nPlanificación preventiva anual",
"B1":"Definición y calendarización de Delegaciones\n(Proc. 1.1)",
"B2":"Apreciación situacional del territorio\n(Proc. 1.2)",
"B3":"Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",
"DEC":"¿Se identifican riesgos prioritarios?",
"NO1":"Patrullaje rutinario y vigilancia continua",
"NO2":"Registro de factores menores en RAP",
"NO3":"Integración al análisis situacional",
"SI1":"Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
"SI2":"Construcción de líneas de acción preventivas\n(Proc. 2.3)",
"SI3":"Planificación de programas policiales preventivos\n(Proc. 2.4)",
"SI4":"Elaboración de órdenes de servicio para operativos",
"SI5":"Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
"SI6":"Reporte de operativos (RAP, DATAPOL, informes)",
"SI7":"Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
"SI8":"Retroalimentación a la planificación preventiva",
"FIN":"FIN\nEvaluación global de resultados\n(Indicadores, metas, impacto – 3.3)",
# Nodos (resumen 6 pasos)
"N1":"Convoca reunión EDO (2º nivel)",
"N2":"Verifica insumos mínimos (capas, encuestas, informes)",
"N3":"Completa Matriz de Nodos priorizados",
"N4":"Elabora órdenes de servicio (evidencia/monitoreo)",
"N5":"Presenta factores críticos y variaciones del mes anterior",
"N6":"Analiza puntos críticos y oportunidades (cualitativo)",
# Reiterada (resumen 5 pasos)
"R1":"Estudia antecedentes judiciales del objetivo",
"R2":"Elabora ficha de conducta delictiva reiterada",
"R3":"Remite fichas a operaciones regionales",
"R4":"Presenta fichas en reunión EDO (primer nivel)",
"R5":"Documenta para EDO (primer y segundo nivel)",
}

# ---------------- Render del diagrama ----------------
def render_png(txt:dict=TXT) -> bytes:
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    d.rectangle([40,40,W-40,H-40], outline=BORDER, width=3)
    d.text((W//2, 90), "Modelo Preventivo de Gestión Policial – Proyecto Integrado (RESUMEN)", font=F_TITLE, fill=BLUE, anchor="mm")

    cx=W//2; x_no=430; x_si=W-430

    # Columna central
    y=180
    ini=[cx-270,y-54,cx+270,y+54];  oval(d,ini); draw_center(d,txt["INICIO"],ini,F)
    y+=150
    b1=[cx-300,y-60,cx+300,y+60];   rrect(d,b1); draw_center(d,txt["B1"],b1)
    d.line([(cx,y-60-20),(cx,y-60)],fill=BLUE,width=4)
    y+=150
    b2=[cx-300,y-60,cx+300,y+60];   rrect(d,b2); draw_center(d,txt["B2"],b2)
    d.line([(cx,y-60-20),(cx,y-60)],fill=BLUE,width=4)
    y+=150
    b3=[cx-300,y-60,cx+300,y+60];   rrect(d,b3); draw_center(d,txt["B3"],b3)
    d.line([(cx,y-60-20),(cx,y-60)],fill=BLUE,width=4)
    y+=140
    dec=[cx-320,y-70,cx+320,y+70];  diamond(d,dec); draw_center(d,txt["DEC"],dec)

    # Rama NO (izquierda)
    yno=(dec[1]+dec[3])//2
    no1=[x_no-300, 260, x_no+300, 340]; rrect(d,no1); draw_center(d,txt["NO1"],no1)
    no2=[x_no-300, 420, x_no+300, 500]; rrect(d,no2); draw_center(d,txt["NO2"],no2)
    no3=[x_no-300, 580, x_no+300, 660]; rrect(d,no3); draw_center(d,txt["NO3"],no3)
    arrow(d, (dec[0]-10, yno), (x_no+300+60, (no1[1]+no1[3])//2))
    label(d, (dec[0]+x_no+300+60)/2, yno-30, "No")
    arrow(d, ((no1[0]+no1[2])//2, no1[3]+10), ((no2[0]+no2[2])//2, no2[1]-10))
    arrow(d, ((no2[0]+no2[2])//2, no2[3]+10), ((no3[0]+no3[2])//2, no3[1]-10))

    # Rama SÍ (derecha)
    ysi=(dec[1]+dec[3])//2
    si_y_top=240; si_step=140
    si=[]; si_txt=["SI1","SI2","SI3","SI4","SI5","SI6","SI7","SI8"]
    for i,key in enumerate(si_txt):
        hh = 150 if key=="SI5" else 92
        yb = si_y_top + i*si_step + (10 if i>=4 else 0)
        r=[x_si-300, yb-hh//2, x_si+300, yb+hh//2]
        rrect(d,r); draw_center(d,txt[key],r); si.append(r)
        if i>0: arrow(d, (((si[i-1][0]+si[i-1][2])//2, si[i-1][3]+10)),
                        (((r[0]+r[2])//2, r[1]-10)))
    arrow(d, (dec[2]+10, ysi), (x_si-300-60, (si[0][1]+si[0][3])//2)); label(d, (dec[2]+x_si-300-60)/2, ysi-30, "Sí")

    # Retroalimentación (SI8 → B2)
    rail_x = x_si+360
    arrow(d, (si[-1][2]+10, (si[-1][1]+si[-1][3])//2), (rail_x, (si[-1][1]+si[-1][3])//2))
    d.line([(rail_x, (si[-1][1]+si[-1][3])//2), (rail_x, (b2[1]+b2[3])//2)], fill=BLUE, width=4)
    arrow(d, (rail_x, (b2[1]+b2[3])//2), (b2[2]+20, (b2[1]+b2[3])//2))
    d.text((rail_x-8, ((si[-1][1]+si[-1][3])//2 + (b2[1]+b2[3])//2)//2),
           "Retroalimentación", font=FS, fill=BLUE, anchor="rm")

    # FIN central
    d.line([(cx, dec[3]+10),(cx, dec[3]+10+370)],fill=BLUE,width=4)
    fin=[cx-300, dec[3]+10+420, cx+300, dec[3]+10+520]
    oval(d,fin); draw_center(d,txt["FIN"],fin,F)

    # NODOS (2x3)
    sec_y = dec[3]+10+560
    d.text((W//2, sec_y), "Focalización por Nodos Demandantes – Resumen (Proc. 1.4)", font=font(32), fill=BLUE, anchor="mm")
    y_sup = sec_y+70; x0=200; bw=420; gap=70; bh=100
    n_keys=["N1","N2","N3","N4","N5","N6"]; n=[]
    for i,k in enumerate(n_keys):
        row=0 if i<3 else 1; col=i if i<3 else i-3
        xc=x0 + col*(bw+gap); yc=y_sup + row*170
        r=[xc, yc, xc+bw, yc+bh]; rrect(d,r); draw_center(d,txt[k],r); n.append(r)
    arrow(d, (n[0][2]+10,(n[0][1]+n[0][3])//2), (n[1][0]-10,(n[1][1]+n[1][3])//2))
    arrow(d, (n[1][2]+10,(n[1][1]+n[1][3])//2), (n[2][0]-10,(n[2][1]+n[2][3])//2))
    arrow(d, (((n[0][0]+n[2][2])//2, n[2][3]+10)), (((n[3][0]+n[5][2])//2, n[3][1]-20)))
    arrow(d, (n[3][2]+10,(n[3][1]+n[3][3])//2), (n[4][0]-10,(n[4][1]+n[4][3])//2))
    arrow(d, (n[4][2]+10,(n[4][1]+n[4][3])//2), (n[5][0]-10,(n[5][1]+n[5][3])//2))
    # Integración SÍ1 → Nodos → SÍ3
    arrow(d, (si[0][2]+10, (si[0][1]+si[0][3])//2), (n[0][0]-20, (n[0][1]+n[0][3])//2))
    arrow(d, (n[5][2]+10, (n[5][1]+n[5][3])//2), (si[2][0]-10, (si[2][1]+si[2][3])//2))

    # REITERADA (fila 5)
    sec2_y = y_sup+170*2+80
    d.text((W//2, sec2_y), "Conducta delictiva reiterada – Resumen", font=font(32), fill=BLUE, anchor="mm")
    y_r = sec2_y+60; bw=420; gap=90; bh=100; x0=160
    r_keys=["R1","R2","R3","R4","R5"]; r_boxes=[]
    for i,k in enumerate(r_keys):
        xc=x0 + i*(bw+gap); r=[xc, y_r, xc+bw, y_r+bh]
        rrect(d,r); draw_center(d,txt[k],r); r_boxes.append(r)
        if i>0: arrow(d, (r_boxes[i-1][2]+10,(r_boxes[i-1][1]+r_boxes[i-1][3])//2),
                          (r[0]-10,(r[1]+r[3])//2))
    # Integración SÍ6 → Reiterada → SÍ7
    arrow(d, (si[5][2]+10,(si[5][1]+si[5][3])//2),
             (r_boxes[0][0]-10,(r_boxes[0][1]+r_boxes[0][3])//2))
    arrow(d, (r_boxes[-1][2]+10,(r_boxes[-1][1]+r_boxes[-1][3])//2),
             (si[6][0]-10,(si[6][1]+si[6][3])//2))

    # PNG en bytes
    buff=io.BytesIO(); img.save(buff, format="PNG")
    return buff.getvalue()

def make_pdf(png:bytes)->bytes:
    img=Image.open(io.BytesIO(png)).convert("RGB")
    out=io.BytesIO(); img.save(out, "PDF"); return out.getvalue()

def make_pptx(png:bytes)->bytes:
    prs=Presentation(); slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png), Inches(0.3), Inches(0.3), width=Inches(10.0))
    out=io.BytesIO(); prs.save(out); return out.getvalue()

# ---------------- UI (simple y directa) ----------------
st.set_page_config(page_title="MPGP – Generador de diagrama", layout="wide")
st.title("MPGP – Diagrama integrado (generador)")
st.caption("Hecho, ordenado y resumido. Descarga en PNG / PDF" + (" / PPTX." if HAS_PPTX else "."))

# Generar al cargar y con botón
if st.button("🛠️ Generar/Actualizar diagrama", use_container_width=True) or "png" not in st.session_state:
    st.session_state.png = render_png()

# Preview + descargas
st.image(st.session_state.png, use_column_width=True)
col1,col2,col3 = st.columns(3)
with col1:
    st.download_button("⬇️ PNG", st.session_state.png, "MPGP_integrado.png", "image/png", use_container_width=True)
with col2:
    st.download_button("⬇️ PDF", make_pdf(st.session_state.png), "MPGP_integrado.pdf", "application/pdf", use_container_width=True)
with col3:
    if HAS_PPTX:
        st.download_button(
            "⬇️ PPTX",
            make_pptx(st.session_state.png),
            "MPGP_integrado.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )
    else:
        st.info("Para habilitar PPTX agrega 'python-pptx==0.6.23' a requirements.txt y redeploy.")



