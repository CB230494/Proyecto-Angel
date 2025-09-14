# ===========================================
# MPGP – Lienzo libre con paleta de símbolos
# Arrastra/acomoda tú. Incluye textos de plantilla.
# Exporta PNG y JSON (para reabrir).
# ===========================================

import io
import json
from typing import Any, Dict

import streamlit as st
from PIL import Image

# --- Autoinstalación del lienzo si falta el paquete ---
import sys, subprocess
try:
    from streamlit_drawable_canvas import st_canvas
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-drawable-canvas==0.9.3"])
    from streamlit_drawable_canvas import st_canvas


# ----------------------- Utilidades -----------------------
def _sx(x) -> str:
    """Devuelve siempre str (evita None)."""
    return "" if x is None else str(x)


def fabric_group(shape: Dict[str, Any], text: str, left: int, top: int,
                 w: int, h: int, font_size: int = 18) -> Dict[str, Any]:
    """Crea un grupo FabricJS (forma + textbox) centrado en (left, top)."""
    textbox = {
        "type": "textbox",
        "left": 12,                  # relativo al grupo
        "top": -h // 2 + 12,         # relativo al grupo
        "width": max(60, w - 24),
        "text": _sx(text),
        "fontSize": font_size,
        "fill": "#1f1f1f",
        "textAlign": "center",
        "fontFamily": "DejaVu Sans, Arial",
        "editable": True,
    }
    return {
        "type": "group",
        "left": left,
        "top": top,
        "originX": "center",
        "originY": "center",
        "objects": [shape, textbox],
        "selectable": True,
    }


# ------- Formas básicas (estética MPGP) -------
def shape_proceso(w: int, h: int,
                  stroke="#1f4e79", fill="#ffffff", radius=22) -> Dict[str, Any]:
    return {
        "type": "rect",
        "left": -w // 2, "top": -h // 2, "width": w, "height": h,
        "rx": radius, "ry": radius,
        "fill": fill, "stroke": stroke, "strokeWidth": 3,
    }


def shape_terminador(w: int, h: int,
                     stroke="#1f4e79", fill="#dcebf7") -> Dict[str, Any]:
    return {
        "type": "ellipse",
        "left": -w // 2, "top": -h // 2, "rx": w // 2, "ry": h // 2,
        "fill": fill, "stroke": stroke, "strokeWidth": 3,
    }


