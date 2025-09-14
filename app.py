# ===========================================
# MPGP – Lienzo libre PREARMADO (editable)
# - Carga una plantilla base ya ordenada
# - Puedes mover, borrar, redimensionar y agregar símbolos
# - Exporta PNG y guarda/carga JSON
# ===========================================

import io, json, sys, subprocess
from typing import Any, Dict, List

import streamlit as st
from PIL import Image

# --- Autoinstalación del lienzo si no está ---
try:
    from streamlit_drawable_canvas import st_canvas
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-drawable-canvas==0.9.3"])
    from streamlit_drawable_canvas import st_canvas


# ------------------ Utilidades FabricJS ------------------
def _sx(x) -> str:
    return "" if x is None else str(x)

def shape_proceso(w: int, h: int, stroke="#1f4e79", fill="#ffffff", radius=22) -> Dict[str, Any]:
    return {"type":"rect","left":-w//2,"top":-h//2,"width":w,"height":h,"rx":radius,"ry":radius,
            "fill":fill,"stroke":stroke,"strokeWidth":3}

def shape_terminador(w: int, h: int, stroke="#1f4e79", fill="#dcebf7") -> Dict[str, Any]:
    return {"type":"ellipse","left":-w//2,"top":-h//2,"rx":w//2,"ry":h//2,
            "fill":fill,"stroke":stroke,"strokeWidth":3}

