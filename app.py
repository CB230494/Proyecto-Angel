# ===========================================
# MPGP – Canvas libre con paleta de símbolos
# Arrastra/acomoda tú. Incluye textos de plantilla.
# Exporta PNG y JSON (para reabrir).
# ===========================================
import json
import io
from typing import Dict, List, Any

import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas  # pip install streamlit-drawable-canvas

st.set_page_config(page_title="MPGP – Canvas libre", layout="wide")
st.title("MPGP – Lienzo libre (símbolos + textos)")

# ----------------------- Helpers -----------------------
def _sx(x) -> str:
    return "" if x is None else str(x)

def fabric_group(shape: Dict[str, Any], text: str, left: int, top: int,
                 w: int, h: int, font_size: int = 18) -> Dict[str, Any]:
    """Devuelve un objeto 'group' de FabricJS (shape + textbox)."""
    # Normalizamos coords del texto dentro del grupo
    # Nota: en Fabric las coords internas del grupo son relativas
    tx = 0 + 12
    ty = -h//2 + 12
    textbox = {
        "type": "textbox",
        "left": tx,
        "top": ty,
        "width": w-24,
        "text": _sx(text),
        "fontSize": font_size,
        "fill": "#1f1f1f",
        "textAlign": "center",
        "fontFamily": "DejaVu Sans, Arial",
        "editable": True,
    }
    # Ajustamos 'originX/Y' para mover el grupo desde el centro
    grp = {
        "type": "group",
        "left": left,
        "top": top,
        "originX": "center",
        "originY": "center",
        "objects": [shape, textbox],
        "selectable": True
    }
    return grp

def shape_process(w: int, h: int, stroke="#1f4e79", fill="#ffffff", radius=22) -> Dict[str, Any]:
    return {
        "type": "rect",
        "left": -w//2, "top": -h//2, "width": w, "height": h,
        "rx": radius, "ry": radius,
        "fill": fill, "stroke": stroke, "strokeWidth": 3
    }

def shape_terminator(w: int, h: int, stroke="#1f4e79", fill="#dcebf7") -> Dict[str, Any]:
    # Óvalo
    return {
        "type": "ellipse",
        "left": -w//2, "top": -h//2, "rx": w//2, "ry": h//2,
        "fill": fill, "stroke": stroke, "strokeWidth": 3
    }

