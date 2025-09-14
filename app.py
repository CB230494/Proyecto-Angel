# MPGP – Proyecto Integrado (principal + nodos + reiterada) con texto autoajustado y flechas ortogonales
import io, math
from typing import List, Tuple
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, Image as PIL
from pptx import Presentation
from pptx.util import Inches

# ---------- Estilo ----------
BLUE=(31,78,121); BORDER=(155,187,217); LIGHTBLUE=(220,235,247); LIGHTYELLOW=(255,248,225)
LANE_BG=(234,240,249); WHITE=(255,255,255); BLACK=(0,0,0); BG=(247,250,255)
SAFE=16; ARW=18; HEAD_CLEAR=SAFE+ARW+6
W=2000
BASE_H=1400; H_NODOS=760; H_REIT=920

def _font(sz:int):
    try: return ImageFont.truetype("DejaVuSans.ttf", sz)
    except: return ImageFont.load_default()
FONT=_font(22); FONT_S=_font(18); FONT_T=_font(28); FONT_LANE=_font(20); FONT_SUB=_font(24)

# ---------- Utilidades robustas ----------
def sx(x): return "" if x is None else str(x)

def wrap(d:ImageDraw.ImageDraw, text, font, max_w)->List[str]:
    text=sx(text)
    out=[]
    for raw in text.split("\n"):
        words=raw.split(" "); cur=""
        for w in words:
            t=(cur+" "+w).strip()
            if d.textlength(t,font=font)<=max_w:
                cur=t
            else:
                if cur: out.append(cur)
                cur=w
        if cur: out.append(cur)
    return out

def h_for_text(d, text, font, max_w, pad_v=20, leading=6, min_h=78):
    lines=wrap(d,text,font,max_w); lh=font.size+leading
    return max(min_h, pad_v*2 + lh*max(1,len(lines)))

def draw_text_center(d, text, box, font=FONT, fill=BLACK, leading=6):
    x0,y0,x1,y1=box; max_w=x1-x0-30
    lines=wrap(d,text,font,max_w); lh=font.size+leading
    total=lh*max(1,len(lines))
    y=y0+(y1-y0-total)//2
    for ln in lines:
        w=d.textlength(ln,font=font); x=x0+(x1-x0-w)//2
        d.text((x,y),ln,font=font,fill=fill); y+=lh

def rrect(d,box,r=22,fill=WHITE,outline=BLUE,w=3): d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)
def oval(d,box,fill=LIGHTBLUE,outline=BLUE,w=3): d.ellipse(box,fill=fill,outline=outline,width=w)
def diamond(d,box,fill=LIGHTYELLOW,outline=BLUE,w=3):
    x0,y0,x1,y1=box; cx=(x0+x1)//2; cy=(y0+y1)//2
    d.polygon([(cx,y0),(x1,cy),(cx,y1),(x0,cy)],fill=fill,outline=outline)

def arrow(d,p1,p2,color=BLUE,w=4):
    d.line([p1,p2],fill=color,width=w)
    ang=math.atan2(p2[1]-p1[1],p2[0]-p1[0])
    a1=(p2[0]-ARW*math.cos(ang-0.4), p2[1]-ARW*math.sin(ang-0.4))
    a2=(p2[0]-ARW*math.cos(ang+0.4), p2[1]-ARW*math.sin(ang+0.4))
    d.polygon([p2,a1,a2],fill=color)

def orth(d, start, end, via_x=None, via_y=None, color=BLUE, w=4):
    """Flecha ortogonal: H-V-H o V-H-V (sin diagonales)."""
    x1,y1=start; x2,y2=end
    pts=[(x1,y1)]
    if via_x is not None and via_y is None:
        pts += [(via_x,y1),(via_x,y2),(x2,y2)]
    elif via_y is not None and via_x is None:
        pts += [(x1,via_y),(x2,via_y),(x2,y2)]
    elif via_x is not None and via_y is not None:
        pts += [(via_x,y1),(via_x,via_y),(x2,via_y),(x2,y2)]
    else:  # sin guías: camino en L estándar
        pts += [(x1,y2),(x2,y2)]
    # dibuja segmentos y cabeza
    for i in range(len(pts)-2):
        d.line([pts[i],pts[i+1]],fill=color,width=w)
    arrow(d,pts[-2],pts[-1],color=color,w=w)

def label_mid(d,p1,p2,text):
    mx=(p1[0]+p2[0])/2; my=(p1[1]+p2[1])/2
    w=d.textlength(text,font=FONT_S); h=FONT_S.size; pad=6
    d.rounded_rectangle([mx-w/2-pad,my-h/2-pad,mx+w/2+pad,my+h/2+pad],radius=8,fill=WHITE,outline=BLUE,width=2)
    d.text((mx,my),text,font=FONT_S,fill=BLUE,anchor="mm")