def shape_decision(w: int, h: int, stroke="#1f4e79", fill="#fff8e1") -> Dict[str, Any]:
    return {"type":"polygon","left":-w//2,"top":-h//2,
            "points":[{"x":0,"y":-h//2},{"x":w//2,"y":0},{"x":0,"y":h//2},{"x":-w//2,"y":0}],
            "fill":fill,"stroke":stroke,"strokeWidth":3}

def shape_datos(w: int, h: int, stroke="#1f4e79", fill="#ffffff", skew=20) -> Dict[str, Any]:
    return {"type":"polygon","left":-w//2,"top":-h//2,
            "points":[{"x":-w//2+skew,"y":-h//2},{"x":w//2,"y":-h//2},
                      {"x":w//2-skew,"y":h//2},{"x":-w//2,"y":h//2}],
            "fill":fill,"stroke":stroke,"strokeWidth":3}

def fabric_group(shape: Dict[str, Any], text: str, left: int, top: int,
                 w: int, h: int, font_size: int = 18) -> Dict[str, Any]:
    textbox = {"type":"textbox","left":12,"top":-h//2+12,"width":max(60,w-24),
               "text":_sx(text),"fontSize":font_size,"fill":"#1f1f1f",
               "textAlign":"center","fontFamily":"DejaVu Sans, Arial","editable":True}
    return {"type":"group","left":left,"top":top,"originX":"center","originY":"center",
            "objects":[shape, textbox],"selectable":True}

def add_symbol(tipo: str, texto: str, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
    if tipo=="oval":   return fabric_group(shape_terminador(w,h),texto,x,y,w,h,18)
    if tipo=="rect":   return fabric_group(shape_proceso(w,h),texto,x,y,w,h,18)
    if tipo=="diamond":return fabric_group(shape_decision(w,h),texto,x,y,w,h,18)
    if tipo=="para":   return fabric_group(shape_datos(w,h),texto,x,y,w,h,18)
    # fallback
    return fabric_group(shape_proceso(w,h),texto,x,y,w,h,18)

def line(x1,y1,x2,y2,color="#1f4e79",w=3) -> Dict[str, Any]:
    return {"type":"line","x1":x1,"y1":y1,"x2":x2,"y2":y2,
            "stroke":color,"strokeWidth":w, "selectable":True}

# ------------------ Plantilla de textos ------------------
TXT = {
"INICIO":"INICIO\nPlanificación preventiva anual",
"B1":"Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)",
"B2":"Apreciación situacional del territorio\n(Procedimiento 1.2)",
"B3":"Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",
"DEC":"¿Se identifican riesgos prioritarios?",
"NO1":"Patrullaje rutinario y vigilancia continua",
"NO2":"Registro de factores menores en RAP",
"NO3":"Integración al análisis situacional",
"SI1":"Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
"SI2":"Construcción de líneas de acción preventivas\n(Procedimiento 2.3)",
"SI3":"Planificación de programas policiales preventivos\n(Procedimiento 2.4)",
"SI4":"Elaboración de órdenes de servicio para operativos",
"SI5":"Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
"SI6":"Reporte de operativos (RAP, DATAPOL, informes)",
"SI7":"Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
"SI8":"Retroalimentación a la planificación preventiva",
"FIN":"FIN\nEvaluación global de resultados\n(Indicadores, metas, impacto – 3.3)",
# Nodos
"A1":"Convoca a reunión EDO de segundo nivel con plantillas diferenciadas",
"A2":"Verifica insumos mínimos para análisis (capas, encuestas, informes)",
"A3":"Completa la Matriz de Nodos demandantes priorizados",
"A4":"Elabora órdenes de servicio para evidencia y monitoreo",
"A5":"Abre el SIG para visualizar y mapear la información de nodos",
"A6":"Selecciona capas de información disponibles en el SIG",
"A7":"Presenta factores de riesgo críticos y variaciones del mes anterior",
"A8":"Analiza puntos críticos y oportunidades (Análisis cualitativo)",
# Reiterada
"R1":"Realiza el estudio de antecedentes judiciales ante el Ministerio Público",
"R2":"Elabora la ficha de personas con conducta delictiva reiterada",
"R3":"Remite fichas a la oficina de operaciones regional para su distribución",
"R4":"Participa y presenta fichas en la reunión EDO de planificación/testeo (primer nivel)",
"RM1":"Envía fichas a oficinas de operaciones de las Delegaciones Policiales",
"RM2":"Incluye fichas como documentación para la reunión EDO (primer nivel)",
"RB1":"Incluye fichas como documentación para la reunión EDO (segundo nivel)",
}

# ------------------ Plantilla PREARMADA ------------------
def plantilla_base(canvas_w=1800, canvas_h=1400) -> Dict[str, Any]:
    objs: List[Dict[str, Any]] = []
    # coordenadas base
    cx = canvas_w//2
    x_no = 420
    x_si = canvas_w - 420
    w_rect = 520; h_rect = 92
    y = 180; step = 140

    # Centro
    def add(kind, txt, x, y, w=w_rect, h=h_rect):
        objs.append(add_symbol(kind, txt, x, y, w, h))
        return w, h

    add("oval",   TXT["INICIO"], cx, y-60, 520, 84)
    add("rect",   TXT["B1"], cx, y+80)
    add("rect",   TXT["B2"], cx, y+80+step)
    add("rect",   TXT["B3"], cx, y+80+step*2)
    add("diamond",TXT["DEC"], cx, y+80+step*3, 560, 120)
    fin_w, fin_h = 560, 100
    add("oval",   TXT["FIN"], cx, y+80+step*3 + 460, fin_w, fin_h)

    # NO (alineado a la izquierda)
    y_no = y+20
    add("rect", TXT["NO1"], x_no, y_no, w_rect, h_rect)
    add("rect", TXT["NO2"], x_no, y_no+step, w_rect, h_rect)
    add("rect", TXT["NO3"], x_no, y_no+step*2, w_rect, h_rect)

    # SI (columna derecha)
    y_si = y-10
    add("rect", TXT["SI1"], x_si, y_si, w_rect, h_rect)
    add("rect", TXT["SI2"], x_si, y_si+step, w_rect, h_rect)
    add("rect", TXT["SI3"], x_si, y_si+step*2, w_rect, h_rect)
    add("rect", TXT["SI4"], x_si, y_si+step*3, w_rect, h_rect)
    add("rect", TXT["SI5"], x_si, y_si+step*4+10, w_rect, 150)
    add("rect", TXT["SI6"], x_si, y_si+step*5+40, w_rect, h_rect)
    add("rect", TXT["SI7"], x_si, y_si+step*6+70, w_rect, h_rect)
    add("rect", TXT["SI8"], x_si, y_si+step*7+100, w_rect, h_rect)

    # Nodos Demandantes (2 filas)
    y_nd_title = y+80+step*3 + 250
    objs.append({"type":"textbox","left":canvas_w//2,"top":y_nd_title,
                 "originX":"center","originY":"center","width":900,
                 "text":"Focalización por Nodos Demandantes (Proc. 1.4 – parte 1)",
                 "fontSize":22,"fill":"#1f4e79","textAlign":"center"})

    bw, bh, gap = 420, 92, 70
    y_sup = y_nd_title + 80
    x0 = 140
    for i, key in enumerate(["A1","A2","A3","A4"]):
        add("rect", TXT[key], x0 + i*(bw+gap), y_sup, bw, bh)
    y_inf = y_sup + 180
    for i, key in enumerate(["A5","A6","A7","A8"]):
        add("rect", TXT[key], x0 + i*(bw+gap), y_inf, bw, bh)

    # Conducta Reiterada (3 carriles con cajas)
    y_r_title = y_inf + 220
    objs.append({"type":"textbox","left":canvas_w//2,"top":y_r_title,
                 "originX":"center","originY":"center","width":700,
                 "text":"Conducta delictiva reiterada","fontSize":22,
                 "fill":"#1f4e79","textAlign":"center"})

    lane_left, lane_right = 80, canvas_w-80
    lane_h, lane_gap = 200, 24
    lane_w = lane_right - lane_left
    for i, titulo in enumerate(["Asesor(a) legal de la Dirección Regional",
                                "Oficial de Operaciones de la Dirección Regional",
                                "Agente de Operaciones de la Delegación Policial"]):
        y0 = y_r_title + 40 + i*(lane_h+lane_gap)
        y1 = y0 + lane_h
        objs.append({"type":"rect","left":lane_left,"top":y0,"width":lane_w,"height":lane_h,
                     "fill":"rgba(0,0,0,0)","stroke":"#9bbbd9","strokeWidth":2,"originX":"left","originY":"top"})
        # etiqueta vertical (texto simple en lateral)
        objs.append({"type":"textbox","left":lane_left+16,"top":(y0+y1)//2,
                     "originX":"left","originY":"center","angle":-90,"width":lane_h-20,
                     "text":titulo,"fontSize":16,"fill":"#1f4e79","textAlign":"center"})

    # Cajas de Reiterada
    y_sup = y_r_title + 40 + lane_h//2
    x_start = 260
    add("rect", TXT["R1"], x_start, y_sup, 420, 92)
    add("rect", TXT["R2"], x_start+ (420+90), y_sup, 420, 92)
    add("rect", TXT["R3"], x_start+ 2*(420+90), y_sup, 420, 92)
    add("rect", TXT["R4"], x_start+ 3*(420+90), y_sup, 420, 92)

    y_mid = y_sup + lane_h + lane_gap
    add("rect", TXT["RM1"], x_start+ 0.6*(420+90), y_mid, 420, 92)
    add("rect", TXT["RM2"], x_start+ 1.8*(420+90), y_mid, 420, 92)

    y_inf = y_mid + lane_h + lane_gap
    add("rect", TXT["RB1"], x_start+ 1.2*(420+90), y_inf, 420, 92)

    # (Opcional) Algunas líneas guía rectas (sin flecha)
    # Conecta B1->B2->B3->DEC
    objs += [
        line(cx, y+80-30, cx, y+80+30),
        line(cx, y+80+step-30, cx, y+80+step+30),
        line(cx, y+80+2*step-30, cx, y+80+2*step+30),
    ]
    # Desde DEC a SI1 y NO1 (tramos horizontales)
    objs += [
        line(cx+280, y+80+3*step, x_si-300, y_si),
        line(cx-280, y+80+3*step, x_no+300, y_no),
    ]

    return {"version":"5.2.4","objects":objs}


# ------------------ UI ------------------
st.set_page_config(page_title="MPGP – Canvas Prearmado", layout="wide")
st.title("MPGP – Lienzo prearmado (mueve/borra/agrega libremente)")
st.caption("El diagrama ya viene armado. Usa la barra de herramientas para mover, borrar, agregar flechas y nuevas cajas.")

# Estado del lienzo
if "fabric_json" not in st.session_state:
    st.session_state.fabric_json = plantilla_base()

# --------- Paleta simple para agregar más símbolos ----------
with st.sidebar:
    st.header("Agregar símbolo")
    tipo_humano = st.selectbox("Tipo", [
        "Proceso (rectángulo redondeado)",
        "Decisión (rombo)",
        "Inicio/Fin (óvalo)",
        "Datos (paralelogramo)",
        "Texto suelto",
    ])
    tipo = {"Proceso (rectángulo redondeado)":"rect",
            "Decisión (rombo)":"diamond",
            "Inicio/Fin (óvalo)":"oval",
            "Datos (paralelogramo)":"para",
            "Texto suelto":"text"}[tipo_humano]
    texto = st.text_area("Texto del símbolo", "Nuevo proceso")
    w = st.number_input("Ancho", 120, 900, 420, 10)
    h = st.number_input("Alto",   40,  300, 92, 5)
    x = st.number_input("X (posición)", 50, 3000, 300, 10)
    y = st.number_input("Y (posición)", 50, 3000, 200, 10)

    if st.button("➕ Agregar al lienzo", use_container_width=True):
        if tipo=="text":
            obj = {"type":"textbox","left":int(x),"top":int(y),
                   "originX":"center","originY":"center","width":int(w),
                   "text":_sx(texto),"fontSize":18,"fill":"#1f1f1f","textAlign":"center",
                   "fontFamily":"DejaVu Sans, Arial","editable":True}
        else:
            obj = add_symbol(tipo, texto, int(x), int(y), int(w), int(h))
        st.session_state.fabric_json["objects"].append(obj)

    st.divider()
    st.subheader("Plantilla")
    if st.button("🔁 Reiniciar con plantilla base"):
        st.session_state.fabric_json = plantilla_base()
        st.success("Plantilla recargada.")

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


# ------------------ Herramientas en ESPAÑOL ------------------
st.markdown("### Lienzo")
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
    height = st.number_input("Alto del lienzo", 800, 3000, 1600, 50)
    width  = st.number_input("Ancho del lienzo", 1200, 3200, 2000, 50)
    st.caption("Usa **Transformar** para mover/borrar (ícono papelera). Con **Flecha** dibujas conectores.")

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

# Persistimos cambios en tiempo real
if result.json_data is not None:
    st.session_state.fabric_json = result.json_data

# ------------------ Exportar PNG ------------------
st.markdown("### Exportar")
if result.image_data is not None:
    img = Image.fromarray(result.image_data.astype("uint8"))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    st.download_button("⬇️ Descargar PNG del lienzo", data=buf.getvalue(),
                       file_name="mpgp_canvas_prearmado.png", mime="image/png")
else:
    st.info("Dibuja o mueve algo para habilitar la exportación a PNG.")