def shape_decision(w: int, h: int,
                   stroke="#1f4e79", fill="#fff8e1") -> Dict[str, Any]:
    return {
        "type": "polygon",
        "left": -w // 2, "top": -h // 2,
        "points": [
            {"x": 0, "y": -h // 2},
            {"x":  w // 2, "y": 0},
            {"x": 0, "y":  h // 2},
            {"x": -w // 2, "y": 0},
        ],
        "fill": fill, "stroke": stroke, "strokeWidth": 3,
    }


def shape_datos(w: int, h: int,
                stroke="#1f4e79", fill="#ffffff", skew=20) -> Dict[str, Any]:
    return {
        "type": "polygon",
        "left": -w // 2, "top": -h // 2,
        "points": [
            {"x": -w // 2 + skew, "y": -h // 2},
            {"x":  w // 2,        "y": -h // 2},
            {"x":  w // 2 - skew, "y":  h // 2},
            {"x": -w // 2,        "y":  h // 2},
        ],
        "fill": fill, "stroke": stroke, "strokeWidth": 3,
    }


def shape_conector(r=12, stroke="#1f4e79", fill="#ffffff") -> Dict[str, Any]:
    return {
        "type": "circle", "left": -r, "top": -r, "radius": r,
        "fill": fill, "stroke": stroke, "strokeWidth": 3,
    }


def add_symbol(tipo: str, texto: str, w: int, h: int, left: int, top: int) -> Dict[str, Any]:
    if tipo == "Inicio/Fin (óvalo)":
        return fabric_group(shape_terminador(w, h), texto, left, top, w, h, 18)
    if tipo == "Proceso (rectángulo redondeado)":
        return fabric_group(shape_proceso(w, h), texto, left, top, w, h, 18)
    if tipo == "Decisión (rombo)":
        return fabric_group(shape_decision(w, h), texto, left, top, w, h, 18)
    if tipo == "Datos (paralelogramo)":
        return fabric_group(shape_datos(w, h), texto, left, top, w, h, 18)
    if tipo == "Conector (círculo)":
        return fabric_group(shape_conector(), texto, left, top, 80, 40, 16)
    if tipo == "Texto suelto":
        return {
            "type": "textbox",
            "left": left, "top": top, "originX": "center", "originY": "center",
            "width": w, "text": _sx(texto), "fontSize": 18,
            "fill": "#1f1f1f", "textAlign": "center",
            "fontFamily": "DejaVu Sans, Arial", "editable": True,
        }
    # Fallback
    return fabric_group(shape_proceso(w, h), texto, left, top, w, h, 18)


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


# ----------------------- Página -----------------------
st.set_page_config(page_title="MPGP – Canvas libre", layout="wide")
st.title("MPGP – Lienzo libre (símbolos + textos)")
st.caption("Arrastra y conéctalo como quieras. Exporta PNG y guarda/recupera JSON del diagrama.")

# Estado inicial del canvas
if "fabric_json" not in st.session_state:
    st.session_state.fabric_json = {"version": "5.2.4", "objects": []}


# ----------------------- Sidebar: paleta -----------------------
with st.sidebar:
    st.header("Paleta de símbolos")

    tipo = st.selectbox("Tipo de símbolo", [
        "Proceso (rectángulo redondeado)",
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

    # Sugerencias de tamaño por tipo
    W_default = 420 if "rectángulo" in tipo or "paralelogramo" in tipo else 520 if "rombo" in tipo else 480
    H_default = 92 if "rectángulo" in tipo or "paralelogramo" in tipo else 120 if "rombo" in tipo else 80

    w_box = st.number_input("Ancho", 120, 900, W_default, 10)
    h_box = st.number_input("Alto",   40,  300, H_default, 5)
    left  = st.number_input("X (posición)", 50, 3000, 300, 10)
    top   = st.number_input("Y (posición)", 50, 3000, 200, 10)

    texto = manual if txt_src == "Escribir manual" or txt_src.startswith("—") else txt_src

    if st.button("➕ Agregar al lienzo", use_container_width=True):
        obj = add_symbol(tipo, texto, int(w_box), int(h_box), int(left), int(top))
        st.session_state.fabric_json["objects"].append(obj)

    st.divider()
    st.subheader("Plantillas rápidas")
    if st.button("Cargar SOLO textos del principal (objetos sueltos)"):
        x, y = 300, 200
        for t in PLANTILLA_PRINCIPAL:
            t_tipo = ("Decisión (rombo)" if "¿Se identifican" in t else
                      "Inicio/Fin (óvalo)" if t.startswith("INICIO") or t.startswith("FIN") else
                      "Proceso (rectángulo redondeado)")
            st.session_state.fabric_json["objects"].append(
                add_symbol(t_tipo, t, 520 if "INICIO" in t or "FIN" in t else 480,
                           120 if "¿Se identifican" in t else 92, x, y)
            )
            y += 120

    if st.button("Vaciar lienzo"):
        st.session_state.fabric_json = {"version": "5.2.4", "objects": []}

    st.divider()
    st.subheader("Guardar / Cargar")
    st.download_button(
        "⬇️ Descargar JSON del diagrama",
        data=json.dumps(st.session_state.fabric_json, ensure_ascii=False).encode("utf-8"),
        file_name="mpgp_diagrama.json",
        mime="application/json",
    )
    up = st.file_uploader("Cargar JSON (reabre un diagrama)", type=["json"])
    if up:
        try:
            st.session_state.fabric_json = json.loads(up.read().decode("utf-8"))
            st.success("JSON cargado correctamente.")
        except Exception as e:
            st.error(f"JSON inválido: {e}")


# ----------------------- Herramientas (ES) + Canvas -----------------------
st.markdown("### Lienzo")

# Etiquetas ES → códigos que espera el canvas
tool_labels = {
    "Transformar (mover/seleccionar)": "transform",
    "Rectángulo": "rect",
    "Círculo": "circle",
    "Línea": "line",
    "Flecha": "arrow",
    "Texto": "text",
    "Polígono": "polygon",
}

col_canvas, col_opts = st.columns([4, 1])

with col_opts:
    opcion = st.radio("Herramienta", list(tool_labels.keys()), index=0)
    drawing_mode = tool_labels[opcion]

    stroke_width = st.slider("Grosor de línea", 1, 10, 3)
    stroke_color = st.color_picker("Color de línea", "#1f4e79")
    fill_color   = st.color_picker("Relleno", "#ffffff")
    bg_color     = st.color_picker("Fondo del lienzo", "#f7faff")

    height = st.number_input("Alto del lienzo", 600, 3000, 1200, 50)
    width  = st.number_input("Ancho del lienzo", 800,  3000, 1800, 50)

    st.caption("Tip: usa **Flecha** para conectores. Con **Transformar** puedes mover, redimensionar y rotar.")

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
        key="canvas_es",
    )

# Guardamos estado si hubo cambios
if result.json_data is not None:
    st.session_state.fabric_json = result.json_data

# ----------------------- Exportar PNG -----------------------
st.markdown("### Exportar")
if result.image_data is not None:
    img = Image.fromarray(result.image_data.astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button("⬇️ Descargar PNG del lienzo", data=buf.getvalue(),
                       file_name="mpgp_canvas.png", mime="image/png")
else:
    st.info("Dibuja o agrega símbolos para habilitar la exportación a PNG.")