def shape_decision(w: int, h: int, stroke="#1f4e79", fill="#fff8e1") -> Dict[str, Any]:
    # Rombo como polígono
    return {
        "type": "polygon",
        "left": -w//2, "top": -h//2,
        "points": [
            {"x": 0, "y": -h//2},
            {"x":  w//2, "y": 0},
            {"x": 0, "y":  h//2},
            {"x": -w//2, "y": 0}
        ],
        "fill": fill, "stroke": stroke, "strokeWidth": 3
    }

def shape_data(w: int, h: int, stroke="#1f4e79", fill="#ffffff", skew=20) -> Dict[str, Any]:
    # Paralelogramo
    return {
        "type": "polygon",
        "left": -w//2, "top": -h//2,
        "points": [
            {"x": -w//2 + skew, "y": -h//2},
            {"x":  w//2,        "y": -h//2},
            {"x":  w//2 - skew, "y":  h//2},
            {"x": -w//2,        "y":  h//2},
        ],
        "fill": fill, "stroke": stroke, "strokeWidth": 3
    }

def shape_connector(r=12, stroke="#1f4e79", fill="#ffffff") -> Dict[str, Any]:
    return {
        "type": "circle", "left": -r, "top": -r, "radius": r,
        "fill": fill, "stroke": stroke, "strokeWidth": 3
    }

def add_symbol(kind: str, text: str, w: int, h: int, left: int, top: int) -> Dict[str, Any]:
    if kind == "Inicio/Fin (óvalo)":
        shp = shape_terminator(w, h)
        return fabric_group(shp, text, left, top, w, h, 18)
    if kind == "Proceso (rect redondeado)":
        shp = shape_process(w, h)
        return fabric_group(shp, text, left, top, w, h, 18)
    if kind == "Decisión (rombo)":
        shp = shape_decision(w, h)
        return fabric_group(shp, text, left, top, w, h, 18)
    if kind == "Datos (paralelogramo)":
        shp = shape_data(w, h)
        return fabric_group(shp, text, left, top, w, h, 18)
    if kind == "Conector (círculo)":
        shp = shape_connector()
        return fabric_group(shp, text, left, top, 80, 40, 16)  # texto corto
    if kind == "Texto suelto":
        return {
            "type": "textbox",
            "left": left, "top": top, "originX": "center", "originY": "center",
            "width": w, "text": _sx(text), "fontSize": 18,
            "fill": "#1f1f1f", "textAlign": "center",
            "fontFamily": "DejaVu Sans, Arial", "editable": True
        }
    # Fallback
    return shape_process(w, h)

# ----------------------- Plantillas de texto -----------------------
PLANTILLA_PRINCIPAL = [
    "INICIO\nPlanificación preventiva anual",
    "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)",
    "Apreciación situacional del territorio\n(Procedimiento 1.2)",
    "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)",
    "¿Se identifican riesgos prioritarios?",
    "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)",
    "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)",
    "Planificación de programas policiales preventivos\n(Procedimiento 2.4)",
    "Elaboración de órdenes de servicio para operativos",
    "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local",
    "Reporte de operativos (RAP, DATAPOL, informes)",
    "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)",
    "Retroalimentación a la planificación preventiva",
    "Patrullaje rutinario y vigilancia continua",
    "Registro de factores menores en RAP",
    "Integración al análisis situacional",
    "FIN\nEvaluación global de resultados\n(Indicadores, metas, impacto – 3.3)",
]

PLANTILLA_NODOS = [
    "Convoca a reunión EDO de segundo nivel con plantillas diferenciadas",
    "Verifica insumos mínimos para análisis (capas, encuestas, informes)",
    "Completa la Matriz de Nodos demandantes priorizados",
    "Elabora órdenes de servicio para evidencia y monitoreo",
    "Abre el SIG para visualizar y mapear la información de nodos",
    "Selecciona capas de información disponibles en el SIG",
    "Presenta factores de riesgo críticos y variaciones del mes anterior",
    "Analiza puntos críticos y oportunidades (Análisis cualitativo)",
]

PLANTILLA_REITERADA = [
    "Realiza el estudio de antecedentes judiciales ante el Ministerio Público",
    "Elabora la ficha de personas con conducta delictiva reiterada",
    "Remite fichas a la oficina de operaciones regional para su distribución",
    "Participa y presenta fichas en la reunión EDO de planificación/testeo (primer nivel)",
    "Envía fichas a oficinas de operaciones de las Delegaciones Policiales",
    "Incluye fichas como documentación para la reunión EDO (primer nivel)",
    "Incluye fichas como documentación para la reunión EDO (segundo nivel)",
]

# ----------------------- Estado -----------------------
if "fabric_json" not in st.session_state:
    st.session_state.fabric_json = {"version":"5.2.4","objects":[]}

# ----------------------- Sidebar: paleta -----------------------
with st.sidebar:
    st.header("Paleta de símbolos")
    kind = st.selectbox("Tipo", [
        "Proceso (rect redondeado)",
        "Decisión (rombo)",
        "Inicio/Fin (óvalo)",
        "Datos (paralelogramo)",
        "Conector (círculo)",
        "Texto suelto",
    ])
    txt_src = st.selectbox("Texto de plantilla (opcional)", [
        "Escribir manual",
        "— Principal —",
        *PLANTILLA_PRINCIPAL,
        "— Nodos —",
        *PLANTILLA_NODOS,
        "— Reiterada —",
        *PLANTILLA_REITERADA,
    ])
    manual = st.text_area("Texto (si eliges 'Escribir manual')", "", height=100)

    W_default = 420 if "Proceso" in kind or "Datos" in kind else 520 if "Decisión" in kind else 480
    H_default = 92 if "Proceso" in kind or "Datos" in kind else 120 if "Decisión" in kind else 80
    w_box = st.number_input("Ancho", 120, 900, W_default, 10)
    h_box = st.number_input("Alto",  40,  300, H_default, 5)
    left = st.number_input("X (posición)", 50, 1900, 300, 10)
    top  = st.number_input("Y (posición)", 50, 1900, 200, 10)

    text_to_use = manual if txt_src == "Escribir manual" or txt_src.startswith("—") else txt_src

    if st.button("➕ Agregar al lienzo", use_container_width=True):
        obj = add_symbol(kind, text_to_use, int(w_box), int(h_box), int(left), int(top))
        st.session_state.fabric_json["objects"].append(obj)

    st.divider()
    st.subheader("Plantillas rápidas")
    if st.button("Cargar SOLO textos del principal (como objetos sueltos)"):
        x,y=300,200
        for t in PLANTILLA_PRINCIPAL:
            st.session_state.fabric_json["objects"].append(
                add_symbol("Proceso (rect redondeado)" if "¿Se identifican" not in t and "INICIO" not in t and "FIN" not in t else
                           ("Decisión (rombo)" if "¿Se identifican" in t else "Inicio/Fin (óvalo)"),
                           t, 480 if "INICIO" not in t and "FIN" not in t else 520, 92 if "¿Se identifican" not in t else 120, x, y)
            )
            y += 120

    if st.button("Vaciar lienzo"):
        st.session_state.fabric_json = {"version":"5.2.4","objects":[]}

    st.divider()
    st.subheader("Guardar / Cargar")
    st.download_button("⬇️ Descargar JSON del diagrama",
        data=json.dumps(st.session_state.fabric_json, ensure_ascii=False).encode("utf-8"),
        file_name="mpgp_diagrama.json", mime="application/json")
    uploaded = st.file_uploader("Cargar JSON (reabre un diagrama)", type=["json"])
    if uploaded:
        try:
            st.session_state.fabric_json = json.loads(uploaded.read().decode("utf-8"))
            st.success("JSON cargado.")
        except Exception as e:
            st.error(f"JSON inválido: {e}")

# ----------------------- Canvas -----------------------
st.markdown("### Lienzo")
col1, col2 = st.columns([4,1])
with col2:
    drawing_mode = st.radio("Herramienta", ["transform","rect","circle","line","arrow","text","polygon"], index=0)
    stroke_width = st.slider("Grosor de línea", 1, 8, 3)
    stroke_color = st.color_picker("Color de línea", "#1f4e79")
    fill_color   = st.color_picker("Relleno", "#ffffff")
    bg_color     = st.color_picker("Fondo del lienzo", "#f7faff")
    height = st.number_input("Alto del lienzo", 600, 2000, 1200, 50)
    width  = st.number_input("Ancho del lienzo", 800, 2400, 1800, 50)
    st.caption("Tip: usa la herramienta **arrow** para tus conectores.")

with col1:
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
        initial_drawing=st.session_state.fabric_json,  # carga los objetos
        key="canvas"
    )

# Si el usuario mueve/edita, guardamos el JSON devuelto por el canvas
if result.json_data is not None:
    st.session_state.fabric_json = result.json_data

# ----------------------- Export PNG -----------------------
st.markdown("### Exportar")
if result.image_data is not None:
    # image_data es un ndarray RGBA; lo convertimos a PNG
    img = Image.fromarray(result.image_data.astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button("⬇️ Descargar PNG del lienzo", data=buf.getvalue(),
                       file_name="mpgp_canvas.png", mime="image/png")
else:
    st.info("Dibuja algo o agrega símbolos para habilitar el PNG.")


