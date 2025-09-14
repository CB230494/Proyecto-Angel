# =========================
# 📊 Diagrama MPGP – Exportador (matplotlib)
# =========================
# - Alineación automática por columnas (izq / centro / der)
# - Flechas curvas para la retroalimentación (evita cruces)
# - Exporta PNG, PDF y PPTX
# - Sin cairo, sin graphviz, sin reportlab (solo matplotlib + Pillow + python-pptx)
# =========================

import io
import textwrap
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import patches
from pptx import Presentation
from pptx.util import Inches
from PIL import Image

# ---------- Estilos / colores ----------
BLUE = "#1F4E79"
BORDER = "#9BBBD9"
LIGHTBLUE = "#DCEBF7"
LIGHTYELLOW = "#FFF8E1"
BLACK = "#000000"
BG = "#F7FAFF"

# ---------- Config Streamlit ----------
st.set_page_config(page_title="Diagrama MPGP – Exportador (matplotlib)", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial (layout limpio)")
st.caption("Genera PNG, PDF y PPTX con columnas alineadas y flechas curvas. Sin dependencias nativas.")

# ---------- Entradas ----------
colA, colB = st.columns(2)
with colA:
    t_inicio = st.text_input("INICIO", "Planificación preventiva anual")
    b1 = st.text_area("Bloque 1", "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)", height=70)
    b2 = st.text_area("Bloque 2", "Apreciación situacional del territorio\n(Procedimiento 1.2)", height=70)
    b3 = st.text_area("Bloque 3", "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)", height=70)
    q_dec = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")

with colB:
    s1 = st.text_area("SÍ 1", "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)", height=70)
    s2 = st.text_area("SÍ 2", "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)", height=70)
    s3 = st.text_area("SÍ 3", "Planificación de programas policiales preventivos\n(Procedimiento 2.4)", height=70)
    s4 = st.text_area("SÍ 4", "Elaboración de órdenes de servicio para operativos", height=70)
    s5 = st.text_area("SÍ 5", "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local", height=90)
    s6 = st.text_area("SÍ 6", "Reporte de operativos (RAP, DATAPOL, informes)", height=70)
    s7 = st.text_area("SÍ 7", "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)", height=70)
    s8 = st.text_area("SÍ 8", "Retroalimentación a la planificación preventiva", height=70)

colC, colD = st.columns(2)
with colC:
    n1 = st.text_area("NO 1", "Patrullaje rutinario y vigilancia continua", height=70)
    n2 = st.text_area("NO 2", "Registro de factores menores en RAP", height=70)
    n3 = st.text_area("NO 3", "Integración al análisis situacional", height=70)
with colD:
    t_fin = st.text_area("FIN", "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)", height=70)

# ---------- Utilidades de dibujo ----------
@dataclass
class Node:
    x: float
    y: float
    w: float
    h: float
    text: str
    shape: str  # 'rect'|'oval'|'diamond'
    fc: str
    ec: str = BLUE

def wrap(txt: str, max_chars: int) -> str:
    # Envuelve respetando saltos manuales
    parts = []
    for block in txt.split("\n"):
        parts.append(textwrap.fill(block, width=max_chars))
    return "\n".join(parts)

def draw_node(ax, n: Node, fontsize=9):
    if n.shape == "rect":
        ax.add_patch(patches.FancyBboxPatch(
            (n.x - n.w/2, n.y - n.h/2), n.w, n.h,
            boxstyle="round,pad=0.02,rounding_size=6",
            linewidth=1.8, edgecolor=n.ec, facecolor=n.fc
        ))
    elif n.shape == "oval":
        ax.add_patch(patches.Ellipse((n.x, n.y), n.w, n.h,
                                     linewidth=1.8, edgecolor=n.ec, facecolor=n.fc))
    elif n.shape == "diamond":
        vx = [(n.x, n.y + n.h/2), (n.x + n.w/2, n.y),
              (n.x, n.y - n.h/2), (n.x - n.w/2, n.y)]
        ax.add_patch(patches.Polygon(vx, closed=True, linewidth=1.8, edgecolor=n.ec, facecolor=n.fc))
    ax.text(n.x, n.y, wrap(n.text, max_chars=int(n.w/6.5)), ha="center", va="center", fontsize=fontsize, color=BLACK)

def arrow(ax, p1: Tuple[float,float], p2: Tuple[float,float], label: str = "", curve: float = 0.0, color: str = BLUE):
    style = f"arc3,rad={curve}" if curve != 0 else "arc3"
    ax.add_patch(patches.FancyArrowPatch(p1, p2, connectionstyle=style,
                                         arrowstyle="-|>", mutation_scale=12,
                                         linewidth=1.6, color=color))
    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + 2, label, color=color, fontsize=9, ha="center")