def paste_lane_label(img, box, text):
    x0,y0,x1,y1=box
    d=ImageDraw.Draw(img)
    d.rectangle(box,fill=LANE_BG,outline=BORDER,width=2)
    tmp=PIL.new("RGBA",(y1-y0,x1-x0),(0,0,0,0))
    td=ImageDraw.Draw(tmp)
    tw=td.textlength(sx(text),font=FONT_LANE)
    td.text(((y1-y0-tw)//2, ((x1-x0)-FONT_LANE.size)//2), sx(text), font=FONT_LANE, fill=BLUE)
    rot=tmp.rotate(90,expand=True)
    img.paste(rot,(x0,y0),rot)

# ---------- UI ----------
st.set_page_config(page_title="MPGP Integrado",layout="wide")
st.title("MPGP – Proyecto Integrado")
st.caption("Principal + Nodos + Reiterada en un solo flujo, con flechas ortogonales y autoajuste de texto.")

# Textos base (iguales a la versión anterior)
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

st.markdown("### Ajustes rápidos")
a1,a2,a3=st.columns(3)
with a1: start_offset=st.slider("Inicio rama SÍ (relativo al rombo)",-800,240,-320,5)
with a2: ancho_si=st.slider("Ancho cuadros SÍ/NO (px)",520,680,560,10)
with a3: retro_gap=st.slider("Separación retroalimentación (px)",140,260,170,5)

# Nodos (Proc. 1.4 – parte 1)
st.markdown("### Nodos Demandantes (integrado en el flujo)")
a_sup1=st.text_area("A-Superior 1","Convoca a reunión EDO de segundo nivel con plantillas diferenciadas")
a_sup2=st.text_area("A-Superior 2","Verifica insumos mínimos para análisis (capas, encuestas, informes)")
a_sup3=st.text_area("A-Superior 3","Completa la Matriz de Nodos demandantes priorizados")
a_sup4=st.text_area("A-Superior 4","Elabora órdenes de servicio para evidencia y monitoreo")
a_inf1=st.text_area("A-Inferior 1","Abre el SIG para visualizar y mapear la información de nodos")
a_inf2=st.text_area("A-Inferior 2","Selecciona capas de información disponibles en el SIG")
a_inf3=st.text_area("A-Inferior 3","Presenta factores de riesgo críticos y variaciones del mes anterior")
a_inf4=st.text_area("A-Inferior 4","Analiza puntos críticos y oportunidades (Análisis cualitativo)")
a_inf5=st.text_area("A-Inferior 5","Diseña respuestas policiales diferenciadas (prevención/disuasión)")
a_inf6=st.text_area("A-Inferior 6","Presenta avance de cumplimiento de órdenes y coordinación interinstitucional")
nw=st.slider("Ancho cajas Nodos (px)",360,560,420,10); ng=st.slider("Separación Nodos (px)",40,140,70,5)

# Reiterada (3 carriles)
st.markdown("### Conducta delictiva reiterada (integrado)")
lane1=st.text_input("Carril 1","Asesor(a) legal de la Dirección Regional")
lane2=st.text_input("Carril 2","Oficial de Operaciones de la Dirección Regional")
lane3=st.text_input("Carril 3","Agente de Operaciones de la Delegación Policial")
r1=st.text_area("R1","Realiza el estudio de antecedentes judiciales a cada objetivo priorizado ante el Ministerio Público")
r2=st.text_area("R2","Elabora la ficha de personas con conducta delictiva reiterada")
r3=st.text_area("R3","Remite las fichas a la oficina de operaciones regional para su distribución")
r4=st.text_area("R4","Participa y presenta las fichas en la reunión EDO de Planificación/Testeo (primer nivel)")
rm1=st.text_area("RM1","Envía las fichas a las oficinas de operaciones de las Delegaciones Policiales")
rm2=st.text_area("RM2","Incluye las fichas como documentación para la reunión EDO (primer nivel)")
rb1=st.text_area("RB1","Incluye las fichas como documentación para la reunión EDO (segundo nivel)")
rw=st.slider("Ancho cajas Reiterada (px)",360,520,420,10); rg=st.slider("Separación Reiterada (px)",40,120,70,5)

# ---------- Render ----------
def render()->bytes:
    H=BASE_H+H_NODOS+H_REIT
    img=PIL.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    d.rectangle([20,20,W-20,H-20],outline=BORDER,width=3)
    d.text((W//2,50),"Modelo Preventivo de Gestión Policial – Proyecto Integrado",font=FONT_T,fill=BLUE,anchor="mm")

    # ----- Principal -----
    cx=W//2; y0=120; vgap=130; bw=480; pad=22
    def center_box(x,y,w,text,min_h=78):
        h=h_for_text(d,text,FONT,w-30, pad_v=pad, min_h=min_h)
        return [x-w//2, y-h//2, x+w//2, y+h//2], h

    r_inicio,h= center_box(cx,y0,bw,f"INICIO\n{t_inicio}",min_h=96)
    oval(d,r_inicio); draw_text_center(d,f"INICIO\n{t_inicio}",r_inicio)
    r1,h1= center_box(cx,y0+vgap,bw,b1)
    rrect(d,r1); draw_text_center(d,b1,r1)
    r2,h2= center_box(cx,y0+vgap*2,bw,b2)
    rrect(d,r2); draw_text_center(d,b2,r2)
    r3,h3= center_box(cx,y0+vgap*3,bw,b3)
    rrect(d,r3); draw_text_center(d,b3,r3)
    # rombo fijo ancho 520, alto 124
    r_dec=[cx-260, y0+vgap*4-62, cx+260, y0+vgap*4+62]
    diamond(d,r_dec); draw_text_center(d,q_dec,r_dec)
    r_fin,_= center_box(cx,y0+vgap*8+60,560,f"FIN\n{t_fin}",min_h=104)
    oval(d,r_fin); draw_text_center(d,f"FIN\n{t_fin}",r_fin)

    def top_pt(r):   return ((r[0]+r[2])//2, r[1]-HEAD_CLEAR)
    def bot_pt(r):   return ((r[0]+r[2])//2, r[3]+SAFE)
    def left_pt(r):  return (r[0]-HEAD_CLEAR, (r[1]+r[3])//2)
    def right_pt(r): return (r[2]+HEAD_CLEAR, (r[1]+r[3])//2)

    for a,b in [(r_inicio,r1),(r1,r2),(r2,r3)]:
        arrow(d, bot_pt(a), top_pt(b))
    arrow(d, bot_pt(r3), top_pt(r_dec))
    arrow(d, ((r_dec[0]+r_dec[2])//2, r_dec[3]+SAFE), top_pt(r_fin))

    # Rama SÍ / NO (auto altura)
    rx=cx+620; lx=cx-620; w_si=int(ancho_si)
    y_dec=(r_dec[1]+r_dec[3])//2 + start_offset
    chain_si=[s1,s2,s3,s4,s5,s6,s7,s8]
    rs=[]; yy=y_dec
    for i,txt in enumerate(chain_si):
        h_box=h_for_text(d,txt,FONT,w_si-30, pad_v=18, min_h=78 if i!=4 else 140)
        r=[rx-w_si//2, yy-h_box//2, rx+w_si//2, yy+h_box//2]
        rrect(d,r); draw_text_center(d,txt,r); rs.append(r)
        if i>0: arrow(d, ( (rs[i-1][0]+rs[i-1][2])//2, rs[i-1][3]+SAFE ), ( (r[0]+r[2])//2, r[1]-SAFE ))
        yy += 110 if i<4 else 100  # compacidad visible; ya no se solapa

    chain_no=[n1,n2,n3]; rn=[]
    yy=y_dec
    for i,txt in enumerate(chain_no):
        h_box=h_for_text(d,txt,FONT,w_si-30, pad_v=18)
        r=[lx-w_si//2, yy-h_box//2, lx+w_si//2, yy+h_box//2]
        rrect(d,r); draw_text_center(d,txt,r); rn.append(r)
        if i>0: arrow(d, ( (rn[i-1][0]+rn[i-1][2])//2, rn[i-1][3]+SAFE ), ( (r[0]+r[2])//2, r[1]-SAFE ))
        yy += 110

    # Decisión → SÍ/NO (con rótulo en medio)
    p_dec=( (r_dec[0]+r_dec[2])//2, (r_dec[1]+r_dec[3])//2 )
    p_si=(rs[0][0]-HEAD_CLEAR, (rs[0][1]+rs[0][3])//2)
    p_no=(rn[0][2]+HEAD_CLEAR, (rn[0][1]+rn[0][3])//2)
    orth(d, right_pt(r_dec), p_si, via_y=p_si[1]); label_mid(d, right_pt(r_dec), p_si, "Sí")
    orth(d, left_pt(r_dec),  p_no, via_y=p_no[1]);  label_mid(d, left_pt(r_dec),  p_no, "No")

    # Retroalimentación externa (rail a la derecha)
    rail_x=min(W-40, rs[-1][2] + int(retro_gap))
    start=(rs[-1][2]+SAFE, (rs[-1][1]+rs[-1][3])//2)
    end=(r2[2]+HEAD_CLEAR, (r2[1]+r2[3])//2)
    orth(d, start, (rail_x, start[1]), via_x=rail_x)
    arrow(d, (rail_x,(r2[1]+r2[3])//2), end)
    d.text((rail_x-10, (start[1]+(r2[1]+r2[3])//2)//2), "Retroalimentación", font=FONT_S, fill=BLUE, anchor="rm")

    # ----- NODOS (SÍ-1 → Nodos → SÍ-3) -----
    topA=r_fin[3]+110
    d.text((W//2, topA-40), "Focalización por Nodos Demandantes (Proc. 1.4 – parte 1)", font=FONT_SUB, fill=BLUE, anchor="mm")
    bw=nw; gap=ng; bh=92
    left, right = 80, W-80

    tot=4*bw+3*gap; sx = left + max(0,(right-left-tot)//2); y_sup=topA+120
    sup_txt=[a_sup1,a_sup2,a_sup3,a_sup4]; sup=[]
    for i,txt in enumerate(sup_txt):
        h=h_for_text(d,txt,FONT,bw-30, min_h=bh)
        cx= sx + i*(bw+gap) + bw//2
        r=[cx-bw//2,y_sup-h//2,cx+bw//2,y_sup+h//2]
        rrect(d,r); draw_text_center(d,txt,r); sup.append(r)
        if i>0: arrow(d,(sup[i-1][2]+SAFE,y_sup),(r[0]-SAFE,y_sup))
    # riel superior
    y_rail=y_sup - (sup[0][3]-sup[0][1])//2 - 40
    arrow(d,(sup[-1][2],y_rail),(sup[-1][2],y_sup-(sup[-1][3]-sup[-1][1])//2-6))
    d.line([(sup[0][0],y_rail),(sup[-1][2],y_rail)],fill=BLUE,width=4)

    tot2=6*bw+5*gap; sx2=left+max(0,(right-left-tot2)//2); y_inf=y_sup+220
    inf_txt=[a_inf1,a_inf2,a_inf3,a_inf4,a_inf5,a_inf6]; inf=[]
    for i,txt in enumerate(inf_txt):
        h=h_for_text(d,txt,FONT,bw-30, min_h=bh)
        cx=sx2 + i*(bw+gap) + bw//2
        r=[cx-bw//2,y_inf-h//2,cx+bw//2,y_inf+h//2]
        rrect(d,r); draw_text_center(d,txt,r); inf.append(r)
        if i>0: arrow(d,(inf[i-1][2]+SAFE,y_inf),(r[0]-SAFE,y_inf))
    # verticales puntuales
    arrow(d, ( (sup[1][0]+sup[1][2])//2, sup[1][3]+SAFE ), ( (inf[0][0]+inf[0][2])//2, inf[0][1]-SAFE ))
    arrow(d, ( (sup[2][0]+sup[2][2])//2, sup[2][3]+SAFE ), ( (inf[2][0]+inf[2][2])//2, inf[2][1]-SAFE ))

    # Conectores de integración
    #   SÍ-1 → primer sup de nodos (corredor x fijo)
    corridor_l = rs[0][2]+60
    orth(d, (rs[0][2]+SAFE,(rs[0][1]+rs[0][3])//2),
            (sup[0][0]-SAFE,y_sup), via_x=corridor_l)
    #   último inf de nodos → SÍ-3
    corridor_r = rs[2][0]-60
    orth(d, (inf[-1][2]+SAFE,y_inf), (rs[2][0]-SAFE,(rs[2][1]+rs[2][3])//2), via_x=corridor_r)

    # ----- REITERADA (SÍ-6 → Reiterada → SÍ-7) -----
    topB=y_inf + (inf[0][3]-inf[0][1])//2 + 120
    d.text((W//2, topB-40), "Conducta delictiva reiterada", font=FONT_SUB, fill=BLUE, anchor="mm")
    lane_h=220; lane_gap=24; lane_w=42
    lane_left=60; lane_right=W-40

    for i,title in enumerate([lane1,lane2,lane3]):
        y0=topB + i*(lane_h+lane_gap); y1=y0+lane_h
        d.rectangle([lane_left,y0,lane_right,y1],outline=BORDER,width=2)
        paste_lane_label(img,(lane_left,y0,lane_left+lane_w,y1),title)

    bw=rw; gap=rg; bh=92
    left = lane_left+lane_w+24; right=lane_right-24

    # fila superior (4 cajas + FIN)
    total=4*bw+3*gap; sx=left+max(0,(right-left-total)//2)
    y_s=topB + lane_h//2
    supB=[]; supB_txt=[r1,r2,r3,r4]
    for i,txt in enumerate(supB_txt):
        h=h_for_text(d,txt,FONT,bw-30,min_h=bh)
        cx=sx + i*(bw+gap) + bw//2
        r=[cx-bw//2,y_s-h//2,cx+bw//2,y_s+h//2]
        rrect(d,r); draw_text_center(d,txt,r); supB.append(r)
        if i>0: arrow(d,(supB[i-1][2]+SAFE,y_s),(r[0]-SAFE,y_s))
    fin_w, fin_h = 120, 56
    fin=[supB[-1][2]+90-fin_w//2, y_s-fin_h//2, supB[-1][2]+90+fin_w//2, y_s+fin_h//2]
    oval(d,fin); draw_text_center(d,"FIN",fin)
    arrow(d,(supB[-1][2]+SAFE,y_s),(fin[0]-SAFE,y_s))

    # fila media (2)
    y_m=topB + lane_h + lane_gap + lane_h//2
    mid=[]
    for i,txt in enumerate([rm1,rm2]):
        h=h_for_text(d,txt,FONT,bw-30,min_h=bh)
        cx=sx + bw//2 + i*(bw+gap*1.2) + (bw+gap)*0.5
        r=[int(cx-bw//2),y_m-h//2,int(cx+bw//2),y_m+h//2]
        rrect(d,r); draw_text_center(d,txt,r); mid.append(r)
    arrow(d,(mid[0][2]+SAFE,y_m),(mid[1][0]-SAFE,y_m))
    # sup3 ↓ mid1 ; mid2 ↑ sup4
    arrow(d,(((supB[2][0]+supB[2][2])//2, supB[2][3]+SAFE)),
             (((mid[0][0]+mid[0][2])//2, mid[0][1]-SAFE)))
    orth(d, (((mid[1][0]+mid[1][2])//2, mid[1][1]-SAFE)),
             (((supB[3][0]+supB[3][2])//2, supB[3][1]-SAFE)), via_x=mid[1][0])

    # fila inferior (1)
    y_i=topB + 2*(lane_h+lane_gap) + lane_h//2
    h=h_for_text(d,rb1,FONT,bw-30,min_h=bh)
    inf=[int(sx + (bw+gap)*1.2)-bw//2, y_i-h//2, int(sx + (bw+gap)*1.2)+bw//2, y_i+h//2]
    rrect(d,inf); draw_text_center(d,rb1,inf)
    # mid1 ↓ inf ; inf ↗ mid2 (ortogonal)
    arrow(d,(((mid[0][0]+mid[0][2])//2, mid[0][3]+SAFE)),
             (((inf[0]+inf[2])//2, inf[1]-SAFE)))
    orth(d,(((inf[0]+inf[2])//2, inf[1]-SAFE-20)),
            (((mid[1][0]+mid[1][2])//2, mid[1][3]+SAFE+20)),
            via_x=mid[1][0])

    # Integración con el principal (SÍ-6 → Reiterada → SÍ-7)
    orth(d,(rs[5][2]+SAFE, (rs[5][1]+rs[5][3])//2),
            (supB[0][0]-SAFE, y_s), via_x=rs[5][2]+60)
    orth(d,(fin[2]+SAFE, y_s),
            (rs[6][0]-SAFE, (rs[6][1]+rs[6][3])//2),
            via_x=rs[6][0]-60)

    # PNG
    out=io.BytesIO(); img.save(out,format="PNG"); return out.getvalue()

# ---------- Export ----------
png=render()
pdf_io=io.BytesIO(); PIL.open(io.BytesIO(png)).convert("RGB").save(pdf_io,format="PDF")
pptx=Presentation(); s=pptx.slides.add_slide(pptx.slide_layouts[6])
s.shapes.add_picture(io.BytesIO(png), Inches(0.2), Inches(0.2), width=Inches(9.6))
ppt_io=io.BytesIO(); pptx.save(ppt_io)

st.image(png, use_column_width=True)
c1,c2,c3=st.columns(3)
with c1: st.download_button("⬇️ PNG", png, "mpgp_integrado.png", "image/png")
with c2: st.download_button("⬇️ PDF", pdf_io.getvalue(), "mpgp_integrado.pdf", "application/pdf")
with c3: st.download_button("⬇️ PPTX", ppt_io.getvalue(), "mpgp_integrado.pptx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation")

