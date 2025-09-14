# ===========================================
# MPGP – Lienzo PREARMADO y EDITABLE (Streamlit)
# - Diagrama integrado (principal + Sí/No + Nodos + Reiterada)
# - Mover / borrar / redimensionar / agregar símbolos
# - Exportar PNG y guardar/cargar JSON
# ===========================================
import io, json, sys, subprocess
from typing import Any, Dict, List
import streamlit as st
from PIL import Image

# --- Autoinstalar el lienzo si falta ---
try:
    from streamlit_drawable_canvas import st_canvas
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-drawable-canvas==0.9.3"])
    from streamlit_drawable_canvas import st_canvas

# ---------- helpers de FabricJS ----------
def shape_rect(w:int,h:int,stroke="#1f4e79",fill="#ffffff",radius=22)->Dict[str,Any]:
    return {"type":"rect","left":-w//2,"top":-h//2,"width":w,"height":h,"rx":radius,"ry":radius,
            "fill":fill,"stroke":stroke,"strokeWidth":3}
def shape_oval(w:int,h:int,stroke="#1f4e79",fill="#dcebf7")->Dict[str,Any]:
    return {"type":"ellipse","left":-w//2,"top":-h//2,"rx":w//2,"ry":h//2,
            "fill":fill,"stroke":stroke,"strokeWidth":3}