def draw_diagram() -> bytes:
    # Canvas en coordenadas "lienzo": ancho=200, alto=160 (más alto para que quepa todo)
    W, H = 200, 160
    fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

    # Columnas (x): izquierda / centro / derecha
    X_L, X_C, X_R = 50, 100, 150

    # Y de la columna central
    Y = { "inicio":150, "b1":132, "b2":114, "b3":96, "dec":78, "fin":20 }

    # Nodos centrales
    nodes = []
    nodes += [Node(X_C, Y["inicio"], 60, 16, f"INICIO\n{t_inicio}", "oval", LIGHTBLUE)]
    nodes += [Node(X_C, Y["b1"], 64, 14, b1, "rect", "#FFFFFF")]
    nodes += [Node(X_C, Y["b2"], 64, 14, b2, "rect", "#FFFFFF")]
    nodes += [Node(X_C, Y["b3"], 64, 14, b3, "rect", "#FFFFFF")]
    nodes += [Node(X_C, Y["dec"], 44, 16, q_dec, "diamond", LIGHTYELLOW)]
    nodes += [Node(X_C, Y["fin"], 66, 16, f"FIN\n{t_fin}", "oval", LIGHTBLUE)]

    # Rama SÍ (alineada a la derecha, niveles uniformes)
    YR = [70, 62, 54, 46, 38, 30, 22, 14]
    Stexts = [s1, s2, s3, s4, s5, s6, s7, s8]
    Snodes = [Node(X_R, y, 74, 14 if i != 4 else 16, Stexts[i], "rect", "#FFFFFF") for i, y in enumerate(YR)]
    nodes += Snodes

    # Rama NO (alineada a la izquierda, 3 niveles)
    YL = YR[:3]  # mismos Y de los 3 primeros de la derecha para simetría
    Ntexts = [n1, n2, n3]
    Nnodes = [Node(X_L, y, 74, 14, Ntexts[i], "rect", "#FFFFFF") for i, y in enumerate(YL)]
    nodes += Nnodes

    # Dibujo de todos los nodos
    for nd in nodes:
        draw_node(ax, nd, fontsize=9)

    # Flechas columna central
    def top(n: Node): return (n.x, n.y + n.h/2)
    def bottom(n: Node): return (n.x, n.y - n.h/2)
    def left(n: Node): return (n.x - n.w/2, n.y)
    def right(n: Node): return (n.x + n.w/2, n.y)

    n_inicio, n_b1, n_b2, n_b3, n_dec, n_fin = nodes[0:6]
    arrow(ax, bottom(n_inicio), top(n_b1))
    arrow(ax, bottom(n_b1), top(n_b2))
    arrow(ax, bottom(n_b2), top(n_b3))
    arrow(ax, bottom(n_b3), top(n_dec))

    # Decisión a ramas
    arrow(ax, right(n_dec), left(Snodes[0]), label="Sí")
    arrow(ax, left(n_dec), right(Nnodes[0]), label="No")

    # Cadena SÍ
    for a, b in zip(Snodes[:-1], Snodes[1:]):
        arrow(ax, bottom(a), top(b))

    # Cadena NO
    for a, b in zip(Nnodes[:-1], Nnodes[1:]):
        arrow(ax, bottom(a), top(b))

    # Retroalimentación (curva, de último SÍ hacia Bloque 2)
    arrow(ax, left(Snodes[-1]), right(n_b2), label="Retroalimentación", curve=0.25)

    # Cierre hacia FIN (del Bloque 2 → FIN, recto)
    arrow(ax, bottom(n_b2), top(n_fin))

    # Título y marco
    ax.text(100, 156, "Modelo Preventivo de Gestión Policial – Función de Operacionales",
            ha="center", va="center", fontsize=12, color=BLUE, weight="bold")
    ax.add_patch(patches.Rectangle((3, 3), W-6, H-8, fill=False, linewidth=1.5, edgecolor=BORDER))

    # Export a PNG bytes
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    return buf.getvalue()

def make_pdf(png_bytes: bytes) -> bytes:
    # PDF directo con matplotlib (ya es raster); usamos Pillow para convertir a PDF
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO()
    img.save(out, format="PDF")  # 1 página
    return out.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation()
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.2), Inches(0.2), width=Inches(9.6))
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()

# ---------- Render y descargas ----------
png_bytes = draw_diagram()
pdf_bytes = make_pdf(png_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, use_column_width=True)

dl1, dl2, dl3 = st.columns(3)
with dl1:
    st.download_button("⬇️ PNG", data=png_bytes, file_name="diagrama_modelo_preventivo.png", mime="image/png")
with dl2:
    st.download_button("⬇️ PDF", data=pdf_bytes, file_name="diagrama_modelo_preventivo.pdf", mime="application/pdf")
with dl3:
    st.download_button("⬇️ PPTX", data=pptx_bytes,
        file_name="diagrama_modelo_preventivo.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Tip: podés editar los textos y volver a descargar. El diseño mantiene columnas alineadas y flechas sin cruces.")