def shape_diamond(w:int,h:int,stroke="#1f4e79",fill="#fff8e1")->Dict[str,Any]:
    return {"type":"polygon","left":-w//2,"top":-h//2,
            "points":[{"x":0,"y":-h//2},{"x":w//2,"y":0},{"x":0,"y":h//2},{"x":-w//2,"y":0}],
            "fill":fill,"stroke":stroke,"strokeWidth":3}

def group(shape:Dict[str,Any], text:str, x:int, y:int, w:int, h:int, font=18)->Dict[str,Any]:
    tb = {"type":"textbox","left":12,"top":-h//2+12,"width":max(60,w-24),
          "text":text, "fontSize":font, "fill":"#202020",
          "textAlign":"center","fontFamily":"DejaVu Sans, Arial","editable":True}
    return {"type":"group","left":x,"top":y,"originX":"center","originY":"center",
            "objects":[shape,tb],"selectable":True}

def add(tipo:str, texto:str, x:int, y:int, w:int, h:int)->Dict[str,Any]:
    if tipo=="oval":    return group(shape_oval(w,h), texto, x,y,w,h,18)
    if tipo=="rect":    return group(shape_rect(w,h), texto, x,y,w,h,18)
    if tipo=="diamond": return group(shape_diamond(w,h), texto, x,y,w,h,18)
    # fallback
    return group(shape_rect(w,h), texto, x,y,w,h,18)

def line(x1,y1,x2,y2,color="#1f4e79",w=3)->Dict[str,Any]:
    return {"type":"line","x1":x1,"y1":y1,"x2":x2,"y2":y2,"stroke":color,"strokeWidth":w,"selectable":True}

# ---------- plantilla PREARMADA (ordenada y resumida) ----------
def plantilla_base(W=2000,H=1600)->Dict[str,Any]:
    objs:List[Dict[str,Any]]=[]
    cx=W//2; x_no=420; x_si=W-420
    step=140; bw=520; bh=92

    # Centro
    y=180
    objs.append(add("oval","INICIO\nPlanificación preventiva anual",cx,y-60,520,84))
    objs.append(add("rect","Definición y calendarización de Delegaciones\n(Proc. 1.1)",cx,y+80,bw,bh))
    objs.append(add("rect","Apreciación situacional del territorio\n(Proc. 1.2)",cx,y+80+step,bw,bh))
    objs.append(add("rect","Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",cx,y+80+2*step,bw,bh))
    objs.append(add("diamond","¿Se identifican riesgos prioritarios?",cx,y+80+3*step,560,120))
    objs.append(add("oval","FIN\nEvaluación global de resultados\n(Indicadores, metas, impacto – 3.3)",cx,y+80+3*step+420,560,100))

    # NO (izquierda)
    objs.append(add("rect","Patrullaje rutinario y vigilancia continua",x_no,260,bw,bh))
    objs.append(add("rect","Registro de factores menores en RAP",x_no,260+step,bw,bh))
    objs.append(add("rect","Integración al análisis situacional",x_no,260+2*step,bw,bh))

    # SÍ (derecha)
    si_texts=[
        "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
        "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)",
        "Planificación de programas policiales preventivos\n(Procedimiento 2.4)",
        "Elaboración de órdenes de servicio para operativos",
        "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
        "Reporte de operativos (RAP, DATAPOL, informes)",
        "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
        "Retroalimentación a la planificación preventiva",
    ]
    y_si=240
    for i,txt in enumerate(si_texts):
        h = 150 if i==4 else bh
        objs.append(add("rect",txt,x_si,y_si+i*step+(10 if i>=4 else 0),bw,h))

    # Nodos (2x3)
    title_y = y+80+3*step+540
    objs.append({"type":"textbox","left":W//2,"top":title_y,"originX":"center","originY":"center",
                 "width":900,"text":"Focalización por Nodos Demandantes – Resumen (Proc. 1.4)",
                 "fontSize":22,"fill":"#1f4e79","textAlign":"center"})
    nx0=220; gap=80; nbw=420; nbh=100; y1=title_y+70; y2=y1+180
    nodos=[
        ("Convoca reunión EDO (2º nivel)", nx0, y1),
        ("Verifica insumos mínimos (capas, encuestas, informes)", nx0+(nbw+gap), y1),
        ("Completa Matriz de Nodos priorizados", nx0+2*(nbw+gap), y1),
        ("Elabora órdenes de servicio (evidencia/monitoreo)", nx0, y2),
        ("Presenta factores críticos y variaciones del mes anterior", nx0+(nbw+gap), y2),
        ("Analiza puntos críticos y oportunidades (cualitativo)", nx0+2*(nbw+gap), y2),
    ]
    for t,x,yc in nodos:
        objs.append(add("rect",t,x,yc,nbw,nbh))

    # Reiterada (fila 5)
    rtitle_y=y2+220
    objs.append({"type":"textbox","left":W//2,"top":rtitle_y,"originX":"center","originY":"center",
                 "width":700,"text":"Conducta delictiva reiterada – Resumen",
                 "fontSize":22,"fill":"#1f4e79","textAlign":"center"})
    rx0=160; rgap=90; rbw=420; rbh=100; ry=rtitle_y+60
    reiter=[
        "Estudia antecedentes judiciales del objetivo",
        "Elabora ficha de conducta delictiva reiterada",
        "Remite fichas a operaciones regionales",
        "Presenta fichas en reunión EDO (primer nivel)",
        "Documenta para EDO (primer y segundo nivel)",
    ]
    for i,t in enumerate(reiter):
        objs.append(add("rect",t,rx0+i*(rbw+rgap),ry,rbw,rbh))

    return {"version":"5.2.4","objects":objs}

# ---------- UI ----------
st.set_page_config(page_title="MPGP – Diagrama prearmado", layout="wide")
st.title("MPGP – Diagrama integrado (prearmado y editable)")

# Estado
if "fabric_json" not in st.session_state:
    st.session_state.fabric_json = plantilla_base()

# Paleta para agregar símbolos
with st.sidebar:
    st.header("Agregar símbolo")
    tipo_hum = st.selectbox("Tipo", ["Proceso (rect)", "Decisión (rombo)", "Inicio/Fin (óvalo)", "Texto suelto"])
    tipo = {"Proceso (rect)":"rect","Decisión (rombo)":"diamond","Inicio/Fin (óvalo)":"oval","Texto suelto":"text"}[tipo_hum]
    texto = st.text_area("Texto", "Nuevo proceso")
    w = st.number_input("Ancho", 120, 900, 420, 10)
    h = st.number_input("Alto",   40,  300, 92, 5)
    x = st.number_input("Posición X", 50, 3000, 300, 10)
    y = st.number_input("Posición Y", 50, 3000, 200, 10)
    if st.button("➕ Agregar"):
        if tipo=="text":
            obj={"type":"textbox","left":int(x),"top":int(y),"originX":"center","originY":"center",
                 "width":int(w),"text":texto,"fontSize":18,"fill":"#202020","textAlign":"center",
                 "fontFamily":"DejaVu Sans, Arial","editable":True}
        else:
            obj=add(tipo, texto, int(x), int(y), int(w), int(h))
        st.session_state.fabric_json["objects"].append(obj)

    st.divider()
    st.subheader("Guardar / Cargar")
    st.download_button("⬇️ Descargar JSON", data=json.dumps(st.session_state.fabric_json, ensure_ascii=False).encode("utf-8"),
                       file_name="mpgp_diagrama.json", mime="application/json")
    up = st.file_uploader("Cargar JSON", type=["json"])
    if up:
        try:
            st.session_state.fabric_json = json.loads(up.read().decode("utf-8"))
            st.success("Diagrama cargado.")
        except Exception as e:
            st.error(f"JSON inválido: {e}")

# Herramientas (ES)
labels = {
    "Transformar (mover/seleccionar)":"transform",
    "Rectángulo":"rect",
    "Círculo":"circle",
    "Línea":"line",
    "Flecha":"arrow",
    "Texto":"text",
    "Polígono":"polygon",
}
col_canvas, col_opts = st.columns([4,1])
with col_opts:
    tool = st.radio("Herramienta", list(labels.keys()), index=0)
    drawing_mode = labels[tool]
    stroke_width = st.slider("Grosor de línea", 1, 10, 3)
    stroke_color = st.color_picker("Color de línea", "#1f4e79")
    fill_color   = st.color_picker("Relleno", "#ffffff")
    bg_color     = st.color_picker("Fondo del lienzo", "#f7faff")
    height = st.number_input("Alto del lienzo", 900, 3000, 1700, 50)
    width  = st.number_input("Ancho del lienzo", 1200, 3200, 2000, 50)
    st.caption("Con **Transformar** mueves/borras; con **Flecha** dibujas conectores.")

with col_canvas:
    result = st_canvas(
        background_color=bg_color,
        height=int(height),
        width=int(width),
        drawing_mode=drawing_mode,
        stroke_width=int(stroke_width),
        stroke_color=stroke_color,
        fill_color=fill_color,
        update_streamlit=True,
        display_toolbar=True,
        initial_drawing=st.session_state.fabric_json,
        key="canvas_prearmado",
    )

# Persistir cambios
if result.json_data is not None:
    st.session_state.fabric_json = result.json_data

# Exportar
st.markdown("### Exportar")
if result.image_data is not None:
    img = Image.fromarray(result.image_data.astype("uint8"))
    buf_png = io.BytesIO(); img.save(buf_png, format="PNG")
    st.download_button("⬇️ Descargar PNG", data=buf_png.getvalue(),
                       file_name="mpgp_prearmado.png", mime="image/png")

    # PDF opcional (una página)
    buf_pdf = io.BytesIO(); img.convert("RGB").save(buf_pdf, "PDF")
    st.download_button("⬇️ Descargar PDF", data=buf_pdf.getvalue(),
                       file_name="mpgp_prearmado.pdf", mime="application/pdf")
else:
    st.info("Mueve o agrega algo para habilitar la exportación.")
